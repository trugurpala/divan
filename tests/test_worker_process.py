"""What Divan can tell about a worker process while it is still running.

These use a Python child rather than a real worker, so the timing and the
output are the test's own and nothing here depends on a CLI being installed.
"""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "plugins" / "sadrazam"))

from divan_runtime.worker_process import run_bounded  # noqa: E402


def _python(source: str) -> list[str]:
    return [sys.executable, "-c", source]


class RunBoundedTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.cwd = pathlib.Path(self._dir.name)
        self.addCleanup(self._dir.cleanup)

    def test_output_and_exit_code_are_reported(self):
        outcome = run_bounded(
            _python("import sys; print('out'); print('err', file=sys.stderr); sys.exit(3)"),
            cwd=self.cwd,
            stdin_text="",
            timeout_seconds=30,
            poll_seconds=0.05,
        )

        self.assertEqual(outcome.exit_code, 3)
        self.assertIn("out", outcome.stdout)
        self.assertIn("err", outcome.stderr)
        self.assertFalse(outcome.timed_out)

    def test_instructions_reach_the_worker_on_stdin(self):
        outcome = run_bounded(
            _python("import sys; sys.stdout.write(sys.stdin.read().upper())"),
            cwd=self.cwd,
            stdin_text="build the thing",
            timeout_seconds=30,
            poll_seconds=0.05,
        )

        self.assertIn("BUILD THE THING", outcome.stdout)

    def test_a_worker_that_never_finishes_is_stopped_and_named(self):
        outcome = run_bounded(
            _python("import time; time.sleep(120)"),
            cwd=self.cwd,
            stdin_text="",
            timeout_seconds=0.5,
            poll_seconds=0.05,
        )

        self.assertTrue(outcome.timed_out)

    def test_a_talkative_worker_does_not_deadlock(self):
        # More than any pipe buffer holds. Draining after the wait would hang
        # here forever, and Divan would record the deadlock as a stall.
        outcome = run_bounded(
            _python("print('x' * 200000)"),
            cwd=self.cwd,
            stdin_text="",
            timeout_seconds=60,
            poll_seconds=0.05,
        )

        self.assertFalse(outcome.timed_out)
        self.assertEqual(outcome.exit_code, 0)
        self.assertGreater(len(outcome.stdout), 199000)

    def test_progress_is_reported_only_when_the_worker_produces_output(self):
        beats: list[str] = []
        run_bounded(
            # Flushed, because a worker that never emits anything is exactly
            # the case the next test covers.
            _python("import time; print('step', flush=True); time.sleep(0.6)"),
            cwd=self.cwd,
            stdin_text="",
            timeout_seconds=30,
            poll_seconds=0.05,
            on_alive=lambda: beats.append("alive"),
            on_progress=lambda: beats.append("progress"),
        )

        self.assertIn("alive", beats)
        self.assertIn("progress", beats)

    def test_a_silent_worker_is_alive_without_being_credited_with_progress(self):
        beats: list[str] = []
        run_bounded(
            _python("import time; time.sleep(0.6)"),
            cwd=self.cwd,
            stdin_text="",
            timeout_seconds=30,
            poll_seconds=0.05,
            on_alive=lambda: beats.append("alive"),
            on_progress=lambda: beats.append("progress"),
        )

        self.assertIn("alive", beats)
        self.assertNotIn("progress", beats)

    def test_the_caller_is_handed_the_process_it_started(self):
        seen: list[int] = []
        run_bounded(
            _python("pass"),
            cwd=self.cwd,
            stdin_text="",
            timeout_seconds=30,
            poll_seconds=0.05,
            on_start=lambda process: seen.append(process.pid),
        )

        self.assertEqual(len(seen), 1)
        self.assertGreater(seen[0], 0)


if __name__ == "__main__":
    unittest.main()
