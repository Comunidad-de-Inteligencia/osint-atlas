"""Publish bounded, stable maintenance issues; never merge or change editorial data."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys,tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from osint_atlas.catalog import load_catalog
from osint_atlas.governance import route_review
from osint_atlas.maintenance import markdown_url


def gh(*args):
    result=subprocess.run(["gh",*args],check=True,capture_output=True,text=True,timeout=45,encoding="utf-8")
    return result.stdout


def stable_fingerprint(report,label):
    items=report.get("actionable") or report.get("due") or report.get("candidates") or []
    keys=sorted({item.get("key") or str(item.get("id"))+":"+str(item.get("reason",item.get("status"))) for item in items})
    return hashlib.sha256(json.dumps([label,keys],sort_keys=True).encode()).hexdigest()[:12]


def groups(report):
    grouped=defaultdict(list)
    items=report.get("actionable") or report.get("due") or report.get("candidates") or []
    for item in items:
        if not item.get("resolved"):
            # Keep candidates, editorial reviews and availability in different threads.
            kind="candidates" if item.get("reason")=="candidate" else item.get("kind","technical")
            grouped[(item.get("specialty","editorial"),kind)].append(item)
    return {key:sorted(value,key=lambda i:i["key"]) for key,value in grouped.items()}


def render_issue(marker,items,registry):
    lines=[marker,"","La automatización ha preparado estas observaciones. Revisar la fuente responsable antes de cambiar el catálogo.",
           "","Los cambios sensibles requieren otra persona competente. Las cuentas de bot no cuentan como revisión independiente.",""]
    for item in items:
        routing=route_review(item,registry)
        lines += [f"### {item['key']}","",f"Motivo: **{item['reason']}**. [Consultar la fuente responsable]({markdown_url(item['url'])}).",
                  f"Asignación: {routing['status']}.",""]
        if item.get("before_sha256"):
            lines += [f"Huella anterior: {item['before_sha256']}.",f"Huella observada: {item['after_sha256']}.",
                      "El texto visible cambió. Comprobar cobertura, contactos y requisitos; no hay sustitución automática.",""]
        if item.get("source_url"):
            lines += [f"[Catálogo de procedencia]({markdown_url(item['source_url'])}). {item.get('license_note','Licencia pendiente.')}",""]
    return "\n".join(lines)


def publish(report,label,registry):
    # Do not create a new issue for a changed timestamp, ETag, item order or aggregate membership.
    existing=json.loads(gh("issue","list","--state","all","--label",label,"--limit","1000","--json","number,body,state,assignees"))
    active_groups=groups(report)
    for (specialty,kind),items in active_groups.items():
        marker=f"<!-- atlas-maintenance:{label}:{specialty}:{kind} -->"
        found=next((issue for issue in existing if marker in issue["body"]),None)
        body=render_issue(marker,items,registry)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"body.md"; path.write_text(body,encoding="utf-8")
            if found:
                if found["state"]=="CLOSED":
                    # Human-closed editorial work is not reopened for identical observations.
                    hashes=[i.get("after_sha256",i["key"]) for i in items]
                    if kind!="technical" and all(value in found["body"] for value in hashes): continue
                    gh("issue","reopen",str(found["number"]))
                if found["body"]!=body:
                    gh("issue","edit",str(found["number"]),"--body-file",str(path))
                number=found["number"]
            else:
                url=gh("issue","create","--title",f"Revisar {specialty}: {kind}","--label",label,"--body-file",str(path)).strip()
                number=int(url.rsplit("/",1)[-1])
        assignees={route_review(item,registry).get("assignee") for item in items}-{None}
        # Verify live permissions before assignment, not merely registry assertions.
        for login in sorted(assignees):
            permission=json.loads(gh("api",f"repos/{os.environ['GITHUB_REPOSITORY']}/collaborators/{login}/permission"))
            if permission.get("permission") not in ("admin","maintain","write"): continue
            old={a["login"] for a in found.get("assignees",[])} if found else set()
            if login not in old: gh("issue","edit",str(number),"--add-assignee",login)
    # Only close technical issues whose *every* target has an explicit recovery.
    incidents=report.get("state",{}).get("incidents",{})
    for issue in existing:
        if issue["state"]!="OPEN" or ":technical -->" not in issue["body"]: continue
        keys=[line.removeprefix("### ") for line in issue["body"].splitlines() if line.startswith("### ")]
        if keys and all(incidents.get(k,{}).get("resolved") for k in keys):
            gh("issue","close",str(issue["number"]))


def main():
    p=argparse.ArgumentParser(); p.add_argument("report",type=Path); p.add_argument("--label",default="maintenance")
    p.add_argument("--title",default="Mantenimiento"); p.add_argument("--publish",action="store_true")
    args=p.parse_args(); report=json.loads(args.report.read_text(encoding="utf-8"))
    if not args.publish:
        print(f"Propuestas preparadas: {len(groups(report))}; publicación desactivada"); return 0
    if not os.environ.get("GITHUB_REPOSITORY"): raise ValueError("Falta repositorio autorizado")
    if os.environ["GITHUB_REPOSITORY"]!="P3M-ACTF/osint-atlas": raise ValueError("Repositorio no autorizado")
    gh("label","create",args.label,"--color","1D76DB","--description","Revisión agrupada del catálogo","--force")
    registry=load_catalog()["maintainers"]
    for person in registry["people"]:
        try:
            permission=json.loads(gh("api",f"repos/{os.environ['GITHUB_REPOSITORY']}/collaborators/{person['login']}/permission"))
            person.update(permission=permission.get("permission","unknown"),permission_checked_at=date.today().isoformat())
        except subprocess.CalledProcessError:
            person["permission"]="unknown"
    publish(report,args.label,registry)
    return 0
if __name__=="__main__": raise SystemExit(main())
