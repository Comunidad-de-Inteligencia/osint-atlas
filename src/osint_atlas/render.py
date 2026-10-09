from __future__ import annotations
import json
import os
import re
from pathlib import Path
from .catalog import ROOT, DATA, applies_to, coverage

GENERATED = "<!-- GENERADO: editar data/ o content/ y reconstruir con tools/build_catalog.py -->"
STATE_URL = "https://github.com/Comunidad-de-Inteligencia/osint-atlas/blob/maintenance-state/README.md"
KINDS = {"emergency":"Emergencia", "assistance":"Asistencia", "hotline":"Ayuda especializada",
         "guidance":"Orientación", "reporting":"Comunicación de indicios", "takedown":"Solicitud de retirada",
         "platform-report":"Reporte a la plataforma", "formal-complaint":"Denuncia formal"}
LANGUAGES = {"und":"desconocido", "es":"español", "de":"alemán", "en":"inglés", "it":"italiano", "fr":"francés", "pt":"portugués"}
ACCESS = {"unknown":"desconocido", "api-key":"clave de API", "open":"consulta abierta", "registration":"registro", "restricted":"restringido"}


def ficha_path(r):
    return Path("docs/es") / r["categories"][0] / f"{r['id']}.md"


def resource_link(r, from_dir):
    rel = Path(os.path.relpath(ROOT / ficha_path(r), from_dir)).as_posix()
    return f"[{r['name']}]({rel})"


def place_label(j):
    mark = (j.get("mark") or "").strip()
    return f"{mark} {j['name']}".strip() if mark else j["name"]


def contact_text(c):
    return f"[{c['name']}]({c['url']}) — **{c['value']}**"


def resolve_contacts(value, catalog):
    contacts = {c['id']: c for c in catalog['contacts']}
    if isinstance(value, str):
        return re.sub(r"\{\{contact:([^}]+)\}\}", lambda m: contact_text(contacts[m[1]]), value)
    if isinstance(value, list):
        return [resolve_contacts(v, catalog) for v in value]
    if isinstance(value, dict):
        return {k: resolve_contacts(v, catalog) for k, v in value.items()}
    return value


def review_text(item, field):
    label = {'pending':'pendiente','verified':'verificado'}[item['review_status']]
    when = item.get(field)
    checked = f"**{when}**" if when else "**pendiente**"
    return f"Estado editorial: **{label}**. Comprobado: {checked}."


def render_playbook(p, catalog):
    contacts = {c["id"]:c for c in catalog["contacts"]}
    body = (ROOT / p["source_path"]).read_text(encoding="utf-8")
    body = re.sub(r"\{\{contact:([^}]+)\}\}", lambda m: contact_text(contacts[m[1]]), body)
    heading, rest = body.split("\n", 1)
    status = "pendiente de revisión humana" if p["review_status"] == "pending" else "revisada"
    body = f"{GENERATED}\n{heading}\n\n> Guía {status}. Comprueba siempre la fuente competente.\n{rest}"
    if p["contacts"]:
        body += "\n## Vías de ayuda y comunicación\n\n"
        for cid in p["contacts"]:
            c = contacts[cid]
            body += f"- **{KINDS[c['kind']]}:** {contact_text(c)}. {c['note']}\n"
    body += "\n## Cobertura territorial y revisión\n\n"+p["territorial_limitations"]+"\n\n"+review_text(p,"last_reviewed")+"\n"
    body += "\n## Referencias responsables\n\n"+"\n".join(f"- [{r['title']}]({r['url']})" for r in p["references"])+"\n"
    return body


def jurisdiction_index(jurisdictions):
    nodes = {j["id"]: j for j in jurisdictions}
    children = {j["id"]: [] for j in jurisdictions}
    roots = []
    for j in jurisdictions:
        parent = j.get("parent")
        if parent in children:
            children[parent].append(j["id"])
        else:
            roots.append(j["id"])
    return nodes, children, roots


def territory_tree_lines(jurisdictions, href):
    nodes, children, roots = jurisdiction_index(jurisdictions)
    lines = []

    def walk(jid, depth):
        node = nodes[jid]
        lines.append(f"{'  ' * depth}- [{place_label(node)}]({href(node)})")
        for child in children[jid]:
            walk(child, depth + 1)

    for root in roots:
        walk(root, 0)
    return lines


def descendant_ids(jid, children):
    ordered = []

    def walk(current):
        for child in children[current]:
            ordered.append(child)
            walk(child)

    walk(jid)
    return ordered


