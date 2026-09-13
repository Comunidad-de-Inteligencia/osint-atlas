from __future__ import annotations
import copy,io,json,subprocess,tempfile,unittest
from contextlib import closing
from datetime import date,datetime,timezone
from pathlib import Path
from unittest.mock import patch
from osint_atlas import catalog as cat, service, sync
from osint_atlas.maintenance import check_target,markdown_url
from osint_atlas.governance import review_decision
from tools.publish_state import publish_state


class AdditionalRegressionTests(unittest.TestCase):
    def test_discovery_timeout_has_one_bounded_retry(self):
        from tools.discover_candidates import fetch_catalog
        with patch("tools.discover_candidates.safe_url"),patch("time.sleep") as sleep:
            with patch("urllib.request.urlopen",side_effect=[TimeoutError(),io.BytesIO(b"OK")]) as opener:
                self.assertEqual(fetch_catalog({"url":"https://example.org"},opener,set(),sleep=sleep),"OK")
                self.assertEqual(opener.call_count,2)
                sleep.assert_called_once_with(2)

    def test_discovery_temporary_failure_requires_three_runs_and_recovers(self):
        from tools.discover_candidates import record_discovery
        from osint_atlas.maintenance import empty_state
        state=empty_state();sources=[{"id":"source"}]
        error={"key":"discovery:source","status":"temporary-error","opened_at":"2026-09-13T00:00:00+00:00","resolved":False}
        for count in range(1,4):
            state=record_discovery(state,sources,[],[error])
            self.assertEqual(error["key"] in state["incidents"],count==3)
        state=record_discovery(state,sources,[],[])
        self.assertTrue(state["incidents"][error["key"]]["resolved"])
        self.assertEqual(state["discovery"][error["key"]]["consecutive_failures"],0)

    def test_daily_weekly_share_target_identity_and_metadata(self):
        from osint_atlas.maintenance import targets
        c=cat.load_catalog()
        self.assertEqual(targets(c,"critical"),[t for t in targets(c,"all") if t["critical"]])

    def test_repository_discovery_preserves_provenance_and_ignores_images(self):
        from tools.discover_candidates import select_candidates
        source={"id":"repo","url":"https://example.org/README.md","provenance_url":"https://github.com/example/catalog",
                "format":"markdown","territory":"BR","specialty":"editorial","include_patterns":["/"],"exclude_patterns":[],"license_note":"MIT; destinos por revisar"}
        body="![Imagen](https://example.org/image.svg)\n[Fuente](https://example.org/dataset/one)\n[Ejecutar](javascript:alert)"
        candidates=select_candidates(source,body,set())
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]["source_url"],source["provenance_url"])
        self.assertEqual(candidates[0]["specialty"],"editorial")

    def test_unknown_resource_contact_is_rejected(self):
        c=copy.deepcopy(cat.load_catalog())
        c["resources"][0]["purpose"]="Consultar {{contact:invented}}"
        self.assertTrue(any("contacto desconocido" in error for error in cat.validate_catalog(c)))

    def test_catalog_paths_have_portable_order(self):
        paths=cat.source_files()
        self.assertEqual(paths,sorted(paths,key=lambda p:p.relative_to(cat.ROOT).as_posix()))

    def test_200_contact_change_is_detected_including_footer(self):
        class Response(io.BytesIO):
            status=200
            headers={"Content-Type":"text/html","ETag":"test"}
            def geturl(self):return "https://example.org/docs"
        target={"id":"test","url":"https://example.org/docs"}
        first=check_target(target,opener=lambda req,timeout:Response(b"<main>Help</main><footer>Contact 1</footer>"))
        second=check_target(target,previous=first,opener=lambda req,timeout:Response(b"<main>Help</main><footer>Contact 2</footer>"))
        self.assertEqual(first["status"],"ok")
        self.assertNotEqual(first["sha256"],second["sha256"])

    def test_markdown_destinations_cannot_inject_mentions_or_links(self):
        value=markdown_url("https://example.org/dataset/) @someone [x](y")
        self.assertNotIn(")",value);self.assertNotIn("@someone",value);self.assertNotIn(" ",value)

    def test_expired_reviews_cannot_produce_developed_coverage(self):
        c=copy.deepcopy(cat.load_catalog())
        s=next(s for s in c["scenarios"] if s["id"]=="business")
        for r in c["resources"]:
            if "business" in r["scenarios"] and "ES" in r["jurisdictions"]:
                r.update(review_status="verified",editorial_reviewed="2020-01-01",reviewer="reviewer")
        row=cat.coverage(c,s,"ES",as_of=date(2026,9,13))
        self.assertEqual(row["status"],"pendiente")

    def test_dirty_divergent_and_wrong_remote_do_not_update(self):
        for mode,expected in [("dirty","skipped-dirty"),("remote","unapproved-remote"),("diverged","needs-review")]:
            calls=[]
            def git(*args,**kwargs):
                calls.append(args)
                stdout="";code=0
                if args[0]=="log":stdout="1700000000"
                if args[0]=="status" and mode=="dirty":stdout=" M README.md"
                if args[0]=="remote":stdout="https://github.com/elsewhere/repo.git" if mode=="remote" else "https://github.com/P3M-ACTF/osint-atlas.git"
                if args[0]=="merge-base":code=1
                return subprocess.CompletedProcess([],code,stdout,"")
            with patch.dict("os.environ",{"OSINT_ATLAS_DEDICATED":"1"}),patch.object(sync,"_git",side_effect=git):
                self.assertEqual(sync.try_safe_sync()["status"],expected)
            self.assertFalse(any(args[0]=="worktree" for args in calls))

    def test_valid_index_remains_readable_during_failed_rebuild(self):
        c=cat.load_catalog()
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/"catalog.sqlite"
            cat.build_sqlite(c,"old",db)
            with patch.object(cat.os,"replace",side_effect=PermissionError("reader busy")):
                with self.assertRaises(PermissionError):cat.build_sqlite(c,"new",db)
            self.assertTrue(cat.database_is_current(db,"old"))

    def test_publisher_only_writes_state_branch_and_two_paths(self):
        from osint_atlas.maintenance import empty_state,advance
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"state.json";p.write_text(json.dumps(advance(empty_state(),[],"daily","v")),encoding="utf-8")
            calls=[]
            def api(endpoint,method="GET",payload=None,optional=False):
                calls.append((endpoint,method,payload))
                if endpoint.startswith("git/ref/"):return None
                return {"sha":"new"}
            with patch("tools.publish_state.api",side_effect=api):publish_state(p)
            tree=next(payload for endpoint,_,payload in calls if endpoint=="git/trees")
            self.assertEqual({x["path"] for x in tree["tree"]},{"README.md","state.json"})
            self.assertEqual(calls[-1][2]["ref"],"refs/heads/maintenance-state")
            self.assertFalse(any("heads/main"==endpoint.rsplit("/",1)[-1] for endpoint,_,_ in calls))

if __name__=="__main__":unittest.main()

