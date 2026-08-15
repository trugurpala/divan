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
from divan_runtime.project_registry import ProjectRegistry


class DesktopGoalWorkPackageTests(unittest.TestCase):
    def _registered_project(self, data_dir: str, root: pathlib.Path) -> str:
        completed = subprocess.run(
            ["git", "init", str(root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        (root / "README.md").write_text("# Demo\n", encoding="utf-8")
        with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
            return ProjectRegistry().register(str(root)).project_id

    def test_goal_create_returns_planned_dependency_aware_work_packages(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as project:
            root = pathlib.Path(project)
            project_id = self._registered_project(data_dir, root)
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                response = handle_request(
                    {
                        "command": "goal.create",
                        "project_id": project_id,
                        "intent": "Projeyi kullanıcı dostu hale getir ve kanıtlı teslim et",
                        "approve_plan_write": True,
                    }
                )
                tasks = handle_request({"command": "task.list"})

            self.assertTrue(response["ok"], response)
            self.assertTrue(tasks["ok"], tasks)
            packages = response["result"]["work_packages"]
            self.assertEqual(response["result"]["execution_authority"], "not-granted")
            self.assertEqual(packages["execution_authority"], "not-granted")
            self.assertGreater(packages["task_count"], 0)
            self.assertGreater(len(packages["ready_task_ids"]), 0)
            self.assertEqual(len(tasks["result"]), packages["task_count"])
            self.assertTrue(all(task["state"] == "planned" for task in tasks["result"]))
            self.assertTrue(all(task["mandate_id"] is None for task in tasks["result"]))

    def test_goal_create_without_plan_write_approval_creates_no_tasks(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as project:
            root = pathlib.Path(project)
            project_id = self._registered_project(data_dir, root)
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                response = handle_request(
                    {
                        "command": "goal.create",
                        "project_id": project_id,
                        "intent": "Projeyi kullanıcı dostu hale getir",
                    }
                )
                tasks = handle_request({"command": "task.list"})

            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "DESKTOP_GOAL_WRITE_APPROVAL_REQUIRED")
            self.assertTrue(tasks["ok"], tasks)
            self.assertEqual(tasks["result"], [])
            self.assertFalse((root / ".divan").exists())


if __name__ == "__main__":
    unittest.main()
