from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CARGO = ROOT / "apps" / "desktop" / "src-tauri" / "Cargo.toml"
MAIN = ROOT / "apps" / "desktop" / "src-tauri" / "src" / "main.rs"
E2E_RUST = ROOT / "apps" / "desktop" / "src-tauri" / "src" / "updater_e2e.rs"
BASE_CONFIG = ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json"
WINDOWS_CONFIG = ROOT / "apps" / "desktop" / "src-tauri" / "tauri.windows.conf.json"
PREPARE_RELEASE = ROOT / "scripts" / "prepare_desktop_release_config.py"
UPDATER_SCRIPT = ROOT / "scripts" / "windows_desktop_updater_e2e.ps1"
PRODUCTION_VERIFY_SCRIPT = ROOT / "scripts" / "windows_desktop_production_updater_verify.ps1"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "desktop-release.yml"


class DesktopUpdaterE2EContractTests(unittest.TestCase):
    def test_runtime_probe_is_test_only_and_still_uses_signed_updater(self) -> None:
        cargo = CARGO.read_text(encoding="utf-8")
        main = MAIN.read_text(encoding="utf-8")
        runtime = E2E_RUST.read_text(encoding="utf-8")

        self.assertIn('updater-e2e = ["signed-updater"]', cargo)
        self.assertIn('#[cfg(feature = "updater-e2e")]', main)
        self.assertIn("mod updater_e2e;", main)
        self.assertIn("updater_e2e::maybe_start(app.handle())", main)
        self.assertIn("download_and_install", runtime)
        self.assertIn('"expect-install-error"', runtime)
        self.assertIn('"expect-no-update"', runtime)
        self.assertIn('"verify-download"', runtime)
        self.assertIn(".version_comparator(|_, _| true)", runtime)
        self.assertIn("update.download(|_, _| {}, || {}).await", runtime)
        self.assertIn("app.package_info().version", runtime)

    def test_insecure_local_transport_exists_only_in_ephemeral_e2e_configs(self) -> None:
        script = UPDATER_SCRIPT.read_text(encoding="utf-8")
        production_verify = PRODUCTION_VERIFY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("dangerousInsecureTransportProtocol = $true", script)
        self.assertIn('production_transport_policy = "https-only"', script)
        self.assertIn("dangerousInsecureTransportProtocol = $true", production_verify)
        self.assertIn('production_transport_policy = "https-only"', production_verify)

        for path in (BASE_CONFIG, WINDOWS_CONFIG, PREPARE_RELEASE):
            self.assertNotIn(
                "dangerousInsecureTransportProtocol",
                path.read_text(encoding="utf-8"),
                path.name,
            )

    def test_e2e_is_bound_to_exact_pull_request_head_before_build(self) -> None:
        script = UPDATER_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("GITHUB_EVENT_PATH", script)
        self.assertIn('PSObject.Properties["pull_request"]', script)
        self.assertIn('PSObject.Properties["sha"]', script)
        self.assertIn("git -C $repoRoot fetch --no-tags --depth=1 origin $headSha", script)
        self.assertIn("git -C $repoRoot checkout --force $headSha", script)
        self.assertIn("Set-ExactWorkflowSource", script)
        self.assertLess(
            script.index("Set-ExactWorkflowSource"),
            script.index("$baseConfig = Get-Content $baseConfigPath"),
        )
        self.assertIn("pnpm install --frozen-lockfile", script)
        self.assertIn("pnpm build", script)
        self.assertIn("source_commit = $sourceCommit", script)
        self.assertIn("source_tree = $sourceTree", script)

    def test_e2e_proves_upgrade_bad_signature_recovery_and_no_downgrade(self) -> None:
        script = UPDATER_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("Build-TestVersion -Version $versionN", script)
        self.assertIn("Build-TestVersion -Version $versionN1", script)
        self.assertIn("Build-TestVersion -Version $versionN2", script)
        self.assertIn("Invoke-SignedUpgrade -Expected $versionN1", script)
        self.assertIn("-TamperSignature", script)
        self.assertIn('Invoke-Probe -Mode "expect-install-error"', script)
        self.assertIn("Invoke-SignedUpgrade -Expected $versionN2", script)
        self.assertIn('Invoke-Probe -Mode "expect-no-update"', script)
        self.assertIn("tampered_signature_rejected = $tamperedSignatureRejected", script)
        self.assertIn("forward_signed_recovery = $forwardRecovery", script)
        self.assertIn("downgrade_not_offered = $downgradeNotOffered", script)

    def test_production_key_pair_verifier_uses_tauri_download_without_install(self) -> None:
        script = PRODUCTION_VERIFY_SCRIPT.read_text(encoding="utf-8")
        runtime = E2E_RUST.read_text(encoding="utf-8")
        self.assertIn("pnpm tauri build --no-bundle --features updater-e2e", script)
        self.assertIn('DIVAN_UPDATER_E2E_MODE = "verify-download"', script)
        self.assertIn("production_public_key_runtime_verified = $true", script)
        self.assertIn("install_performed = $false", script)
        self.assertIn("installer_sha256", script)
        self.assertIn("updater_signature_sha256", script)
        verify_start = runtime.index('"verify-download" =>')
        verify_end = runtime.index("        _ => finish(", verify_start)
        verify_block = runtime[verify_start:verify_end]
        self.assertIn(".version_comparator(|_, _| true)", verify_block)
        self.assertIn("update.download(|_, _| {}, || {}).await", verify_block)
        self.assertNotIn("download_and_install", verify_block)
        self.assertNotIn("app.restart()", verify_block)

    def test_release_workflow_builds_frontend_before_updater_cargo_checks(self) -> None:
        workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        e2e_start = workflow.index("  updater-e2e-windows:")
        signed_start = workflow.index("  signed-windows-candidate:")
        e2e = workflow[e2e_start:signed_start]
        signed = workflow[signed_start:]

        self.assertIn("Build updater e2e frontend context", e2e)
        self.assertLess(e2e.index("run: pnpm build"), e2e.index("--features updater-e2e --locked"))
        self.assertIn("Build signed updater frontend context", signed)
        self.assertLess(
            signed.index("run: pnpm build"),
            signed.index("--features signed-updater --locked"),
        )

    def test_release_workflow_requires_runtime_e2e_before_signed_candidate(self) -> None:
        workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("updater-e2e-windows:", workflow)
        self.assertIn("name: signed-updater-e2e", workflow)
        self.assertIn("windows_desktop_updater_e2e.ps1", workflow)
        self.assertIn("--features updater-e2e --locked", workflow)
        self.assertIn("divan-desktop-updater-e2e", workflow)
        self.assertIn("needs: [contract, updater-e2e-windows]", workflow)
        self.assertIn("pnpm tauri build --bundles nsis --features signed-updater", workflow)
        self.assertNotIn(
            "pnpm tauri build --bundles nsis --features updater-e2e --config $env:DIVAN_RELEASE_CONFIG",
            workflow,
        )

    def test_signed_candidate_verifies_production_key_pair_with_tauri_runtime(self) -> None:
        workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        signed = workflow[workflow.index("  signed-windows-candidate:") :]
        self.assertIn("Verify production updater key pair with Tauri runtime", signed)
        self.assertIn("windows_desktop_production_updater_verify.ps1", signed)
        self.assertIn("-PublicKey $env:DIVAN_UPDATER_PUBKEY", signed)
        self.assertIn("DIVAN_PRODUCTION_UPDATER_VERIFY_EVIDENCE", signed)
        self.assertLess(
            signed.index("Verify production updater key pair with Tauri runtime"),
            signed.index("Generate source-bound updater feed and promotion manifest"),
        )


if __name__ == "__main__":
    unittest.main()
