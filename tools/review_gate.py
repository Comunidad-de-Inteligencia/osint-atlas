"""Run from the trusted base checkout. Never execute PR code."""
from __future__ import annotations
import argparse,base64,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from osint_atlas.governance import classify_changes,review_decision


def api(endpoint,method="GET",payload=None):
    command=["gh","api",endpoint,"--method",method]
    if payload is not None: command+=["--input","-"]
    result=subprocess.run(command,input=json.dumps(payload) if payload is not None else None,capture_output=True,text=True,encoding="utf-8",check=True,timeout=45)
    return json.loads(result.stdout)


def pages(endpoint):
    items=[];page=1
    while True:
        result=api(endpoint+("?" if "?" not in endpoint else "&")+f"per_page=100&page={page}")
        items+=result
        if len(result)<100: return items
        page+=1


def evaluate(repo,number,publish=False):
    pr=api(f"repos/{repo}/pulls/{number}")
    data=api(f"repos/{repo}/contents/data/export/catalog.json?ref={pr['base']['sha']}")
    catalog=json.loads(base64.b64decode(data["content"]))
    paths=[f["filename"] for f in pages(f"repos/{repo}/pulls/{number}/files")]
    sensitive,specialties=classify_changes(paths,catalog)
    registry=catalog["maintainers"]
    registry.setdefault("people",[])  # v0.1 contains no independently verified reviewer.
    # Refresh actual permissions in memory; only the base registry grants competence.
    for person in registry["people"]:
        try:
            permission=api(f"repos/{repo}/collaborators/{person['login']}/permission")
            person["permission"]=permission.get("permission","unknown")
            from datetime import date
            person["permission_checked_at"]=date.today().isoformat()
        except subprocess.CalledProcessError:
            person["permission"]="unknown"
    reviews=pages(f"repos/{repo}/pulls/{number}/reviews")
    result=review_decision(pr["user"]["login"],pr["user"]["type"],pr["head"]["sha"],reviews,registry,specialties,sensitive)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if publish:
        api(f"repos/{repo}/statuses/{pr['head']['sha']}","POST",{
            "state":"success" if result["approved"] else "pending","context":"Revisión independiente",
            "description":"Revisión humana válida" if result["approved"] else "Falta revisión humana competente de esta versión",
            "target_url":pr["html_url"]})
    return result


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--pr",type=int,required=True)
    parser.add_argument("--repo",default="P3M-ACTF/osint-atlas"); parser.add_argument("--publish",action="store_true")
    args=parser.parse_args()
    if args.repo!="P3M-ACTF/osint-atlas": raise ValueError("Repositorio no autorizado")
    evaluate(args.repo,args.pr,args.publish)
if __name__=="__main__": main()
