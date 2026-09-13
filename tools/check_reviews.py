from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from datetime import date,timedelta
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from osint_atlas.catalog import load_catalog,generated_timestamp
from osint_atlas.governance import route_review


def due_reviews(catalog,as_of):
    due=[]; scenarios={s["id"]:s for s in catalog["scenarios"]}
    for group,field in [("resources","editorial_reviewed"),("playbooks","last_reviewed"),("contacts","last_reviewed")]:
        for item in catalog[group]:
            reviewed=item[field]
            deadline=date.fromisoformat(reviewed)+timedelta(days=item["review_days"]) if reviewed else date.fromisoformat(item["created_at"])
            if item["review_status"]!="verified" or deadline<=as_of:
                scenario_ids=item.get("scenarios",[item.get("scenario")])
                specialties=sorted({scenarios[s]["specialty"] for s in scenario_ids if s in scenarios}) or ["editorial"]
                for specialty in specialties:
                    entry={"key":f"review:{group}:{item['id']}:{specialty}","kind":"editorial","id":item["id"],
                           "url":item.get("url",f"https://github.com/P3M-ACTF/osint-atlas/blob/main/{item.get('path','')}"),
                           "specialty":specialty,"critical":group=="contacts" or item.get("criticality") in ("alta","critica") or any(scenarios[s].get("sensitive") for s in scenario_ids if s in scenarios),
                           "reason":"unreviewed" if not reviewed else "review-overdue","opened_at":deadline.isoformat()+"T00:00:00+00:00","resolved":False}
                    entry["routing"]=route_review(entry,catalog["maintainers"])
                    due.append(entry)
    return due


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--as-of",type=date.fromisoformat,default=date.today())
    p.add_argument("--output",type=Path,default=ROOT/"reports/stale-reviews.json")
    args=p.parse_args(); due=due_reviews(load_catalog(),args.as_of)
    report={"generated_at":generated_timestamp(),"action_required":bool(due),"due_count":len(due),"due":due}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Revisiones pendientes: {len(due)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
