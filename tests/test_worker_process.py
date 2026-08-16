"""What Divan can tell about a worker process while it is still running.

These use a Python child rather than a real worker, so the timing and the
output are the test's own and nothing here depends on a CLI being installed.
"""
import io
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "plugins" / "sadrazam"))

import time  # noqa: E402

from divan_runtime.worker_process import _Drain, run_bounded  # noqa: E402


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

    def test_the_bound_is_not_widened_by_a_longer_poll(self):
        # The poll interval is how often we look, not how long the worker may
        # run. Sleeping past the deadline and only then checking would wave
        # through a worker that finished well after its bound.
        started = time.monotonic()
        outcome = run_bounded(
            _python("import time; time.sleep(3)"),
            cwd=self.cwd,
            stdin_text="",
            timeout_seconds=0.5,
            poll_seconds=5.0,
        )
        elapsed = time.monotonic() - started

        self.assertTrue(outcome.timed_out)
        self.assertLess(elapsed, 2.5)

    def test_a_worker_that_never_reads_its_instructions_does_not_hang_us(self):
        # More than a pipe buffer holds, sent to a worker that exits without
        # reading. Writing on the calling thread would block or raise.
        outcome = run_bounded(
            _python("import time; time.sleep(0.2)"),
            cwd=self.cwd,
            stdin_text="x" * 400_000,
            timeout_seconds=20,
            poll_seconds=0.05,
        )

        self.assertFalse(outcome.timed_out)
        self.assertEqual(outcome.exit_code, 0)

    def test_a_timed_out_worker_takes_its_children_with_it(self):
        # A coding agent spawns compilers and test runners. Killing only the
        # process we started leaves those alive, and a survivor can still write
        # into the worktree after the attempt was recorded failed.
        marker = self.cwd / "leaked.txt"
        grandchild = self.cwd / "grandchild.py"
        grandchild.write_text(
            "import pathlib, sys, time\n"
            "time.sleep(2.5)\n"
            "pathlib.Path(sys.argv[1]).write_text('leaked')\n",
            encoding="utf-8",
        )
        parent = self.cwd / "parent.py"
        parent.write_text(
            "import subprocess, sys, time\n"
            "subprocess.Popen([sys.executable, sys.argv[1], sys.argv[2]])\n"
            "time.sleep(30)\n",
            encoding="utf-8",
        )

        outcome = run_bounded(
            [sys.executable, str(parent), str(grandchild), str(marker)],
            cwd=self.cwd,
            stdin_text="",
            timeout_seconds=0.6,
            poll_seconds=0.05,
        )
        self.assertTrue(outcome.timed_out)

        # Long enough that the descendant would have written by now.
        time.sleep(3.5)
        self.assertFalse(
            marker.exists(),
            "a descendant outlived the bound and could still change the worktree",
        )

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


class DrainTests(unittest.TestCase):
    """Progress is counted, not flagged.

    A flag has to be cleared by the reader, and clearing it races with the
    thread setting it: output that arrives in that window is never reported as
    progress. A count only ever moves forward, so no observation is lost.
    """

    def test_arrivals_are_counted_and_never_reset(self):
        drain = _Drain()
        self.assertEqual(drain.count, 0)

        drain.pump(io.StringIO("one\ntwo\nthree\n"))

        self.assertEqual(drain.count, 3)
        self.assertEqual(drain.text, "one\ntwo\nthree\n")
        # Reading it again does not consume it.
        self.assertEqual(drain.count, 3)

    def test_a_later_batch_moves_the_count_further(self):
        drain = _Drain()
        drain.pump(io.StringIO("first\n"))
        after_first = drain.count
        drain.pump(io.StringIO("second\n"))

        self.assertGreater(drain.count, after_first)


if __name__ == "__main__":
    unittest.main()
