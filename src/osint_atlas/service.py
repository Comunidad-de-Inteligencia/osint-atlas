from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
import unicodedata
from pathlib import Path
from typing import Any
from .catalog import ROOT, CatalogError, build_sqlite, catalog_version, database_is_current, load_catalog, coverage
from .sync import source_age_days

DEFAULT_DB = ROOT / ".cache/catalog.sqlite"
_INDEX_STATUS = "current"


def ensure_database(path: Path | None = None) -> tuple[Path, str]:
    global _INDEX_STATUS
    path = path or DEFAULT_DB
    try:
        version = catalog_version()
        if not database_is_current(path, version):
            build_sqlite(load_catalog(), version, path)
        _INDEX_STATUS = "current"
    except (CatalogError, OSError, ValueError, KeyError, TypeError, sqlite3.Error):
        if not path.exists():
            raise
        with closing(sqlite3.connect(path)) as con:
            version = con.execute("SELECT value FROM meta WHERE key='catalog_version'").fetchone()[0]
        if not database_is_current(path, version):
            raise CatalogError("No hay una instantánea compatible válida")
        _INDEX_STATUS = "last-valid-snapshot"
    return path, version


def _snapshot():
    path, version = ensure_database()
    with closing(sqlite3.connect(path)) as con:
        catalog = json.loads(con.execute("SELECT value FROM meta WHERE key='catalog'").fetchone()[0])
    return path, version, catalog


def _metadata(version):
    state_file = ROOT / ".cache/maintenance-state/state.json"
    maintenance = {"status":"unknown","processes":{}}
    if state_file.exists():
        try:
            state=json.loads(state_file.read_text(encoding="utf-8"))
            from .maintenance import process_health
            maintenance={"status":"available","processes":process_health(state)}
        except (OSError, ValueError, KeyError, TypeError):
            maintenance={"status":"invalid-state","processes":{}}
    return {"catalog_version":version,"source_age_days":source_age_days(),"index_status":_INDEX_STATUS,
            "maintenance":maintenance,"limitations":"Catálogo de consulta; comprobar cobertura, fuentes y revisión humana. No envía reportes ni determina delitos."}


def _normalize(value):
    return "".join(c for c in unicodedata.normalize("NFKD",str(value)).casefold() if not unicodedata.combining(c)).strip()


def _jurisdiction(value,catalog):
    if value is None: return None
    aliases={_normalize(j["id"]):j["id"] for j in catalog["jurisdictions"]}
    aliases.update({_normalize(j["name"]):j["id"] for j in catalog["jurisdictions"]})
    aliases.update({"uk":"GB","ue":"EU"})
    return aliases.get(_normalize(value))


def _error(version,code,field):
    return {**_metadata(version),"found":False,"error":{"code":code,"field":field},"count":0,"total":0,"results":[],"routes":[]}


def _fts_query(text):
    tokens=re.findall(r"[^\W_]+",text,flags=re.UNICODE)[:32]
    return " AND ".join('"'+token+'"*' for token in tokens)


def _page(rows,total,version,limit,offset):
    return {**_metadata(version),"count":len(rows),"total":total,"offset":offset,"limit":limit,
            "next_offset":offset+len(rows) if offset+len(rows)<total else None,"results":rows}


def _pagination(limit,offset):
    return max(1,min(int(limit),100)),max(0,int(offset))


def _technical(item):
    result=dict(item)
    state_file=ROOT/".cache/maintenance-state/state.json"
    try:
        state=json.loads(state_file.read_text(encoding="utf-8"))
        urls=set(item.get("maintenance_urls",[item.get("url")]))
        checks=[v for v in state["checks"].values() if v.get("url") in urls]
        result["technical_observations"]=checks
    except (OSError,ValueError,KeyError,TypeError):
        result["technical_observations"]=[]
    return result


def _public(item, catalog):
    from .render import resolve_contacts
    return resolve_contacts(_technical(item), catalog)


