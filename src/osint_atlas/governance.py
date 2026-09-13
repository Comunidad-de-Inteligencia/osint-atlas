"""Review routing and approval decisions, using the trusted base registry."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone


def eligible(person,specialty,now=None):
    now=now or datetime.now(timezone.utc)
    checked=person.get("permission_checked_at")
    if not checked: return False
    try: fresh=0<=(now.date()-datetime.fromisoformat(checked).date()).days<=30
    except ValueError: return False
    return (person.get("kind")=="human" and person.get("permission") in {"admin","maintain","write"}
            and specialty in person.get("specialties",[]) and fresh)


def route_review(item,registry,now=None):
    now=now or datetime.now(timezone.utc)
    specialty=item.get("specialty","editorial")
    spec=next((s for s in registry["specialties"] if s["id"]==specialty),None)
    people={p["login"]:p for p in registry.get("people",[])}
    opened=datetime.fromisoformat(item["opened_at"].replace("Z","+00:00"))
    threshold=timedelta(hours=48) if item.get("critical") else timedelta(days=7)
    escalated=now-opened>=threshold
    candidate=(spec.get("backup") if escalated else spec.get("primary")) if spec else None
    if candidate and eligible(people.get(candidate,{}),specialty,now):
        return {"assignee":candidate,"status":"backup" if escalated else "primary","escalated":escalated}
    primary=spec.get("primary") if spec else None
    if escalated and primary and eligible(people.get(primary,{}),specialty,now):
        return {"assignee":primary,"status":"missing-backup","escalated":True}
    return {"assignee":None,"status":"missing-reviewer","escalated":escalated,"coordinator":registry["default_owner"]}


def review_decision(author,author_type,head_sha,reviews,registry,specialties,sensitive,now=None):
    now=now or datetime.now(timezone.utc)
    people={p["login"]:p for p in registry.get("people",[])}
    human_author=author if author_type=="User" else registry["default_owner"]
    latest={}
    for review in sorted(reviews,key=lambda r:r.get("submitted_at") or ""):
        # A comment does not invalidate a preceding approval.
        if review.get("state") in {"APPROVED","CHANGES_REQUESTED","DISMISSED"}:
            latest[review["user"]["login"]]=review
    approved=[]
    for login,review in latest.items():
        if login==human_author or review["user"].get("type")!="User": continue
        if review.get("state")!="APPROVED" or review.get("commit_id")!=head_sha: continue
        if sensitive and login==registry["default_owner"] and author_type!="User": continue
        approved.append(login)
    missing=[specialty for specialty in specialties if not any(eligible(people.get(login,{}),specialty,now) for login in approved)]
    objections=[login for login,review in latest.items() if review.get("state")=="CHANGES_REQUESTED"
                and any(eligible(people.get(login,{}),specialty,now) for specialty in specialties)]
    # Ordinary editorial/code work still requires a different human with write permissions.
    if not sensitive:
        valid=[login for login in approved if people.get(login,{}).get("permission") in {"admin","maintain","write"}
               and people.get(login,{}).get("kind")=="human"]
        missing=[] if valid else ["independent-human"]
    return {"approved":not missing and not objections,"missing_specialties":missing,"reviewers":approved,"changes_requested_by":objections,
            "head_sha":head_sha,"sensitive":sensitive,"human_author":human_author}


def classify_changes(paths,catalog):
    scenarios={s["id"]:s for s in catalog["scenarios"]}
    sensitive=False; specialties=set()
    resources={r["id"]:r for r in catalog["resources"]}
    for path in paths:
        if path.startswith(("data/contacts","data/playbooks","content/procedimientos/","docs/procedimientos/","data/resolutions")):
            sensitive=True
            specialties|={"safeguarding","geoint","cyber","legal"}
        elif path.startswith(("data/maintainers","data/scenarios",".github/","tools/review_gate","src/osint_atlas/governance")):
            sensitive=True; specialties.add("editorial")
        elif path.startswith(("data/resources/","docs/fuentes/")):
            rid=path.rsplit("/",1)[-1].rsplit(".",1)[0]
            affected=[resources[rid]] if rid in resources else list(resources.values())
            for resource in affected:
                for sid in resource["scenarios"]:
                    s=scenarios[sid]
                    specialties.add(s["specialty"])
                    sensitive=sensitive or s.get("sensitive",sid in {"missing-adult","missing-child","immediate-emergency","disaster-crisis","grooming-sextortion","sexual-digital-violence","csam-report","platform-report","legal-claim"})
        elif path in {"LEGAL.md","SECURITY.md"}:
            sensitive=True; specialties.add("legal")
    return sensitive,sorted(specialties or {"editorial"})
