from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from project_memory import main as memory_main
from project_memory_store import (
    LIFECYCLE_STATES,
    REQUIRED_DIRECTORIES,
    REQUIRED_FILES,
    TASK_STATUSES,
    MemoryLock,
    ProjectMemoryError,
    initialize,
)
from project_memory_validation import validate_memory
from project_memory_workflow import (
    add_decision,
    add_lesson,
    add_task,
    checkpoint,
    complete_task,
    resume_summary,
    start_task,
    transition,
)


class ProjectMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="divan-memory-")
        self.root = pathlib.Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def init(self) -> None:
        initialize(self.root, "Sample App", "Build a durable sample", execute=True)

    def evidence(self, name: str = "proof.txt") -> str:
        path = self.root / ".divan" / "evidence" / name
        path.write_text("PASS\n", encoding="utf-8")
        return path.relative_to(self.root).as_posix()

    def test_init_is_dry_run_first(self) -> None:
        result = initialize(self.root, "Sample App", "Build a durable sample")
        self.assertEqual(result["status"], "planned")
        self.assertFalse((self.root / ".divan").exists())

    def test_init_creates_valid_memory_without_overwrite(self) -> None:
        self.init()
        self.assertEqual(validate_memory(self.root), [])
        with self.assertRaises(ProjectMemoryError):
            initialize(self.root, "Other", "No overwrite", execute=True)

    def test_corrupt_json_is_reported(self) -> None:
        self.init()
        (self.root / ".divan/tasks.json").write_text("{", encoding="utf-8")
        self.assertTrue(validate_memory(self.root))

    def test_task_dependencies_and_single_active_task(self) -> None:
        self.init()
        first = add_task(self.root, "Create schema", execute=True)["task"]["id"]
        second = add_task(
            self.root, "Create API", depends_on=[first], execute=True
        )["task"]["id"]
        with self.assertRaises(ProjectMemoryError):
            start_task(self.root, second, execute=True)
        start_task(self.root, first, execute=True)
        with self.assertRaises(ProjectMemoryError):
            start_task(self.root, second, execute=True)

    def test_complete_requires_existing_in_project_evidence(self) -> None:
        self.init()
        task_id = add_task(self.root, "Create schema", execute=True)["task"]["id"]
        start_task(self.root, task_id, execute=True)
        with self.assertRaises(ProjectMemoryError):
            complete_task(self.root, task_id, ["missing.txt"], "Next", execute=True)
        proof = self.evidence()
        complete_task(self.root, task_id, [proof], "Create API", execute=True)
        self.assertEqual(validate_memory(self.root), [])
        summary = resume_summary(self.root)
        self.assertEqual(summary["task_counts"]["completed"], 1)
        self.assertIsNone(summary["active_task"])

    def test_transition_is_adjacent_and_evidence_backed(self) -> None:
        self.init()
        proof = self.evidence()
        with self.assertRaises(ProjectMemoryError):
            transition(self.root, "PLANNED", [proof], execute=True)
        transition(self.root, "BASELINED", [proof], execute=True)
        with self.assertRaises(ProjectMemoryError):
            transition(self.root, "PLANNED", [proof], execute=True)
        task_id = add_task(self.root, "First slice", execute=True)["task"]["id"]
        transition(self.root, "PLANNED", [proof], execute=True)
        with self.assertRaises(ProjectMemoryError):
            transition(self.root, "IMPLEMENTING", [proof], execute=True)
        start_task(self.root, task_id, execute=True)
        transition(self.root, "IMPLEMENTING", [proof], execute=True)
        self.assertEqual(resume_summary(self.root)["lifecycle_state"], "IMPLEMENTING")

    def test_checkpoint_creates_handoff_and_resume_point(self) -> None:
        self.init()
        result = checkpoint(
            self.root,
            "Implement the next slice",
            done=["Memory initialized"],
            remaining=["Add task"],
            gate="unit-tests",
            execute=True,
        )
        handoff = self.root / result["handoff"]
        self.assertTrue(handoff.is_file())
        summary = resume_summary(self.root)
        self.assertEqual(summary["next_action"], "Implement the next slice")
        self.assertEqual(summary["last_successful_gate"], "unit-tests")
        self.assertEqual(summary["last_handoff"], result["handoff"])

    def test_decision_and_lesson_are_durable(self) -> None:
        self.init()
        decision = add_decision(
            self.root,
            "Use PostgreSQL",
            "Transactions are required.",
            "Use PostgreSQL.",
            ["Run migrations in CI."],
            execute=True,
        )
        lesson = add_lesson(
            self.root,
            "Migrations",
            "Downgrade tests must run before release.",
            execute=True,
        )
        self.assertTrue((self.root / decision["path"]).is_file())
        self.assertTrue((self.root / lesson["path"]).is_file())

    def test_lock_prevents_second_writer(self) -> None:
        self.init()
        with MemoryLock(self.root):
            with self.assertRaises(ProjectMemoryError):
                with MemoryLock(self.root):
                    pass

    def test_completed_task_without_evidence_is_invalid(self) -> None:
        self.init()
        path = self.root / ".divan/tasks.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["tasks"].append(
            {
                "id": "TASK-001",
                "title": "Broken",
                "description": "",
                "status": "completed",
                "depends_on": [],
                "acceptance_criteria": [],
                "evidence": [],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "completed_at": "2026-01-01T00:00:00Z",
                "blocker": None,
            }
        )
        payload["next_sequence"] = 2
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.assertTrue(any("requires evidence" in error for error in validate_memory(self.root)))

    def test_contract_matches_runtime(self) -> None:
        contract = json.loads(
            (ROOT / "registry/project-memory-contract.json").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["required_files"], list(REQUIRED_FILES))
        self.assertEqual(contract["required_directories"], list(REQUIRED_DIRECTORIES))
        self.assertEqual(set(contract["task_statuses"]), TASK_STATUSES)
        self.assertEqual(contract["lifecycle_states"], list(LIFECYCLE_STATES))

    def test_cli_init_and_continue(self) -> None:
        code = memory_main(
            [
                "init",
                "--root",
                str(self.root),
                "--name",
                "CLI App",
                "--goal",
                "Remember everything",
                "--execute",
                "--json",
            ]
        )
        self.assertEqual(code, 0)
        code = memory_main(["continue", "--root", str(self.root), "--json"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
