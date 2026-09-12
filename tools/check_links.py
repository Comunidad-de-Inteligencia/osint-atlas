#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from osint_atlas.catalog import generated_timestamp, load_catalog  # noqa: E402

USER_AGENT = "OSINT-Atlas-LinkCheck/0.1 (+private-catalog-maintenance)"


def classify(code: int | None, error: str | None) -> str:
    if code is not None and 200 <= code < 300:
        return "ok"
    if code is not None and 300 <= code < 400:
        return "redirected"
    if code in (401, 403):
        return "auth-required"
    if code == 429:
        return "rate-limited"
    if code is not None and 500 <= code < 600:
        return "temporary-error"
    if code in (404, 410):
        return "offline"
    return "temporary-error" if error else "unknown"


def check(resource: dict, timeout: float) -> dict:
    request = urllib.request.Request(resource["url"], headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/json;q=0.8,*/*;q=0.5"})
    code = None
    final_url = resource["url"]
    error = None
    digest = None
    etag = None
    modified = None
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            code = response.status
            final_url = response.geturl()
            etag = response.headers.get("ETag")
            modified = response.headers.get("Last-Modified")
            body = response.read(65536)
            digest = hashlib.sha256(body).hexdigest()
    except urllib.error.HTTPError as exc:
        code = exc.code
        final_url = exc.geturl()
        error = str(exc.reason)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        error = str(exc)[:300]
    status = classify(code, error)
    if status == "ok" and final_url.rstrip("/") != resource["url"].rstrip("/"):
        status = "redirected"
    return {
        "id": resource["id"], "url": resource["url"], "final_url": final_url,
        "http_status": code, "status": status, "error": error,
        "etag": etag, "last_modified": modified, "content_prefix_sha256": digest,
        "duration_ms": round((time.monotonic() - started) * 1000),
        "checked_at": generated_timestamp(), "criticality": resource["criticality"],
    }


def check_group(resources: list[dict], timeout: float, delay: float) -> list[dict]:
    results = []
    for index, resource in enumerate(resources):
        if index:
            time.sleep(delay)
        results.append(check(resource, timeout))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Comprueba URLs aprobadas sin modificar su contenido editorial")
    parser.add_argument("--scope", choices=("critical", "all"), default="all")
    parser.add_argument("--timeout", type=float, default=12)
    parser.add_argument("--delay", type=float, default=0.75)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "link-health.json")
    args = parser.parse_args()
    resources = load_catalog()["resources"]
    if args.scope == "critical":
        resources = [item for item in resources if item["criticality"] in ("alta", "critica")]
    groups: dict[str, list[dict]] = {}
    for resource in resources:
        groups.setdefault(urlsplit(resource["url"]).netloc.casefold(), []).append(resource)
    results = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8))) as executor:
        futures = [executor.submit(check_group, group, args.timeout, args.delay) for group in groups.values()]
        for future in as_completed(futures):
            results.extend(future.result())
    results.sort(key=lambda item: item["id"])
    actionable = [item for item in results if item["status"] in ("offline", "auth-required", "rate-limited")]
    report = {"generated_at": generated_timestamp(), "scope": args.scope, "total": len(results), "actionable_count": len(actionable), "action_required": bool(actionable), "actionable": actionable, "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Comprobadas {len(results)} URLs; {len(actionable)} requieren revisión")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
