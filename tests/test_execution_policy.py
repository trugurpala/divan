from __future__ import annotations

import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


class ExecutionPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        from divan_runtime import execution, timeouts

        self.execution = execution
        self.decision = timeouts.TimeoutDecision(
            command_class="fast-check",
            configured_seconds=1,
            source="test",
            sample_count=0,
            percentile_seconds=None,
            minimum_seconds=1,
            maximum_seconds=1,
        )

    def test_success_failure_and_timeout_are_distinct(self) -> None:
        success = self.execution.run(
            [sys.executable, "-c", "print('ok')"], self.decision
        )
        failure = self.execution.run(
            [sys.executable, "-c", "raise SystemExit(3)"], self.decision
        )
        timed_out = self.execution.run(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            self.decision,
        )

        self.assertEqual(success.status, "PASS")
        self.assertEqual(success.stdout.strip(), "ok")
        self.assertEqual(failure.status, "FAILED")
        self.assertEqual(failure.returncode, 3)
        self.assertEqual(timed_out.status, "TIMEOUT")
        self.assertIsNone(timed_out.returncode)
        self.assertEqual(timed_out.timeout["configured_seconds"], 1)

    def test_timeout_never_retries_and_mutation_is_not_retryable(self) -> None:
        calls = 0

        def runner(*args, **kwargs):
            nonlocal calls
            calls += 1
            raise subprocess.TimeoutExpired(args[0], timeout=1, output="partial")

        result = self.execution.run(
            ["provider", "mutate"],
            self.decision,
            mutating=True,
            runner=runner,
        )

        self.assertEqual(calls, 1)
        self.assertEqual(result.status, "TIMEOUT")
        self.assertFalse(result.retry_allowed)
        self.assertEqual(result.stdout, "partial")

    def test_read_only_timeout_has_bounded_retry_guidance(self) -> None:
        def runner(*args, **kwargs):
            raise subprocess.TimeoutExpired(args[0], timeout=1)

        result = self.execution.run(
            ["provider", "inspect"],
            self.decision,
            mutating=False,
            runner=runner,
        )

        self.assertTrue(result.retry_allowed)
        self.assertIn("controlled timeout", result.next_action)

    def test_cancellation_and_secret_redaction_are_explicit(self) -> None:
        def cancelled(*args, **kwargs):
            raise KeyboardInterrupt

        result = self.execution.run(
            ["provider"],
            self.decision,
            runner=cancelled,
        )

        def leaks(*args, **kwargs):
            return subprocess.CompletedProcess(
                args[0],
                2,
                "",
                "token=ghp_abcdefghijklmnopqrstuvwxyz123456",
            )

        failed = self.execution.run(
            ["provider"],
            self.decision,
            runner=leaks,
        )
        self.assertEqual(result.status, "CANCELLED")
        self.assertFalse(result.retry_allowed)
        self.assertNotIn("ghp_", failed.stderr)
        self.assertIn("[REDACTED_SECRET]", failed.stderr)

    def test_shell_strings_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "argument list"):
            self.execution.run("python -c pass", self.decision)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
