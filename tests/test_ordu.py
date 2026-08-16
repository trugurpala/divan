from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import ordu


class OrduTests(unittest.TestCase):
    def test_plan_is_ordered_and_requires_explicit_execution_approval(self):
        result = ordu.plan("Build a user-friendly settings panel", logical_cpus=24)
        self.assertEqual(result["max_parallel_workers"], 4)
        self.assertTrue(result["approval_required_before_mutation"])
        self.assertEqual([unit["id"] for unit in result["units"]], [
            "discover", "plan", "quality-map", "implement", "verify", "review",
        ])
        verify = next(unit for unit in result["units"] if unit["id"] == "verify")
        self.assertEqual(verify["depends_on"], ("implement", "quality-map"))

    def test_budget_keeps_one_worker_on_small_hardware(self):
        self.assertEqual(ordu.worker_budget(2), 1)

    def test_planning_receipts_do_not_claim_execution_or_review_completed(self):
        statuses = ordu.initial_unit_statuses(ordu.plan("Improve onboarding"))
        self.assertEqual(statuses["discover"], "pass")
        self.assertEqual(statuses["quality-map"], "pass")
        self.assertEqual(statuses["implement"], "pending")
        self.assertEqual(statuses["verify"], "pending")
        self.assertEqual(statuses["review"], "pending")


if __name__ == "__main__":
    unittest.main()
