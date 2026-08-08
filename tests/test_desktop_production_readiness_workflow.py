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

    def test_readiness_receives_required_signing_material_only_in_protected_job(self) -> None:
        for name in (
            "DIVAN_UPDATER_PUBKEY",
            "DIVAN_UPDATER_ENDPOINT",
            "DIVAN_UPDATER_ARTIFACT_BASE_URL",
            "DIVAN_WINDOWS_SIGN_COMMAND",
            "TAURI_SIGNING_PRIVATE_KEY",
            "TAURI_SIGNING_PRIVATE_KEY_PASSWORD",
        ):
            self.assertIn(f"{name}: ${{{{ secrets.{name} }}}}", self.workflow)
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
        self.assertIn('System32/where.exe', self.probe)
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