def resource_markdown(r, catalog, version, state=None):
    from .maintenance import resource_check_summary
    r = resolve_contacts(r, catalog)
    names={j["id"]:place_label(j) for j in catalog["jurisdictions"]}
    contacts={c["id"]:c for c in catalog["contacts"]}
    resource_by_id={x["id"]:x for x in catalog["resources"]}
    lines=[GENERATED, f"# {r['name']}", "", "## Para qué sirve", "", r["purpose"], "",
           "## Qué necesitas", "", ", ".join(r["inputs"]) or "Una pregunta concreta y un territorio.", "",
           f"Acceso: **{ACCESS[r['access']]}**. Coste: **{r['cost']}**.",
           f"Idiomas observados: **{', '.join(LANGUAGES.get(x,x) for x in r['languages'])}**.", "",
           f"Cobertura declarada: {', '.join(names[x] for x in r['jurisdictions'])}. Consulta el estado de revisión antes de darla por validada.", "",
           "## Cómo utilizarla", "", f"Abre la [página responsable de {r['name']}]({r['url']}).",""]
    lines += [f"{i}. {step}" for i,step in enumerate(r["steps"],1)]+["","## Ejemplo ficticio","",r["example"]["input"],""]
    lines += [f"{i}. {step}" for i,step in enumerate(r["example"]["steps"],1)]
    lines += ["", "**Resultado esperado:** "+r["example"]["expected"], "",
              "## Cómo interpretar el resultado","",r["interpretation"],"", "## Limitaciones y alternativas","",r["limitations"],""]
    if r.get("coverage_exclusions"):
        lines += ["Exclusiones: "+", ".join(names[x] for x in r["coverage_exclusions"])+".",""]
    lines += ["Resultados que puede ofrecer: "+", ".join(r["outputs"])+".",""]
    if len(r["categories"]) > 1:
        lines += ["También se agrupa en: "+", ".join(r["categories"][1:])+". El archivo no se copia.",""]
    here = ROOT / ficha_path(r)
    if r["alternatives"]:
        lines += ["Fuentes complementarias; comprobar sus diferencias de cobertura:",""]+[f"- {resource_link(resource_by_id[x], here.parent)}" for x in r["alternatives"]]+[""]
    else:
        lines += ["Alternativa específica pendiente de documentar. Consulta el índice del escenario y confirma la competencia territorial.",""]
    if r.get("reporting_routes"):
        lines += ["## Asistencia o reporte",""]
        for cid in r["reporting_routes"]:
            c=contacts[cid]
            lines += [f"- **{KINDS[c['kind']]}:** {contact_text(c)}. {c['note']}"]
        lines += [""]
    lines += ["## Condiciones conocidas","",r["terms"],"", "## Procedencia y revisión","",
              f"Publicador: {r['owner']}. Procedencia declarada: {r['tier']} ({catalog['taxonomy']['authority_tiers'][r['tier']]}). No es una puntuación de veracidad.","",
              review_text(r,"editorial_reviewed"),"",
              f"Revisión prevista: cada {r['review_days']} días.","",
              f"[Consultar la disponibilidad técnica y última ejecución]({STATE_URL}). Responder en la web no implica revisión editorial.",
              resource_check_summary(r, state),"",
              "## Referencias",""]+[f"- [{v['title']}]({v['url']})" for v in r["references"]]
    for e in r["metadata_evidence"]:
        lines.append(f"- Observación de {', '.join(e['fields'])}, {e['observed_at']}: [página comprobada]({e['url']}). {e['note']} No equivale a aprobación humana.")
    lines += ["",f"Versión: {version}. [Volver al catálogo](../catalogo.md).",""]
    return "\n".join(lines)


