from __future__ import annotations

import csv
import importlib.util
import os
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("divan_validate", ROOT / "scripts" / "validate.py")
assert SPEC and SPEC.loader
VALIDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATE)


class FrontmatterTests(unittest.TestCase):
    def test_inline_scalar(self) -> None:
        self.assertEqual(VALIDATE.frontmatter_alani("name: sadrazam", "name"), "sadrazam")

    def test_literal_block_scalar(self) -> None:
        value = VALIDATE.frontmatter_alani("description: |-\n  ilk satir\n  ikinci satir", "description")
        self.assertEqual(value, "ilk satir\nikinci satir")

    def test_folded_block_scalar(self) -> None:
        value = VALIDATE.frontmatter_alani("description: >\n  ilk satir\n  ikinci satir", "description")
        self.assertEqual(value, "ilk satir ikinci satir")

    def test_indented_plain_scalar(self) -> None:
        value = VALIDATE.frontmatter_alani("description:\n  ilk satir\n  ikinci satir\nlicense: MIT", "description")
        self.assertEqual(value, "ilk satir ikinci satir")


class RepositoryTests(unittest.TestCase):
    def test_repository_audit_includes_community_standards(self) -> None:
        with mock.patch.object(
            VALIDATE, "standards_validate_contract", return_value=["fixture standards issue"]
        ):
            errors, _warnings, _packages, _skills = VALIDATE.denetle(ROOT)

        self.assertIn("TOPLULUK STANDARTLARI: fixture standards issue", errors)

    def test_repository_audit_includes_source_hygiene(self) -> None:
        with mock.patch.object(
            VALIDATE, "hijyen_source_issues", return_value=["fixture encoding issue"]
        ):
            errors, _warnings, _packages, _skills = VALIDATE.denetle(ROOT)

        self.assertIn("REPO HIJYENI: fixture encoding issue", errors)
    def test_repository_passes_local_audit(self) -> None:
        errors, _warnings, packages, skills = VALIDATE.denetle(ROOT)
        self.assertEqual(errors, [])
        self.assertEqual((packages, skills), (5, 41))

    def test_eval_contract_rejects_empty_and_escaping_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-eval-test-") as temporary:
            skill_dir = pathlib.Path(temporary) / "ornek"
            eval_dir = skill_dir / "evals"
            eval_dir.mkdir(parents=True)
            (eval_dir / "evals.json").write_text(
                """{
                  "skill_name": "yanlis",
                  "evals": [
                    {"id": 1, "prompt": "", "expected_output": "sonuc", "expectations": [], "files": ["../../sir.txt"]},
                    {"id": 2, "prompt": "ikinci", "expected_output": "sonuc", "expectations": ["olcut"], "files": []}
                  ]
                }""",
                encoding="utf-8",
            )
            errors: list[str] = []
            VALIDATE.eval_sozlesmesini_denetle(skill_dir, "ornek", errors)
            joined = "\n".join(errors)
            self.assertIn("skill_name", joined)
            self.assertIn("prompt", joined)
            self.assertIn("expectations", joined)
            self.assertIn("skill disina cikiyor", joined)

    def test_release_records_reject_stale_public_surface(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-test-") as temporary:
            root = pathlib.Path(temporary)
            (root / "docs").mkdir()
            (root / "site").mkdir()
            (root / "evals").mkdir()
            (root / "registry").mkdir()
            (root / ".divan").mkdir()
            records = {
                "VERSION": "0.10.0\n",
                "README.md": "Sürüm: v0.10.0\n",
                "README.en.md": "Current release: v0.10.0\n",
                "CHANGELOG.md": "## [0.10.0] - 2026-07-18\n",
                "BLUEPRINT.md": "- **v0.10.0 ✓** published\n",
                "docs/Kurulum.md": "DIVAN_REF=v0.10.0\n",
                "docs/index.html": "v0.10.0\n",
                "site/index.html": "v0.10.0\n",
                "evals/README.md": "python evals/run.py --check\n",
                "docs/Home.md": "Divan Wiki v0.10.0\n",
                "docs/Durum-ve-Yol-Haritasi.md": "Durum v0.10.0\n",
                "wiki-pages.json": '{"pages": [{"source": "docs/Home.md"}]}\n',
                "docs/Aday-Meclisi.md": "never-auto-install\n",
                "registry/candidates.json": '{"autonomy": "never-auto-install"}\n',
                ".divan/progress.md": "## Sıradaki kesin adım\nEval runner\n",
            }
            for relative, content in records.items():
                (root / relative).write_text(content, encoding="utf-8")

            marketplace = {"version": "0.10.0", "metadata": {"version": "0.10.0"}}
            errors: list[str] = []
            VALIDATE.surum_kayitlarini_denetle(root, marketplace, errors)
            self.assertEqual(errors, [])

            (root / "README.md").write_text("Sürüm: v0.7.0\n", encoding="utf-8")
            errors = []
            VALIDATE.surum_kayitlarini_denetle(root, marketplace, errors)
            self.assertIn("README 'v0.10.0'", "\n".join(errors))

    def test_fallback_installers_require_checksum_and_provenance(self) -> None:
        for name in ("kur-codex.ps1", "kur-codex.sh"):
            text = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            normalized = text.lower().replace("-", "_")
            self.assertNotIn("DIVAN_REF:-main", text)
            self.assertNotIn('else { "main" }', text)
            self.assertIn("archive_sha256", normalized)
            self.assertIn("source_commit", normalized)
            self.assertIn("ls-remote", text)
            self.assertIn("installed_at", normalized)
            self.assertIn("SHA256", text.upper())
        release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("git archive --format=zip", release)
        self.assertIn("source_commit=", release)
        self.assertIn("gh release create", release)
        self.assertNotIn("--clobber", release)

    @unittest.skipIf(os.name == "nt", "Shell installer coverage runs on POSIX hosts")
    def test_shell_installer_backs_up_collisions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-installer-test-") as temporary:
            base = pathlib.Path(temporary)
            skills_dir = base / "skills"
            state_dir = base / "state"
            env = os.environ.copy()
            env.update(
                {
                    "DIVAN_SOURCE_DIR": str(ROOT),
                    "CODEX_SKILLS_DIR": str(skills_dir),
                    "DIVAN_STATE_DIR": str(state_dir),
                }
            )
            command = ["bash", str(ROOT / "scripts" / "kur-codex.sh")]
            subprocess.run(command, check=True, env=env, capture_output=True, text=True)
            self.assertEqual(len(list(skills_dir.glob("*/SKILL.md"))), 41)

            marker = skills_dir / "sadrazam" / "kullanici-dosyasi.txt"
            marker.write_text("koru", encoding="utf-8")
            subprocess.run(command, check=True, env=env, capture_output=True, text=True)
            self.assertFalse(marker.exists())
            backups = list(state_dir.glob("divan-backups/*/sadrazam/kullanici-dosyasi.txt"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "koru")

            subprocess.run(
                ["bash", str(ROOT / "scripts" / "kaldir-codex.sh")],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertTrue(marker.exists())
            self.assertEqual(marker.read_text(encoding="utf-8"), "koru")

    @unittest.skipUnless(os.name == "nt", "PowerShell installer coverage runs on Windows hosts")
    def test_powershell_installer_backs_up_collisions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-installer-test-") as temporary:
            base = pathlib.Path(temporary)
            skills_dir = base / "skills"
            state_dir = base / "state"
            env = os.environ.copy()
            env.update(
                {
                    "DIVAN_SOURCE_DIR": str(ROOT),
                    "CODEX_SKILLS_DIR": str(skills_dir),
                    "DIVAN_STATE_DIR": str(state_dir),
                }
            )
            install = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(ROOT / "scripts" / "kur-codex.ps1"),
            ]
            uninstall = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(ROOT / "scripts" / "kaldir-codex.ps1"),
            ]
            subprocess.run(install, check=True, env=env, capture_output=True, text=True)
            self.assertEqual(len(list(skills_dir.glob("*/SKILL.md"))), 41)
            pointer = state_dir / "divan-install-latest"
            manifest = pathlib.Path(pointer.read_text(encoding="utf-8-sig").strip())
            with manifest.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(len(rows), 41)
            self.assertEqual(
                set(rows[0]),
                {
                    "skill",
                    "hedef",
                    "yedek",
                    "surum",
                    "ref",
                    "source_commit",
                    "archive_sha256",
                    "installed_sha256",
                    "installed_at",
                },
            )
            self.assertEqual(
                rows[0]["surum"], (ROOT / "VERSION").read_text(encoding="utf-8").strip()
            )
            self.assertEqual(rows[0]["archive_sha256"], "local-source")

            marker = skills_dir / "sadrazam" / "kullanici-dosyasi.txt"
            marker.write_text("koru", encoding="utf-8")
            subprocess.run(install, check=True, env=env, capture_output=True, text=True)
            self.assertFalse(marker.exists())
            backups = list(state_dir.glob("divan-backups/*/sadrazam/kullanici-dosyasi.txt"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "koru")

            subprocess.run(uninstall, check=True, env=env, capture_output=True, text=True)
            self.assertTrue(marker.exists())
            self.assertEqual(marker.read_text(encoding="utf-8"), "koru")

    @unittest.skipUnless(os.name == "nt", "PowerShell checksum coverage runs on Windows hosts")
    def test_powershell_installer_rejects_checksum_mismatch_before_extract(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-checksum-test-") as temporary:
            base = pathlib.Path(temporary)
            archive = base / "divan-v0.11.1.zip"
            archive.write_bytes(b"not a trusted archive")
            skills_dir = base / "skills"
            env = os.environ.copy()
            env.pop("DIVAN_SOURCE_DIR", None)
            env.update(
                {
                    "DIVAN_REF": "v0.11.1",
                    "DIVAN_ARCHIVE_PATH": str(archive),
                    "DIVAN_ARCHIVE_SHA256": "0" * 64,
                    "DIVAN_SOURCE_COMMIT": "fixture-commit",
                    "CODEX_SKILLS_DIR": str(skills_dir),
                    "DIVAN_STATE_DIR": str(base / "state"),
                }
            )
            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(ROOT / "scripts" / "kur-codex.ps1"),
                ],
                check=False,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SHA-256", result.stderr + result.stdout)
            self.assertFalse(skills_dir.exists())


if __name__ == "__main__":
    unittest.main()