def search_resources(query="",jurisdiction=None,category=None,scenario=None,access=None,limit=20,
                     offset=0,input_type=None,output_type=None,platform=None):
    path,version,catalog=_snapshot()
    normalized_jurisdiction=_jurisdiction(jurisdiction,catalog)
    if jurisdiction is not None and normalized_jurisdiction is None:
        return _error(version,"unknown_filter","jurisdiction")
    allowed={"category":catalog["taxonomy"]["categories"],"scenario":[s["id"] for s in catalog["scenarios"]],
             "access":catalog["taxonomy"]["access_types"],"input_type":catalog["taxonomy"]["input_types"],
             "output_type":catalog["taxonomy"]["output_types"],"platform":sorted({v for r in catalog["resources"] for v in r["platforms"]})}
    filters={"category":category,"scenario":scenario,"access":access,"input_type":input_type,"output_type":output_type,"platform":platform}
    for key,value in filters.items():
        if value is not None and value not in allowed[key]:
            return _error(version,"unknown_filter",key)
    fts=_fts_query(query)
    if query.strip() and not fts: return _error(version,"invalid_query","query")
    limit,offset=_pagination(limit,offset)
    table="resources r"; where=[]; params=[]
    rank="0"
    if fts:
        table+=" JOIN resource_fts ON resource_fts.id=r.id"
        where.append("resource_fts MATCH ?"); params.append(fts); rank="bm25(resource_fts)"
    if normalized_jurisdiction:
        where.append("EXISTS(SELECT 1 FROM applicability a WHERE a.resource_id=r.id AND a.jurisdiction=?)")
        params.append(normalized_jurisdiction)
    mapping={"category":"categories","scenario":"scenarios","input_type":"input_types","output_type":"output_types","platform":"platforms"}
    for key,field in mapping.items():
        if filters[key] is not None:
            where.append(f"EXISTS(SELECT 1 FROM json_each(r.payload,'$.{field}') WHERE value=?)"); params.append(filters[key])
    if access:
        where.append("json_extract(r.payload,'$.access')=?"); params.append(access)
    clause=" WHERE "+" AND ".join(where) if where else ""
    with closing(sqlite3.connect(path)) as con:
        total=con.execute(f"SELECT count(*) FROM {table}{clause}",params).fetchone()[0]
        rows=con.execute(f"SELECT r.payload,{rank} AS rank FROM {table}{clause} ORDER BY rank,r.name,r.id LIMIT ? OFFSET ?",[*params,limit,offset]).fetchall()
    results=[{**_public(json.loads(p),catalog),"rank":rank,"source_file":f"data/resources/{json.loads(p)['id']}.yaml"} for p,rank in rows]
    return _page(results,total,version,limit,offset)


def get_resource(resource_id):
    path,version,catalog=_snapshot()
    with closing(sqlite3.connect(path)) as con:
        row=con.execute("SELECT payload FROM resources WHERE id=?",(resource_id,)).fetchone()
    if not row: return {**_metadata(version),"found":False,"id":resource_id}
    item=_public(json.loads(row[0]),catalog)
    contacts={c["id"]:c for c in catalog["contacts"]}
    item["resolved_reporting_routes"]=[contacts[cid] for cid in item.get("reporting_routes",[])]
    item["coverage"]=[coverage(catalog,s,j) for s in catalog["scenarios"] if s["id"] in item["scenarios"] for j in item["jurisdictions"]]
    return {**_metadata(version),"found":True,"source_file":f"data/resources/{resource_id}.yaml","resource":item}


def get_jurisdiction(jurisdiction_id,limit=20,offset=0):
    path,version,catalog=_snapshot()
    jid=_jurisdiction(jurisdiction_id,catalog)
    if not jid: return _error(version,"unknown_filter","jurisdiction")
    result=search_resources(jurisdiction=jid,limit=limit,offset=offset)
    return {**_metadata(version),"found":True,"jurisdiction":next(j for j in catalog["jurisdictions"] if j["id"]==jid),
            "resource_count":result["total"],"next_offset":result["next_offset"],"resources":result["results"],
            "coverage":[coverage(catalog,s,jid) for s in catalog["scenarios"]]}


def search_playbooks(query="",scenario=None,limit=20,offset=0,jurisdiction=None):
    path,version,catalog=_snapshot()
    if scenario is not None and scenario not in {s["id"] for s in catalog["scenarios"]}:
        return _error(version,"unknown_filter","scenario")
    jid=_jurisdiction(jurisdiction,catalog)
    if jurisdiction is not None and not jid: return _error(version,"unknown_filter","jurisdiction")
    fts=_fts_query(query)
    if query.strip() and not fts: return _error(version,"invalid_query","query")
    limit,offset=_pagination(limit,offset)
    table="playbooks p"; where=[]; params=[]; rank="0"
    if fts:
        table+=" JOIN docs_fts ON docs_fts.id=p.id"; where.append("docs_fts MATCH ?"); params.append(fts); rank="bm25(docs_fts)"
    if scenario: where.append("p.scenario=?"); params.append(scenario)
    if jid:
        where.append("EXISTS(SELECT 1 FROM json_each(p.payload,'$.jurisdictions') WHERE value=?)"); params.append(jid)
    clause=" WHERE "+" AND ".join(where) if where else ""
    with closing(sqlite3.connect(path)) as con:
        total=con.execute(f"SELECT count(*) FROM {table}{clause}",params).fetchone()[0]
        rows=con.execute(f"SELECT p.payload,{rank} AS rank FROM {table}{clause} ORDER BY rank,p.title,p.id LIMIT ? OFFSET ?",[*params,limit,offset]).fetchall()
    return _page([{**json.loads(p),"rank":rank} for p,rank in rows],total,version,limit,offset)


