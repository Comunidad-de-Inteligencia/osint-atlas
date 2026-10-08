from __future__ import annotations
import argparse,base64,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from osint_atlas.maintenance import read_state,dashboard
REPO=os.environ.get("GITHUB_REPOSITORY","Comunidad-de-Inteligencia/osint-atlas")
BRANCH="maintenance-state"


def api(path,method="GET",payload=None,optional=False):
    cmd=["gh","api",f"repos/{REPO}/{path}","--method",method]
    if payload is not None: cmd+=["--input","-"]
    result=subprocess.run(cmd,input=json.dumps(payload) if payload is not None else None,capture_output=True,text=True,encoding="utf-8",timeout=45)
    if result.returncode:
        if optional and "404" in result.stderr:return None
        raise RuntimeError(result.stderr[:400])
    return json.loads(result.stdout) if result.stdout.strip() else {}


def publish_state(path):
    if REPO not in {"Comunidad-de-Inteligencia/osint-atlas","P3M-ACTF/osint-atlas"}: raise ValueError("Repositorio no autorizado")
    state=read_state(path)
    if not state["processes"]: raise ValueError("No se publican estados sin ninguna ejecución")
    previous=api(f"git/ref/heads/{BRANCH}",optional=True)
    parent=previous["object"]["sha"] if previous else None
    tree=[]
    for name,body in {"state.json":json.dumps(state,ensure_ascii=False,sort_keys=True,indent=2)+"\n","README.md":dashboard(state)}.items():
        blob=api("git/blobs","POST",{"content":body,"encoding":"utf-8"})
        tree.append({"path":name,"mode":"100644","type":"blob","sha":blob["sha"]})
    # A fresh tree deliberately contains only the two approved output paths.
    created_tree=api("git/trees","POST",{"tree":tree})
    commit=api("git/commits","POST",{"message":"Actualizar comprobaciones técnicas del catálogo","tree":created_tree["sha"],"parents":[parent] if parent else []})
    if previous:
        api(f"git/refs/heads/{BRANCH}","PATCH",{"sha":commit["sha"],"force":False})
    else:
        api("git/refs","POST",{"ref":f"refs/heads/{BRANCH}","sha":commit["sha"]})
    print(f"Estado técnico publicado en {BRANCH}: {commit['sha']}")
    return commit["sha"]


def main():
    p=argparse.ArgumentParser(); p.add_argument("state",type=Path); p.add_argument("--publish",action="store_true")
    args=p.parse_args()
    if args.publish: publish_state(args.state)
    else: print(dashboard(read_state(args.state)))
if __name__=="__main__": main()
