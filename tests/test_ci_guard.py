from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


class CIGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        from divan_runtime import ci_guard

        self.guard = ci_guard

    def test_fingerprint_removes_volatile_path_sha_time_and_ansi(self) -> None:
        first = self.guard.fingerprint(
            "quality-gate",
            "validate",
            "tests",
            "\x1b[31mFAIL C:\\work\\one\\test_x.py "
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa "
            "2026-07-30T12:01:02Z\x1b[0m",
        )
        second = self.guard.fingerprint(
            "quality-gate",
            "validate",
            "tests",
            "FAIL D:\\different\\two\\test_x.py "
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb "
            "2026-07-31T01:02:03Z",
        )
        other = self.guard.fingerprint(
            "codeql",
            "analyze",
            "tests",
            "FAIL D:\\different\\two\\test_x.py",
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)

    def test_two_evidence_backed_changed_hypotheses_then_block(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-ci-guard-") as temporary:
            ledger = pathlib.Path(temporary) / "ci-failures.json"
            common = {
                "ledger_path": ledger,
                "workflow": "quality-gate",
                "job": "validate",
                "check": "tests.test_install",
                "error_signature": "AssertionError: expected healthy",
                "evidence": ["tests/test_host_install.py"],
                "execute": True,
            }
            first = self.guard.evaluate(
                **common,
                hypothesis="PATH was stale after installation",
                recorded_at="2026-07-30T12:00:00Z",
            )
            duplicate = self.guard.evaluate(
                **common,
                hypothesis="PATH was stale after installation",
                recorded_at="2026-07-30T12:01:00Z",
            )
            second = self.guard.evaluate(
                **common,
                hypothesis="PowerShell selected the blocked ps1 shim",
                recorded_at="2026-07-30T12:02:00Z",
            )
            blocked = self.guard.evaluate(
                **common,
                hypothesis="Try an unrelated third patch",
                recorded_at="2026-07-30T12:03:00Z",
            )

            self.assertEqual(first["status"], "REMEDIATION_ALLOWED")
            self.assertTrue(first["mutation_allowed"])
            self.assertEqual(duplicate["status"], "CHANGED_HYPOTHESIS_REQUIRED")
            self.assertFalse(duplicate["mutation_allowed"])
            self.assertEqual(second["attempt_number"], 2)
            self.assertEqual(blocked["status"], "BLOCKED")
            self.assertFalse(blocked["mutation_allowed"])
            stored = json.loads(ledger.read_text(encoding="utf-8"))
            row = next(iter(stored["records"].values()))
            self.assertEqual(len(row["attempts"]), 2)
            self.assertEqual(row["status"], "BLOCKED")

    def test_missing_focused_evidence_does_not_authorize_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-ci-guard-") as temporary:
            result = self.guard.evaluate(
                pathlib.Path(temporary) / "ci-failures.json",
                workflow="quality-gate",
                job="validate",
                check="tests",
                error_signature="failed",
                hypothesis="guess",
                evidence=[],
                execute=True,
                recorded_at="2026-07-30T12:00:00Z",
            )
            self.assertEqual(result["status"], "FOCUSED_EVIDENCE_REQUIRED")
            self.assertFalse(result["mutation_allowed"])

    def test_ledger_never_stores_raw_error_or_hypothesis_secrets(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-ci-guard-") as temporary:
            ledger = pathlib.Path(temporary) / "ci-failures.json"
            self.guard.evaluate(
                ledger,
                workflow="quality-gate",
                job="validate",
                check="tests",
                error_signature="token=ghp_abcdefghijklmnopqrstuvwxyz123456 failed",
                hypothesis="secret=ghp_abcdefghijklmnopqrstuvwxyz123456 is stale",
                evidence=["tests/test_guard.py"],
                execute=True,
                recorded_at="2026-07-30T12:00:00Z",
            )
            text = ledger.read_text(encoding="utf-8")
            self.assertNotIn("ghp_", text)
            self.assertNotIn("error_signature", text)
            self.assertNotIn("is stale", text)
            self.assertIn("hypothesis_digest", text)

    def test_corrupt_or_symlink_ledger_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-ci-guard-") as temporary:
            root = pathlib.Path(temporary)
            corrupt = root / "corrupt.json"
            corrupt.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ledger"):
                self.guard.evaluate(
                    corrupt,
                    workflow="quality",
                    job="validate",
                    check="tests",
                    error_signature="failed",
                    hypothesis="cause",
                    evidence=["tests/test.py"],
                    recorded_at="2026-07-30T12:00:00Z",
                )
            target = root / "target.json"
            target.write_text('{"schema_version":1,"records":{}}\n', encoding="utf-8")
            link = root / "link.json"
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(ValueError, "symlink"):
                self.guard.evaluate(
                    link,
                    workflow="quality",
                    job="validate",
                    check="tests",
                    error_signature="failed",
                    hypothesis="cause",
                    evidence=["tests/test.py"],
                    recorded_at="2026-07-30T12:00:00Z",
                )


if __name__ == "__main__":
    unittest.main()
