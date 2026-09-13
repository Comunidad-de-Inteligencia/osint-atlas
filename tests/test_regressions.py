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

