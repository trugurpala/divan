from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.desktop_protocol import handle_request
from divan_runtime.execution_contract import ExecutionAction, ExecutionReceipt
from divan_runtime.execution_router import ExecutionRouter
from divan_runtime.project_registry import ProjectRegistry


class RecordingEngine:
    """Minimal engine that records requests so an accepted start is observable."""

    engine_id = "native"

    def __init__(self) -> None:
        self.requests: list[object] = []

    def execute(self, request):
        self.requests.append(request)
        return ExecutionReceipt(
            engine="native",
            action=request.action,
            ok=True,
            exit_code=0,
            payload={"worktree": "C:/tmp/worktree", "agent": "codex"},
            stdout="",
            stderr="",
            argv=("codex", "exec", "<redacted-prompt>"),
            mandate_id=request.mandate_id,
        )


class DesktopGoalIntegrityTests(unittest.TestCase):
    # An intent whose redaction changes the planning text. start_goal plans from
    # the redacted form, so a preview built from the raw form used to describe a
    # different plan than the one that got written.
    SECRET_INTENT = "API_KEY=abc123 ile calisan odeme entegrasyonunu duzelt ve test et"

    def _git_project(self, root: pathlib.Path) -> None:
        completed = subprocess.run(
            ["git", "init", str(root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        (root / "README.md").write_text("# Demo\n", encoding="utf-8")

    def _registered_project(self, data_dir: str, root: pathlib.Path) -> str:
        self._git_project(root)
        with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
            return ProjectRegistry().register(str(root)).project_id

    def test_preview_describes_the_plan_that_gets_persisted(self):
        with (
            tempfile.TemporaryDirectory() as data_dir,
            tempfile.TemporaryDirectory() as project,
        ):
            root = pathlib.Path(project)
            project_id = self._registered_project(data_dir, root)
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                preview = handle_request(
                    {
                        "command": "goal.preview",
                        "project_id": project_id,
                        "intent": self.SECRET_INTENT,
                    }
                )
                created = handle_request(
                    {
                        "command": "goal.create",
                        "project_id": project_id,
                        "intent": self.SECRET_INTENT,
                        "approve_plan_write": True,
                    }
                )

            self.assertTrue(preview["ok"], preview)
            self.assertTrue(created["ok"], created)
            previewed = preview["result"]["summary"]
            summary = created["result"]["summary"]
            packages = created["result"]["work_packages"]

            self.assertEqual(previewed["route_id"], packages["route_id"])
            self.assertEqual(previewed["task_count"], packages["task_count"])
            self.assertEqual(summary["route_id"], packages["route_id"])
            self.assertEqual(summary["task_count"], packages["task_count"])
            self.assertNotIn("abc123", preview["result"]["intent"])

    def test_goal_create_refuses_a_project_root_that_is_not_a_git_repository(self):
        with (
            tempfile.TemporaryDirectory() as data_dir,
            tempfile.TemporaryDirectory() as project,
        ):
            root = pathlib.Path(project) / "plain"
            root.mkdir()
            (root / "README.md").write_text("# plain\n", encoding="utf-8")
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                response = handle_request(
                    {
                        "command": "goal.create",
                        "project_root": str(root),
                        "intent": "bu klasoru incele ve testleri gecir",
                        "approve_plan_write": True,
                    }
                )
                tasks = handle_request({"command": "task.list"})

            self.assertFalse(response["ok"], response)
            self.assertEqual(response["error"]["code"], "DESKTOP_PROJECT_ROOT_INVALID")
            self.assertFalse((root / ".divan").exists())
            self.assertTrue(tasks["ok"], tasks)
            self.assertEqual(tasks["result"], [])

    def test_task_start_refuses_a_work_package_with_unmerged_dependencies(self):
        with (
            tempfile.TemporaryDirectory() as data_dir,
            tempfile.TemporaryDirectory() as project,
        ):
            root = pathlib.Path(project)
            project_id = self._registered_project(data_dir, root)
            router = ExecutionRouter([RecordingEngine()], default_engine="native")
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                created = handle_request(
                    {
                        "command": "goal.create",
                        "project_id": project_id,
                        "intent": "Projeyi kullanıcı dostu hale getir ve kanıtlı teslim et",
                        "approve_plan_write": True,
                    }
                )
                self.assertTrue(created["ok"], created)
                packages = created["result"]["work_packages"]
                ready = set(packages["ready_task_ids"])
                blocked = [
                    task
                    for task in packages["tasks"]
                    if task["task_id"] not in ready
                    and task["metadata"].get("depends_on")
                ]
                self.assertTrue(blocked, packages)

                response = handle_request(
                    {
                        "command": "task.start",
                        "task_id": blocked[0]["task_id"],
                        "agent": "codex",
                        "approve_execution": True,
                    },
                    router,
                )

            self.assertFalse(response["ok"], response)
            self.assertEqual(
                response["error"]["code"], "DESKTOP_TASK_DEPENDENCIES_PENDING"
            )

    def test_saved_work_packages_stay_queryable_by_goal(self):
        with (
            tempfile.TemporaryDirectory() as data_dir,
            tempfile.TemporaryDirectory() as project,
        ):
            root = pathlib.Path(project)
            project_id = self._registered_project(data_dir, root)
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                created = handle_request(
                    {
                        "command": "goal.create",
                        "project_id": project_id,
                        "intent": "Projeyi kullanıcı dostu hale getir ve kanıtlı teslim et",
                        "approve_plan_write": True,
                    }
                )
                self.assertTrue(created["ok"], created)
                goal_id = created["result"]["goal"]["goal_id"]
                # A later session only knows the project and the goal id.
                response = handle_request(
                    {
                        "command": "goal.tasks",
                        "project_id": project_id,
                        "goal_id": goal_id,
                    }
                )

            self.assertTrue(response["ok"], response)
            packages = created["result"]["work_packages"]
            self.assertEqual(response["result"]["goal_id"], goal_id)
            self.assertEqual(response["result"]["task_count"], packages["task_count"])
            self.assertEqual(
                response["result"]["ready_task_ids"], packages["ready_task_ids"]
            )


if __name__ == "__main__":
    unittest.main()
