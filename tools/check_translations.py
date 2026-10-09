"""Compara la huella de cada par de idioma. No traduce ni rellena el otro archivo."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def fingerprint(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def pending(root: Path = ROOT) -> list[str]:
    spec_path = root / "docs" / "i18n-pares.yaml"
    if not spec_path.is_file():
        return ["falta docs/i18n-pares.yaml"]
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    errors = []
    for pair in spec.get("pairs") or []:
        es_rel = pair["es"]
        en_rel = pair["en"]
        es_path = root / es_rel
        en_path = root / en_rel
        if not es_path.is_file():
            errors.append(f"falta el archivo: {es_rel}")
            continue
        if not en_path.is_file():
            errors.append(f"falta el archivo: {en_rel}")
            continue
        es_ok = fingerprint(es_path) == pair.get("es_sha256")
        en_ok = fingerprint(en_path) == pair.get("en_sha256")
        if es_ok and en_ok:
            continue
        if not es_ok and en_ok:
            errors.append(f"traducción pendiente: {en_rel}")
        elif es_ok and not en_ok:
            errors.append(f"traducción pendiente: {es_rel}")
        else:
            errors.append(f"huella pendiente: {es_rel} y {en_rel}")
    return errors


def main() -> int:
    errors = pending()
    for error in errors:
        print("ERROR: " + error, file=sys.stderr)
    if not errors:
        print("OK: pares de idioma al día")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
