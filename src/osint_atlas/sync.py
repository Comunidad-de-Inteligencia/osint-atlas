from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .catalog import ROOT, SOURCE_FILES, catalog_version


def _git(*args: str, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def source_age_days() -> float:
    newest = max(path.stat().st_mtime for path in SOURCE_FILES if path.exists())
    return round((datetime.now(timezone.utc).timestamp() - newest) / 86400, 2)


def try_safe_sync() -> dict[str, Any]:
    """Fast-forward a clean dedicated checkout; never merges or overwrites edits."""
    base = {
        "catalog_version": catalog_version(),
        "source_age_days": source_age_days(),
        "repository": str(ROOT),
    }
    if not (ROOT / ".git").exists():
        return {**base, "status": "local-only", "detail": "No hay metadatos Git; se usa la versión local."}
    dirty = _git("status", "--porcelain")
    if dirty.returncode or dirty.stdout.strip():
        return {**base, "status": "skipped-dirty", "detail": "Hay cambios locales; no se intentó actualizar."}
    branch = _git("branch", "--show-current").stdout.strip()
    remote = _git("remote", "get-url", "origin")
    if not branch or remote.returncode:
        return {**base, "status": "local-only", "detail": "No existe una rama con remoto origin configurado."}
    fetched = _git("fetch", "--quiet", "origin", branch)
    if fetched.returncode:
        return {**base, "status": "sync-failed", "detail": (fetched.stderr or "No se pudo consultar el remoto.").strip()[:300]}
    upstream = f"origin/{branch}"
    ancestor = _git("merge-base", "--is-ancestor", "HEAD", upstream)
    if ancestor.returncode:
        return {**base, "status": "needs-review", "detail": "La historia local y remota no permiten avance rápido."}
    merged = _git("merge", "--ff-only", upstream)
    if merged.returncode:
        return {**base, "status": "sync-failed", "detail": (merged.stderr or "No se pudo aplicar el avance rápido.").strip()[:300]}
    return {
        "catalog_version": catalog_version(),
        "source_age_days": source_age_days(),
        "repository": str(ROOT),
        "status": "updated" if "Already up to date" not in merged.stdout else "current",
        "detail": merged.stdout.strip() or "Copia actualizada.",
    }
