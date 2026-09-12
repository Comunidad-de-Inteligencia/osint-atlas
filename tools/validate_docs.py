#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors = []
    files = [ROOT / "README.md", ROOT / "LEGAL.md", ROOT / "SECURITY.md", ROOT / "CONTRIBUTING.md", *sorted((ROOT / "docs").rglob("*.md"))]
    image = re.compile(r"!\[([^]]*)\]\(([^)]+)\)")
    link = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
    heading = re.compile(r"^(#{1,6})\s+\S")
    for path in files:
        text = path.read_text(encoding="utf-8")
        levels = [len(match.group(1)) for line in text.splitlines() if (match := heading.match(line))]
        if not levels or levels[0] != 1:
            errors.append(f"{path.relative_to(ROOT)}: falta H1 inicial")
        for previous, current in zip(levels, levels[1:]):
            if current > previous + 1:
                errors.append(f"{path.relative_to(ROOT)}: salto H{previous} a H{current}")
        for alt, _ in image.findall(text):
            if not alt.strip():
                errors.append(f"{path.relative_to(ROOT)}: imagen sin texto alternativo")
        for target in link.findall(text):
            if target.startswith(("https://", "http://", "mailto:", "#")):
                continue
            target_path = (path.parent / target.split("#", 1)[0]).resolve()
            if target.split("#", 1)[0] and not target_path.exists():
                errors.append(f"{path.relative_to(ROOT)}: enlace interno roto {target}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if not errors:
        print(f"OK: {len(files)} documentos accesibles y enlazados")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
