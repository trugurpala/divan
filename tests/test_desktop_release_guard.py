from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile
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
        self.assertFalse(report["updater_configured"])
        self.assertFalse(report["windows_signing_configured"])

    def test_stable_release_fails_closed_without_external_release_materials(self) -> None:
        report = inspect_desktop(ROOT)

        with self.assertRaisesRegex(DesktopReleaseError, "stable desktop release blocked"):
            require_stable_release(report, {})

    def test_stable_release_requires_signed_config_private_key_and_real_e2e(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            temp_root = pathlib.Path(temp)
            release_config = temp_root / "release.json"
            release_config.write_text(
                json.dumps(
                    {
                        "bundle": {
                            "createUpdaterArtifacts": True,
                            "windows": {"signCommand": "sign-tool %1"},
                        },
                        "plugins": {
                            "updater": {
                                "pubkey": "PUBLIC-KEY",
                                "endpoints": ["https://updates.example.test/latest.json"],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            acceptance = temp_root / "acceptance.json"
            acceptance.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "product": "Divan",
                        "version": version,
                        "platform": "windows",
                        "result": "PASS",
                        "authenticated_worker": True,
                        "worker_agent": "codex",
                        "independent_reviewer": True,
                        "reviewer": "claude",
                        "review_bound_to_diff": True,
                        "ff_only_merge": True,
                        "task_state": "merged",
                        "evidence_kinds": ["execution", "review", "approval"],
                    }
                ),
                encoding="utf-8",
            )

            report = inspect_desktop(
                ROOT,
                release_config=release_config,
                acceptance_evidence=acceptance,
            )
            ready = require_stable_release(
                report,
                {"TAURI_SIGNING_PRIVATE_KEY": "configured-in-secret-store"},
            )

        self.assertTrue(ready["updater_configured"])
        self.assertTrue(ready["windows_signing_configured"])
        self.assertTrue(ready["acceptance_evidence"]["accepted"])
        self.assertEqual(ready["stable_release"], "READY")

    def test_acceptance_evidence_rejects_review_without_diff_binding(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            evidence = pathlib.Path(temp) / "acceptance.json"
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "product": "Divan",
                        "version": version,
                        "platform": "windows",
                        "result": "PASS",
                        "authenticated_worker": True,
                        "worker_agent": "codex",
                        "independent_reviewer": True,
                        "reviewer": "claude",
                        "review_bound_to_diff": False,
                        "ff_only_merge": True,
                        "task_state": "merged",
                        "evidence_kinds": ["execution", "review", "approval"],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DesktopReleaseError, "review_bound_to_diff"):
                inspect_desktop(ROOT, acceptance_evidence=evidence)


if __name__ == "__main__":
    unittest.main()
