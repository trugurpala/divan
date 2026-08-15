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
from divan_runtime.task_model import TaskState
from divan_runtime.task_store import TaskStore


class GoalWorkPackageTests(unittest.TestCase):
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

    def _goal(self, root: pathlib.Path) -> str:
        result = goals.start_goal(
            root,
            "Kullanıcı dostu akışı geliştir ve kanıtlı teslim et",
            "verified",
            True,
            environment={},
        )
        return str(result["goal_id"])

    def test_materialization_is_idempotent_and_preserves_route_metadata(self):
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as state:
            root = pathlib.Path(project)
            self._git_project(root)
            goal_id = self._goal(root)
            store = TaskStore(pathlib.Path(state) / "tasks")

            first = store.materialize_goal(root, goal_id)
            second = store.materialize_goal(root, goal_id)

            self.assertGreater(first["task_count"], 0)
            self.assertEqual(len(first["created_task_ids"]), first["task_count"])
            self.assertEqual(second["created_task_ids"], [])
            self.assertEqual(len(second["retained_task_ids"]), first["task_count"])
            self.assertGreater(len(first["ready_task_ids"]), 0)
            self.assertEqual(first["execution_authority"], "not-granted")
            for task in first["tasks"]:
                metadata = task["metadata"]
                self.assertEqual(metadata["goal_id"], goal_id)
                self.assertEqual(metadata["source"], "nizam-i-sefer")
                self.assertIsInstance(metadata["depends_on"], list)
                self.assertIsInstance(metadata["required_evidence"], list)

    def test_ready_tasks_advance_only_after_dependencies_are_merged(self):
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as state:
            root = pathlib.Path(project)
            self._git_project(root)
            goal_id = self._goal(root)
            store = TaskStore(pathlib.Path(state) / "tasks")
            materialized = store.materialize_goal(root, goal_id)
            first_ready = materialized["ready_task_ids"][0]
            task = store.load(first_ready)
            for target in (
                TaskState.RUNNING,
                TaskState.REVIEW,
                TaskState.PASSED,
                TaskState.APPROVAL,
                TaskState.MERGED,
            ):
                task = task.transition(target, "test progression")
            store.save(task)

            status = store.goal_tasks(root, goal_id)

            self.assertNotIn(first_ready, status["ready_task_ids"])
            self.assertGreater(len(status["ready_task_ids"]), 0)

    def test_materialization_rejects_any_route_byte_tampering(self):
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as state:
            root = pathlib.Path(project)
            self._git_project(root)
            goal_id = self._goal(root)
            route = root / ".divan" / "specs" / goal_id / "route.json"
            route.write_bytes(route.read_bytes() + b" ")
            verification = goals.goal_status(root, goal_id)
            self.assertFalse(verification["ok"], verification)

            with self.assertRaises(ValueError):
                TaskStore(pathlib.Path(state) / "tasks").materialize_goal(root, goal_id)

    def test_same_goal_id_isolated_by_project_root(self):
        with (
            tempfile.TemporaryDirectory() as first_project,
            tempfile.TemporaryDirectory() as second_project,
            tempfile.TemporaryDirectory() as state,
        ):
            # The goal ID seed includes the inspected project name, so two roots
            # must share a directory name to collide the way this test requires.
            first = pathlib.Path(first_project) / "demo"
            second = pathlib.Path(second_project) / "demo"
            self._git_project(first)
            self._git_project(second)
            first_goal = self._goal(first)
            second_goal = self._goal(second)
            self.assertEqual(first_goal, second_goal)
            store = TaskStore(pathlib.Path(state) / "tasks")

            first_result = store.materialize_goal(first, first_goal)
            second_result = store.materialize_goal(second, second_goal)
            first_status = store.goal_tasks(first, first_goal)

            self.assertEqual(first_status["task_count"], first_result["task_count"])
            self.assertNotEqual(
                set(first_result["created_task_ids"]),
                set(second_result["created_task_ids"]),
            )
            self.assertTrue(
                all(
                    task["project_root"] == str(first.resolve())
                    for task in first_status["tasks"]
                )
            )


if __name__ == "__main__":
    unittest.main()
