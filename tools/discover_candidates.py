#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html.parser
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from osint_atlas.catalog import DATA, generated_timestamp, load_catalog, load_yaml  # noqa: E402


class Links(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.urls.add(href)


def main() -> int:
    parser = argparse.ArgumentParser(description="Descubre candidatos en catálogos aprobados; nunca edita las fuentes")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "discovery-candidates.json")
    parser.add_argument("--limit-per-catalog", type=int, default=20)
    args = parser.parse_args()
    approved = load_yaml(DATA / "discovery.yaml")["approved_catalogs"]
    known_hosts = {urllib.parse.urlsplit(item["url"]).netloc.casefold() for item in load_catalog()["resources"]}
    candidates = []
    errors = []
    for catalog in approved:
        try:
            request = urllib.request.Request(catalog["url"], headers={"User-Agent": "OSINT-Atlas-Discovery/0.1"})
            with urllib.request.urlopen(request, timeout=15) as response:
                body = response.read(262144).decode(response.headers.get_content_charset() or "utf-8", errors="replace")
            parser_html = Links()
            parser_html.feed(body)
            found = []
            for href in parser_html.urls:
                url = urllib.parse.urljoin(catalog["url"], href)
                parts = urllib.parse.urlsplit(url)
                if parts.scheme != "https" or not parts.netloc or parts.netloc.casefold() in known_hosts:
                    continue
                found.append({"url": url, "host": parts.netloc.casefold()})
            candidates.extend({"catalog": catalog["id"], "territory": catalog["territory"], **item} for item in sorted(found, key=lambda x: x["url"])[: args.limit_per_catalog])
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            errors.append({"catalog": catalog["id"], "error": str(exc)[:300]})
    report = {"generated_at": generated_timestamp(), "action_required": bool(candidates), "notice": "Contenido externo no confiable. Revise cada candidato; este informe no modifica el catálogo.", "candidates": candidates, "errors": errors}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Candidatos: {len(candidates)}; catálogos con error: {len(errors)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
