from __future__ import annotations
import json,os,sys,tempfile,unittest
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from osint_atlas.catalog import ROOT,load_catalog


class MCPWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_nine_tools_and_sixteen_walkthroughs_over_stdio(self):
        params=StdioServerParameters(command=sys.executable,args=["-m","osint_atlas.mcp_server"],
            cwd=str(ROOT),env={**os.environ,"OSINT_ATLAS_DEDICATED":"0","PYTHONIOENCODING":"utf-8"})
        with tempfile.TemporaryFile(mode="w+",encoding="utf-8") as log:
            async with stdio_client(params,errlog=log) as (read,write):
                async with ClientSession(read,write,read_timeout_seconds=30) as session:
                    await session.initialize()
                    self.assertEqual(len((await session.list_tools()).tools),9)
                    async def call(name,args):
                        result=await session.call_tool(name,args,read_timeout_seconds=30)
                        self.assertFalse(result.is_error,(name,result))
                        value=json.loads(result.content[0].text)
                        self.assertIn("catalog_version",value)
                        return value
                    resources=await call("search_resources",{"jurisdiction":"España","scenario":"procurement","limit":1})
                    self.assertGreater(resources["total"],0);self.assertEqual(resources["count"],1)
                    self.assertTrue((await call("get_resource",{"resource_id":"de-handelsregister"}))["found"])
                    self.assertGreater((await call("get_jurisdiction",{"jurisdiction_id":"ES","limit":1}))["resource_count"],1)
                    self.assertEqual((await call("search_playbooks",{"scenario":"procurement","limit":1}))["count"],1)
                    self.assertGreater((await call("search_docs",{"query":"mantenimiento","limit":1}))["total"],1)
                    self.assertTrue((await call("get_doc",{"doc_id":"mantenimiento"}))["found"])
                    self.assertTrue((await call("list_scenarios",{"jurisdiction":"AR"}))["results"][0]["gaps"])
                    routes=await call("get_reporting_routes",{"scenario":"platform-report","jurisdiction":"AR","platform":"telegram","kind":"platform-report"})
                    self.assertEqual(routes["routes"][0]["id"],"telegram-report")
                    self.assertEqual((await call("search_resources",{"query":"!!!"}))["error"]["code"],"invalid_query")
                    for p in load_catalog()["playbooks"]:
                        result=await call("get_playbook",{"playbook_id":p["id"]})
                        self.assertTrue(result["found"])
                        for section in ("Recorrido de práctica","Plantilla del resultado","Referencias responsables","Cobertura territorial"):
                            self.assertIn(section,result["content"])
                        self.assertNotIn("{{contact:",result["content"])

if __name__=="__main__":unittest.main()
