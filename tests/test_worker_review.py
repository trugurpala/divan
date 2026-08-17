"""When a second opinion is worth having, and when it only looks like one."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugins" / "sadrazam"))

from divan_runtime.worker_review import (  # noqa: E402
    REVIEW_COMMANDS,
    Independence,
    ReviewOutcome,
    WriteAccess,
    _provider_independence,
    _worktree_fingerprint,
)


def _outcome(**kwargs: object) -> ReviewOutcome:
    base: dict[str, object] = {
        "reviewer_id": "codex",
        "writer_id": "codex",
        "findings": "one real problem",
        "provider_independence": Independence.UNAVAILABLE,
        "process_independence": Independence.PROVEN,
        "write_access": WriteAccess.DENIED,
        "writer_pid": 100,
        "reviewer_pid": 200,
        "exit_code": 0,
        "duration_seconds": 1.0,
    }
    base.update(kwargs)
    return ReviewOutcome(**base)  # type: ignore[arg-type]


class InvocationTests(unittest.TestCase):
    def test_a_reviewer_is_given_no_way_to_write(self):
        args = REVIEW_COMMANDS["codex"].extra_args
        self.assertIn("--sandbox", args)
        self.assertEqual(args[args.index("--sandbox") + 1], "read-only")

    def test_a_reviewer_never_gets_write_or_bypass(self):
        joined = " ".join(REVIEW_COMMANDS["codex"].extra_args)
        self.assertNotIn("workspace-write", joined)
        self.assertNotIn("danger-full-access", joined)
        self.assertNotIn("bypass-approvals", joined)

    def test_a_reviewer_reads_its_brief_from_stdin(self):
        self.assertEqual(REVIEW_COMMANDS["codex"].stdin_marker, "-")


class ProviderIndependenceTests(unittest.TestCase):
    def test_one_vendor_reviewing_itself_is_not_independence(self):
        self.assertIs(
            _provider_independence("codex", "codex"), Independence.UNAVAILABLE
        )

    def test_a_different_vendor_is_independence(self):
        self.assertIs(_provider_independence("codex", "claude"), Independence.PROVEN)


class UsabilityTests(unittest.TestCase):
    def test_a_review_that_could_edit_the_work_does_not_count(self):
        self.assertFalse(_outcome(write_access=WriteAccess.GRANTED).usable)

    def test_a_review_from_the_writers_own_process_does_not_count(self):
        self.assertFalse(_outcome(process_independence=Independence.ABSENT).usable)

    def test_a_review_that_said_nothing_does_not_count(self):
        self.assertFalse(_outcome(findings="   ").usable)

    def test_a_reviewer_that_failed_did_not_review_anything(self):
        # An authentication error or a crash still prints text, and that text
        # is not a review. Counting it would let a broken reviewer certify work.
        self.assertFalse(_outcome(exit_code=1, findings="not logged in").usable)

    def test_a_reviewer_that_ran_out_of_time_did_not_finish(self):
        self.assertFalse(_outcome(timed_out=True, findings="starting review").usable)

    def test_a_tree_that_could_not_be_read_proves_nothing_about_write_access(self):
        outcome = _outcome(write_access=WriteAccess.UNOBSERVED)
        self.assertFalse(outcome.usable)
        self.assertEqual(outcome.to_dict()["write_access"], "unobserved")

    def test_a_single_vendor_review_still_counts_when_it_is_honest_about_it(self):
        # Vendor independence is missing and recorded as missing. That is a
        # stated limitation, not a reason to throw the reading away.
        outcome = _outcome()
        self.assertTrue(outcome.usable)
        self.assertEqual(outcome.to_dict()["provider_independence"], "unavailable")


class FingerprintTests(unittest.TestCase):
    def test_a_change_during_review_is_visible(self):
        with tempfile.TemporaryDirectory() as raw:
            worktree = Path(raw)
            for args in (
                ("init", "-q"),
                ("config", "user.name", "Divan"),
                ("config", "user.email", "divan@example.invalid"),
            ):
                subprocess.run(
                    ["git", "-C", str(worktree), *args], check=True, capture_output=True
                )
            (worktree / "a.txt").write_text("one\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(worktree), "add", "-A"], check=True, capture_output=True
            )
            subprocess.run(
                ["git", "-C", str(worktree), "commit", "-qm", "base"],
                check=True,
                capture_output=True,
            )

            before = _worktree_fingerprint(worktree)
            (worktree / "b.txt").write_text("two\n", encoding="utf-8")
            after = _worktree_fingerprint(worktree)

            self.assertNotEqual(before, after)

    def test_a_tree_that_cannot_be_read_reports_nothing_rather_than_nothing_changed(self):
        # Two failed reads both return empty output. Treating that as a match
        # would report a reviewer as unable to write when nothing was observed.
        with tempfile.TemporaryDirectory() as raw:
            self.assertIsNone(_worktree_fingerprint(Path(raw)))


if __name__ == "__main__":
    unittest.main()
