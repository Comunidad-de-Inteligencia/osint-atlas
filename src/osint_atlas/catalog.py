from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

SOURCE_FILES = (
    DATA / "taxonomy.yaml",
    DATA / "contacts.yaml",
    DATA / "jurisdictions.yaml",
    DATA / "maintainers.yaml",
    DATA / "scenarios.yaml",
    DATA / "playbooks.yaml",
    DATA / "discovery.yaml",
    DATA / "resources" / "core.yaml",
    DATA / "schemas" / "resource.schema.json",
)


class CatalogError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    """Load the JSON-compatible YAML used by the project without dependencies."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"No se pudo leer {path.relative_to(ROOT)}: {exc}") from exc


def load_catalog() -> dict[str, Any]:
    taxonomy = load_yaml(DATA / "taxonomy.yaml")
    contacts_doc = load_yaml(DATA / "contacts.yaml")
    jurisdictions_doc = load_yaml(DATA / "jurisdictions.yaml")
    maintainers = load_yaml(DATA / "maintainers.yaml")
    scenarios_doc = load_yaml(DATA / "scenarios.yaml")
    playbooks_doc = load_yaml(DATA / "playbooks.yaml")
    resource_doc = load_yaml(DATA / "resources" / "core.yaml")
    defaults = resource_doc.get("defaults", {})
    resources = [{**defaults, **item} for item in resource_doc["resources"]]
    return {
        "taxonomy": taxonomy,
        "contacts": contacts_doc["contacts"],
        "jurisdictions": jurisdictions_doc["jurisdictions"],
        "maintainers": maintainers,
        "scenarios": scenarios_doc["scenarios"],
        "playbooks": playbooks_doc["playbooks"],
        "resources": resources,
    }


def catalog_version() -> str:
    digest = hashlib.sha256()
    for path in SOURCE_FILES:
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    playbook_doc = load_yaml(DATA / "playbooks.yaml")
    for item in sorted(playbook_doc["playbooks"], key=lambda x: x["path"]):
        path = ROOT / item["path"]
        digest.update(item["path"].encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    repeated: set[str] = set()
    for value in values:
        if value in seen:
            repeated.add(value)
        seen.add(value)
    return repeated


def validate_catalog(catalog: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    resources = catalog["resources"]
    contacts = catalog["contacts"]
    jurisdictions = catalog["jurisdictions"]
    scenarios = catalog["scenarios"]
    playbooks = catalog["playbooks"]
    taxonomy = catalog["taxonomy"]

    for label, items in (
        ("recurso", resources), ("contacto", contacts),
        ("jurisdicción", jurisdictions), ("escenario", scenarios),
        ("procedimiento", playbooks),
    ):
        repeated = _duplicates(item.get("id", "") for item in items)
        errors.extend(f"{label} duplicado: {value}" for value in sorted(repeated))

    jurisdiction_ids = {item["id"] for item in jurisdictions}
    scenario_ids = {item["id"] for item in scenarios}
    contact_ids = {item["id"] for item in contacts}
    categories = set(taxonomy["categories"])
    resource_types = set(taxonomy["resource_types"])
    tiers = set(taxonomy["authority_tiers"])
    criticalities = set(taxonomy["criticality"])
    required = {
        "id", "name", "owner", "jurisdictions", "type", "tier", "categories",
        "scenarios", "url", "purpose", "inputs", "outputs", "usage",
        "interpretation", "limitations", "review_days", "criticality",
        "editorial_reviewed", "access", "cost", "languages", "terms",
        "maintainer", "backup_maintainer", "technical_check", "pending_changes",
    }
    schema = load_yaml(DATA / "schemas" / "resource.schema.json")
    schema_validator = Draft202012Validator(schema)

    if len(resources) < 80:
        errors.append(f"se esperaban al menos 80 recursos; hay {len(resources)}")
    if len(playbooks) != 16:
        errors.append(f"se esperaban 16 procedimientos; hay {len(playbooks)}")

    for resource in resources:
        rid = resource.get("id", "<sin-id>")
        for schema_error in sorted(schema_validator.iter_errors(resource), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in schema_error.path) or "ficha"
            errors.append(f"{rid}: esquema {location}: {schema_error.message}")
        missing = required - resource.keys()
        if missing:
            errors.append(f"{rid}: faltan campos {', '.join(sorted(missing))}")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]+", rid):
            errors.append(f"{rid}: id inválido")
        if not str(resource.get("url", "")).startswith("https://"):
            errors.append(f"{rid}: URL no HTTPS")
        for field in ("purpose", "usage", "interpretation", "limitations"):
            if len(str(resource.get(field, ""))) < 15:
                errors.append(f"{rid}: explicación insuficiente en {field}")
        unknown = set(resource.get("jurisdictions", [])) | set(resource.get("coverage_exclusions", []))
        for value in sorted(unknown - jurisdiction_ids):
            errors.append(f"{rid}: jurisdicción desconocida {value}")
        for value in sorted(set(resource.get("scenarios", [])) - scenario_ids):
            errors.append(f"{rid}: escenario desconocido {value}")
        for value in sorted(set(resource.get("categories", [])) - categories):
            errors.append(f"{rid}: categoría desconocida {value}")
        for value in sorted(set(resource.get("reporting_routes", [])) - contact_ids):
            errors.append(f"{rid}: contacto desconocido {value}")
        for route_scenario, route_ids in resource.get("reporting_routes_by_scenario", {}).items():
            if route_scenario not in resource.get("scenarios", []):
                errors.append(f"{rid}: rutas definidas para un escenario no asociado {route_scenario}")
            for value in sorted(set(route_ids) - contact_ids):
                errors.append(f"{rid}: contacto desconocido {value}")
        if resource.get("type") not in resource_types:
            errors.append(f"{rid}: tipo desconocido {resource.get('type')}")
        if resource.get("tier") not in tiers:
            errors.append(f"{rid}: procedencia desconocida {resource.get('tier')}")
        if resource.get("criticality") not in criticalities:
            errors.append(f"{rid}: criticidad desconocida {resource.get('criticality')}")
        technical = resource.get("technical_check", {})
        if not isinstance(technical, dict) or technical.get("status") not in taxonomy["health_status"]:
            errors.append(f"{rid}: comprobación técnica inválida")
        if not isinstance(resource.get("pending_changes"), list):
            errors.append(f"{rid}: pending_changes debe ser una lista")
        try:
            date.fromisoformat(resource.get("editorial_reviewed", ""))
        except ValueError:
            errors.append(f"{rid}: editorial_reviewed no es una fecha ISO")

    for playbook in playbooks:
        path = ROOT / playbook["path"]
        if playbook.get("scenario") not in scenario_ids:
            errors.append(f"{playbook['id']}: escenario de procedimiento desconocido")
        if not path.is_file():
            errors.append(f"{playbook['id']}: falta {playbook['path']}")
        elif not path.read_text(encoding="utf-8").startswith("# "):
            errors.append(f"{playbook['id']}: el documento debe comenzar con H1")

    playbook_scenarios = {item["scenario"] for item in playbooks}
    for scenario in sorted(scenario_ids - playbook_scenarios):
        errors.append(f"escenario sin procedimiento: {scenario}")
    return errors


def applies_to(resource: dict[str, Any], jurisdiction_id: str, jurisdictions: list[dict[str, Any]]) -> bool:
    if jurisdiction_id in resource.get("coverage_exclusions", []):
        return False
    if jurisdiction_id in resource["jurisdictions"] or "GLOBAL" in resource["jurisdictions"]:
        return True
    parents = {item["id"]: item.get("parent") for item in jurisdictions}
    current = parents.get(jurisdiction_id)
    while current:
        if current in resource.get("coverage_exclusions", []):
            return False
        if current in resource["jurisdictions"]:
            return True
        current = parents.get(current)
    return False


def resource_markdown(resource: dict[str, Any], catalog: dict[str, Any], version: str) -> str:
    contacts = {item["id"]: item for item in catalog["contacts"]}
    tier = catalog["taxonomy"]["authority_tiers"][resource["tier"]]
    lines = [
        "<!-- GENERADO: edite data/resources/core.yaml -->",
        f"# {resource['name']}", "",
        f"> **Para qué sirve:** {resource['purpose']}", "",
        "## Antes de empezar", "",
        f"Necesitas: {', '.join(resource['inputs']) if resource['inputs'] else 'ningún identificador obligatorio'}.", "",
        f"Acceso: **{resource['access']}**. Coste: **{resource['cost']}**. Idiomas: **{', '.join(resource['languages'])}**.", "",
        f"Cobertura: **{', '.join(resource['jurisdictions'])}**.", "",
        "## Cómo utilizarla", "",
        f"1. {resource['usage']}",
        f"2. Abre la [fuente principal]({resource['url']}) y registra la fecha de consulta.",
        f"3. Conserva como resultado: {', '.join(resource['outputs'])}.", "",
        "## Ejemplo", "",
        f"Ejemplo ilustrativo: parte de {resource['inputs'][0] if resource['inputs'] else 'una pregunta concreta'}, realiza la consulta y conserva {resource['outputs'][0]} con su fecha y enlace.", "",
        "## Cómo interpretar el resultado", "", resource["interpretation"], "",
        "## Límites y alternativas", "", resource["limitations"], "",
    ]
    exclusions = resource.get("coverage_exclusions", [])
    if exclusions:
        lines.extend([f"Exclusiones territoriales conocidas: **{', '.join(exclusions)}**.", ""])
    alternatives = resource.get("alternatives", [])
    if alternatives:
        lines.extend([f"Alternativas relacionadas: {', '.join(alternatives)}.", ""])
    routes = [contacts[item] for item in resource.get("reporting_routes", [])]
    if routes:
        lines.extend(["## Asistencia o reporte", ""])
        for contact in routes:
            lines.append(f"- [{contact['name']}]({contact['url']}): {contact['value']}. {contact['note']}")
        lines.append("")
    technical = resource["technical_check"]
    technical_date = technical.get("checked_at") or "todavía no registrada"
    pending = resource["pending_changes"]
    lines.extend([
        "## Condiciones conocidas", "", resource["terms"], "",
        "## Procedencia y revisión", "",
        f"- Responsable de la fuente: {resource['owner']}",
        f"- Nivel de procedencia: **{resource['tier']} — {tier}**",
        f"- Revisión editorial: {resource['editorial_reviewed']}",
        f"- Comprobación técnica: {technical['status']} ({technical_date})",
        f"- Responsable del catálogo: {resource['maintainer'] or 'por asignar'}",
        f"- Suplente: {resource['backup_maintainer'] or 'por asignar'}",
        f"- Cambios pendientes: {len(pending)}",
        f"- Próxima revisión prevista: cada {resource['review_days']} días",
        f"- Criticidad: {resource['criticality']}",
        f"- Versión del catálogo: `{version}`", "",
    ])
    for reference in resource.get("references", []):
        lines.append(f"- [{reference['title']}]({reference['url']})")
    lines.extend(["", "[Volver al catálogo](../CATALOGO.md)", ""])
    return "\n".join(lines)


def _resource_link(resource: dict[str, Any], prefix: str = "../fuentes") -> str:
    return f"[{resource['name']}]({prefix}/{resource['id']}.md)"


def build_outputs(catalog: dict[str, Any], version: str) -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    resources = sorted(catalog["resources"], key=lambda item: item["name"].casefold())
    scenarios = sorted(catalog["scenarios"], key=lambda item: item["name"].casefold())
    jurisdictions = catalog["jurisdictions"]
    playbooks = {item["scenario"]: item for item in catalog["playbooks"]}

    for resource in resources:
        outputs[ROOT / "docs" / "fuentes" / f"{resource['id']}.md"] = resource_markdown(resource, catalog, version)

    catalog_lines = ["<!-- GENERADO: edite data/resources/core.yaml -->", "# Catálogo de fuentes", "", f"Esta versión contiene **{len(resources)} recursos**. Usa los índices por escenario o jurisdicción para reducir la búsqueda.", "", "| Fuente | Cobertura | Temas |", "|---|---|---|"]
    for resource in resources:
        catalog_lines.append(f"| {_resource_link(resource, 'fuentes')} | {', '.join(resource['jurisdictions'])} | {', '.join(resource['categories'])} |")
    catalog_lines.append("")
    outputs[ROOT / "docs" / "CATALOGO.md"] = "\n".join(catalog_lines)

    coverage_rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        matching = [item for item in resources if scenario["id"] in item["scenarios"]]
        lines = ["<!-- GENERADO -->", f"# {scenario['name']}", "", scenario["description"], "", f"[Abrir el procedimiento](../procedimientos/{Path(playbooks[scenario['id']]['path']).name})", "", "## Fuentes", ""]
        lines.extend(f"- {_resource_link(item)} — {item['purpose']}" for item in matching)
        lines.append("")
        outputs[ROOT / "docs" / "indices" / f"escenario-{scenario['id']}.md"] = "\n".join(lines)
        for jurisdiction in jurisdictions:
            count = sum(applies_to(item, jurisdiction["id"], jurisdictions) for item in matching)
            status = "desarrollado" if count >= 3 else "inicial" if count else "pendiente"
            coverage_rows.append({"scenario": scenario["id"], "jurisdiction": jurisdiction["id"], "resources": count, "status": status, "specialty": scenario["specialty"]})

    for jurisdiction in jurisdictions:
        matching = [item for item in resources if applies_to(item, jurisdiction["id"], jurisdictions)]
        lines = ["<!-- GENERADO -->", f"# {jurisdiction['name']}", "", jurisdiction.get("notes", "Consulta las particularidades locales antes de utilizar una fuente."), "", f"Recursos aplicables: **{len(matching)}**.", "", "## Fuentes", ""]
        lines.extend(f"- {_resource_link(item)} — {item['purpose']}" for item in matching)
        lines.append("")
        outputs[ROOT / "docs" / "indices" / f"jurisdiccion-{jurisdiction['id'].lower()}.md"] = "\n".join(lines)

    matrix = ["<!-- GENERADO -->", "# Matriz de cobertura", "", "La matriz hace visibles las lagunas. **Desarrollado** significa tres o más recursos aplicables; **inicial**, uno o dos; **pendiente**, ninguno.", "", "| Escenario | Jurisdicción | Recursos | Estado | Especialidad |", "|---|---|---:|---|---|"]
    scenario_names = {item["id"]: item["name"] for item in scenarios}
    jurisdiction_names = {item["id"]: item["name"] for item in jurisdictions}
    for row in coverage_rows:
        matrix.append(f"| {scenario_names[row['scenario']]} | {jurisdiction_names[row['jurisdiction']]} | {row['resources']} | {row['status']} | {row['specialty']} |")
    matrix.append("")
    outputs[ROOT / "docs" / "COBERTURA.md"] = "\n".join(matrix)

    procedures = ["<!-- GENERADO -->", "# Procedimientos", "", "Cada procedimiento explica el objetivo, los pasos, la interpretación y el criterio de finalización.", ""]
    for item in catalog["playbooks"]:
        procedures.append(f"- [{item['title']}]({Path(item['path']).name}) — revisado {item['last_reviewed']}")
    procedures.append("")
    outputs[ROOT / "docs" / "procedimientos" / "README.md"] = "\n".join(procedures)

    contacts = ["<!-- GENERADO: edite data/contacts.yaml -->", "# Contactos y rutas de asistencia", "", "Comprueba siempre la página oficial antes de utilizar un contacto. Una vía de asistencia o retirada no equivale necesariamente a una denuncia.", "", "| Territorio | Contacto | Canal | Nota |", "|---|---|---|---|"]
    for item in catalog["contacts"]:
        contacts.append(f"| {', '.join(item['territories'])} | [{item['name']}]({item['url']}) | {item['value']} | {item['note']} |")
    contacts.append("")
    outputs[ROOT / "docs" / "CONTACTOS.md"] = "\n".join(contacts)

    export = {"version": version, "generated_at": "deterministic-from-source", **catalog}
    outputs[DATA / "export" / "catalog.json"] = json.dumps(export, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    outputs[DATA / "export" / "coverage.json"] = json.dumps({"version": version, "coverage": coverage_rows}, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    search_records = [{"id": r["id"], "name": r["name"], "text": " ".join([r["name"], r["purpose"], r["usage"], r["interpretation"], " ".join(r["categories"]), " ".join(r["scenarios"]), " ".join(r["jurisdictions"])]), "url": r["url"]} for r in resources]
    outputs[DATA / "export" / "search-index.json"] = json.dumps({"version": version, "resources": search_records}, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return outputs


def write_outputs(outputs: dict[Path, str]) -> None:
    expected = set(outputs)
    for directory in (ROOT / "docs" / "fuentes", ROOT / "docs" / "indices"):
        if directory.exists():
            for path in directory.glob("*.md"):
                if path not in expected:
                    path.unlink()
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def check_outputs(outputs: dict[Path, str]) -> list[str]:
    errors: list[str] = []
    for path, content in outputs.items():
        if not path.is_file():
            errors.append(f"falta generado: {path.relative_to(ROOT)}")
        elif path.read_text(encoding="utf-8") != content:
            errors.append(f"generado desactualizado: {path.relative_to(ROOT)}")
    return errors


def build_sqlite(catalog: dict[str, Any], version: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        connection.executescript("""
            CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE resources (id TEXT PRIMARY KEY, name TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE VIRTUAL TABLE resource_fts USING fts5(id UNINDEXED, name, purpose, body, tokenize='unicode61 remove_diacritics 2');
            CREATE TABLE jurisdictions (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE scenarios (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE playbooks (id TEXT PRIMARY KEY, scenario TEXT NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE VIRTUAL TABLE docs_fts USING fts5(id UNINDEXED, title, content, tokenize='unicode61 remove_diacritics 2');
        """)
        connection.execute("INSERT INTO meta VALUES (?, ?)", ("catalog_version", version))
        for resource in catalog["resources"]:
            payload = json.dumps(resource, ensure_ascii=False, sort_keys=True)
            body = " ".join([resource["purpose"], resource["usage"], resource["interpretation"], resource["limitations"], " ".join(resource["categories"]), " ".join(resource["scenarios"]), " ".join(resource["jurisdictions"])])
            connection.execute("INSERT INTO resources VALUES (?, ?, ?)", (resource["id"], resource["name"], payload))
            connection.execute("INSERT INTO resource_fts VALUES (?, ?, ?, ?)", (resource["id"], resource["name"], resource["purpose"], body))
        for item in catalog["jurisdictions"]:
            connection.execute("INSERT INTO jurisdictions VALUES (?, ?)", (item["id"], json.dumps(item, ensure_ascii=False, sort_keys=True)))
        for item in catalog["scenarios"]:
            connection.execute("INSERT INTO scenarios VALUES (?, ?)", (item["id"], json.dumps(item, ensure_ascii=False, sort_keys=True)))
        for item in catalog["playbooks"]:
            content = (ROOT / item["path"]).read_text(encoding="utf-8")
            payload = json.dumps(item, ensure_ascii=False, sort_keys=True)
            connection.execute("INSERT INTO playbooks VALUES (?, ?, ?, ?, ?)", (item["id"], item["scenario"], item["title"], content, payload))
            connection.execute("INSERT INTO docs_fts VALUES (?, ?, ?)", (item["id"], item["title"], content))
        manual_docs = {
            "readme": ("Presentación", ROOT / "README.md"),
            "empezar": ("Cómo empezar", ROOT / "docs" / "EMPEZAR.md"),
            "ia": ("Uso con IA", ROOT / "docs" / "IA.md"),
            "glosario": ("Glosario", ROOT / "docs" / "GLOSARIO.md"),
            "contribuir": ("Cómo contribuir", ROOT / "CONTRIBUTING.md"),
            "legal": ("Marco legal y uso responsable", ROOT / "LEGAL.md"),
        }
        for doc_id, (title, doc_path) in manual_docs.items():
            connection.execute(
                "INSERT INTO docs_fts VALUES (?, ?, ?)",
                (doc_id, title, doc_path.read_text(encoding="utf-8")),
            )
        connection.commit()
    finally:
        connection.close()


def database_is_current(path: Path, version: str) -> bool:
    if not path.is_file():
        return False
    try:
        with sqlite3.connect(path) as connection:
            row = connection.execute("SELECT value FROM meta WHERE key='catalog_version'").fetchone()
        return bool(row and row[0] == version)
    except sqlite3.Error:
        return False


def generated_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
