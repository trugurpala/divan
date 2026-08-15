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
    def _project(self, data_dir: str, root: pathlib.Path) -> str:
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

    def _create_goal(self, data_dir: str, project_id: str) -> str:
        with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
            response = handle_request(
                {
                    "command": "goal.create",
                    "project_id": project_id,
                    "intent": "Projeyi kullanıcı dostu hale getir ve kanıtlı teslim et",
                    "approve_plan_write": True,
                }
            )
        self.assertTrue(response["ok"], response)
        return str(response["result"]["goal"]["goal_id"])

    def test_capabilities_advertise_goal_work_package_commands(self):
        response = handle_request({"command": "capabilities"})

        self.assertTrue(response["ok"], response)
        self.assertIn("goal.materialize", response["result"]["commands"])
        self.assertIn("goal.tasks", response["result"]["commands"])

    def test_materialization_requires_explicit_local_task_write_approval(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as project:
            root = pathlib.Path(project)
            project_id = self._project(data_dir, root)
            goal_id = self._create_goal(data_dir, project_id)
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                response = handle_request(
                    {
                        "command": "goal.materialize",
                        "project_id": project_id,
                        "goal_id": goal_id,
                    }
                )

            self.assertFalse(response["ok"])
            self.assertEqual(
                response["error"]["code"],
                "DESKTOP_GOAL_TASK_APPROVAL_REQUIRED",
            )

    def test_materialized_work_packages_are_listed_as_planned_not_executing(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as project:
            root = pathlib.Path(project)
            project_id = self._project(data_dir, root)
            goal_id = self._create_goal(data_dir, project_id)
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                created = handle_request(
                    {
                        "command": "goal.materialize",
                        "project_id": project_id,
                        "goal_id": goal_id,
                        "approve_task_materialization": True,
                    }
                )
                listed = handle_request(
                    {
                        "command": "goal.tasks",
                        "project_id": project_id,
                        "goal_id": goal_id,
                    }
                )

            self.assertTrue(created["ok"], created)
            self.assertTrue(listed["ok"], listed)
            self.assertEqual(created["result"]["execution_authority"], "not-granted")
            self.assertEqual(
                listed["result"]["task_count"],
                created["result"]["task_count"],
            )
            self.assertGreater(len(listed["result"]["ready_task_ids"]), 0)
            self.assertTrue(
                all(task["state"] == "planned" for task in listed["result"]["tasks"])
            )
            self.assertTrue(
                all(task["mandate_id"] is None for task in listed["result"]["tasks"])
            )


if __name__ == "__main__":
    unittest.main()
