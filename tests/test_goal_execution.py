from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import goal_execution, goals, receipts, seyir_state


class GoalExecutionPreparationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="divan-goal-prepare-")
        self.addCleanup(self.temporary.cleanup)
        self.project = pathlib.Path(self.temporary.name).resolve()
        created = goals.start_goal(
            self.project,
            "prepare a deterministic execution goal",
            "verified",
            True,
            environment={},
        )
        self.goal_id = str(created["goal_id"])
        self.receipt_path = (
            self.project / ".divan" / "evidence" / self.goal_id / "receipt.json"
        )

    def test_preview_is_read_only_and_lists_legal_transitions(self) -> None:
        before = self.receipt_path.read_bytes()
        result = goal_execution.prepare_goal(
            self.project,
            self.goal_id,
            execute=False,
        )
        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["from"], "DISCOVERED")
        self.assertEqual(result["to"], "PLANNED")
        self.assertEqual(result["transitions"], ["SPECIFIED", "PLANNED"])
        self.assertEqual(self.receipt_path.read_bytes(), before)

    def test_execute_advances_in_order_and_rebinds_seyir_cursor(self) -> None:
        result = goal_execution.prepare_goal(
            self.project,
            self.goal_id,
            execute=True,
        )
        self.assertEqual(result["status"], "prepared")
        verification = receipts.verify_receipt(self.receipt_path)
        self.assertTrue(verification["ok"], verification["errors"])
        self.assertEqual(verification["state"], "PLANNED")

        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(
            [event["to_state"] for event in receipt["events"]],
            ["DISCOVERED", "SPECIFIED", "PLANNED"],
        )
        active = seyir_state.load(self.project)
        self.assertEqual(active["active_goal_id"], self.goal_id)
        self.assertEqual(active["receipt_event_hash"], receipt["events"][-1]["hash"])

    def test_prepare_is_idempotent_once_goal_is_planned(self) -> None:
        goal_execution.prepare_goal(self.project, self.goal_id, execute=True)
        before = self.receipt_path.read_bytes()
        result = goal_execution.prepare_goal(self.project, self.goal_id, execute=True)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["transitions"], [])
        self.assertEqual(self.receipt_path.read_bytes(), before)

    def test_tampered_bound_plan_is_rejected(self) -> None:
        plan = self.project / ".divan" / "specs" / self.goal_id / "plan.md"
        plan.write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "hash does not match"):
            goal_execution.prepare_goal(self.project, self.goal_id, execute=True)


if __name__ == "__main__":
    unittest.main()
