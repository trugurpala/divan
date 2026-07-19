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
    def test_invalid_utf8_bom_and_mojibake_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            invalid = root / "invalid.md"
            bom = root / "bom.md"
            mojibake = root / "mojibake.md"
            clean = root / "clean.md"
            invalid.write_bytes(b"invalid: \xff\n")
            bom.write_bytes(b"\xef\xbb\xbfheading\n")
            mojibake.write_text("G\u00c3\u00b6rev bozuk\n", encoding="utf-8")
            clean.write_text("Görev temiz\n", encoding="utf-8")

            issues = hijyen.text_issues(root, [invalid, bom, mojibake, clean])

            self.assertEqual(len(issues), 3)
            self.assertTrue(any("UTF-8" in issue and "invalid.md" in issue for issue in issues))
            self.assertTrue(any("BOM" in issue and "bom.md" in issue for issue in issues))
            self.assertTrue(any("mojibake" in issue and "mojibake.md" in issue for issue in issues))

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

            issues = hijyen.subprocess_encoding_issues(root)

            self.assertEqual(issues, ["scripts/unsafe.py:2: text subprocess encoding='utf-8' ister"])


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
