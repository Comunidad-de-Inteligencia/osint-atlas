from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from .catalog import ROOT, applies_to, build_sqlite, catalog_version, database_is_current, load_catalog
from .sync import source_age_days

DEFAULT_DB = ROOT / ".cache" / "catalog.sqlite"


def _metadata(version: str) -> dict[str, Any]:
    return {"catalog_version": version, "source_age_days": source_age_days()}


def ensure_database(path: Path = DEFAULT_DB) -> tuple[Path, str]:
    version = catalog_version()
    if not database_is_current(path, version):
        catalog = load_catalog()
        build_sqlite(catalog, version, path)
    return path, version


def _fts_query(text: str) -> str:
    tokens = re.findall(r"[\wÀ-ÿ-]+", text, flags=re.UNICODE)
    return " AND ".join(f'"{token.replace(chr(34), "")}"*' for token in tokens)


def search_resources(
    query: str = "",
    jurisdiction: str | None = None,
    category: str | None = None,
    scenario: str | None = None,
    access: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    limit = max(1, min(limit, 100))
    path, version = ensure_database()
    catalog = load_catalog()
    if query.strip():
        sql = "SELECT r.payload, bm25(resource_fts) AS rank FROM resource_fts JOIN resources r ON r.id=resource_fts.id WHERE resource_fts MATCH ? ORDER BY rank LIMIT ?"
        params: tuple[Any, ...] = (_fts_query(query), 1000)
    else:
        sql = "SELECT payload, 0 AS rank FROM resources ORDER BY name LIMIT ?"
        params = (1000,)
    with sqlite3.connect(path) as connection:
        rows = connection.execute(sql, params).fetchall()
    results = []
    for payload, rank in rows:
        item = json.loads(payload)
        if jurisdiction and not applies_to(item, jurisdiction, catalog["jurisdictions"]):
            continue
        if category and category not in item["categories"]:
            continue
        if scenario and scenario not in item["scenarios"]:
            continue
        if access and item["access"] != access:
            continue
        results.append({**item, "rank": rank, "catalog_version": version, "source_file": "data/resources/core.yaml"})
        if len(results) >= limit:
            break
    return {**_metadata(version), "count": len(results), "results": results}


def get_resource(resource_id: str) -> dict[str, Any]:
    path, version = ensure_database()
    with sqlite3.connect(path) as connection:
        row = connection.execute("SELECT payload FROM resources WHERE id=?", (resource_id,)).fetchone()
    if not row:
        return {**_metadata(version), "found": False, "id": resource_id}
    item = json.loads(row[0])
    contacts = {entry["id"]: entry for entry in load_catalog()["contacts"]}
    item["resolved_reporting_routes"] = [contacts[rid] for rid in item.get("reporting_routes", [])]
    return {**_metadata(version), "found": True, "source_file": "data/resources/core.yaml", "resource": item}


def get_jurisdiction(jurisdiction_id: str) -> dict[str, Any]:
    path, version = ensure_database()
    with sqlite3.connect(path) as connection:
        row = connection.execute("SELECT payload FROM jurisdictions WHERE id=?", (jurisdiction_id,)).fetchone()
    if not row:
        return {**_metadata(version), "found": False, "id": jurisdiction_id}
    resources = search_resources(jurisdiction=jurisdiction_id, limit=200)["results"]
    return {**_metadata(version), "found": True, "jurisdiction": json.loads(row[0]), "resource_count": len(resources), "resources": [{"id": r["id"], "name": r["name"], "scenarios": r["scenarios"]} for r in resources]}


def search_playbooks(query: str = "", scenario: str | None = None, limit: int = 20) -> dict[str, Any]:
    limit = max(1, min(limit, 100))
    path, version = ensure_database()
    with sqlite3.connect(path) as connection:
        if query.strip():
            rows = connection.execute("SELECT p.payload, p.content, bm25(docs_fts) FROM docs_fts JOIN playbooks p ON p.id=docs_fts.id WHERE docs_fts MATCH ? ORDER BY bm25(docs_fts) LIMIT ?", (_fts_query(query), limit)).fetchall()
        else:
            rows = connection.execute("SELECT payload, content, 0 FROM playbooks ORDER BY title LIMIT ?", (limit,)).fetchall()
    results = []
    for payload, content, rank in rows:
        item = json.loads(payload)
        if scenario and item["scenario"] != scenario:
            continue
        results.append({**item, "summary": content.split("\n\n", 2)[1] if "\n\n" in content else content[:240], "rank": rank})
    return {**_metadata(version), "count": len(results), "results": results}


def get_playbook(playbook_id: str) -> dict[str, Any]:
    path, version = ensure_database()
    with sqlite3.connect(path) as connection:
        row = connection.execute("SELECT payload, content FROM playbooks WHERE id=?", (playbook_id,)).fetchone()
    if not row:
        return {**_metadata(version), "found": False, "id": playbook_id}
    return {**_metadata(version), "found": True, "playbook": json.loads(row[0]), "content": row[1]}


def search_docs(query: str, limit: int = 20) -> dict[str, Any]:
    path, version = ensure_database()
    if not query.strip():
        return {**_metadata(version), "count": 0, "results": []}
    with sqlite3.connect(path) as connection:
        rows = connection.execute("SELECT id, title, snippet(docs_fts, 2, '[', ']', ' … ', 24), bm25(docs_fts) FROM docs_fts WHERE docs_fts MATCH ? ORDER BY bm25(docs_fts) LIMIT ?", (_fts_query(query), limit)).fetchall()
    return {**_metadata(version), "count": len(rows), "results": [{"id": rid, "title": title, "snippet": snippet, "rank": rank} for rid, title, snippet, rank in rows]}


def get_doc(doc_id: str) -> dict[str, Any]:
    playbook = get_playbook(doc_id)
    if playbook.get("found"):
        return {**_metadata(playbook["catalog_version"]), "found": True, "id": doc_id, "content": playbook["content"], "source_file": playbook["playbook"]["path"]}
    docs = {"readme": ROOT / "README.md", "empezar": ROOT / "docs" / "EMPEZAR.md", "ia": ROOT / "docs" / "IA.md", "glosario": ROOT / "docs" / "GLOSARIO.md", "contribuir": ROOT / "CONTRIBUTING.md", "legal": ROOT / "LEGAL.md"}
    path = docs.get(doc_id)
    version = catalog_version()
    if not path or not path.is_file():
        return {**_metadata(version), "found": False, "id": doc_id}
    return {**_metadata(version), "found": True, "id": doc_id, "source_file": path.relative_to(ROOT).as_posix(), "content": path.read_text(encoding="utf-8")}


def list_scenarios(jurisdiction: str | None = None) -> dict[str, Any]:
    catalog = load_catalog()
    version = catalog_version()
    jurisdiction_ids = {item["id"] for item in catalog["jurisdictions"]}
    if jurisdiction and jurisdiction not in jurisdiction_ids:
        return {**_metadata(version), "found": False, "jurisdiction": jurisdiction, "results": []}
    results = []
    for scenario in catalog["scenarios"]:
        matching = [resource for resource in catalog["resources"] if scenario["id"] in resource["scenarios"] and (not jurisdiction or applies_to(resource, jurisdiction, catalog["jurisdictions"]))]
        status = "desarrollado" if len(matching) >= 3 else "inicial" if matching else "pendiente"
        results.append({**scenario, "jurisdiction": jurisdiction, "resource_count": len(matching), "status": status})
    return {**_metadata(version), "results": results}


def get_reporting_routes(scenario: str, jurisdiction: str) -> dict[str, Any]:
    catalog = load_catalog()
    scenario_ids = {item["id"] for item in catalog["scenarios"]}
    jurisdiction_ids = {item["id"] for item in catalog["jurisdictions"]}
    version = catalog_version()
    if scenario not in scenario_ids or jurisdiction not in jurisdiction_ids:
        return {**_metadata(version), "found": False, "scenario": scenario, "jurisdiction": jurisdiction, "routes": []}
    contact_by_id = {item["id"]: item for item in catalog["contacts"]}
    parents = {item["id"]: item.get("parent") for item in catalog["jurisdictions"]}

    def contact_applies(contact: dict[str, Any]) -> bool:
        territories = set(contact["territories"])
        if "GLOBAL" in territories or jurisdiction in territories:
            return True
        current = parents.get(jurisdiction)
        while current:
            if current in territories:
                return True
            current = parents.get(current)
        return False

    matching = [item for item in catalog["resources"] if scenario in item["scenarios"] and applies_to(item, jurisdiction, catalog["jurisdictions"])]
    routes: dict[str, dict[str, Any]] = {}
    for resource in matching:
        scoped_routes = resource.get("reporting_routes_by_scenario", {}).get(scenario, resource.get("reporting_routes", []))
        for contact_id in scoped_routes:
            contact = contact_by_id[contact_id]
            if not contact_applies(contact):
                continue
            routes[contact_id] = {**contact, "mentioned_by": sorted(set(routes.get(contact_id, {}).get("mentioned_by", []) + [resource["id"]]))}
    return {**_metadata(version), "found": True, "scenario": scenario, "jurisdiction": jurisdiction, "notice": "Orientación de solo lectura. Comprueba la fuente oficial; el MCP no envía reportes ni determina delitos.", "routes": list(routes.values())}
