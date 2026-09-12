from __future__ import annotations

import unittest

from tools.check_links import classify
from tools.publish_maintenance_issue import stable_fingerprint


class MaintenanceTests(unittest.TestCase):
    def test_http_states_are_distinct(self) -> None:
        self.assertEqual(classify(403, None), "auth-required")
        self.assertEqual(classify(429, None), "rate-limited")
        self.assertEqual(classify(503, None), "temporary-error")
        self.assertEqual(classify(410, None), "offline")

    def test_fingerprint_ignores_run_timestamp(self) -> None:
        first = {"generated_at": "2026-01-01T00:00:00Z", "actionable": [{"id": "x", "status": "offline", "checked_at": "a", "duration_ms": 1}]}
        second = {"generated_at": "2026-01-02T00:00:00Z", "actionable": [{"id": "x", "status": "offline", "checked_at": "b", "duration_ms": 9}]}
        self.assertEqual(stable_fingerprint(first, "maintenance"), stable_fingerprint(second, "maintenance"))


if __name__ == "__main__":
    unittest.main()