def get_playbook(playbook_id):
    path,version,_=_snapshot()
    with closing(sqlite3.connect(path)) as con:
        row=con.execute("SELECT payload,content FROM playbooks WHERE id=?",(playbook_id,)).fetchone()
    if not row: return {**_metadata(version),"found":False,"id":playbook_id}
    return {**_metadata(version),"found":True,"playbook":json.loads(row[0]),"content":row[1]}


def search_docs(query="",limit=20,offset=0):
    path,version,_=_snapshot()
    fts=_fts_query(query)
    if query.strip() and not fts: return _error(version,"invalid_query","query")
    limit,offset=_pagination(limit,offset)
    with closing(sqlite3.connect(path)) as con:
        if fts:
            total=con.execute("SELECT count(*) FROM docs_fts WHERE docs_fts MATCH ?",(fts,)).fetchone()[0]
            rows=con.execute("SELECT id,title,snippet(docs_fts,2,'[',']',' … ',24),bm25(docs_fts) FROM docs_fts WHERE docs_fts MATCH ? ORDER BY bm25(docs_fts),id LIMIT ? OFFSET ?",(fts,limit,offset)).fetchall()
        else:
            total=con.execute("SELECT count(*) FROM docs").fetchone()[0]
            rows=con.execute("SELECT id,title,substr(content,1,200),0 FROM docs ORDER BY title,id LIMIT ? OFFSET ?",(limit,offset)).fetchall()
    return _page([{"id":rid,"title":title,"snippet":snippet,"rank":rank} for rid,title,snippet,rank in rows],total,version,limit,offset)


def get_doc(doc_id):
    path,version,_=_snapshot()
    with closing(sqlite3.connect(path)) as con:
        row=con.execute("SELECT path,content FROM docs WHERE id=?",(doc_id,)).fetchone()
    if not row: return {**_metadata(version),"found":False,"id":doc_id}
    return {**_metadata(version),"found":True,"id":doc_id,"source_file":row[0],"content":row[1]}


def list_scenarios(jurisdiction=None):
    _,version,catalog=_snapshot()
    jid=_jurisdiction(jurisdiction,catalog)
    if jurisdiction is not None and not jid: return _error(version,"unknown_filter","jurisdiction")
    territories=[jid] if jid else [j["id"] for j in catalog["jurisdictions"]]
    results=[]
    for s in catalog["scenarios"]:
        rows=[coverage(catalog,s,j) for j in territories]
        result={**s,"coverage":rows}
        if jid: result.update(rows[0],resource_count=rows[0]["resources"])
        results.append(result)
    return {**_metadata(version),"found":True,"results":results}


def get_reporting_routes(scenario,jurisdiction,platform=None,kind=None):
    _,version,catalog=_snapshot()
    jid=_jurisdiction(jurisdiction,catalog)
    if not jid: return _error(version,"unknown_filter","jurisdiction")
    if scenario not in {s["id"] for s in catalog["scenarios"]}: return _error(version,"unknown_filter","scenario")
    known_platforms={x for r in catalog["resources"] for x in r["platforms"]}
    if platform and platform not in known_platforms: return _error(version,"unknown_filter","platform")
    if kind and kind not in {"emergency","assistance","hotline","guidance","reporting","takedown","platform-report","formal-complaint"}:
        return _error(version,"unknown_filter","kind")
    from .catalog import applies_to
    routes=[_technical(c) for c in catalog["contacts"] if scenario in c["scenarios"] and applies_to(c,jid,catalog["jurisdictions"])
            and (not kind or c["kind"]==kind) and (not platform or not c["platforms"] or platform in c["platforms"])]
    sc=next(s for s in catalog["scenarios"] if s["id"]==scenario)
    return {**_metadata(version),"found":True,"scenario":scenario,"jurisdiction":jid,"platform":platform,
            "coverage":coverage(catalog,sc,jid),"notice":"Orientación de solo lectura. Verifica requisitos, competencia y revisión en las fuentes responsables.","routes":routes}
