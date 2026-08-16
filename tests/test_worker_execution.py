"""What Divan is allowed to call a finished piece of work.

These tests pin the two ways an attempt can look successful without being
successful: a worker that exits cleanly having changed nothing, and a worker
whose output the host is not permitted to read back.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugins" / "sadrazam"))

from divan_runtime.attempt_contract import FailureClass  # noqa: E402
from divan_runtime.worker_execution import (  # noqa: E402
    WORKER_COMMANDS,
    ExecutionResult,
    WorktreeReading,
    _classify,
    _unreadable_paths,
    worktree_changes,
)


def _reading(**kwargs: object) -> WorktreeReading:
    base: dict[str, object] = {"changed": ("a.py",), "diff": "+x"}
    base.update(kwargs)
    return WorktreeReading(**base)  # type: ignore[arg-type]


class ClassifyTests(unittest.TestCase):
    def test_clean_exit_that_changed_nothing_is_not_a_result(self):
        # The worker was happy to report success; it produced no work.
        verdict = _classify(0, False, _reading(changed=(), diff=""))
        self.assertIs(verdict, FailureClass.WORK_REJECTED)

    def test_clean_exit_with_real_changes_is_accepted(self):
        self.assertIsNone(_classify(0, False, _reading()))

    def test_unreadable_output_is_not_a_result(self):
        # Files exist and git listed them, but the host cannot open them.
        verdict = _classify(0, False, _reading(unreadable=("a.py",)))
        self.assertIs(verdict, FailureClass.ENVIRONMENT)

    def test_unstageable_worktree_is_not_a_result(self):
        verdict = _classify(0, False, _reading(read_error="fatal: not a git repository"))
        self.assertIs(verdict, FailureClass.ENVIRONMENT)

    def test_timeout_outranks_everything_else(self):
        self.assertIs(
            _classify(0, True, _reading()),
            FailureClass.WORKER_STALLED,
        )

    def test_missing_exit_code_is_a_lost_worker(self):
        self.assertIs(_classify(None, False, _reading()), FailureClass.WORKER_LOST)

    def test_failed_exit_with_changes_is_rejected_work(self):
        self.assertIs(_classify(1, False, _reading()), FailureClass.WORK_REJECTED)

    def test_failed_exit_with_nothing_written_is_environmental(self):
        verdict = _classify(1, False, _reading(changed=(), diff=""))
        self.assertIs(verdict, FailureClass.ENVIRONMENT)


class UnreadablePathTests(unittest.TestCase):
    def test_reads_the_names_git_reported(self):
        stderr = (
            'error: open("jsoncheck.py"): Permission denied\n'
            "error: unable to index file 'jsoncheck.py'\n"
            "fatal: adding files failed\n"
        )
        self.assertEqual(_unreadable_paths(stderr), ("jsoncheck.py",))

    def test_reads_every_refused_file(self):
        stderr = (
            'error: open("a.py"): Permission denied\n'
            'error: open("b/c.py"): Permission denied\n'
        )
        self.assertEqual(_unreadable_paths(stderr), ("a.py", "b/c.py"))

    def test_ordinary_git_noise_names_nothing(self):
        self.assertEqual(_unreadable_paths("warning: LF will be replaced by CRLF\n"), ())


class WorktreeReadingTests(unittest.TestCase):
    def test_real_worktree_reports_created_files_and_a_diff(self):
        with tempfile.TemporaryDirectory() as raw:
            worktree = Path(raw)
            self._init(worktree)
            (worktree / "made.py").write_text("value = 1\n", encoding="utf-8")

            reading = worktree_changes(worktree)

            self.assertIn("made.py", reading.changed)
            self.assertIn("value = 1", reading.diff)
            self.assertTrue(reading.readable)

    def test_a_worktree_git_cannot_stage_reports_why(self):
        with tempfile.TemporaryDirectory() as raw:
            # No repository here at all, so staging cannot succeed.
            reading = worktree_changes(Path(raw))

            self.assertFalse(reading.readable)
            self.assertIsNotNone(reading.read_error)

    @staticmethod
    def _init(worktree: Path) -> None:
        for args in (
            ("init", "-q"),
            ("config", "user.name", "Divan"),
            ("config", "user.email", "divan@example.invalid"),
        ):
            subprocess.run(
                ["git", "-C", str(worktree), *args], check=True, capture_output=True
            )


class ProducedWorkTests(unittest.TestCase):
    def test_unreadable_files_do_not_count_as_produced_work(self):
        result = self._result(changed=("a.py",), unreadable=("a.py",))
        self.assertFalse(result.produced_work)
        self.assertFalse(result.to_dict()["produced_work"])

    def test_readable_changes_count_as_produced_work(self):
        self.assertTrue(self._result(changed=("a.py",)).produced_work)

    def test_no_changes_are_not_produced_work(self):
        self.assertFalse(self._result(changed=()).produced_work)

    @staticmethod
    def _result(*, changed: tuple[str, ...], unreadable: tuple[str, ...] = ()) -> ExecutionResult:
        from divan_runtime.attempt_contract import AttemptRecord

        attempt = AttemptRecord(
            attempt_id="T-A001",
            task_id="T",
            worker_id="codex",
            provider="codex",
            agent="codex",
            started_at="2026-08-16T00:00:00Z",
            heartbeat_at="2026-08-16T00:00:00Z",
        )
        return ExecutionResult(
            attempt=attempt,
            exit_code=0,
            stdout="",
            stderr="",
            changed_files=changed,
            diff="",
            duration_seconds=1.0,
            unreadable_files=unreadable,
        )


class InvocationTests(unittest.TestCase):
    def test_codex_is_given_a_writable_workspace_and_nothing_wider(self):
        args = WORKER_COMMANDS["codex"].extra_args
        self.assertIn("--sandbox", args)
        self.assertEqual(args[args.index("--sandbox") + 1], "workspace-write")

    def test_codex_is_never_run_with_the_sandbox_bypassed(self):
        joined = " ".join(WORKER_COMMANDS["codex"].extra_args)
        self.assertNotIn("danger-full-access", joined)
        self.assertNotIn("bypass-approvals", joined)


if __name__ == "__main__":
    unittest.main()
