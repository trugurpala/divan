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

from divan_runtime.desktop_api import create_goal, preview_goal
from divan_runtime.desktop_protocol_support import ProtocolValidationError
from divan_runtime.project_registry import ProjectRegistry


class DesktopGoalTests(unittest.TestCase):
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

    def test_preview_is_read_only_and_exposes_nizam_i_sefer_summary(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as project:
            project_root = pathlib.Path(project)
            self._git_project(project_root)
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                record = ProjectRegistry().register(str(project_root))
                result = preview_goal(
                    {
                        "project_id": record.project_id,
                        "intent": "Kullanıcı dostu bir giriş akışı ekle ve test et",
                    }
                )

            self.assertEqual(result["writes"], [])
            self.assertEqual(result["execution_authority"], "not-granted")
            self.assertGreater(result["summary"]["task_count"], 0)
            self.assertGreater(result["summary"]["workstream_count"], 0)
            self.assertIn(
                result["summary"]["lane"],
                {"sequential", "bounded-parallel"},
            )
            self.assertFalse((project_root / ".divan").exists())

    def test_create_requires_explicit_plan_write_approval(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as project:
            project_root = pathlib.Path(project)
            self._git_project(project_root)
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                record = ProjectRegistry().register(str(project_root))
                with self.assertRaises(ProtocolValidationError) as caught:
                    create_goal(
                        {
                            "project_id": record.project_id,
                            "intent": "Projeyi incele ve teslim planı hazırla",
                        }
                    )

            self.assertEqual(
                caught.exception.code,
                "DESKTOP_GOAL_WRITE_APPROVAL_REQUIRED",
            )
            self.assertFalse((project_root / ".divan").exists())

    def test_create_persists_goal_artifacts_but_grants_no_execution_authority(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as project:
            project_root = pathlib.Path(project)
            self._git_project(project_root)
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                record = ProjectRegistry().register(str(project_root))
                result = create_goal(
                    {
                        "project_id": record.project_id,
                        "intent": "Projeyi incele, işi parçalara ayır ve kanıtlı teslim planla",
                        "approve_plan_write": True,
                    }
                )

            goal = result["goal"]
            goal_id = goal["goal_id"]
            spec_root = project_root / ".divan" / "specs" / goal_id
            receipt = project_root / ".divan" / "evidence" / goal_id / "receipt.json"
            self.assertIn(goal["status"], {"created", "unchanged"})
            self.assertEqual(result["execution_authority"], "not-granted")
            self.assertTrue((spec_root / "spec.md").is_file())
            self.assertTrue((spec_root / "plan.md").is_file())
            self.assertTrue((spec_root / "tasks.md").is_file())
            self.assertTrue((spec_root / "route.json").is_file())
            self.assertTrue(receipt.is_file())
            self.assertGreater(result["summary"]["task_count"], 0)


if __name__ == "__main__":
    unittest.main()
