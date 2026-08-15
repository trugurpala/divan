from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import goals
from divan_runtime.agency_status import build_project_agency_status
from divan_runtime.task_model import TaskState
from divan_runtime.task_store import TaskStore


class AgencyStatusTests(unittest.TestCase):
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

    def _planned_project(
        self,
        project: pathlib.Path,
        task_root: pathlib.Path,
    ) -> tuple[TaskStore, dict[str, object]]:
        self._git_project(project)
        goal = goals.start_goal(
            project,
            "Kullanıcı dostu bir durum görünümü ekle ve kanıtla",
            "verified",
            True,
            environment={},
        )
        store = TaskStore(task_root)
        work_packages = store.materialize_goal(project, str(goal["goal_id"]))
        return store, work_packages

    def test_project_without_active_goal_is_intake(self):
        with tempfile.TemporaryDirectory() as project_dir, tempfile.TemporaryDirectory() as data_dir:
            project = pathlib.Path(project_dir)
            self._git_project(project)
            status = build_project_agency_status(
                project,
                TaskStore(pathlib.Path(data_dir) / "tasks"),
            )

        self.assertEqual(status["phase"], "INTAKE")
        self.assertEqual(status["attention"], "none")
        self.assertIsNone(status["active_goal_id"])
        self.assertEqual(status["work_packages"]["total"], 0)

    def test_materialized_goal_is_ready_without_execution_authority(self):
        with tempfile.TemporaryDirectory() as project_dir, tempfile.TemporaryDirectory() as data_dir:
            project = pathlib.Path(project_dir)
            store, work_packages = self._planned_project(
                project,
                pathlib.Path(data_dir) / "tasks",
            )
            status = build_project_agency_status(project, store)

        self.assertEqual(status["phase"], "READY_FOR_EXECUTION")
        self.assertEqual(status["attention"], "none")
        self.assertEqual(status["execution_authority"], "not-granted")
        self.assertEqual(
            status["work_packages"]["total"],
            work_packages["task_count"],
        )
        self.assertGreater(len(status["work_packages"]["ready_task_ids"]), 0)

    def test_blocked_work_package_elevates_project_attention(self):
        with tempfile.TemporaryDirectory() as project_dir, tempfile.TemporaryDirectory() as data_dir:
            project = pathlib.Path(project_dir)
            store, work_packages = self._planned_project(
                project,
                pathlib.Path(data_dir) / "tasks",
            )
            first = store.load(work_packages["ready_task_ids"][0])
            store.save(first.transition(TaskState.BLOCKED, "controlled test blocker"))
            status = build_project_agency_status(project, store)

        self.assertEqual(status["phase"], "BLOCKED")
        self.assertEqual(status["attention"], "blocked")
        self.assertEqual(status["work_packages"]["blocked"], 1)

    def test_invalid_active_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as project_dir, tempfile.TemporaryDirectory() as data_dir:
            project = pathlib.Path(project_dir)
            store, _ = self._planned_project(
                project,
                pathlib.Path(data_dir) / "tasks",
            )
            state_path = project / ".divan" / "state" / "seyir.json"
            state_path.write_text('{"schema_version": 999}\n', encoding="utf-8")
            status = build_project_agency_status(project, store)

        self.assertEqual(status["phase"], "BLOCKED")
        self.assertEqual(status["attention"], "blocked")
        self.assertEqual(status["state_health"], "invalid")


if __name__ == "__main__":
    unittest.main()
