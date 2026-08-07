from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import receipts
from divan_runtime.orca_coordinator import create_worktree
from divan_runtime.orca_engine import OrcaEngine, RunnerResult

GOAL_ID = "goal-123456789abc"


class FakeRunner:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv, cwd, timeout):
        self.calls.append(tuple(argv))
        return RunnerResult(
            self.returncode,
            '{"worktree":{"id":"wt-1"}}' if self.returncode == 0 else "",
            "" if self.returncode == 0 else "orca failed",
        )


class OrcaCoordinatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="divan-orca-coordinator-")
        self.addCleanup(self.temporary.cleanup)
        self.project = pathlib.Path(self.temporary.name).resolve()
        self.receipt_path = self._seed_goal()

    def _seed_goal(self) -> pathlib.Path:
        artifact = self.project / ".divan" / "specs" / GOAL_ID / "spec.md"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("# Test goal\n", encoding="utf-8")
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        value = receipts.new_receipt(
            GOAL_ID,
            "test governed Orca execution",
            "VERIFIED",
            {f".divan/specs/{GOAL_ID}/spec.md": digest},
        )
        receipt_path = self.project / ".divan" / "evidence" / GOAL_ID / "receipt.json"
        receipts.write_receipt(receipt_path, value)
        receipts.append_transition(receipt_path, "SPECIFIED")
        receipts.append_transition(receipt_path, "PLANNED")
        return receipt_path

    def _engine(self, runner: FakeRunner) -> OrcaEngine:
        return OrcaEngine(runner=runner)

    def test_execute_binds_existing_governance_mandate_and_advances_receipt(self) -> None:
        runner = FakeRunner()
        result = create_worktree(
            self.project,
            GOAL_ID,
            name="fix-login",
            agent="codex",
            prompt="token=super-secret-task-context",
            execute=True,
            engine=self._engine(runner),
        )

        self.assertEqual(result["status"], "started")
        self.assertEqual(result["goal_state"], "IMPLEMENTING")
        self.assertTrue(result["receipt_updated"])
        self.assertRegex(result["authority"]["mandate_id"], r"^mandate-[0-9a-f]{16}$")
        self.assertEqual(result["engine_result"]["mandate_id"], result["authority"]["mandate_id"])
        self.assertIn("token=super-secret-task-context", runner.calls[0])
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("super-secret-task-context", serialized)

        receipt_text = self.receipt_path.read_text(encoding="utf-8")
        self.assertNotIn("super-secret-task-context", receipt_text)
        receipt = json.loads(receipt_text)
        self.assertEqual(receipt["state"], "IMPLEMENTING")
        self.assertIn("engine:orca", receipt["events"][-1]["evidence"])

    def test_preview_authority_cannot_mutate_or_call_orca(self) -> None:
        runner = FakeRunner()
        with self.assertRaisesRegex(ValueError, "explicit --execute"):
            create_worktree(
                self.project,
                GOAL_ID,
                name="fix-login",
                execute=False,
                engine=self._engine(runner),
            )
        self.assertEqual(runner.calls, [])

    def test_failed_orca_does_not_advance_goal_receipt(self) -> None:
        runner = FakeRunner(returncode=2)
        result = create_worktree(
            self.project,
            GOAL_ID,
            name="fix-login",
            execute=True,
            engine=self._engine(runner),
        )
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["receipt_updated"])
        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["state"], "PLANNED")

    def test_unplanned_goal_is_rejected_before_orca(self) -> None:
        other = "goal-aaaaaaaaaaaa"
        artifact = self.project / ".divan" / "specs" / other / "spec.md"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("# Other\n", encoding="utf-8")
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        receipt_path = self.project / ".divan" / "evidence" / other / "receipt.json"
        receipts.write_receipt(
            receipt_path,
            receipts.new_receipt(
                other,
                "not planned",
                "VERIFIED",
                {f".divan/specs/{other}/spec.md": digest},
            ),
        )
        runner = FakeRunner()
        with self.assertRaisesRegex(ValueError, "cannot execute Orca"):
            create_worktree(
                self.project,
                other,
                name="not-allowed",
                execute=True,
                engine=self._engine(runner),
            )
        self.assertEqual(runner.calls, [])


if __name__ == "__main__":
    unittest.main()
