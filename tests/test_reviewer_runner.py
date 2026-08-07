from __future__ import annotations

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.reviewer_runner import AutomatedReviewer, ReviewerUnavailable


class ReviewerRunnerTests(unittest.TestCase):
    def test_claude_reviewer_uses_plan_mode_and_parses_pass(self):
        calls: list[tuple[tuple[str, ...], str]] = []

        def runner(argv, cwd, timeout, stdin_text):
            del cwd, timeout
            calls.append((tuple(argv), stdin_text))
            inner = json.dumps(
                {
                    "verdict": "PASS",
                    "summary": "Patch is safe.",
                    "findings": [],
                }
            )
            return 0, json.dumps({"result": inner}), ""

        review = AutomatedReviewer(
            binaries={"claude": "claude"},
            runner=runner,
        ).review(task_title="Fix bug", diff="diff --git a/a.py b/a.py")

        self.assertEqual(review.verdict, "PASS")
        self.assertTrue(review.check().passed)
        self.assertIn("--permission-mode", calls[0][0])
        self.assertIn("plan", calls[0][0])
        self.assertIn("diff --git", calls[0][1])

    def test_codex_reviewer_uses_read_only_and_parses_retry(self):
        def runner(argv, cwd, timeout, stdin_text):
            del cwd, timeout, stdin_text
            self.assertIn("read-only", argv)
            event = {
                "item": {
                    "text": json.dumps(
                        {
                            "verdict": "RETRY",
                            "summary": "Regression found.",
                            "findings": ["missing validation"],
                        }
                    )
                }
            }
            return 0, json.dumps(event), ""

        review = AutomatedReviewer(
            binaries={"codex": "codex"},
            runner=runner,
        ).review(task_title="Change API", diff="diff --git a/a.py b/a.py")

        self.assertEqual(review.verdict, "RETRY")
        self.assertFalse(review.check().passed)
        self.assertEqual(review.findings, ("missing validation",))

    def test_prefers_reviewer_different_from_worker(self):
        def runner(argv, cwd, timeout, stdin_text):
            del cwd, timeout, stdin_text
            self.assertEqual(argv[0], "codex")
            event = {
                "item": {
                    "text": json.dumps(
                        {"verdict": "PASS", "summary": "ok", "findings": []}
                    )
                }
            }
            return 0, json.dumps(event), ""

        review = AutomatedReviewer(
            binaries={"claude": "claude", "codex": "codex"},
            runner=runner,
        ).review(
            task_title="Task",
            diff="diff --git a/a b/a",
            worker_agent="claude",
        )
        self.assertEqual(review.reviewer, "codex")

    def test_empty_diff_fails_closed_without_calling_agent(self):
        review = AutomatedReviewer(binaries={}).review(task_title="Task", diff="")
        self.assertEqual(review.verdict, "RETRY")
        self.assertEqual(review.reviewer, "builtin")

    def test_missing_reviewer_is_explicit_failure(self):
        with self.assertRaises(ReviewerUnavailable):
            AutomatedReviewer(binaries={}).review(
                task_title="Task",
                diff="diff --git a/a b/a",
            )


if __name__ == "__main__":
    unittest.main()
