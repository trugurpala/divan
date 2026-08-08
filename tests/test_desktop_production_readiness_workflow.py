from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "desktop-production-readiness.yml"
PROBE = ROOT / "scripts" / "windows_desktop_production_readiness.ps1"


class DesktopProductionReadinessWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = WORKFLOW.read_text(encoding="utf-8")
        self.probe = PROBE.read_text(encoding="utf-8")

    def test_readiness_is_manual_main_only_and_environment_protected(self) -> None:
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertNotIn("pull_request:", self.workflow)
        self.assertIn("if: github.ref == 'refs/heads/main'", self.workflow)
        self.assertIn("environment: production-release", self.workflow)
        self.assertIn("runs-on: windows-latest", self.workflow)
        self.assertIn("needs: production-release-environment-policy", self.workflow)

    def test_production_release_policy_is_fail_closed_before_and_after_approval(self) -> None:
        preflight_start = self.workflow.index("  production-release-environment-policy:")
        readiness_start = self.workflow.index("  production-readiness:")
        preflight = self.workflow[preflight_start:readiness_start]
        readiness = self.workflow[readiness_start:]

        self.assertIn(
            "Verify production-release environment is protected before readiness approval",
            preflight,
        )
        self.assertIn("GH_TOKEN: ${{ github.token }}", preflight)
        self.assertIn("environments/production-release", preflight)
        self.assertIn('select(.type == "required_reviewers")', preflight)
        self.assertIn("prevent_self_review", preflight)
        self.assertIn("can_admins_bypass", preflight)
        self.assertIn("deployment-branch-policies", preflight)
        self.assertIn("production-release must allow only the main branch policy", preflight)
        self.assertNotIn("secrets.", preflight)

        self.assertIn("needs: production-release-environment-policy", readiness)
        post_start = readiness.index("- name: Re-verify production-release policy after environment approval")
        checkout_start = readiness.index("- name: Checkout exact main source", post_start)
        post_approval = readiness[post_start:checkout_start]
        self.assertLess(post_start, checkout_start)
        self.assertIn("DIVAN_POLICY_TOKEN: ${{ github.token }}", post_approval)
        self.assertIn("Bearer $env:DIVAN_POLICY_TOKEN", post_approval)
        self.assertIn("required_reviewers", post_approval)
        self.assertIn("prevent_self_review", post_approval)
        self.assertIn("can_admins_bypass", post_approval)
        self.assertIn("deployment-branch-policies", post_approval)
        self.assertIn("must still allow only the main branch after environment approval", post_approval)
        self.assertNotIn("secrets.", post_approval)
        self.assertEqual(self.workflow.count("DIVAN_POLICY_TOKEN: ${{ github.token }}"), 1)

    def test_readiness_requires_exact_accepted_main_source_sha_pin(self) -> None:
        self.assertIn("source_sha:", self.workflow)
        self.assertIn("required: true", self.workflow)
        self.assertIn("DIVAN_EXPECTED_SOURCE_SHA: ${{ inputs.source_sha }}", self.workflow)
        self.assertIn("Verify requested production-readiness source identity", self.workflow)
        self.assertIn("source_sha must be an exact 40-character Git commit SHA", self.workflow)
        self.assertIn("Production readiness checkout does not match the workflow event source SHA", self.workflow)
        self.assertIn(
            "Requested production readiness source SHA does not match the workflow source commit",
            self.workflow,
        )
        self.assertIn("Invoke-RestMethod", self.workflow)
        self.assertIn("git/ref/heads/main", self.workflow)
        self.assertIn(
            "main moved after production readiness dispatch; restart DSK-06 and DSK-07 on current main",
            self.workflow,
        )

    def test_live_main_token_is_scoped_only_to_source_verification_step(self) -> None:
        verify_start = self.workflow.index("Verify requested production-readiness source identity")
        setup_start = self.workflow.index("Setup Python", verify_start)
        verify = self.workflow[verify_start:setup_start]
        rest = self.workflow[setup_start:]
        self.assertIn("DIVAN_GITHUB_TOKEN: ${{ github.token }}", verify)
        self.assertIn("Bearer $env:DIVAN_GITHUB_TOKEN", verify)
        self.assertNotIn("DIVAN_GITHUB_TOKEN", rest)

    def test_signing_material_is_scoped_only_to_the_probe_step(self) -> None:
        probe_start = self.workflow.index("Probe production signing and updater material")
        attest_start = self.workflow.index("Attest production readiness evidence", probe_start)
        probe = self.workflow[probe_start:attest_start]
        before_probe = self.workflow[:probe_start]
        after_probe = self.workflow[attest_start:]
        for name in (
            "DIVAN_UPDATER_PUBKEY",
            "DIVAN_UPDATER_ENDPOINT",
            "DIVAN_UPDATER_ARTIFACT_BASE_URL",
            "DIVAN_WINDOWS_SIGN_COMMAND",
            "TAURI_SIGNING_PRIVATE_KEY",
            "TAURI_SIGNING_PRIVATE_KEY_PASSWORD",
        ):
            secret_ref = f"{name}: ${{{{ secrets.{name} }}}}"
            self.assertIn(secret_ref, probe)
            self.assertNotIn(secret_ref, before_probe)
            self.assertNotIn(secret_ref, after_probe)
            self.assertEqual(self.workflow.count(secret_ref), 1)
        self.assertIn("permissions: read-all", self.workflow)
        self.assertIn("contents: read", self.workflow)
        self.assertNotIn("contents: write", self.workflow)

    def test_probe_fails_closed_before_claiming_readiness(self) -> None:
        self.assertIn('Require-EnvironmentValue -Name "DIVAN_UPDATER_PUBKEY"', self.probe)
        self.assertIn('Require-EnvironmentValue -Name "DIVAN_UPDATER_ENDPOINT"', self.probe)
        self.assertIn('Require-EnvironmentValue -Name "DIVAN_UPDATER_ARTIFACT_BASE_URL"', self.probe)
        self.assertIn('Require-EnvironmentValue -Name "DIVAN_WINDOWS_SIGN_COMMAND"', self.probe)
        self.assertIn('Require-EnvironmentValue -Name "TAURI_SIGNING_PRIVATE_KEY"', self.probe)
        self.assertIn("prepare_desktop_release_config.py", self.probe)
        self.assertIn("git -C $repoRoot rev-parse HEAD", self.probe)
        self.assertIn("git -C $repoRoot rev-parse 'HEAD^{tree}'", self.probe)
        self.assertIn("GITHUB_SHA", self.probe)

    def test_authenticode_probe_executes_real_sign_command_on_isolated_pe(self) -> None:
        self.assertIn("System32/where.exe", self.probe)
        self.assertIn('$signCommandTemplate.Replace("%1", $quotedProbe)', self.probe)
        self.assertIn("& $env:ComSpec /d /s /c $signCommand", self.probe)
        self.assertIn("Get-AuthenticodeSignature $authenticodeProbe", self.probe)
        self.assertIn('$authenticode.Status -ne "Valid"', self.probe)
        self.assertIn("SignerCertificate.NotAfter", self.probe)

    def test_tauri_private_key_is_exercised_by_official_signer(self) -> None:
        self.assertIn("pnpm tauri signer sign $updaterProbe", self.probe)
        self.assertIn("TAURI_SIGNING_PRIVATE_KEY", self.workflow)
        self.assertIn("TAURI_SIGNING_PRIVATE_KEY_PASSWORD", self.workflow)
        self.assertIn("tauri_private_key_sign_probe = $true", self.probe)

    def test_artifact_base_is_exact_immutable_desktop_release_tag(self) -> None:
        self.assertIn('$tag = "desktop-v$version"', self.probe)
        self.assertIn(
            '$expectedArtifactBase = "https://github.com/$env:GITHUB_REPOSITORY/releases/download/$tag"',
            self.probe,
        )
        self.assertIn("artifact_base_exact_release_tag = $true", self.probe)

    def test_evidence_is_attested_and_secret_minimal(self) -> None:
        self.assertIn("actions/attest-build-provenance@", self.workflow)
        self.assertIn("actions/upload-artifact@", self.workflow)
        self.assertIn("name: divan-production-readiness", self.workflow)
        self.assertIn("private_signing_material_persisted = $false", self.probe)
        self.assertIn("secret_values_in_evidence = $false", self.probe)
        evidence_block = self.probe[self.probe.index("$evidence = [ordered]@{") :]
        self.assertNotIn("privateKey =", evidence_block)
        self.assertNotIn("signCommandTemplate =", evidence_block)
        self.assertNotIn("updaterEndpoint =", evidence_block)

    def test_all_actions_are_immutable_sha_pinned(self) -> None:
        mutable = []
        for number, line in enumerate(self.workflow.splitlines(), 1):
            if "uses:" not in line or line.lstrip().startswith("#"):
                continue
            if not re.search(r"uses:\s+[^\s@]+@[0-9a-f]{40}\s+#\s+v\d+", line):
                mutable.append(f"{number}: {line.strip()}")
        self.assertEqual(mutable, [])


if __name__ == "__main__":
    unittest.main()
