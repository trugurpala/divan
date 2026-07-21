from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("divan_yayin", ROOT / "scripts" / "yayin.py")
assert SPEC and SPEC.loader
YAYIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(YAYIN)


class PublicationTests(unittest.TestCase):
    def test_failed_rollback_reports_and_retains_recovery_backup(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-rollback-backup-") as temporary:
            root = pathlib.Path(temporary)
            first = root / "first.txt"
            second = root / "second.txt"
            first.write_text("old-first\n", encoding="utf-8")
            second.write_text("old-second\n", encoding="utf-8")
            real_replace = YAYIN.os.replace
            calls = 0

            def fail_write_and_restore(source, destination):
                nonlocal calls
                calls += 1
                if calls in {2, 3}:
                    raise OSError(f"fixture failure {calls}")
                return real_replace(source, destination)

            with mock.patch.object(YAYIN.os, "replace", side_effect=fail_write_and_restore):
                with self.assertRaisesRegex(RuntimeError, "kurtarma yedeği:") as raised:
                    YAYIN._write_transaction(
                        [(first, "new-first\n"), (second, "new-second\n")]
                    )

            recovery_backups = list(root.glob(".first.txt.*"))
            self.assertEqual(len(recovery_backups), 1)
            self.assertIn(str(recovery_backups[0]), str(raised.exception))
            self.assertEqual(recovery_backups[0].read_text(encoding="utf-8"), "old-first\n")

    def test_repository_publication_surfaces_match(self) -> None:
        current = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        result = YAYIN.denetle(ROOT)
        self.assertEqual(result["version"], current)
        self.assertGreaterEqual(result["surface_count"], 10)

    def test_release_notes_come_from_current_changelog(self) -> None:
        current = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        notes = YAYIN.release_notu(ROOT)
        self.assertTrue(notes.startswith(f"# Divan v{current}"))
        self.assertIn("## Sabitlenmiş kurulum", notes)
        self.assertIn(f"--ref v{current}", notes)
        self.assertIn("scripts/kur-hostlar.py --host both", notes)
        self.assertIn(f"divan-v{current}.sha256", notes)

    def test_both_native_marketplaces_match_release_version(self) -> None:
        current = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        claude = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        codex = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual(claude["version"], current)
        self.assertEqual(codex["version"], current)

    def test_release_manifest_covers_new_public_contracts(self) -> None:
        manifest = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))
        paths = {surface["path"] for surface in manifest["public_surfaces"]}
        self.assertTrue(
            {
                ".agents/plugins/marketplace.json",
                "scripts/kur-hostlar.py",
                "scripts/legacy_state.py",
                "scripts/hijyen.py",
                "scripts/standartlar.py",
                "evals/run.py",
                "evals/adapters/claude_agent.py",
                "evals/adapters/codex_judge.py",
                "NOTICE.md",
                "registry/upstream-baselines.json",
                ".github/workflows/uyumluluk.yml",
                ".github/workflows/teftis.yml",
                "registry/community-standards.json",
                "registry/standard-exceptions.json",
                "docs/Topluluk-Standartlari.md",
                "scripts/validate.py",
            }.issubset(paths)
        )
        real_evidence = next(
            surface
            for surface in manifest["public_surfaces"]
            if surface["id"] == "real-eval-evidence"
        )
        self.assertNotIn("{version}", real_evidence["marker"])

    def test_stale_surface_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-yayin-test-") as temporary:
            root = pathlib.Path(temporary)
            (root / ".claude-plugin").mkdir()
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            (root / "README.md").write_text("v1.2.2\n", encoding="utf-8")
            (root / "CHANGELOG.md").write_text("## [1.2.3]\n\n### Added\n\n- x\n", encoding="utf-8")
            (root / "release-manifest.json").write_text(
                json.dumps({
                    "schema_version": 1,
                    "version_source": "VERSION",
                    "public_surfaces": [{"id": "readme", "path": "README.md", "marker": "v{version}"}],
                }),
                encoding="utf-8",
            )
            (root / ".claude-plugin/marketplace.json").write_text(
                json.dumps({"version": "1.2.3", "metadata": {"version": "1.2.3"}}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "readme"):
                YAYIN.denetle(root)

    def test_prepare_preflights_all_surfaces_before_writing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-prepare-test-") as temporary:
            root = pathlib.Path(temporary)
            (root / ".claude-plugin").mkdir()
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            (root / "README.md").write_text("v1.2.3 version-1.2.3\n", encoding="utf-8")
            (root / "STALE.md").write_text("version missing\n", encoding="utf-8")
            (root / "release-manifest.json").write_text(
                json.dumps({
                    "schema_version": 1,
                    "version_source": "VERSION",
                    "public_surfaces": [
                        {"id": "readme", "path": "README.md", "marker": "v{version}", "replace_version": True, "version_patterns": ["v{version}", "version-{version}"]},
                        {"id": "stale", "path": "STALE.md", "marker": "v{version}", "replace_version": True, "version_patterns": ["v{version}"]},
                    ],
                }),
                encoding="utf-8",
            )
            (root / ".claude-plugin/marketplace.json").write_text(
                json.dumps({"version": "1.2.3", "metadata": {"version": "1.2.3"}}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "STALE.md"):
                YAYIN.hazirla("1.3.0", root)
            self.assertEqual((root / "VERSION").read_text(encoding="utf-8"), "1.2.3\n")
            self.assertEqual((root / "README.md").read_text(encoding="utf-8"), "v1.2.3 version-1.2.3\n")

    def test_prepare_preserves_historical_version_mentions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-prepare-history-") as temporary:
            root = pathlib.Path(temporary)
            (root / ".claude-plugin").mkdir()
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            (root / "README.md").write_text(
                "Current v1.2.3\nHistory v1.2.3\nbadge version-1.2.3\n",
                encoding="utf-8",
            )
            (root / "release-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "version_source": "VERSION",
                        "public_surfaces": [
                            {
                                "id": "readme",
                                "path": "README.md",
                                "marker": "Current v{version}",
                                "replace_version": True,
                                "version_patterns": [
                                    "Current v{version}",
                                    "version-{version}",
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (root / ".claude-plugin/marketplace.json").write_text(
                json.dumps({"version": "1.2.3", "metadata": {"version": "1.2.3"}}),
                encoding="utf-8",
            )

            YAYIN.hazirla("1.2.4", root)

            self.assertEqual(
                (root / "README.md").read_text(encoding="utf-8"),
                "Current v1.2.4\nHistory v1.2.3\nbadge version-1.2.4\n",
            )

    def test_prepare_rolls_back_every_file_when_replace_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-prepare-atomic-") as temporary:
            root = pathlib.Path(temporary)
            (root / ".claude-plugin").mkdir()
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            (root / "README.md").write_text("Current v1.2.3\n", encoding="utf-8")
            (root / "release-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "version_source": "VERSION",
                        "public_surfaces": [
                            {
                                "id": "readme",
                                "path": "README.md",
                                "marker": "Current v{version}",
                                "replace_version": True,
                                "version_patterns": ["Current v{version}"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            marketplace = root / ".claude-plugin" / "marketplace.json"
            marketplace.write_text(
                json.dumps({"version": "1.2.3", "metadata": {"version": "1.2.3"}}),
                encoding="utf-8",
            )
            real_replace = YAYIN.os.replace
            calls = 0

            def fail_once(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("fixture replace failure")
                return real_replace(source, destination)

            with mock.patch.object(YAYIN.os, "replace", side_effect=fail_once):
                with self.assertRaisesRegex(OSError, "fixture replace failure"):
                    YAYIN.hazirla("1.2.4", root)

            self.assertEqual((root / "VERSION").read_text(encoding="utf-8"), "1.2.3\n")
            self.assertIn('"version": "1.2.3"', marketplace.read_text(encoding="utf-8"))
            self.assertEqual((root / "README.md").read_text(encoding="utf-8"), "Current v1.2.3\n")


if __name__ == "__main__":
    unittest.main()
