from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_desktop_release_config.py"
SPEC = importlib.util.spec_from_file_location("prepare_desktop_release_config", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

ReleaseConfigError = MODULE.ReleaseConfigError
build_release_overlay = MODULE.build_release_overlay


class PrepareDesktopReleaseConfigTests(unittest.TestCase):
    def test_release_overlay_preserves_sidecar_and_adds_signing_and_updater(self) -> None:
        overlay = build_release_overlay(
            ROOT,
            {
                "DIVAN_UPDATER_PUBKEY": "PUBLIC-KEY",
                "DIVAN_UPDATER_ENDPOINT": "https://updates.example.test/divan/{{target}}/{{arch}}/{{current_version}}",
                "DIVAN_WINDOWS_SIGN_COMMAND": "sign-tool --input %1",
            },
        )

        bundle = overlay["bundle"]
        self.assertIn("binaries/divan-core", bundle["externalBin"])
        self.assertTrue(bundle["createUpdaterArtifacts"])
        self.assertEqual(bundle["windows"]["signCommand"], "sign-tool --input %1")
        self.assertEqual(overlay["plugins"]["updater"]["pubkey"], "PUBLIC-KEY")

    def test_release_overlay_rejects_non_https_updater(self) -> None:
        with self.assertRaisesRegex(ReleaseConfigError, "absolute HTTPS"):
            build_release_overlay(
                ROOT,
                {
                    "DIVAN_UPDATER_PUBKEY": "PUBLIC-KEY",
                    "DIVAN_UPDATER_ENDPOINT": "http://updates.example.test/latest.json",
                    "DIVAN_WINDOWS_SIGN_COMMAND": "sign-tool %1",
                },
            )

    def test_release_overlay_rejects_sign_command_without_tauri_placeholder(self) -> None:
        with self.assertRaisesRegex(ReleaseConfigError, "%1"):
            build_release_overlay(
                ROOT,
                {
                    "DIVAN_UPDATER_PUBKEY": "PUBLIC-KEY",
                    "DIVAN_UPDATER_ENDPOINT": "https://updates.example.test/latest.json",
                    "DIVAN_WINDOWS_SIGN_COMMAND": "sign-tool fixed.exe",
                },
            )


if __name__ == "__main__":
    unittest.main()
