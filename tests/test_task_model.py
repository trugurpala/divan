from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.evidence import EvidenceStore, build_evidence
from divan_runtime.task_model import DivanTask, InvalidTaskTransition, TaskState


class TaskModelTests(unittest.TestCase):
    def test_happy_path_reaches_release(self):
        task = DivanTask("task-1", "Fix login")
        for state in (
            TaskState.PLANNED,
            TaskState.RUNNING,
            TaskState.REVIEW,
            TaskState.PASSED,
            TaskState.APPROVAL,
            TaskState.MERGED,
            TaskState.RELEASED,
        ):
            task = task.transition(state)
        self.assertEqual(task.state, TaskState.RELEASED)
        self.assertEqual(len(task.events), 7)

    def test_release_cannot_skip_review(self):
        task = DivanTask("task-1", "Fix login")
        with self.assertRaises(InvalidTaskTransition):
            task.transition(TaskState.RELEASED)

    def test_evidence_is_tamper_evident(self):
        record = build_evidence("task-1", "test", "pass", "all tests pass", {"count": 12})
        with tempfile.TemporaryDirectory() as directory:
            store = EvidenceStore(directory)
            store.append(record)
            payload = store.list("task-1")[0]
            self.assertTrue(store.verify(payload))
            payload["summary"] = "changed"
            self.assertFalse(store.verify(payload))


if __name__ == "__main__":
    unittest.main()
