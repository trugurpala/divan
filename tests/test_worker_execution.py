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
    UNATTENDED_CONTRACT,
    WORKER_COMMANDS,
    ExecutionResult,
    _classify,
    _notes_for,
    build_argv,
    contracted_prompt,
)
from divan_runtime.worker_process import ProcessOutcome  # noqa: E402
from divan_runtime.worktree_reading import (  # noqa: E402
    WorktreeReading,
    commit_result,
    unreadable_paths,
    worktree_changes,
    worktree_snapshot,
)


def _ran(exit_code: int | None = 0, **kwargs: object) -> ProcessOutcome:
    base: dict[str, object] = {
        "exit_code": exit_code,
        "stdout": "",
        "stderr": "",
        "timed_out": False,
    }
    base.update(kwargs)
    return ProcessOutcome(**base)  # type: ignore[arg-type]


def _reading(**kwargs: object) -> WorktreeReading:
    base: dict[str, object] = {"changed": ("a.py",), "diff": "+x"}
    base.update(kwargs)
    return WorktreeReading(**base)  # type: ignore[arg-type]


class ClassifyTests(unittest.TestCase):
    def test_clean_exit_that_changed_nothing_is_not_a_result(self):
        # The worker was happy to report success; it produced no work.
        verdict = _classify(_ran(0), _reading(changed=(), diff=""), produced=False)
        self.assertIs(verdict, FailureClass.WORK_REJECTED)

    def test_clean_exit_with_real_changes_is_accepted(self):
        self.assertIsNone(_classify(_ran(0), _reading(), produced=True))

    def test_work_left_by_an_earlier_attempt_is_not_this_ones(self):
        # The tree still lists files, but this attempt changed nothing. Reading
        # the file list alone would credit it with another attempt's work.
        verdict = _classify(_ran(0), _reading(), produced=False)
        self.assertIs(verdict, FailureClass.WORK_REJECTED)

    def test_instructions_that_never_arrived_are_environmental(self):
        outcome = _ran(0, stdin_error="the worker did not take its instructions")
        self.assertIs(
            _classify(outcome, _reading(), produced=True), FailureClass.ENVIRONMENT
        )

    def test_unreadable_output_is_not_a_result(self):
        # Files exist and git listed them, but the host cannot open them.
        verdict = _classify(_ran(0), _reading(unreadable=("a.py",)), produced=True)
        self.assertIs(verdict, FailureClass.ENVIRONMENT)

    def test_unstageable_worktree_is_not_a_result(self):
        verdict = _classify(
            _ran(0), _reading(read_error="fatal: not a git repository"), produced=True
        )
        self.assertIs(verdict, FailureClass.ENVIRONMENT)

    def test_timeout_outranks_everything_else(self):
        self.assertIs(
            _classify(_ran(0, timed_out=True), _reading(), produced=True),
            FailureClass.WORKER_STALLED,
        )

    def test_missing_exit_code_is_a_lost_worker(self):
        self.assertIs(
            _classify(_ran(None), _reading(), produced=True), FailureClass.WORKER_LOST
        )

    def test_failed_exit_with_changes_is_rejected_work(self):
        self.assertIs(
            _classify(_ran(1), _reading(), produced=True), FailureClass.WORK_REJECTED
        )

    def test_failed_exit_with_nothing_written_is_environmental(self):
        verdict = _classify(_ran(1), _reading(changed=(), diff=""), produced=False)
        self.assertIs(verdict, FailureClass.ENVIRONMENT)


