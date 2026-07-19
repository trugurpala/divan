from __future__ import annotations

import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("divan_hijyen", ROOT / "scripts" / "hijyen.py")
assert SPEC and SPEC.loader
hijyen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hijyen)


class TextHygieneTests(unittest.TestCase):
    def test_text_symlink_escaping_repo_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = pathlib.Path(temp)
            target = pathlib.Path(outside) / "secret.md"
            target.write_bytes("repo dışı\n".encode("utf-8"))
            link = root / "link.md"
            try:
                link.symlink_to(target)
            except OSError as error:
                self.skipTest(f"symlink desteklenmiyor: {error}")

            issues = hijyen.text_issues(root, [link])

            self.assertEqual(issues, ["link.md: repo kökü dışına çıkan symlink reddedildi"])

    def test_invalid_utf8_bom_and_mojibake_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            invalid = root / "invalid.md"
            bom = root / "bom.md"
            mojibake = root / "mojibake.md"
            clean = root / "clean.md"
            crlf = root / "crlf.md"
            invalid.write_bytes(b"invalid: \xff\n")
            bom.write_bytes(b"\xef\xbb\xbfheading\n")
            mojibake.write_bytes("G\u00c3\u00b6rev bozuk\n".encode("utf-8"))
            clean.write_bytes("Görev temiz\n".encode("utf-8"))
            crlf.write_bytes("Satır\r\n".encode("utf-8"))

            issues = hijyen.text_issues(root, [invalid, bom, mojibake, clean, crlf])

            self.assertEqual(len(issues), 4)
            self.assertTrue(any("UTF-8" in issue and "invalid.md" in issue for issue in issues))
            self.assertTrue(any("BOM" in issue and "bom.md" in issue for issue in issues))
            self.assertTrue(any("mojibake" in issue and "mojibake.md" in issue for issue in issues))
            self.assertTrue(any("LF" in issue and "crlf.md" in issue for issue in issues))

    def test_text_subprocess_without_explicit_utf8_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "unsafe.py").write_text(
                "import subprocess\nsubprocess.run(['tool'], text=True)\n",
                encoding="utf-8",
            )
            (scripts / "safe.py").write_text(
                "import subprocess\nsubprocess.run(['tool'], text=True, encoding='utf-8')\n",
                encoding="utf-8",
            )
            (scripts / "latin.py").write_text(
                "import subprocess\nsubprocess.run(['tool'], text=True, encoding='latin-1')\n",
                encoding="utf-8",
            )
            (scripts / "direct.py").write_text(
                "from subprocess import run\nrun(['tool'], text=True)\n",
                encoding="utf-8",
            )
            (scripts / "implicit_text.py").write_text(
                "import subprocess\nsubprocess.run(['tool'], encoding='latin-1')\n",
                encoding="utf-8",
            )

            issues = hijyen.subprocess_encoding_issues(root)

            self.assertEqual(
                issues,
                [
                    "scripts/direct.py:2: text subprocess encoding='utf-8' ister",
                    "scripts/implicit_text.py:2: text subprocess encoding='utf-8' ister",
                    "scripts/latin.py:2: text subprocess encoding='utf-8' ister",
                    "scripts/unsafe.py:2: text subprocess encoding='utf-8' ister",
                ],
            )

    def test_subprocess_scan_reports_syntax_error_and_skips_invalid_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "invalid.py").write_bytes(b"# \xff\n")
            (scripts / "syntax.py").write_bytes(b"if True print('broken')\n")

            issues = hijyen.subprocess_encoding_issues(root)

            self.assertEqual(
                issues,
                ["scripts/syntax.py:1: Python sözdizimi ayrıştırılamadı"],
            )


class GeneratedArtifactTests(unittest.TestCase):
    def test_clean_removes_only_allowlisted_generated_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            generated = [
                root / "pkg" / "__pycache__" / "module.pyc",
                root / ".ruff_cache" / "state",
                root / ".mypy_cache" / "state",
                root / ".pytest_cache" / "state",
                root / "htmlcov" / "index.html",
                root / ".coverage",
            ]
            for path in generated:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("generated", encoding="utf-8")
            protected = [
                root / ".worktrees" / "feature" / "__pycache__" / "keep.pyc",
                root / ".divan" / "evidence" / "teftis.md",
                root / "backups" / "user.txt",
                root / "unknown.tmp",
            ]
            for path in protected:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("keep", encoding="utf-8")

            removed = hijyen.clean_generated(root)

            self.assertEqual(
                {path.relative_to(root).as_posix() for path in removed},
                {
                    ".coverage",
                    ".mypy_cache",
                    ".pytest_cache",
                    ".ruff_cache",
                    "htmlcov",
                    "pkg/__pycache__",
                },
            )
            self.assertTrue(all(path.exists() for path in protected))
            self.assertEqual(hijyen.find_generated(root), [])


if __name__ == "__main__":
    unittest.main()
