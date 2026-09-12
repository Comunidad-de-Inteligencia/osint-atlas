from __future__ import annotations

import unittest

from osint_atlas import service


class ServiceTests(unittest.TestCase):
    def test_search_resource_by_territory_and_scenario(self) -> None:
        result = service.search_resources("contratación", jurisdiction="ES", scenario="procurement")
        self.assertGreater(result["count"], 0)
        self.assertTrue(all("procurement" in item["scenarios"] for item in result["results"]))

    def test_manual_document_is_searchable(self) -> None:
        result = service.search_docs("rutas oficiales asistencia")
        self.assertGreater(result["count"], 0)

    def test_reporting_routes_distinguish_channel_kind(self) -> None:
        result = service.get_reporting_routes("sexual-digital-violence", "ES")
        kinds = {item["kind"] for item in result["routes"]}
        self.assertIn("takedown", kinds)
        self.assertIn("assistance", kinds)

    def test_reporting_routes_respect_territory_and_scenario(self) -> None:
        argentina = service.get_reporting_routes("csam-report", "AR")
        self.assertNotIn("eu-112", {item["id"] for item in argentina["routes"]})
        telegram = service.get_reporting_routes("platform-report", "AR")
        self.assertEqual({item["id"] for item in telegram["routes"]}, {"telegram-report"})

    def test_pending_coverage_is_visible(self) -> None:
        result = service.list_scenarios("AR")
        self.assertEqual(len(result["results"]), 16)
        self.assertTrue(any(item["status"] == "pendiente" for item in result["results"]))


if __name__ == "__main__":
    unittest.main()
