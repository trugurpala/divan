from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "divan_upstream", ROOT / "scripts" / "upstream-denetim.py"
)
assert SPEC and SPEC.loader
UPSTREAM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UPSTREAM)


class UpstreamGovernanceTests(unittest.TestCase):
    def test_root_license_is_canonical_and_notice_is_separate(self) -> None:
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(license_text.startswith("MIT License\n\nCopyright (c) 2026 trugurpala\n"))
        self.assertNotIn("Bundled third-party", license_text)
        self.assertIn("THE SOFTWARE IS PROVIDED \"AS IS\"", license_text)
        notice = (ROOT / "NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("THIRD_PARTY_LICENSES.md", notice)
        self.assertIn("Anthropic", notice)

    def test_all_detected_drift_has_pinned_review_decisions(self) -> None:
        errors, reviews = UPSTREAM.baseline_errors(ROOT)

        self.assertEqual(errors, [])
        self.assertEqual(len(reviews), 15)
        self.assertEqual({review["decision"] for review in reviews}, {"KEEP"})

    def test_unreviewed_or_mutable_baseline_is_rejected(self) -> None:
        invalid = {
            "source": "obra/superpowers",
            "reviewed_head": "main",
            "decision": "PENDING",
            "local_tree_sha256": "not-a-hash",
        }
        errors = UPSTREAM.review_errors(invalid)

        self.assertTrue(any("reviewed_head" in error for error in errors))
        self.assertTrue(any("decision" in error for error in errors))
        self.assertTrue(any("local_tree_sha256" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
