#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def stable_fingerprint(report: dict, label: str) -> str:
    actionable = report.get("actionable") or report.get("due") or report.get("candidates") or report.get("items") or report
    if isinstance(actionable, list):
        actionable = [
            {key: value for key, value in item.items() if key not in {"checked_at", "generated_at", "duration_ms"}}
            if isinstance(item, dict) else item
            for item in actionable
        ]
    stable = json.dumps({"label": label, "actionable": actionable}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(stable.encode()).hexdigest()[:12]


def main() -> int:
    parser = argparse.ArgumentParser(description="Publica una incidencia agrupada si un informe requiere acción")
    parser.add_argument("report", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--label", default="maintenance")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    if not report.get("action_required"):
        print("Sin acciones pendientes")
        return 0
    if not os.environ.get("GITHUB_ACTIONS"):
        print("Fuera de GitHub Actions: informe preparado, no se publica ninguna incidencia")
        return 0
    normalized = json.dumps(report, ensure_ascii=False, sort_keys=True)
    # Las fechas y métricas cambian en cada ejecución. La identidad de una
    # incidencia depende solo de los elementos que todavía requieren acción.
    fingerprint = stable_fingerprint(report, args.label)
    marker = f"<!-- maintenance:{args.label}:{fingerprint} -->"
    existing = subprocess.run(["gh", "issue", "list", "--state", "open", "--label", args.label, "--search", marker, "--json", "number", "--limit", "1"], check=True, capture_output=True, text=True)
    if json.loads(existing.stdout):
        print("Ya existe una incidencia para este informe")
        return 0
    summary = f"{marker}\n\nLa automatización detectó cambios que requieren revisión humana.\n\n```json\n{normalized[:50000]}\n```\n"
    subprocess.run(["gh", "issue", "create", "--title", args.title, "--label", args.label, "--body", summary], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
