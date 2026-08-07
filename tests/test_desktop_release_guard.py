from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "desktop_release_guard.py"
SPEC = importlib.util.spec_from_file_location("desktop_release_guard", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

DesktopReleaseError = MODULE.DesktopReleaseError
inspect_desktop = MODULE.inspect_desktop
require_stable_release = MODULE.require_stable_release


class DesktopReleaseGuardTests(unittest.TestCase):
    def test_desktop_identity_and_versions_are_aligned(self) -> None:
        report = inspect_desktop(ROOT)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["version"], (ROOT / "VERSION").read_text().strip())
        self.assertEqual(report["main_binary"], "Divan.exe")
        self.assertTrue(report["core_sidecar"])

    def test_stable_release_fails_closed_without_updater_and_signing(self) -> None:
        report = inspect_desktop(ROOT)

        with self.assertRaisesRegex(DesktopReleaseError, "stable desktop release blocked"):
            require_stable_release(report, {})

    def test_stable_release_requires_all_external_signing_gates(self) -> None:
        report = {
            "status": "PASS",
            "version": "1.2.3",
            "updater_configured": True,
        }
        ready = require_stable_release(
            report,
            {
                "TAURI_SIGNING_PRIVATE_KEY": "configured-in-secret-store",
                "DIVAN_WINDOWS_CODE_SIGNING_READY": "1",
            },
        )

        self.assertEqual(ready["stable_release"], "READY")


if __name__ == "__main__":
    unittest.main()
