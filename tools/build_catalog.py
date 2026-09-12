#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from osint_atlas.catalog import (  # noqa: E402
    build_outputs,
    build_sqlite,
    catalog_version,
    check_outputs,
    load_catalog,
    validate_catalog,
    write_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida y genera el catálogo OSINT Atlas")
    parser.add_argument("--check", action="store_true", help="No escribe; comprueba que los generados estén al día")
    parser.add_argument("--report", action="store_true", help="Muestra un resumen de cobertura")
    args = parser.parse_args()

    catalog = load_catalog()
    errors = validate_catalog(catalog)
    version = catalog_version()
    outputs = build_outputs(catalog, version)
    if args.check:
        errors.extend(check_outputs(outputs))
        with tempfile.TemporaryDirectory() as directory:
            build_sqlite(catalog, version, Path(directory) / "catalog.sqlite")
    elif not errors:
        write_outputs(outputs)
        build_sqlite(catalog, version, ROOT / ".cache" / "catalog.sqlite")

    if args.report:
        print(f"versión ............. {version}")
        print(f"recursos ............ {len(catalog['resources'])}")
        print(f"procedimientos ...... {len(catalog['playbooks'])}")
        print(f"jurisdicciones ...... {len(catalog['jurisdictions'])}")
        critical = sum(item["criticality"] == "critica" for item in catalog["resources"])
        print(f"recursos críticos ... {critical}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: catálogo válido y sincronizado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
