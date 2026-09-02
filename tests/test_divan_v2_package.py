import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.package_divan_v2 import build_package

ROOT = Path(__file__).resolve().parents[1]


class DivanV2PackageTests(unittest.TestCase):
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
                self.assertFalse(any(name.startswith("tests/") for name in names))
                self.assertFalse(any(name.startswith("docs/") for name in names))
                self.assertFalse(any(name.endswith(".py") for name in names))


if __name__ == "__main__":
    unittest.main()
