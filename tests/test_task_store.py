from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.task_model import DivanTask, TaskState
from divan_runtime.task_store import TaskStore


class TaskStoreTests(unittest.TestCase):
    def test_round_trip_preserves_state_and_events(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TaskStore(directory)
            task = DivanTask("DIV-1", "Fix login").transition(TaskState.PLANNED, "ready")
            store.save(task)
            loaded = store.load("DIV-1")
            self.assertEqual(loaded.task_id, task.task_id)
            self.assertEqual(loaded.state, TaskState.PLANNED)
            self.assertEqual(loaded.events[0].reason, "ready")

    def test_rejects_path_traversal_task_id(self):
        store = TaskStore("tasks")
        with self.assertRaises(ValueError):
            store.path_for("../outside")


if __name__ == "__main__":
    unittest.main()
