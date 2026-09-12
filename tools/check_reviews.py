#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from osint_atlas.catalog import generated_timestamp, load_catalog  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Detecta revisiones editoriales vencidas")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "stale-reviews.json")
    args = parser.parse_args()
    catalog = load_catalog()
    due = []
    for resource in catalog["resources"]:
        reviewed = date.fromisoformat(resource["editorial_reviewed"])
        deadline = reviewed + timedelta(days=resource["review_days"])
        if deadline <= args.as_of:
            due.append({"kind": "resource", "id": resource["id"], "deadline": deadline.isoformat(), "criticality": resource["criticality"], "scenarios": resource["scenarios"]})
    for playbook in catalog["playbooks"]:
        reviewed = date.fromisoformat(playbook["last_reviewed"])
        deadline = reviewed + timedelta(days=playbook["review_days"])
        if deadline <= args.as_of:
            due.append({"kind": "playbook", "id": playbook["id"], "deadline": deadline.isoformat(), "criticality": "critica" if playbook["review_days"] <= 30 else "normal", "scenarios": [playbook["scenario"]]})
    for contact in catalog["contacts"]:
        reviewed = date.fromisoformat(contact["last_reviewed"])
        deadline = reviewed + timedelta(days=30)
        if deadline <= args.as_of:
            due.append({"kind": "contact", "id": contact["id"], "deadline": deadline.isoformat(), "criticality": "critica", "scenarios": []})
    report = {"generated_at": generated_timestamp(), "as_of": args.as_of.isoformat(), "action_required": bool(due), "due_count": len(due), "due": sorted(due, key=lambda item: (item["deadline"], item["id"]))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Revisiones vencidas: {len(due)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
