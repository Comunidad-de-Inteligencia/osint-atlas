from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from contextlib import closing
import tempfile
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(os.environ.get("OSINT_ATLAS_ROOT", Path(__file__).resolve().parents[2])).resolve()
DATA = ROOT / "data"
INDEX_FORMAT = "atlas-2"


class CatalogError(ValueError):
    pass


class StrictLoader(yaml.SafeLoader):
    """Safe YAML: no executable tags, duplicate keys or implicit date objects."""


StrictLoader.yaml_implicit_resolvers = {
    key: [(tag, regex) for tag, regex in values if tag != "tag:yaml.org,2002:timestamp"]
    for key, values in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def _mapping(loader, node, deep=False):
    result = {}
    for key, value in loader.construct_pairs(node, deep=deep):
        if key in result:
            raise CatalogError(f"Clave YAML duplicada: {key}")
        result[key] = value
    return result


StrictLoader.add_constructor("tag:yaml.org,2002:map", _mapping)


def load_yaml(path: Path) -> dict:
    try:
        value = yaml.load(path.read_text(encoding="utf-8-sig"), Loader=StrictLoader)
        if not isinstance(value, dict):
            raise CatalogError(f"{path.name}: se esperaba un objeto")
        return value
    except (OSError, yaml.YAMLError) as exc:
        raise CatalogError(f"No se pudo leer {path.name}: {exc}") from exc


def load_catalog() -> dict:
    catalog = {key: load_yaml(DATA / f"{key}.yaml")[key]
               for key in ("contacts", "jurisdictions", "scenarios", "playbooks")}
    catalog.update({key: load_yaml(DATA / f"{key}.yaml") for key in ("taxonomy", "maintainers")})
    catalog["resources"] = [load_yaml(path) for path in sorted((DATA / "resources").glob("*.yaml"))]
    return catalog


def source_files() -> list[Path]:
    files = list(DATA.glob("*.yaml")) + list((DATA / "resources").glob("*.yaml"))
    files += list((DATA / "schemas").glob("*.json")) + list((ROOT / "content").rglob("*.md"))
    files += list((ROOT / "src/osint_atlas").glob("*.py")) + [ROOT / "pyproject.toml", ROOT / "uv.lock"]
    for path in [*ROOT.glob("*.md"), *(ROOT / "docs").rglob("*.md")]:
        if not path.read_text(encoding="utf-8").startswith("<!-- GENERADO"):
            files.append(path)
    return sorted(set(files), key=lambda p: p.relative_to(ROOT).as_posix())


def catalog_version() -> str:
    digest = hashlib.sha256(INDEX_FORMAT.encode())
    for path in source_files():
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()[:16]


def safe_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise CatalogError("Ruta fuera del catálogo")
    return path


def validate_catalog(catalog: dict) -> list[str]:
    validator = Draft202012Validator(load_yaml(DATA / "schemas/catalog.schema.json"), format_checker=FormatChecker())
    errors = [f"{'.'.join(map(str, e.path))}: {e.message}" for e in validator.iter_errors(catalog)]
    if errors:
        return errors
    extra_errors = []
    for name in ("discovery", "resolutions"):
        extra = load_yaml(DATA / f"{name}.yaml")
        schema = load_yaml(DATA / "schemas" / f"{name}.schema.json")
        extra_errors.extend(f"{name}: {e.message}" for e in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(extra))
    if extra_errors:
        return extra_errors
    ids = {}
    for key in ("resources", "contacts", "jurisdictions", "scenarios", "playbooks"):
        ids[key] = {item["id"] for item in catalog[key]}
        if len(ids[key]) != len(catalog[key]):
            errors.append(f"{key}: identificadores duplicados")
    specs = catalog["maintainers"]["specialties"]
    people = {p["login"] for p in catalog["maintainers"]["people"]}
    specialty_ids = {s["id"] for s in specs}
    sources = load_yaml(DATA / "discovery.yaml")["approved_catalogs"]
    if len({s["id"] for s in sources}) != len(sources):
        errors.append("Descubrimiento: identificadores duplicados")
    for source in sources:
        if source["territory"] not in ids["jurisdictions"] or source.get("specialty", "public-data") not in specialty_ids:
            errors.append(f"{source['id']}: territorio o especialidad desconocidos")
    for person in catalog["maintainers"]["people"]:
        if set(person["specialties"]) - specialty_ids:
            errors.append(f"{person['login']}: especialidad desconocida")
    if len(specialty_ids) != len(specs) or len(people) != len(catalog["maintainers"]["people"]):
        errors.append("Colaboradores o especialidades duplicados")
    for spec in specs:
        for field in ("primary", "backup"):
            if spec[field] and spec[field] not in people:
                errors.append(f"{spec['id']}: colaborador desconocido")
    if len(catalog["resources"]) < 84 or len(catalog["playbooks"]) < 16:
        errors.append("Conservar al menos 84 recursos y 16 procedimientos")

    def refs(item, field, allowed):
        for value in item.get(field, []):
            if value not in allowed:
                errors.append(f"{item['id']}: {field} desconocido {value}")

    for r in catalog["resources"]:
        for cid in re.findall(r"\{\{contact:([^}]+)\}\}", json.dumps(r, ensure_ascii=False)):
            if cid not in ids["contacts"]:
                errors.append(f"{r['id']}: contacto desconocido {cid}")
        fields = {"jurisdictions": ids["jurisdictions"], "coverage_exclusions": ids["jurisdictions"],
                  "scenarios": ids["scenarios"], "reporting_routes": ids["contacts"], "alternatives": ids["resources"],
                  **{k: catalog["taxonomy"][k] for k in ("categories", "input_types", "output_types")}}
        for field, allowed in fields.items():
            refs(r, field, allowed)
        for scenario, routes in r.get("reporting_routes_by_scenario", {}).items():
            if scenario not in r["scenarios"] or not set(routes) <= ids["contacts"]:
                errors.append(f"{r['id']}: rutas por escenario inválidas")
        for field in ("maintainer", "backup_maintainer"):
            if r[field] and r[field] not in people:
                errors.append(f"{r['id']}: responsable desconocido")
        if r["type"] not in catalog["taxonomy"]["resource_types"]:
            errors.append(f"{r['id']}: tipo desconocido")
    for c in catalog["contacts"]:
        refs(c, "territories", ids["jurisdictions"])
        refs(c, "scenarios", ids["scenarios"])
    parents = {j["id"]: j["parent"] for j in catalog["jurisdictions"]}
    for jid in parents:
        current, visited = jid, set()
        while current:
            if current in visited or current not in parents:
                errors.append(f"{jid}: ciclo o padre desconocido")
                break
            visited.add(current)
            current = parents[current]
    for s in catalog["scenarios"]:
        if s["specialty"] not in specialty_ids:
            errors.append(f"{s['id']}: especialidad desconocida")
    for p in catalog["playbooks"]:
        if p["scenario"] not in ids["scenarios"]:
            errors.append(f"{p['id']}: escenario desconocido")
        refs(p, "jurisdictions", ids["jurisdictions"])
        refs(p, "contacts", ids["contacts"])
        try:
            body = safe_path(p["source_path"]).read_text(encoding="utf-8")
            safe_path(p["path"])
            if not body.startswith("# "):
                errors.append(f"{p['id']}: falta H1")
            for cid in re.findall(r"\{\{contact:([^}]+)\}\}", body):
                if cid not in ids["contacts"] or cid not in p["contacts"]:
                    errors.append(f"{p['id']}: contacto sin declarar {cid}")
            if re.search(r"(?<!\d)(112|017|016|116[ ]?000)(?!\d)", re.sub(r"\{\{contact:[^}]+\}\}", "", body)):
                errors.append(f"{p['id']}: contacto literal duplicado")
        except (OSError, CatalogError) as exc:
            errors.append(str(exc))
    if ids["scenarios"] - {p["scenario"] for p in catalog["playbooks"]}:
        errors.append("Escenarios sin procedimiento")
    for group, field in (("resources", "editorial_reviewed"), ("contacts", "last_reviewed"), ("playbooks", "last_reviewed")):
        for item in catalog[group]:
            if item["review_status"] == "verified" and (not item[field] or not item["reviewer"] or not item["references"]):
                errors.append(f"{item['id']}: revisión verificada sin evidencia/fecha/persona")
            if item["reviewer"] and item["reviewer"] not in people:
                errors.append(f"{item['id']}: revisor no registrado")
            if item[field] and date.fromisoformat(item[field]) > date.today():
                errors.append(f"{item['id']}: revisión futura")
    return errors


def applies_to(resource: dict, jurisdiction_id: str, jurisdictions: list[dict]) -> bool:
    parents = {j["id"]: j.get("parent") for j in jurisdictions}
    if jurisdiction_id not in parents:
        return False
    current, lineage = jurisdiction_id, set()
    while current and current not in lineage:
        lineage.add(current)
        current = parents.get(current)
    return not bool(lineage & set(resource.get("coverage_exclusions", []))) and bool(
        lineage & set(resource.get("jurisdictions", resource.get("territories", []))))


def coverage(catalog: dict, scenario: dict, jurisdiction: str, as_of: date | None = None) -> dict:
    if as_of is None:
        dates = [item['created_at'] for key in ('resources', 'contacts', 'playbooks') for item in catalog[key]]
        dates += [item.get(field) for key, field in [('resources','editorial_reviewed'),('contacts','last_reviewed'),('playbooks','last_reviewed')] for item in catalog[key] if item.get(field)]
        dates += [e['observed_at'] for r in catalog['resources'] for e in r['metadata_evidence']]
        as_of = date.fromisoformat(max(dates))
    def valid(item, field):
        reviewed = item.get(field)
        return bool(item['review_status']=='verified' and item['reviewer'] and reviewed
                    and date.fromisoformat(reviewed) <= as_of <= date.fromisoformat(reviewed)+timedelta(days=item['review_days']))
    matching = [r for r in catalog["resources"] if scenario["id"] in r["scenarios"] and applies_to(r, jurisdiction, catalog["jurisdictions"])]
    local = [r for r in matching if jurisdiction in r["jurisdictions"]]
    verified = [r for r in local if valid(r,'editorial_reviewed')]
    procedures = [p for p in catalog["playbooks"] if p["scenario"] == scenario["id"] and jurisdiction in p["jurisdictions"]
                  and valid(p,'last_reviewed')]
    spec = next(s for s in catalog["maintainers"]["specialties"] if s["id"] == scenario["specialty"])
    routes = [c for c in catalog["contacts"] if scenario["id"] in c["scenarios"] and jurisdiction in c["territories"]
              and valid(c,'last_reviewed')]
    gaps = []
    if not verified: gaps.append("Faltan fuentes revisadas específicamente para este territorio.")
    if not procedures: gaps.append("Falta un procedimiento territorial revisado.")
    if not spec["primary"]: gaps.append("Falta responsable de la especialidad.")
    if scenario["requires_routes"] and not routes: gaps.append("Faltan vías competentes verificadas para este territorio.")
    dates = [r["editorial_reviewed"] for r in verified] + [p["last_reviewed"] for p in procedures] + [c["last_reviewed"] for c in routes]
    return {"scenario": scenario["id"], "jurisdiction": jurisdiction, "as_of": as_of.isoformat(), "resources": len(matching),
            "local_resources": len(local), "general_resources": len(matching) - len(local),
            "status": "desarrollado" if not gaps else "inicial" if verified else "pendiente",
            "specialty": scenario["specialty"], "maintainer": spec["primary"], "backup": spec["backup"],
            "last_reviewed": min(dates) if dates else None, "gaps": gaps}


def build_outputs(catalog: dict, version: str) -> dict[Path, str]:
    from .render import build_outputs as render
    return render(catalog, version)


def write_outputs(outputs: dict[Path, str]) -> None:
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def check_outputs(outputs: dict[Path, str]) -> list[str]:
    return [f"generado desactualizado: {p.relative_to(ROOT)}" for p, text in outputs.items()
            if not p.exists() or p.read_text(encoding="utf-8") != text]


def documents(catalog: dict, outputs: dict[Path, str]) -> list[dict]:
    aliases = {
        "README.md": "readme",
        "docs/es/contribuir.md": "contribuir",
        "docs/en/contribuir.md": "en/contribuir",
        "docs/es/legal.md": "legal",
        "docs/en/legal.md": "en/legal",
        "docs/es/empezar.md": "empezar",
        "docs/es/glosario.md": "glosario",
        "docs/es/ia.md": "ia",
        "docs/es/mantenimiento.md": "mantenimiento",
        "docs/es/accesibilidad.md": "accesibilidad",
        "docs/es/seguridad.md": "seguridad",
        "docs/es/atribucion.md": "atribucion",
        "docs/es/index.md": "indice",
        "docs/es/cobertura.md": "cobertura",
        "docs/es/catalogo.md": "catalogo",
        "docs/es/contactos.md": "contactos",
    }
    aliases.update({p["path"]: p["id"] for p in catalog["playbooks"]})
    paths = set(ROOT.glob("*.md")) | set((ROOT / "docs").rglob("*.md")) | {p for p in outputs if p.suffix == ".md"}
    result = []
    for path in sorted(paths, key=lambda p: p.relative_to(ROOT).as_posix()):
        if path.name == "AGENTS.md": continue
        relative = path.relative_to(ROOT).as_posix()
        content = outputs[path] if path in outputs else path.read_text(encoding="utf-8")
        title = next((line[2:] for line in content.splitlines() if line.startswith("# ")), path.stem)
        doc_id = aliases.get(relative, relative.removeprefix("docs/").removesuffix(".md").lower())
        result.append({"id": doc_id, "title": title, "path": relative, "content": content})
    return result


def build_sqlite(catalog: dict, version: str, path: Path) -> None:
    errors = validate_catalog(catalog)
    if errors: raise CatalogError("\n".join(errors))
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="catalog-", suffix=".sqlite", dir=path.parent)
    os.close(fd)
    tmp = Path(name)
    try:
        with closing(sqlite3.connect(tmp)) as con:
            con.executescript("""
                CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE resources (id TEXT PRIMARY KEY, name TEXT, payload TEXT);
                CREATE VIRTUAL TABLE resource_fts USING fts5(id UNINDEXED, name, body, tokenize='unicode61 remove_diacritics 2');
                CREATE TABLE applicability (resource_id TEXT, jurisdiction TEXT, PRIMARY KEY(resource_id,jurisdiction));
                CREATE TABLE playbooks (id TEXT PRIMARY KEY, scenario TEXT, title TEXT, content TEXT, payload TEXT);
                CREATE TABLE docs (id TEXT PRIMARY KEY, title TEXT, path TEXT, content TEXT);
                CREATE VIRTUAL TABLE docs_fts USING fts5(id UNINDEXED, title, content, tokenize='unicode61 remove_diacritics 2');
            """)
            con.executemany("INSERT INTO meta VALUES (?,?)", [
                ("catalog_version", version), ("index_format", INDEX_FORMAT),
                ("catalog", json.dumps(catalog, ensure_ascii=False, sort_keys=True))])
            for r in sorted(catalog["resources"], key=lambda x: x["id"]):
                payload = json.dumps(r, ensure_ascii=False, sort_keys=True)
                con.execute("INSERT INTO resources VALUES (?,?,?)", (r["id"], r["name"], payload))
                con.execute("INSERT INTO resource_fts VALUES (?,?,?)", (r["id"], r["name"], payload))
                con.executemany("INSERT INTO applicability VALUES (?,?)", [(r["id"], j["id"]) for j in catalog["jurisdictions"] if applies_to(r, j["id"], catalog["jurisdictions"])])
            output = build_outputs(catalog, version)
            for doc in documents(catalog, output):
                con.execute("INSERT INTO docs VALUES (?,?,?,?)", (doc["id"], doc["title"], doc["path"], doc["content"]))
                con.execute("INSERT INTO docs_fts VALUES (?,?,?)", (doc["id"], doc["title"], doc["content"]))
            for p in sorted(catalog["playbooks"], key=lambda x: x["id"]):
                con.execute("INSERT INTO playbooks VALUES (?,?,?,?,?)", (p["id"], p["scenario"], p["title"], output[ROOT / p["path"]], json.dumps(p, ensure_ascii=False, sort_keys=True)))
            con.commit()
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise CatalogError("Índice SQLite inválido")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def database_is_current(path: Path, version: str) -> bool:
    if not path.is_file(): return False
    try:
        with closing(sqlite3.connect(path)) as con:
            meta = dict(con.execute("SELECT key,value FROM meta WHERE key != 'catalog'"))
        return meta.get("catalog_version") == version and meta.get("index_format") == INDEX_FORMAT
    except sqlite3.Error:
        return False


def generated_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