def build_outputs(catalog, version):
    from .maintenance import load_optional_state
    outputs={}
    state=load_optional_state()
    resources=sorted(catalog["resources"],key=lambda r:r["name"].casefold())
    scenarios=catalog["scenarios"]; jurisdictions=catalog["jurisdictions"]
    nodes, children, _roots = jurisdiction_index(jurisdictions)
    playbooks={s["id"]:[p for p in catalog["playbooks"] if p["scenario"]==s["id"]] for s in scenarios}
    es = ROOT / "docs" / "es"
    indices = es / "indices"
    for r in resources:
        outputs[ROOT / ficha_path(r)] = resource_markdown(r, catalog, version, state)
    for p in catalog["playbooks"]:
        outputs[es / "procedimientos" / Path(p["path"]).name] = render_playbook(p, catalog)
    rows=[coverage(catalog,s,j["id"]) for s in scenarios for j in jurisdictions]
    index=[GENERATED,"# Catálogo de fuentes","",f"Hay {len(resources)} fichas. Los metadatos pendientes se muestran expresamente; no se presuponen gratuitos ni en español.","","## Qué necesito hacer",""]
    index += [f"- [{s['name']}](indices/escenario-{s['id']}.md)" for s in scenarios]
    index += ["","## En qué territorio",""]+territory_tree_lines(jurisdictions, lambda j: f"indices/jurisdiccion-{j['id'].lower()}.md")
    index += ["","## Qué información tengo",""]
    for input_type in catalog["taxonomy"]["input_types"]:
        index.append(f"- [{input_type.replace('-',' ').capitalize()}](indices/entrada-{input_type}.md)")
        matching=[r for r in resources if input_type in r["input_types"]]
        outputs[indices / f"entrada-{input_type}.md"]="\n".join([GENERATED,f"# Partir de: {input_type.replace('-',' ')}","","Selecciona una fuente y comprueba territorio, límites y resultados esperados.",""]+[f"- {resource_link(r, indices)} — {r['purpose']}" for r in matching]+[""])
    outputs[es / "catalogo.md"]="\n".join(index+[""])
    for s in scenarios:
        matching=[r for r in resources if s["id"] in r["scenarios"]]
        lines=[GENERATED,f"# {s['name']}","",s["description"],"","## Procedimientos",""]
        lines += [f"- [{p['title']}](../procedimientos/{Path(p['path']).name})" for p in playbooks[s["id"]]]
        for j in jurisdictions:
            direct=[r for r in matching if j["id"] in r["jurisdictions"]]
            if direct:
                lines += ["",f"## {place_label(j)}",""]+[f"- {resource_link(r, indices)} — {r['purpose']}" for r in direct]
        lines += ["","[Comprobar cobertura y carencias](../cobertura.md)",""]
        outputs[indices / f"escenario-{s['id']}.md"]="\n".join(lines)
    for j in jurisdictions:
        lines=[GENERATED,f"# {place_label(j)}","",j.get("notes","La adaptación territorial sigue pendiente."),"","## Cobertura por escenario",""]
        for s in scenarios:
            row=next(x for x in rows if x["scenario"]==s["id"] and x["jurisdiction"]==j["id"])
            checked = row["last_reviewed"] or "pendiente"
            lines += [f"### {s['name']}","",f"Estado: **{row['status']}**. Fuentes locales: {row['local_resources']}; apoyo general: {row['general_resources']}.",
                      f"Comprobado: {checked}.","",]
            lines += [f"- {g}" for g in row["gaps"]]
            lines += ["",f"[Ver fuentes de este escenario](escenario-{s['id']}.md)",""]
        direct=[r for r in resources if j["id"] in r["jurisdictions"]]
        lines += ["## Fuentes del territorio",""]+[f"- {resource_link(r, indices)}" for r in direct]+[""]
        finer=[]
        for did in descendant_ids(j["id"], children):
            matching=[r for r in resources if did in r["jurisdictions"]]
            if matching:
                finer += [f"### {place_label(nodes[did])}",""]+[f"- {resource_link(r, indices)}" for r in matching]+[""]
        if finer:
            lines += ["## Fuentes de un territorio más concreto","","Una ficha municipal o autonómica también se lista aquí, además de en su propia página.","",*finer]
        support=[r for r in resources if j["id"] not in r["jurisdictions"] and applies_to(r,j["id"],jurisdictions)]
        lines += ["## Apoyo de otras coberturas",""]+[f"- {resource_link(r, indices)}" for r in support]+[""]
        outputs[indices / f"jurisdiccion-{j['id'].lower()}.md"]="\n".join(lines)
    matrix=[GENERATED,"# Matriz de cobertura","","La cantidad de enlaces no acredita que un territorio esté preparado.","",
            "- **Pendiente:** falta una base local revisada.",
            "- **Inicial:** existen fuentes locales revisadas; faltan procedimiento, responsable o vías competentes.",
            "- **Desarrollado:** todos esos requisitos están documentados y revisados.",
            "","El apoyo global no cuenta como adaptación territorial. Una revisión editorial no es la comprobación de que la página responda.","","## Consultar por territorio",""]
    matrix += territory_tree_lines(jurisdictions, lambda j: f"indices/jurisdiccion-{j['id'].lower()}.md")
    outputs[es / "cobertura.md"]="\n".join(matrix+[""])
    outputs[es / "procedimientos" / "README.md"]="\n".join([GENERATED,"# Procedimientos","","Cada guía incluye recorrido de práctica, límites, fuentes y estado de revisión.",""]+[f"- [{p['title']}]({Path(p['path']).name}) — {p['review_status']}" for p in catalog["playbooks"]]+[""])
    lines=[GENERATED,"# Contactos y rutas de asistencia","","Comprueba la página responsable. Ayuda, comunicación de indicios, retirada y denuncia son vías diferentes.",""]
    for c in catalog["contacts"]:
        lines += [f"## {c['name']}","",f"**{KINDS[c['kind']]}**. Territorios: {', '.join(c['territories'])}.", "",
                  contact_text(c)+". "+c["note"],"",f"Requisitos: {c['requirements']}",f"Accesibilidad: {c['accessibility']}","",review_text(c,"last_reviewed"),""]
    outputs[es / "contactos.md"]="\n".join(lines)
    for name,value in {"catalog":{"version":version,**catalog},"coverage":{"version":version,"coverage":rows},
                       "search-index":{"version":version,"resources":[{"id":r["id"],"name":r["name"],"text":" ".join([r["purpose"],r["usage"],*r["inputs"],*r["outputs"]]),"url":r["url"]} for r in resources]}}.items():
        outputs[DATA/"export"/f"{name}.json"]=json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    return {path: text.rstrip() + "\n" for path, text in outputs.items()}
