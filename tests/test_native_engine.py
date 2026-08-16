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
            agent_runner=lambda argv, cwd, timeout, stdin_text: (0, "", ""),
        )
        receipt = engine.execute(ExecutionRequest(ExecutionAction.STATUS))
        self.assertTrue(receipt.ok)
        by_id = {row["id"]: row for row in receipt.payload["agents"]}
        self.assertTrue(by_id["codex"]["available"])
        self.assertFalse(by_id["claude"]["available"])

    def test_worktree_execution_keeps_codex_prompt_out_of_argv(self):
        with tempfile.TemporaryDirectory() as directory:
            project = pathlib.Path(directory) / "repo"
            project.mkdir()
            data = pathlib.Path(directory) / "data"
            git_runner = FakeGitRunner(project)
            agent_calls = []

            def agent_runner(argv, cwd, timeout, stdin_text):
                agent_calls.append((tuple(argv), cwd, stdin_text))
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
            self.assertNotIn("secret prompt", agent_calls[0][0])
            self.assertEqual(agent_calls[0][2], "secret prompt")
            self.assertNotIn("secret prompt", receipt.argv)
            self.assertNotIn("secret prompt", str(receipt.payload))

    def test_claude_prompt_also_uses_stdin(self):
        with tempfile.TemporaryDirectory() as directory:
            project = pathlib.Path(directory) / "repo"
            project.mkdir()
            data = pathlib.Path(directory) / "data"
            git_runner = FakeGitRunner(project)
            agent_calls = []

            def agent_runner(argv, cwd, timeout, stdin_text):
                agent_calls.append((tuple(argv), stdin_text))
                return 0, '{"result":"done"}', ""

            with patch.dict(os.environ, {"DIVAN_DATA_DIR": str(data)}, clear=False):
                engine = NativeExecutionEngine(
                    agent_binaries={"claude": "C:/bin/claude.exe"},
                    git_runner=git_runner,
                    agent_runner=agent_runner,
                )
                receipt = engine.execute(
                    ExecutionRequest(
                        ExecutionAction.WORKTREE_CREATE,
                        project_root=str(project),
                        mandate_id="m-2",
                        args={
                            "name": "Claude Task",
                            "agent": "claude",
                            "prompt": "private task text",
                        },
                    )
                )

            self.assertTrue(receipt.ok)
            self.assertNotIn("private task text", agent_calls[0][0])
            self.assertEqual(agent_calls[0][1], "private task text")
            self.assertNotIn("private task text", receipt.argv)

    def test_stale_agent_capability_is_rejected_before_worktree_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            project = pathlib.Path(directory) / "repo"
            project.mkdir()
            available = {"codex": "C:/bin/codex.exe"}
            git_runner = FakeGitRunner(project)
            engine = NativeExecutionEngine(
                which=available.get,
                git_runner=git_runner,
                agent_runner=lambda argv, cwd, timeout, stdin_text: (0, "", ""),
            )
            available.clear()

            receipt = engine.execute(
                ExecutionRequest(
                    ExecutionAction.WORKTREE_CREATE,
                    project_root=str(project),
                    mandate_id="m-stale",
                    args={
                        "name": "Stale Agent",
                        "agent": "codex",
                        "prompt": "keep this isolated",
                    },
                )
            )

            self.assertFalse(receipt.ok)
            self.assertIn("capability changed", receipt.stderr)
            self.assertFalse(git_runner.calls)

    def test_file_diff_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            project = pathlib.Path(directory)
            git_runner = FakeGitRunner(project)
            engine = NativeExecutionEngine(
                agent_binaries={"codex": "codex"},
                git_runner=git_runner,
                agent_runner=lambda argv, cwd, timeout, stdin_text: (0, "", ""),
            )
            receipt = engine.execute(
                ExecutionRequest(
                    ExecutionAction.FILE_DIFF,
                    args={"worktree": str(project), "path": "*"},
                )
            )
            self.assertTrue(receipt.ok)
            self.assertIn("diff --git", receipt.payload["diff"])
            self.assertFalse(receipt.payload["staged"])
            self.assertNotIn("--cached", receipt.argv)

    def test_file_diff_can_show_exact_staged_review_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            project = pathlib.Path(directory)
            git_runner = FakeGitRunner(project)
            engine = NativeExecutionEngine(
                agent_binaries={"codex": "codex"},
                git_runner=git_runner,
                agent_runner=lambda argv, cwd, timeout, stdin_text: (0, "", ""),
            )
            receipt = engine.execute(
                ExecutionRequest(
                    ExecutionAction.FILE_DIFF,
                    args={"worktree": str(project), "path": "*", "staged": True},
                )
            )
            self.assertTrue(receipt.ok)
            self.assertTrue(receipt.payload["staged"])
            self.assertIn("--cached", receipt.argv)
            self.assertEqual(receipt.argv[-1], "--")


if __name__ == "__main__":
    unittest.main()
