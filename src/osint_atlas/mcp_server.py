from __future__ import annotations

import json
import sys
from typing import Any

from mcp.server import MCPServer

from . import service

mcp = MCPServer("OSINT Atlas")


def _result(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


@mcp.tool()
def search_resources(query: str = "", jurisdiction: str | None = None, category: str | None = None, scenario: str | None = None, access: str | None = None, limit: int = 20, offset: int = 0, input_type: str | None = None, output_type: str | None = None, platform: str | None = None) -> str:
    """Busca fuentes OSINT por texto y filtros. No consulta las fuentes externas."""
    return _result(service.search_resources(query, jurisdiction, category, scenario, access, limit, offset, input_type, output_type, platform))


@mcp.tool()
def get_resource(resource_id: str) -> str:
    """Devuelve una ficha completa y sus rutas de asistencia resueltas."""
    return _result(service.get_resource(resource_id))


@mcp.tool()
def get_jurisdiction(jurisdiction_id: str, limit: int = 20, offset: int = 0) -> str:
    """Devuelve particularidades y recursos aplicables de una jurisdicción."""
    return _result(service.get_jurisdiction(jurisdiction_id, limit, offset))


@mcp.tool()
def search_playbooks(query: str = "", scenario: str | None = None, limit: int = 20, offset: int = 0, jurisdiction: str | None = None) -> str:
    """Busca procedimientos por texto o escenario."""
    return _result(service.search_playbooks(query, scenario, limit, offset, jurisdiction))


@mcp.tool()
def get_playbook(playbook_id: str) -> str:
    """Devuelve el procedimiento completo solicitado."""
    return _result(service.get_playbook(playbook_id))


@mcp.tool()
def search_docs(query: str = "", limit: int = 20, offset: int = 0) -> str:
    """Busca explicaciones dentro de la documentación indexada."""
    return _result(service.search_docs(query, limit, offset))


@mcp.tool()
def get_doc(doc_id: str) -> str:
    """Devuelve una guía o procedimiento por identificador."""
    return _result(service.get_doc(doc_id))


@mcp.tool()
def list_scenarios(jurisdiction: str | None = None) -> str:
    """Lista escenarios, cobertura y lagunas, opcionalmente por territorio."""
    return _result(service.list_scenarios(jurisdiction))


@mcp.tool()
def get_reporting_routes(scenario: str, jurisdiction: str, platform: str | None = None, kind: str | None = None) -> str:
    """Recupera vías oficiales de ayuda o reporte; no envía comunicaciones."""
    return _result(service.get_reporting_routes(scenario, jurisdiction, platform, kind))


def main() -> None:
    service.ensure_database()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
