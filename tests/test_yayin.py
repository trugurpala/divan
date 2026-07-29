from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import struct
import tempfile
import unittest
import zlib
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("divan_release", ROOT / "scripts" / "release.py")
assert SPEC and SPEC.loader
YAYIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(YAYIN)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def minimal_png(width: int = 1280, height: int = 640) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(b""))
        + png_chunk(b"IEND", b"")
    )


class PublicationTests(unittest.TestCase):
    def test_social_preview_is_release_tracked_with_exact_png_contract(self) -> None:
        manifest = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))
        surface = next(
            row
            for row in manifest["public_surfaces"]
            if row["id"] == "social-preview"
        )
        self.assertEqual(surface["path"], "docs/assets/divan-social-preview.png")
        self.assertEqual(
            surface["binary"],
            {"format": "png", "width": 1280, "height": 640, "max_bytes": 1_000_000},
        )
        YAYIN._validate_binary_surface(ROOT / surface["path"], surface["binary"])

    def test_png_contract_rejects_wrong_dimensions_and_oversize(self) -> None:
        valid_png = minimal_png()
        with tempfile.TemporaryDirectory(prefix="divan-preview-") as temporary:
            preview = pathlib.Path(temporary) / "preview.png"
            preview.write_bytes(valid_png)
            YAYIN._validate_binary_surface(
                preview,
                {"format": "png", "width": 1280, "height": 640, "max_bytes": 100},
            )
            with self.assertRaisesRegex(ValueError, "boyutlar"):
                YAYIN._validate_binary_surface(
                    preview,
                    {"format": "png", "width": 1200, "height": 640, "max_bytes": 100},
                )
            with self.assertRaisesRegex(ValueError, "dosya boyutu"):
                YAYIN._validate_binary_surface(
                    preview,
                    {"format": "png", "width": 1280, "height": 640, "max_bytes": 10},
                )

    def test_png_contract_rejects_truncation_missing_chunks_and_bad_crc(self) -> None:
        contract = {"format": "png", "width": 1280, "height": 640, "max_bytes": 1000}
        payload = minimal_png()
        with tempfile.TemporaryDirectory(prefix="divan-preview-") as temporary:
            preview = pathlib.Path(temporary) / "preview.png"
            for invalid in (payload[:-1], payload[:33]):
                with self.subTest(length=len(invalid)):
                    preview.write_bytes(invalid)
                    with self.assertRaisesRegex(ValueError, "chunk|IDAT|IEND"):
                        YAYIN._validate_binary_surface(preview, contract)
            corrupt = bytearray(payload)
            corrupt[29] ^= 0x01
            preview.write_bytes(corrupt)
            with self.assertRaisesRegex(ValueError, "CRC"):
                YAYIN._validate_binary_surface(preview, contract)

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
        self.assertIn("scripts/divan.py install --host both", notes)
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
                "scripts/divan.py",
                "scripts/host_lifecycle.py",
                "scripts/legacy_state.py",
                "scripts/hygiene.py",
                "scripts/verify.py",
                "scripts/standards.py",
                "scripts/naming.py",
                "evals/run.py",
                "evals/adapters/claude_agent.py",
                "evals/adapters/codex_judge.py",
                "NOTICE.md",
                "registry/upstream-baselines.json",
                ".github/workflows/compatibility.yml",
                ".github/workflows/quality-gate.yml",
                "registry/community-standards.json",
                "registry/standard-exceptions.json",
                "docs/Topluluk-Standartlari.md",
                "scripts/validate.py",
                ".divan/evidence/teftis-20260721-v013-community-standards.md",
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

    def test_real_manifest_prepare_preserves_published_truth(self) -> None:
        old = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        progress = (ROOT / ".divan" / "progress.md").read_text(encoding="utf-8")
        published_prefix = "- Latest published release: v"
        published = next(
            line.removeprefix(published_prefix)
            for line in progress.splitlines()
            if line.startswith(published_prefix)
        )
        major, minor, patch = map(int, old.split("."))
        new = f"{major}.{minor}.{patch + 1}"
        manifest = json.loads(
            (ROOT / "release-manifest.json").read_text(encoding="utf-8")
        )
        manifest["public_surfaces"] = [
            surface
            for surface in manifest["public_surfaces"]
            if surface.get("replace_version")
        ]

        with tempfile.TemporaryDirectory(prefix="divan-real-prepare-") as temporary:
            root = pathlib.Path(temporary)

            def copy(relative: str) -> None:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)

            for relative in (
                "VERSION",
                ".claude-plugin/marketplace.json",
                ".agents/plugins/marketplace.json",
            ):
                copy(relative)
            for surface in manifest["public_surfaces"]:
                copy(surface["path"])
            (root / "release-manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            YAYIN.hazirla(new, root)

            self.assertEqual(
                (root / "VERSION").read_text(encoding="utf-8").strip(), new
            )
            texts = {
                relative: (root / relative).read_text(encoding="utf-8")
                for relative in (
                    "README.md",
                    "README.en.md",
                    "README.tr.md",
                    "docs/Hizli-Baslangic.md",
                    "docs/Kurulum.md",
                )
            }
            english_guard = (
                "If Current source differs from Latest published, substitute "
                "Latest published in every `--ref` command."
            )
            turkish_guard = (
                "Güncel kaynak Son yayımlanan sürümden farklıysa bütün `--ref` "
                "komutlarında Son yayımlanan sürümü kullan."
            )

            self.assertIn(f"**Current source:** v{new}", texts["README.md"])
            self.assertIn(f"**Güncel kaynak:** v{new}", texts["README.tr.md"])
            self.assertIn(
                f"**Latest published:** v{published}", texts["README.md"]
            )
            self.assertIn(
                f"**Son yayımlanan:** v{published}", texts["README.tr.md"]
            )
            self.assertNotIn(f"**Latest published:** v{new}", texts["README.md"])
            self.assertNotIn(f"**Son yayımlanan:** v{new}", texts["README.tr.md"])

            for relative, text in texts.items():
                normalized = " ".join(text.split())
                with self.subTest(relative=relative):
                    self.assertIn(f"--ref v{new}", text)
                    self.assertIn(
                        english_guard
                        if relative in {"README.md", "README.en.md"}
                        else turkish_guard,
                        normalized,
                    )
            self.assertNotIn(f"Both are v{old}", texts["README.md"])
            self.assertNotIn(f"ikisi de v{old}", texts["README.tr.md"])
            self.assertNotIn(
                "Güncel kararlı ref", texts["docs/Hizli-Baslangic.md"]
            )
            self.assertNotIn("Güncel kararlı ref", texts["docs/Kurulum.md"])

            for surface in manifest["public_surfaces"]:
                text = (root / surface["path"]).read_text(encoding="utf-8")
                for pattern in surface["version_patterns"]:
                    with self.subTest(surface=surface["id"], pattern=pattern):
                        self.assertIn(pattern.format(version=new), text)
                        self.assertNotIn(pattern.format(version=old), text)

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
