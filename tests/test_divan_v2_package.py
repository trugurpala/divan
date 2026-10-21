import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts.package_divan_v2 import build_package

ROOT = Path(__file__).resolve().parents[1]


class DivanV2PackageTests(unittest.TestCase):
    def copy_repository(self, destination):
        shutil.copytree(ROOT / "plugins", destination / "plugins")
        shutil.copytree(ROOT / ".agents", destination / ".agents")
        return destination

    def test_build_package_contains_only_publishable_plugin_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "divan-2.0.0-alpha.1.zip"
            report = build_package(ROOT, output)

            self.assertTrue(output.is_file())
            self.assertLess(report["compressed_bytes"], 100 * 1024 * 1024)
            self.assertLessEqual(report["entries"], 5000)

            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertIn(".codex-plugin/plugin.json", names)
                self.assertIn("skills/divan/SKILL.md", names)
                for notice in ("LICENSE", "THIRD_PARTY_LICENSES.md"):
                    self.assertEqual(archive.read(notice), (ROOT / notice).read_bytes())
                for skill in (ROOT / "plugins/divan/skills").iterdir():
                    if skill.is_dir():
                        self.assertEqual(archive.read(f"skills/{skill.name}/LICENSE"), archive.read("LICENSE"))
                self.assertFalse(any(name.startswith("tests/") for name in names))
                self.assertFalse(any(name.startswith("docs/") for name in names))
                self.assertFalse(any(name.endswith(".py") for name in names))

    def test_invalid_repository_preserves_existing_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.copy_repository(Path(tmp) / "repo")
            output = Path(tmp) / "divan.zip"
            build_package(repo, output)
            previous = output.read_bytes()
            manifest = repo / "plugins/divan/.codex-plugin/plugin.json"
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["mcpServers"] = "./.mcp.json"
            manifest.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "skills-only"):
                build_package(repo, output)
            self.assertEqual(output.read_bytes(), previous)

    def test_rejects_unapproved_files_without_producing_package(self):
        paths = (
            ".env",
            ".env.local",
            "credentials.json",
            "dist/bundle.js",
            "skills/divan/references/.env",
            "skills/divan/references/__pycache__/cached.pyc",
        )
        for relative in paths:
            with self.subTest(path=relative), tempfile.TemporaryDirectory() as tmp:
                repo = self.copy_repository(Path(tmp) / "repo")
                unexpected = repo / "plugins/divan" / relative
                unexpected.parent.mkdir(parents=True, exist_ok=True)
                unexpected.write_text("dummy fixture, no secret", encoding="utf-8")
                output = Path(tmp) / "divan.zip"

                with self.assertRaisesRegex(ValueError, "unapproved package file"):
                    build_package(repo, output)
                self.assertFalse(output.exists())

    def test_rejects_output_inside_plugin_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.copy_repository(Path(tmp) / "repo")
            output = repo / "plugins/divan/divan.zip"

            with self.assertRaisesRegex(ValueError, "output.*plugin"):
                build_package(repo, output)
            self.assertFalse(output.exists())

    def test_compressed_limit_failure_preserves_existing_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "divan.zip"
            build_package(ROOT, output)
            previous = output.read_bytes()

            with patch("scripts.package_divan_v2.MAX_COMPRESSED_BYTES", 1):
                with self.assertRaisesRegex(ValueError, "compressed size"):
                    build_package(ROOT, output)

            self.assertTrue(output.exists(), "a failed rebuild removed the last valid package")
            self.assertEqual(output.read_bytes(), previous)
            self.assertEqual([path.name for path in Path(tmp).iterdir()], ["divan.zip"])

    def test_packages_are_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.zip"
            second = Path(tmp) / "second.zip"
            build_package(ROOT, first)
            build_package(ROOT, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_accepts_distribution_license_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.copy_repository(Path(tmp) / "repo")
            for filename in ("LICENSE", "THIRD_PARTY_LICENSES.md"):
                (repo / "plugins/divan" / filename).write_text("fixture license", encoding="utf-8")
            for skill in (repo / "plugins/divan/skills").iterdir():
                if skill.is_dir():
                    (skill / "LICENSE").write_text("fixture license", encoding="utf-8")
            output = Path(tmp) / "divan.zip"
            build_package(repo, output)
            with zipfile.ZipFile(output) as archive:
                self.assertIn("LICENSE", archive.namelist())
                self.assertIn("THIRD_PARTY_LICENSES.md", archive.namelist())

    def test_cli_uses_manifest_version_from_another_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.copy_repository(Path(tmp) / "repo")
            shutil.copytree(ROOT / "scripts", repo / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
            manifest = repo / "plugins/divan/.codex-plugin/plugin.json"
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["version"] = "2.3.4-alpha.9"
            manifest.write_text(json.dumps(payload), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(repo / "scripts/package_divan_v2.py")],
                cwd=tmp, capture_output=True, text=True, check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((repo / "dist/divan-2.3.4-alpha.9.zip").is_file(), result.stdout)
            self.assertEqual(len(list((repo / "dist").glob("*.zip"))), 1)

    def test_rejects_symbolic_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.copy_repository(Path(tmp) / "repo")
            outside = Path(tmp) / "outside.md"
            outside.write_text("dummy outside fixture", encoding="utf-8")
            link = repo / "plugins/divan/skills/divan/references/outside.md"
            link.parent.mkdir(parents=True, exist_ok=True)
            try:
                link.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"creating symlinks is unavailable on this host: {exc}")
            output = Path(tmp) / "divan.zip"

            with self.assertRaisesRegex(ValueError, "link"):
                build_package(repo, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
