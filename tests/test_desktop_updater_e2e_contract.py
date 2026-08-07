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
        self.assertIn("app.package_info().version", runtime)

    def test_insecure_local_transport_exists_only_in_ephemeral_e2e_config(self) -> None:
        script = UPDATER_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("dangerousInsecureTransportProtocol = $true", script)
        self.assertIn('production_transport_policy = "https-only"', script)

        for path in (BASE_CONFIG, WINDOWS_CONFIG, PREPARE_RELEASE):
            self.assertNotIn(
                "dangerousInsecureTransportProtocol",
                path.read_text(encoding="utf-8"),
                path.name,
            )

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


if __name__ == "__main__":
    unittest.main()
