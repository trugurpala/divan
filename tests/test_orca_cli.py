from __future__ import annotations

import contextlib
import hashlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import cli, goal_execution, goals, orca_coordinator, receipts
from divan_runtime.orca_engine import OrcaResult


class FakeOrcaEngine:
    def __init__(self) -> None:
        self.authority_id: str | None = None
        self.prompt: str | None = None

    def worktree_create(
        self,
        *,
        name,
        authority,
        repo_selector=None,
        agent=None,
        prompt=None,
        setup="inherit",
    ):
        self.authority_id = authority.mandate_id
        self.prompt = prompt
        return OrcaResult(
            action="worktree.create",
            argv=(
                "orca",
                "worktree",
                "create",
                "--name",
                name,
                "--agent",
                agent or "default",
                "--prompt",
                "<redacted-prompt>",
                "--setup",
                setup,
                "--json",
            ),
            mutating=True,
            mandate_id=authority.mandate_id,
            exit_code=0,
            payload={"worktree": {"id": "wt-cli-1"}},
            stdout='{"worktree":{"id":"wt-cli-1"}}',
            stderr="",
        )

    def status(self):
        return OrcaResult(
            action="status",
            argv=("orca", "status", "--json"),
            mutating=False,
            mandate_id=None,
            exit_code=0,
            payload={"ok": True},
            stdout='{"ok":true}',
            stderr="",
        )


class OrcaCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="divan-orca-cli-")
        self.addCleanup(self.temporary.cleanup)
        self.project = pathlib.Path(self.temporary.name).resolve()
        created = goals.start_goal(
            self.project,
            "execute one governed Orca CLI task",
            "verified",
            True,
            environment={},
        )
        self.goal_id = str(created["goal_id"])
        goal_execution.prepare_goal(self.project, self.goal_id, execute=True)
        self.fake = FakeOrcaEngine()
        self.original_engine = orca_coordinator.OrcaEngine
        orca_coordinator.OrcaEngine = lambda: self.fake
        self.addCleanup(self._restore_engine)

    def _restore_engine(self) -> None:
        orca_coordinator.OrcaEngine = self.original_engine

    def run_cli(self, argv: list[str]) -> tuple[int, dict]:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = cli.main([*argv, "--json"])
        return code, json.loads(stream.getvalue())

    def test_engine_status_is_read_only(self) -> None:
        code, payload = self.run_cli(["engines", "status", "--engine", "orca"])
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "ready")
        self.assertNotIn("authority", payload)

    def test_worktree_create_reuses_cli_mandate_without_exposing_prompt(self) -> None:
        prompt = "private task context that must not appear in public JSON"
        code, payload = self.run_cli(
            [
                "engines",
                "worktree-create",
                "--engine",
                "orca",
                "--project",
                str(self.project),
                "--goal",
                self.goal_id,
                "--name",
                "fix-login",
                "--agent",
                "codex",
                "--prompt",
                prompt,
                "--execute",
            ]
        )
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["status"], "started")
        self.assertEqual(payload["goal_state"], "IMPLEMENTING")
        self.assertEqual(payload["authority"]["operation"], "engines.worktree-create")
        self.assertEqual(
            payload["authority"]["scope"]["prompt_sha256"],
            hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(self.fake.authority_id, payload["authority"]["mandate_id"])
        self.assertEqual(self.fake.prompt, prompt)
        self.assertNotIn(prompt, json.dumps(payload, sort_keys=True))

        receipt_path = (
            self.project / ".divan" / "evidence" / self.goal_id / "receipt.json"
        )
        verification = receipts.verify_receipt(receipt_path)
        self.assertTrue(verification["ok"], verification["errors"])
        self.assertEqual(verification["state"], "IMPLEMENTING")

    def test_worktree_create_without_execute_is_denied_before_engine(self) -> None:
        code, payload = self.run_cli(
            [
                "engines",
                "worktree-create",
                "--project",
                str(self.project),
                "--goal",
                self.goal_id,
                "--name",
                "no-authority",
            ]
        )
        self.assertEqual(code, 1)
        self.assertFalse(payload["ok"])
        self.assertIn("explicit --execute", payload["errors"][0])
        self.assertIsNone(self.fake.authority_id)


if __name__ == "__main__":
    unittest.main()
