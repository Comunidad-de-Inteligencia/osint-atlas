from __future__ import annotations
import copy,json,sqlite3,tempfile,unittest
from contextlib import closing
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch
from osint_atlas import catalog as cat,service,sync
from osint_atlas.governance import route_review,review_decision
from osint_atlas.maintenance import empty_state,advance,check_target,normalize_content,process_health
from tools.discover_candidates import select_candidates
from tools.validate_docs import validate_document
from tools.publish_maintenance_issue import stable_fingerprint,groups


class CatalogueV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=cat.load_catalog()

    def test_unknown_metadata_and_sources(self):
        self.assertEqual(len(self.catalog["resources"]),84)
        self.assertTrue(all(r["references"] and r["steps"] and r["example"]["expected"] for r in self.catalog["resources"]))
        de=next(r for r in self.catalog["resources"] if r["id"]=="de-handelsregister")
        self.assertNotIn("es",de["languages"])
        self.assertTrue(all(r["editorial_reviewed"] is None for r in self.catalog["resources"] if r["review_status"]=="pending"))

    def test_strict_yaml_and_schema(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.yaml";p.write_text("id: one\nid: two\n")
            with self.assertRaises(cat.CatalogError):cat.load_yaml(p)
        for mutate in [
            lambda c:c["resources"][0].update(typo_field=True),
            lambda c:c["contacts"][0].update(last_reviewed="2026-99-01"),
            lambda c:c["jurisdictions"][0].update(parent="ES"),
            lambda c:c["resources"][0].update(reporting_routes=["nonexistent"]),
            lambda c:c["playbooks"][0].update(source_path="../../escape.md"),
            lambda c:c["resources"][0].update(review_status="verified")]:
            c=copy.deepcopy(self.catalog);mutate(c)
            self.assertTrue(cat.validate_catalog(c))

    def test_seventeenth_playbook_allowed(self):
        c=copy.deepcopy(self.catalog)
        extra=copy.deepcopy(c["playbooks"][0]);extra["id"]="business-extra"
        c["playbooks"].append(extra)
        self.assertEqual(cat.validate_catalog(c),[])

    def test_global_sources_never_prove_local_readiness(self):
        s=next(s for s in self.catalog["scenarios"] if s["id"]=="csam-report")
        row=cat.coverage(self.catalog,s,"AR")
        self.assertGreater(row["general_resources"],0)
        self.assertEqual(row["status"],"pendiente")
        self.assertTrue(row["gaps"])

    def test_documents_and_sqlite_reproducible(self):
        with tempfile.TemporaryDirectory() as d:
            first,second=Path(d)/"a.sqlite",Path(d)/"b.sqlite"
            version=cat.catalog_version()
            cat.build_sqlite(self.catalog,version,first);cat.build_sqlite(self.catalog,version,second)
            self.assertEqual(first.read_bytes(),second.read_bytes())
            with closing(sqlite3.connect(first)) as con:
                self.assertGreater(con.execute("SELECT count(*) FROM docs").fetchone()[0],140)

    def test_guide_changes_change_version_without_touching_files(self):
        original=Path.read_bytes
        def changed(p):
            value=original(p)
            return value+b"\nContenido nuevo\n" if p==cat.ROOT/"docs/IA.md" else value
        before=cat.catalog_version()
        with patch.object(Path,"read_bytes",changed):
            self.assertNotEqual(before,cat.catalog_version())

    def test_last_valid_index_survives_invalid_catalog(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/"catalog.sqlite"
            cat.build_sqlite(self.catalog,"previous",db)
            with patch.object(service,"catalog_version",return_value="changed"),patch.object(service,"load_catalog",side_effect=cat.CatalogError("invalid")):
                self.assertEqual(service.ensure_database(db)[1],"previous")
                self.assertEqual(service._INDEX_STATUS,"last-valid-snapshot")


class SearchV2Tests(unittest.TestCase):
    def test_punctuation_and_empty_queries(self):
        for search in [service.search_resources,service.search_playbooks,service.search_docs]:
            self.assertEqual(search("*** !!!")["error"]["code"],"invalid_query")
            self.assertGreater(search("")["total"],0)

    def test_filter_before_limit_and_pagination(self):
        result=service.search_playbooks(scenario="procurement",limit=1)
        self.assertEqual(result["total"],1)
        self.assertEqual(result["count"],1)
        all_ids=[];offset=0
        while True:
            page=service.search_resources(limit=7,offset=offset)
            all_ids.extend(r["id"] for r in page["results"])
            if page["next_offset"] is None:break
            offset=page["next_offset"]
        self.assertEqual(len(all_ids),84);self.assertEqual(len(set(all_ids)),84)

    def test_unknown_territory_and_alias(self):
        self.assertEqual(service.search_resources(jurisdiction="ZZ")["error"]["code"],"unknown_filter")
        self.assertEqual(service.search_resources(jurisdiction="españa")["total"],service.search_resources(jurisdiction="ES")["total"])
        self.assertEqual(service.get_jurisdiction("España",limit=1)["resource_count"],service.search_resources(jurisdiction="ES")["total"])

    def test_input_output_and_platform_filters(self):
        found=service.search_resources(input_type="dominio",output_type="observacion")
        self.assertGreater(found["total"],0)
        result=service.get_reporting_routes("platform-report","AR",platform="tiktok",kind="platform-report")
        self.assertEqual(result["routes"],[])
        self.assertTrue(result["coverage"]["gaps"])

    def test_all_user_document_kinds_are_indexed(self):
        for doc in ["mantenimiento","cobertura","fuentes/de-handelsregister","indices/jurisdiccion-ar","ia"]:
            self.assertTrue(service.get_doc(doc)["found"])


class MaintenanceV2Tests(unittest.TestCase):
    def target(self,status="ok",hash_value="first"):
        return {"id":"target","url":"https://example.org/documentation","items":["contacts:demo"],
                "specialties":["safeguarding"],"critical":True,"status":status,"sha256":hash_value}

    def test_contact_change_is_proposal_not_mutation(self):
        state=advance(empty_state(),[self.target()],"daily","v1")
        state=advance(state,[self.target(hash_value="second")],"daily","v1")
        incident=state["incidents"]["target:content"]
        self.assertEqual(incident["before_sha256"],"first")
        self.assertEqual(incident["kind"],"editorial")
        self.assertFalse(incident["resolved"])
        state=advance(state,[self.target(hash_value="second")],"daily","v1")
        self.assertFalse(state["incidents"]["target:content"]["resolved"])

    def test_three_failures_recovery_and_baseline(self):
        state=advance(empty_state(),[self.target()],"daily","v1")
        for index in range(3):
            state=advance(state,[self.target("temporary-error",None)],"daily","v1")
            self.assertEqual("target:availability" in state["incidents"],index==2)
        self.assertEqual(state["checks"]["target"]["sha256"],"first")
        state=advance(state,[self.target()],"daily","v1")
        self.assertTrue(state["incidents"]["target:availability"]["resolved"])
        self.assertEqual(state["checks"]["target"]["consecutive_failures"],0)

    def test_304_uses_conditional_headers(self):
        from urllib.error import HTTPError
        seen=[]
        def opener(request,timeout):
            seen.append(dict(request.header_items()))
            raise HTTPError(request.full_url,304,"not modified",{},None)
        result=check_target(self.target(),{"sha256":"hash","etag":"etag"},opener=opener,sleep=lambda _:None)
        self.assertEqual(result["status"],"not-modified")
        self.assertEqual(result["sha256"],"hash")
        self.assertEqual(seen[0]["If-none-match"],"etag")

    def test_http_classification_and_retry_after(self):
        from urllib.error import HTTPError
        for code,expected in [(403,"blocked"),(429,"rate-limited"),(503,"temporary-error"),(410,"offline")]:
            def opener(req,timeout):
                raise HTTPError(req.full_url,code,"test",{"Retry-After":"3600"},None)
            result=check_target(self.target(),opener=opener,sleep=lambda _:None)
            self.assertEqual(result["status"],expected)
            if code==429:self.assertEqual(result["attempts"],1)

    def test_content_noise_does_not_change_hash_input(self):
        self.assertEqual(normalize_content(b"<script>A</script><p>Contacto 1</p>","text/html"),
                         normalize_content(b"<script>B</script><p>Contacto   1</p>","text/html"))
        self.assertNotEqual(normalize_content(b"<footer>Contacto 1</footer>","text/html"),
                            normalize_content(b"<footer>Contacto 2</footer>","text/html"))

    def test_history_retention_failure_and_missing_process(self):
        state=advance(empty_state(),[],"daily","v",now="2026-01-01T00:00:00+00:00")
        state=advance(state,[],"daily","v",now="2026-05-01T00:00:00+00:00",success=False)
        self.assertEqual(len(state["history"]),1)
        self.assertEqual(state["processes"]["daily"]["last_success"],"2026-01-01T00:00:00+00:00")
        self.assertTrue(process_health(state,datetime(2026,5,1,tzinfo=timezone.utc))["daily"]["stale"])
        self.assertEqual(process_health(state)["monthly"]["status"],"not-run")

    def test_same_domain_discovery_and_stable_issues(self):
        source={"id":"catalog","url":"https://example.org/","territory":"ES","include_patterns":["/dataset/"],"exclude_patterns":["/login"],"license_note":"Pendiente"}
        result=select_candidates(source,'<a href="/dataset/new">Dataset</a><a href="/login">Login</a>',set())
        self.assertEqual(len(result),1)
        a={"actionable":[{"key":"same","kind":"editorial","etag":"one"}]}
        b={"actionable":[{"key":"same","kind":"editorial","etag":"two"}]}
        self.assertEqual(stable_fingerprint(a,"m"),stable_fingerprint(b,"m"))
        self.assertEqual(set(groups(a)),set(groups(b)))


class GovernanceV2Tests(unittest.TestCase):
    def registry(self):
        now=date.today().isoformat()
        return {"default_owner":"owner","specialties":[{"id":"safeguarding","primary":"primary","backup":"backup"}],
                "people":[{"login":login,"kind":"human","specialties":["safeguarding"],"permission":"write","permission_checked_at":now} for login in ["owner","primary","backup"]]}

    def test_escalation_and_missing_reviewer(self):
        registry=self.registry(); now=datetime.now(timezone.utc)
        item={"specialty":"safeguarding","critical":True,"opened_at":(now-timedelta(hours=49)).isoformat()}
        self.assertEqual(route_review(item,registry,now)["assignee"],"backup")
        item["critical"]=False
        self.assertEqual(route_review(item,registry,now)["assignee"],"primary")
        item["opened_at"]=(now-timedelta(days=8)).isoformat()
        self.assertEqual(route_review(item,registry,now)["assignee"],"backup")
        registry["people"]=[]
        self.assertEqual(route_review(item,registry,now)["status"],"missing-reviewer")

    def test_independent_human_and_current_commit_required(self):
        registry=self.registry()
        def review(login,sha="head",kind="User"):
            return {"user":{"login":login,"type":kind},"state":"APPROVED","commit_id":sha,"submitted_at":"2026-09-13"}
        for reviews in [[review("owner")],[review("primary","old")],[review("primary",kind="Bot")],[]]:
            self.assertFalse(review_decision("owner","User","head",reviews,registry,["safeguarding"],True)["approved"])
        self.assertTrue(review_decision("owner","User","head",[review("primary")],registry,["safeguarding"],True)["approved"])
        self.assertFalse(review_decision("bot","Bot","head",[review("owner")],registry,["safeguarding"],True)["approved"])


class DocsAndSyncTests(unittest.TestCase):
    def test_anchor_validation_and_code_headings(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/"doc.md"
            p.write_text("# Documento\n\n## Sección\n\n[Ir](#sección)\n\n~~~python\n### código\n~~~\n",encoding="utf-8")
            self.assertEqual(validate_document(p,root),[])
            p.write_text(p.read_text(encoding="utf-8")+"\n[Error](#missing)\n",encoding="utf-8")
            self.assertTrue(validate_document(p,root))

    def test_no_git_and_timeout_keep_local_copy(self):
        import subprocess
        with patch.dict("os.environ",{"OSINT_ATLAS_DEDICATED":"1"}):
            for failure in [FileNotFoundError(),subprocess.TimeoutExpired("git",1)]:
                with patch.object(sync,"_git",side_effect=failure):
                    self.assertEqual(sync.try_safe_sync()["status"],"sync-failed")
                    self.assertIsNone(sync.source_age_days())

    def test_clone_mtime_cannot_reset_age(self):
        import subprocess
        stamp=int((datetime.now(timezone.utc)-timedelta(days=20)).timestamp())
        with patch.object(sync,"_git",return_value=subprocess.CompletedProcess([],0,str(stamp),"")):
            self.assertAlmostEqual(sync.source_age_days(),20,places=1)

if __name__=="__main__":unittest.main()
