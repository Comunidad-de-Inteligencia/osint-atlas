from __future__ import annotations

import unittest

from osint_atlas.mcp_server import mcp


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_exact_public_tool_set(self) -> None:
        tools = await mcp.list_tools()
        names = {tool.name for tool in tools}
        self.assertEqual(
            names,
            {
                "search_resources",
                "get_resource",
                "get_jurisdiction",
                "search_playbooks",
                "get_playbook",
                "search_docs",
                "get_doc",
                "list_scenarios",
                "get_reporting_routes",
            },
        )


if __name__ == "__main__":
    unittest.main()
