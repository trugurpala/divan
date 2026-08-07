from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.review_gate import CheckResult, GateVerdict, decide_review, require_release_ready


class ReviewGateTests(unittest.TestCase):
    def test_required_failure_requests_retry(self):
        decision = decide_review([
            CheckResult("tests", True, summary="tests pass"),
            CheckResult("reviewer", False, summary="review found regression"),
        ])
        self.assertEqual(decision.verdict, GateVerdict.RETRY)
        self.assertEqual(decision.reasons, ("review found regression",))

    def test_optional_failure_does_not_block_pass(self):
        decision = decide_review([CheckResult("advisory", False, required=False)])
        self.assertEqual(decision.verdict, GateVerdict.PASS)

    def test_release_requires_pass_approval_and_mandate(self):
        decision = decide_review([CheckResult("tests", True)])
        require_release_ready(review=decision, approved=True, mandate_id="m-1")
        with self.assertRaises(ValueError):
            require_release_ready(review=decision, approved=False, mandate_id="m-1")


if __name__ == "__main__":
    unittest.main()
