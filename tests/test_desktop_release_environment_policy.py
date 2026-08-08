from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CANDIDATE_WORKFLOW = ROOT / ".github" / "workflows" / "desktop-release.yml"
PROMOTION_WORKFLOW = ROOT / ".github" / "workflows" / "desktop-promote.yml"


class DesktopReleaseEnvironmentPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate = CANDIDATE_WORKFLOW.read_text(encoding="utf-8")
        self.promotion = PROMOTION_WORKFLOW.read_text(encoding="utf-8")

    def _assert_strict_policy_block(self, text: str) -> None:
        if "required_rule_count" in text:
            # GitHub-hosted bash preflight.
            self.assertIn('select(.type == "required_reviewers")', text)
            self.assertIn("required_rule_count", text)
            self.assertIn("reviewer_count", text)
            self.assertIn("prevent_self_review", text)
            self.assertIn("can_admins_bypass", text)
            self.assertIn("custom_branch_policies", text)
            self.assertIn("protected_branches", text)
            self.assertIn("deployment-branch-policies", text)
            self.assertIn("main_policy_count", text)
        else:
            # Windows post-approval revalidation.
            self.assertIn('Where-Object { $_.type -eq "required_reviewers" }', text)
            self.assertIn("prevent_self_review -ne $true", text)
            self.assertIn("can_admins_bypass -ne $false", text)
            self.assertIn("custom_branch_policies", text)
            self.assertIn("protected_branches", text)
            self.assertIn("deployment-branch-policies", text)
            self.assertIn('Where-Object { $_.name -eq "main" }', text)

    def test_candidate_has_unprotected_preflight_before_protected_candidate(self) -> None:
        preflight_start = self.candidate.index("  production-release-environment-policy:")
        candidate_start = self.candidate.index("  signed-windows-candidate:")
        preflight = self.candidate[preflight_start:candidate_start]
        self.assertLess(preflight_start, candidate_start)
        self.assertIn(
            "if: github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'",
            preflight,
        )
        self.assertNotIn("environment: production-release", preflight)
        self.assertIn("GH_TOKEN: ${{ github.token }}", preflight)
        self.assertNotIn("secrets.", preflight)
        self.assertIn("production-release-environment-policy", self.candidate[candidate_start:])
        self._assert_strict_policy_block(preflight)

    def test_candidate_revalidates_policy_after_approval_before_checkout(self) -> None:
        candidate = self.candidate[self.candidate.index("  signed-windows-candidate:") :]
        verify_start = candidate.index(
            "- name: Re-verify production-release policy after environment approval"
        )
        checkout_start = candidate.index("- name: Checkout exact source commit")
        verify = candidate[verify_start:checkout_start]
        self.assertLess(verify_start, checkout_start)
        self.assertIn("DIVAN_POLICY_TOKEN: ${{ github.token }}", verify)
        self.assertNotIn("secrets.", verify)
        self._assert_strict_policy_block(verify)

    def test_promotion_has_unprotected_preflight_before_protected_promotion(self) -> None:
        preflight_start = self.promotion.index("  production-release-environment-policy:")
        promote_start = self.promotion.index("  promote:")
        preflight = self.promotion[preflight_start:promote_start]
        self.assertLess(preflight_start, promote_start)
        self.assertIn("if: github.ref == 'refs/heads/main'", preflight)
        self.assertNotIn("environment: production-release", preflight)
        self.assertIn("GH_TOKEN: ${{ github.token }}", preflight)
        self.assertNotIn("secrets.", preflight)
        promote_header = self.promotion[
            promote_start : self.promotion.index("    steps:", promote_start)
        ]
        self.assertIn("needs: production-release-environment-policy", promote_header)
        self._assert_strict_policy_block(preflight)

    def test_promotion_revalidates_policy_after_approval_before_checkout(self) -> None:
        promote = self.promotion[self.promotion.index("  promote:") :]
        verify_start = promote.index(
            "- name: Re-verify production-release policy after environment approval"
        )
        checkout_start = promote.index("- name: Checkout exact source")
        verify = promote[verify_start:checkout_start]
        self.assertLess(verify_start, checkout_start)
        self.assertIn("DIVAN_POLICY_TOKEN: ${{ github.token }}", verify)
        self.assertNotIn("secrets.", verify)
        self._assert_strict_policy_block(verify)

    def test_release_contract_tracks_policy_and_promotion_workflow_changes(self) -> None:
        self.assertIn('      - ".github/workflows/desktop-promote.yml"', self.candidate)
        self.assertIn(
            '      - "tests/test_desktop_release_environment_policy.py"',
            self.candidate,
        )
        contract = self.candidate[
            self.candidate.index("  contract:") : self.candidate.index("  updater-e2e-windows:")
        ]
        self.assertIn("tests.test_desktop_release_environment_policy", contract)


if __name__ == "__main__":
    unittest.main()
