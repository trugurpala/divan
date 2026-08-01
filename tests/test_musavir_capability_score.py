from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCORER = (
    ROOT
    / "plugins"
    / "sadrazam"
    / "skills"
    / "musavir"
    / "scripts"
    / "score_capabilities.py"
)


def run_scorer(payload: object | str) -> subprocess.CompletedProcess[str]:
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(SCORER)],
        input=raw,
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )


class CapabilityScoreTests(unittest.TestCase):
    def test_scores_explicit_requirement_ledger(self) -> None:
        completed = run_scorer(
            {
                "requirements": [
                    {
                        "id": "repo",
                        "status": "verified",
                        "evidence": ["AGENTS.md read"],
                    },
                    {"id": "browser", "status": "partial"},
                    {"id": "release", "status": "unknown"},
                    {"id": "mobile", "status": "missing"},
                ]
            }
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "requirement_count": 4,
                "counts": {
                    "verified": 1,
                    "partial": 1,
                    "missing": 1,
                    "unknown": 1,
                },
                "coverage_percent": 37.5,
                "gap_percent": 62.5,
                "confidence_percent": 75.0,
            },
        )

    def test_rejects_invalid_ledgers_without_traceback(self) -> None:
        invalid_payloads = {
            "empty": {"requirements": []},
            "duplicate id": {
                "requirements": [
                    {"id": "repo", "status": "verified"},
                    {"id": "repo", "status": "partial"},
                ]
            },
            "unsupported status": {
                "requirements": [{"id": "repo", "status": "ready"}]
            },
            "unsupported status type": {
                "requirements": [{"id": "repo", "status": []}]
            },
            "missing string id": {
                "requirements": [{"id": 7, "status": "verified"}]
            },
            "non-string evidence": {
                "requirements": [
                    {"id": "repo", "status": "verified", "evidence": [42]}
                ]
            },
        }

        for label, payload in invalid_payloads.items():
            with self.subTest(label=label):
                completed = run_scorer(payload)
                self.assertEqual(completed.returncode, 2)
                self.assertTrue(completed.stderr.strip())
                self.assertNotIn("Traceback", completed.stderr)
                self.assertEqual(completed.stdout, "")

    def test_rejects_malformed_json_without_traceback(self) -> None:
        completed = run_scorer('{"requirements": [')

        self.assertEqual(completed.returncode, 2)
        self.assertIn("gecersiz JSON", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(completed.stdout, "")


if __name__ == "__main__":
    unittest.main()
