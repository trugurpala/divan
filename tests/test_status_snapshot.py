from __future__ import annotations

import datetime
import importlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
RUNTIME = PLUGIN_ROOT / "divan_runtime"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import goals, receipts, timeouts  # noqa: E402

NOW = datetime.datetime(2026, 7, 30, 12, 0, tzinfo=datetime.UTC)
SECRET = "ghp_abcdefghijklmnopqrstuvwxyz123456"


def load_status():
    if not (RUNTIME / "status.py").is_file():
        raise AssertionError("status.py is missing")
    return importlib.import_module("divan_runtime.status")


def create_goal(project: pathlib.Path, intent: str = "Build a friendly dashboard") -> str:
    result = goals.start_goal(
        project,
        intent,
        "verified",
        True,
        environment={},
    )
    return str(result["goal_id"])


class StatusSnapshotTests(unittest.TestCase):
    def test_empty_project_is_a_valid_no_active_goal_snapshot(self) -> None:
        module = load_status()
        with tempfile.TemporaryDirectory(prefix="divan-status-empty-") as temporary:
            result = module.build_snapshot(pathlib.Path(temporary), "tr", NOW)

        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["product"]["name"], "Divan")
        self.assertEqual(result["locale"], "tr")
        self.assertEqual(result["copy"]["app.title"], "Divan Seyir")
        self.assertEqual(result["copy"]["progress.current_task"], "Şu an ne yapılıyor?")
        self.assertEqual(result["goal"]["status"], "NO_ACTIVE_GOAL")
        self.assertIsNone(result["goal"]["id"])
        self.assertIsNone(result["blocker"])
        self.assertEqual(result["tasks"], [])
        self.assertEqual(result["wait_state"]["command_class"], "verify")
        self.assertEqual(
            result["wait_state"]["timeout_seconds"],
            timeouts.resolve_default("verify").configured_seconds,
        )
        self.assertGreaterEqual(result["wait_state"]["timeout_seconds"], 720)
        self.assertEqual(result["wait_state"]["normal_after_seconds"], 10)
        self.assertEqual(result["wait_state"]["attention_after_seconds"], 60)
        self.assertIn("wait.title", result["copy"])
        self.assertIn("wait.explanation", result["copy"])

    def test_snapshot_uses_existing_goal_and_never_exposes_absolute_path(self) -> None:
        module = load_status()
        with tempfile.TemporaryDirectory(prefix="divan-status-goal-") as temporary:
            project = pathlib.Path(temporary)
            identifier = create_goal(project)
            result = module.build_snapshot(project, "en", NOW)
            rendered = json.dumps(result, ensure_ascii=False)

        self.assertEqual(result["goal"]["id"], identifier)
        self.assertEqual(result["goal"]["status"], "DISCOVERED")
        self.assertEqual(result["current"]["phase"], "FERMAN")
        self.assertTrue(result["tasks"])
        self.assertEqual(result["wait_state"]["source"], "benchmark")
        self.assertGreaterEqual(result["wait_state"]["sample_count"], 12)
        self.assertNotIn(str(project), rendered)

    def test_snapshot_redacts_secrets_and_surfaces_blocker_reason(self) -> None:
        module = load_status()
        with tempfile.TemporaryDirectory(prefix="divan-status-secret-") as temporary:
            project = pathlib.Path(temporary)
            identifier = create_goal(project, f"Deploy token={SECRET}")
            receipt = (
                project / ".divan" / "evidence" / identifier / "receipt.json"
            )
            receipts.append_transition(
                receipt,
                "BLOCKED",
                reason=f"provider token={SECRET} is unavailable",
            )
            result = module.build_snapshot(project, "en", NOW)
            rendered = json.dumps(result, ensure_ascii=False)

        self.assertNotIn(SECRET, rendered)
        self.assertEqual(result["goal"]["status"], "BLOCKED")
        self.assertIn("[REDACTED_SECRET]", str(result["blocker"]["reason"]))

    def test_git_snapshot_is_bounded_and_reports_dirty_state(self) -> None:
        module = load_status()
        with tempfile.TemporaryDirectory(prefix="divan-status-git-") as temporary:
            project = pathlib.Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=project, check=True)
            subprocess.run(
                ["git", "config", "user.email", "status@example.invalid"],
                cwd=project,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Status Test"],
                cwd=project,
                check=True,
            )
            (project / "tracked.txt").write_text("one\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=project, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "initial"],
                cwd=project,
                check=True,
            )
            (project / "tracked.txt").write_text("two\n", encoding="utf-8")
            result = module.build_snapshot(project, "en", NOW)

        self.assertIsInstance(result["project"]["branch"], str)
        self.assertRegex(result["project"]["head"], r"^[0-9a-f]{7}$")
        self.assertTrue(result["project"]["dirty"])
        self.assertNotIn("path", result["project"])

    def test_etag_ignores_generation_time_but_tracks_real_changes(self) -> None:
        module = load_status()
        with tempfile.TemporaryDirectory(prefix="divan-status-etag-") as temporary:
            project = pathlib.Path(temporary)
            first = module.build_snapshot(project, "en", NOW)
            second = module.build_snapshot(
                project,
                "en",
                NOW + datetime.timedelta(minutes=1),
            )
            changed = {**second, "goal": {**second["goal"], "status": "RUNNING"}}

        self.assertEqual(module.snapshot_etag(first), module.snapshot_etag(second))
        self.assertNotEqual(module.snapshot_etag(second), module.snapshot_etag(changed))

    def test_git_probe_disables_locks_fsmonitor_and_interactive_stdin(self) -> None:
        module = load_status()
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="main\n",
            stderr="",
        )
        with mock.patch.object(
            module.subprocess,
            "run",
            return_value=completed,
        ) as run:
            value = module._git_value(ROOT, ["branch", "--show-current"])

        self.assertEqual(value, "main")
        arguments = run.call_args.args[0]
        self.assertIn("core.fsmonitor=false", arguments)
        self.assertEqual(run.call_args.kwargs["env"]["GIT_OPTIONAL_LOCKS"], "0")
        self.assertIs(run.call_args.kwargs["stdin"], subprocess.DEVNULL)

    def test_runtime_version_uses_the_bundled_identity_file(self) -> None:
        module = load_status()
        with tempfile.TemporaryDirectory(prefix="divan-version-") as temporary:
            runtime = pathlib.Path(temporary)
            (runtime / "version.txt").write_text("0.18.2\n", encoding="utf-8")

            self.assertEqual(module._version(runtime), "0.18.2")


if __name__ == "__main__":
    unittest.main()
