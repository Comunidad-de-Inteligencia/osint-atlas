from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from osint_atlas.catalog import (
    applies_to,
    build_outputs,
    build_sqlite,
    catalog_version,
    load_catalog,
    validate_catalog,
)


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_catalog()
        cls.version = catalog_version()

    def test_v01_scope(self) -> None:
        self.assertGreaterEqual(len(self.catalog["resources"]), 80)
        self.assertEqual(len(self.catalog["playbooks"]), 16)
        self.assertEqual(validate_catalog(self.catalog), [])

    def test_every_scenario_has_resources_and_playbook(self) -> None:
        resource_scenarios = {scenario for resource in self.catalog["resources"] for scenario in resource["scenarios"]}
        playbook_scenarios = {item["scenario"] for item in self.catalog["playbooks"]}
        scenario_ids = {item["id"] for item in self.catalog["scenarios"]}
        self.assertEqual(scenario_ids, playbook_scenarios)
        self.assertEqual(scenario_ids - resource_scenarios, set())

    def test_sensitive_routes_are_present(self) -> None:
        contacts = {item["id"] for item in self.catalog["contacts"]}
        csam = [item for item in self.catalog["resources"] if "csam-report" in item["scenarios"]]
        self.assertTrue(csam)
        self.assertTrue(any(set(item.get("reporting_routes", [])) & contacts for item in csam))
        procedure = Path("docs/es/procedimientos/reportar-csam.md").read_text(encoding="utf-8").casefold()
        for phrase in ("no descargues", "guardes", "no constituye una denuncia"):
            self.assertIn(phrase, procedure)
        self.assertIn("ni compartas", procedure)

    def test_catastro_exclusions(self) -> None:
        resource = next(item for item in self.catalog["resources"] if item["id"] == "es-catastro")
        self.assertTrue(applies_to(resource, "ES", self.catalog["jurisdictions"]))
        self.assertFalse(applies_to(resource, "ES-PV", self.catalog["jurisdictions"]))
        self.assertFalse(applies_to(resource, "ES-NC", self.catalog["jurisdictions"]))
        self.assertFalse(applies_to(resource, "ES-BI", self.catalog["jurisdictions"]))

    def test_new_parents_keep_national_cards(self) -> None:
        jurisdictions = self.catalog["jurisdictions"]
        parents = {item["id"]: item["parent"] for item in jurisdictions}
        self.assertEqual(parents["EU"], "EUROPE")
        self.assertEqual(parents["GB"], "EUROPE")
        self.assertNotEqual(parents["GB"], "EU")
        self.assertEqual(parents["AR"], "AMERICA")
        self.assertEqual(parents["ES-BI"], "ES-PV")
        self.assertEqual(parents["ES-MAD"], "ES")
        by_id = {item["id"]: item for item in self.catalog["resources"]}
        self.assertTrue(applies_to(by_id["es-boe"], "ES", jurisdictions))
        self.assertTrue(applies_to(by_id["ar-boletin"], "AR", jurisdictions))
        self.assertTrue(applies_to(by_id["gb-companies-house"], "GB", jurisdictions))
        self.assertTrue(applies_to(by_id["eu-eurlex"], "ES", jurisdictions))
        self.assertFalse(applies_to(by_id["eu-eurlex"], "GB", jurisdictions))
        spain = build_outputs(self.catalog, self.version)[Path(__file__).resolve().parents[1] / "docs/es/indices/jurisdiccion-es.md"]
        self.assertIn("## Fuentes de un territorio más concreto", spain)
        self.assertIn("Cámaras de tráfico del Ayuntamiento de Madrid", spain)

    def test_generation_is_deterministic(self) -> None:
        self.assertEqual(build_outputs(self.catalog, self.version), build_outputs(self.catalog, self.version))

    def test_sqlite_contains_all_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.sqlite"
            build_sqlite(self.catalog, self.version, path)
            self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
