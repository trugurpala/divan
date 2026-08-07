from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.execution_contract import ExecutionAction, ExecutionRequest
from divan_runtime.native_engine import NativeExecutionEngine


class FakeGitRunner:
    def __init__(self, project_root: pathlib.Path) -> None:
        self.project_root = project_root
        self.calls = []

    def __call__(self, argv, cwd, timeout):
        self.calls.append(tuple(argv))
        if "worktree" in argv and "add" in argv:
            destination = pathlib.Path(argv[-2])
            destination.mkdir(parents=True, exist_ok=True)
            return 0, "", ""
        if tuple(argv[-3:]) == ("worktree", "list", "--porcelain"):
            return 0, f"worktree {self.project_root}\nHEAD abc\nbranch refs/heads/main\n\n", ""
        if "diff" in argv:
            return 0, "diff --git a/a b/a\n", ""
        return 0, "", ""


class NativeExecutionEngineTests(unittest.TestCase):
    def test_status_lists_discovered_agents(self):
        engine = NativeExecutionEngine(
            agent_binaries={"codex": "C:/bin/codex.exe"},
            git_runner=lambda argv, cwd, timeout: (0, "", ""),
            agent_runner=lambda argv, cwd, timeout: (0, "", ""),
        )
        receipt = engine.execute(ExecutionRequest(ExecutionAction.STATUS))
        self.assertTrue(receipt.ok)
        by_id = {row["id"]: row for row in receipt.payload["agents"]}
        self.assertTrue(by_id["codex"]["available"])
        self.assertFalse(by_id["claude"]["available"])

    def test_worktree_execution_redacts_prompt_and_uses_selected_agent(self):
        with tempfile.TemporaryDirectory() as directory:
            project = pathlib.Path(directory) / "repo"
            project.mkdir()
            data = pathlib.Path(directory) / "data"
            git_runner = FakeGitRunner(project)
            agent_calls = []

            def agent_runner(argv, cwd, timeout):
                agent_calls.append((tuple(argv), cwd))
                return 0, '{"type":"turn.completed"}\n', ""

            with patch.dict(os.environ, {"DIVAN_DATA_DIR": str(data)}, clear=False):
                engine = NativeExecutionEngine(
                    agent_binaries={"codex": "C:/bin/codex.exe"},
                    git_runner=git_runner,
                    agent_runner=agent_runner,
                )
                receipt = engine.execute(
                    ExecutionRequest(
                        ExecutionAction.WORKTREE_CREATE,
                        project_root=str(project),
                        mandate_id="m-1",
                        args={
                            "name": "Fix Login",
                            "agent": "codex",
                            "prompt": "secret prompt",
                        },
                    )
                )

            self.assertTrue(receipt.ok)
            self.assertEqual(receipt.payload["agent"], "codex")
            self.assertEqual(receipt.payload["branch"], "divan/fix-login")
            self.assertIn("secret prompt", agent_calls[0][0])
            self.assertNotIn("secret prompt", receipt.argv)
            self.assertIn("<redacted-prompt>", receipt.argv)

    def test_file_diff_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            project = pathlib.Path(directory)
            git_runner = FakeGitRunner(project)
            engine = NativeExecutionEngine(
                agent_binaries={"codex": "codex"},
                git_runner=git_runner,
                agent_runner=lambda argv, cwd, timeout: (0, "", ""),
            )
            receipt = engine.execute(
                ExecutionRequest(
                    ExecutionAction.FILE_DIFF,
                    args={"worktree": str(project), "path": "*"},
                )
            )
            self.assertTrue(receipt.ok)
            self.assertIn("diff --git", receipt.payload["diff"])


if __name__ == "__main__":
    unittest.main()
