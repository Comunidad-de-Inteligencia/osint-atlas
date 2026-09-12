from __future__ import annotations

import argparse
import json

from . import service


def main() -> None:
    parser = argparse.ArgumentParser(description="Consulta local de OSINT Atlas")
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search", help="Buscar recursos")
    search.add_argument("query", nargs="?", default="")
    search.add_argument("--jurisdiction")
    search.add_argument("--scenario")
    search.add_argument("--category")
    get = sub.add_parser("get", help="Abrir una ficha")
    get.add_argument("resource_id")
    args = parser.parse_args()
    if args.command == "search":
        result = service.search_resources(args.query, args.jurisdiction, args.category, args.scenario)
    else:
        result = service.get_resource(args.resource_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
