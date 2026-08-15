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


class DesktopGoalProtocolTests(unittest.TestCase):
    def _registered_project(
        self,
        data_dir: str,
        project_root: pathlib.Path,
    ) -> str:
        completed = subprocess.run(
            ["git", "init", str(project_root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        (project_root / "README.md").write_text("# Demo\n", encoding="utf-8")
        with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
            return ProjectRegistry().register(str(project_root)).project_id

    def test_capabilities_advertise_goal_commands(self):
        response = handle_request({"command": "capabilities"})
        self.assertTrue(response["ok"], response)
        self.assertIn("goal.preview", response["result"]["commands"])
        self.assertIn("goal.create", response["result"]["commands"])

    def test_preview_is_read_only_through_desktop_protocol(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as project:
            project_root = pathlib.Path(project)
            project_id = self._registered_project(data_dir, project_root)
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                response = handle_request(
                    {
                        "command": "goal.preview",
                        "project_id": project_id,
                        "intent": "Kullanıcı dostu giriş akışı ekle ve test et",
                    }
                )

            self.assertTrue(response["ok"], response)
            self.assertEqual(response["result"]["writes"], [])
            self.assertEqual(
                response["result"]["execution_authority"],
                "not-granted",
            )
            self.assertGreater(response["result"]["summary"]["task_count"], 0)
            self.assertFalse((project_root / ".divan").exists())

    def test_create_fails_closed_without_explicit_plan_write_approval(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as project:
            project_root = pathlib.Path(project)
            project_id = self._registered_project(data_dir, project_root)
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                response = handle_request(
                    {
                        "command": "goal.create",
                        "project_id": project_id,
                        "intent": "Projeyi incele ve teslim planı hazırla",
                    }
                )

            self.assertFalse(response["ok"])
            self.assertEqual(
                response["error"]["code"],
                "DESKTOP_GOAL_WRITE_APPROVAL_REQUIRED",
            )
            self.assertFalse((project_root / ".divan").exists())

    def test_create_writes_goal_contract_without_starting_execution(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as project:
            project_root = pathlib.Path(project)
            project_id = self._registered_project(data_dir, project_root)
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                response = handle_request(
                    {
                        "command": "goal.create",
                        "project_id": project_id,
                        "intent": "Projeyi incele, işi parçalara ayır ve kanıtlı teslim planla",
                        "approve_plan_write": True,
                    }
                )

            self.assertTrue(response["ok"], response)
            result = response["result"]
            goal_id = result["goal"]["goal_id"]
            self.assertEqual(result["execution_authority"], "not-granted")
            self.assertTrue(
                (project_root / ".divan" / "specs" / goal_id / "route.json").is_file()
            )
            self.assertTrue(
                (
                    project_root
                    / ".divan"
                    / "evidence"
                    / goal_id
                    / "receipt.json"
                ).is_file()
            )


if __name__ == "__main__":
    unittest.main()