class SnapshotTests(unittest.TestCase):
    def test_a_snapshot_changes_when_the_tree_does(self):
        with tempfile.TemporaryDirectory() as raw:
            worktree = Path(raw)
            subprocess.run(
                ["git", "-C", str(worktree), "init", "-q"],
                check=True,
                capture_output=True,
            )
            before = worktree_snapshot(worktree)
            (worktree / "made.py").write_text("value = 1\n", encoding="utf-8")

            self.assertNotEqual(worktree_snapshot(worktree), before)

    def test_a_snapshot_is_read_only(self):
        # Taken before the worker runs, so it must not stage anything itself.
        with tempfile.TemporaryDirectory() as raw:
            worktree = Path(raw)
            subprocess.run(
                ["git", "-C", str(worktree), "init", "-q"],
                check=True,
                capture_output=True,
            )
            (worktree / "made.py").write_text("value = 1\n", encoding="utf-8")
            worktree_snapshot(worktree)

            staged = subprocess.run(
                ["git", "-C", str(worktree), "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            self.assertEqual(staged.strip(), "")


class UnreadablePathTests(unittest.TestCase):
    def test_reads_the_names_git_reported(self):
        stderr = (
            'error: open("jsoncheck.py"): Permission denied\n'
            "error: unable to index file 'jsoncheck.py'\n"
            "fatal: adding files failed\n"
        )
        self.assertEqual(unreadable_paths(stderr), ("jsoncheck.py",))

    def test_reads_every_refused_file(self):
        stderr = (
            'error: open("a.py"): Permission denied\n'
            'error: open("b/c.py"): Permission denied\n'
        )
        self.assertEqual(unreadable_paths(stderr), ("a.py", "b/c.py"))

    def test_ordinary_git_noise_names_nothing(self):
        self.assertEqual(unreadable_paths("warning: LF will be replaced by CRLF\n"), ())


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


class ResultCommitTests(unittest.TestCase):
    def test_accepted_work_is_committed_without_borrowing_an_identity(self):
        # A disposable project may have no git identity configured at all, and
        # the work was produced by a worker rather than typed by the owner.
        with tempfile.TemporaryDirectory() as raw:
            worktree = Path(raw)
            subprocess.run(
                ["git", "-C", str(worktree), "init", "-q"],
                check=True,
                capture_output=True,
            )
            (worktree / "made.py").write_text("value = 1\n", encoding="utf-8")
            worktree_changes(worktree)

            sha = commit_result(worktree, "T-A001")

            self.assertIsNotNone(sha)
            described = subprocess.run(
                ["git", "-C", str(worktree), "log", "-1", "--format=%an|%s"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            self.assertIn("Divan", described)
            self.assertIn("T-A001", described)

    def test_nothing_to_commit_yields_no_result_name(self):
        with tempfile.TemporaryDirectory() as raw:
            worktree = Path(raw)
            subprocess.run(
                ["git", "-C", str(worktree), "init", "-q"],
                check=True,
                capture_output=True,
            )

            self.assertIsNone(commit_result(worktree, "T-A001"))


class NoteTests(unittest.TestCase):
    def test_a_rejected_attempt_is_not_accused_of_failing_to_commit(self):
        # No commit was attempted, so there is nothing to report as missing.
        notes = _notes_for(_reading(), None, accepted=False)
        self.assertEqual(notes, ())

    def test_an_accepted_attempt_without_a_commit_says_so(self):
        notes = _notes_for(_reading(), None, accepted=True)
        self.assertIn("could not be committed", " ".join(notes))

    def test_unreadable_files_are_named(self):
        notes = _notes_for(_reading(unreadable=("a.py",)), None, accepted=False)
        self.assertIn("a.py", " ".join(notes))


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
            produced=bool(changed),
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

    def test_the_prompt_never_reaches_the_command_line(self):
        # The invariant is about the argv actually handed to the process, not
        # about a promise elsewhere, so the built command line is the subject.
        secret = "build the operations case system for tenant Acme"
        for worker_id, command in WORKER_COMMANDS.items():
            with self.subTest(worker=worker_id):
                argv = build_argv("codex.cmd", command)

                self.assertNotIn(secret, argv)
                self.assertNotIn(secret, " ".join(argv))
                self.assertEqual(argv[-1], command.stdin_marker)
                self.assertEqual(argv[0], "codex.cmd")

    def test_every_worker_takes_its_instructions_from_stdin(self):
        # A command line is readable by every other process on the machine and
        # has a length limit real task context will exceed, so the prompt is
        # never an argument.
        for worker_id, command in WORKER_COMMANDS.items():
            with self.subTest(worker=worker_id):
                self.assertTrue(command.stdin_marker)
                self.assertNotIn(command.stdin_marker, command.extra_args)


if __name__ == "__main__":
    unittest.main()


class UnattendedContractTests(unittest.TestCase):
    """A worker that asks a question asks into a closed pipe.

    Observed rather than imagined: a repair attempt produced a correct plan,
    ended with "do you approve applying this plan?", and wrote no files. Divan
    recorded it as rejected work, which is the wrong story — the work was never
    attempted. The prompt now states the circumstances so the worker knows no
    answer can arrive.
    """

    def test_the_contract_tells_the_worker_nobody_can_answer(self):
        contract = UNATTENDED_CONTRACT.casefold()

        self.assertIn("unattended", contract)
        self.assertIn("closed", contract)
        self.assertIn("do not ask", contract)

    def test_the_contract_still_allows_reporting_impossible_work(self):
        # Refusing to ask must not become refusing to say a task cannot be done.
        contract = UNATTENDED_CONTRACT.casefold()

        self.assertIn("impossible", contract)
        self.assertIn("already done", contract)

    def test_the_task_is_delivered_behind_the_contract(self):
        contracted = contracted_prompt("close the ledger defect")

        self.assertTrue(contracted.startswith(UNATTENDED_CONTRACT))
        self.assertIn("close the ledger defect", contracted)

    def test_the_contract_does_not_bypass_the_sandbox(self):
        # The boundary stays the sandbox. If this ever needs an approval-bypass
        # flag to work, the fix has gone wrong.
        arguments = WORKER_COMMANDS["codex"].extra_args

        self.assertIn("workspace-write", arguments)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", arguments)
        self.assertNotIn("danger-full-access", arguments)
