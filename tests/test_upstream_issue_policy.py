import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "divan_upstream_issue_policy", ROOT / "scripts/upstream_issue_policy.py"
)
POLICY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(POLICY)


class UpstreamIssuePolicyTests(unittest.TestCase):
    def test_debt_creates_only_when_no_open_issue_exists(self):
        self.assertEqual(
            POLICY.decide([], True)["actions"],
            [{"operation": "create"}],
        )
        self.assertEqual(
            POLICY.decide([{"number": 85}], True)["actions"],
            [{"operation": "update", "issue_number": 85}],
        )

    def test_clean_report_closes_the_reused_issue(self):
        self.assertEqual(
            POLICY.decide([{"number": 85}], False)["actions"],
            [{"operation": "close-clean", "issue_number": 85}],
        )
        self.assertEqual(POLICY.decide([], False)["actions"], [])

    def test_duplicates_are_closed_and_oldest_issue_is_reused(self):
        plan = POLICY.decide(
            [{"number": 91}, {"number": 85}, {"number": 88}], True
        )
        self.assertEqual(plan["primary_issue"], 85)
        self.assertEqual(plan["duplicate_issues"], [88, 91])
        self.assertEqual(
            plan["actions"],
            [
                {"operation": "close-duplicate", "issue_number": 88},
                {"operation": "close-duplicate", "issue_number": 91},
                {"operation": "update", "issue_number": 85},
            ],
        )

    def test_pull_requests_and_malformed_rows_cannot_become_primary(self):
        plan = POLICY.decide(
            [
                {"number": 80, "pull_request": {}},
                {"number": True},
                {"number": -1},
                {"number": 85},
            ],
            True,
        )
        self.assertEqual(plan["primary_issue"], 85)


if __name__ == "__main__":
    unittest.main()
