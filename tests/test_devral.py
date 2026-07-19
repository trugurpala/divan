import importlib.util
import pathlib
import tempfile
import unittest

KOK = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("devral", KOK / "scripts" / "devral.py")
devral = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(devral)


class DevralTesti(unittest.TestCase):
    def kur(self, root: pathlib.Path) -> None:
        dosyalar = {
            "CLAUDE.md": "AGENTS.md BLUEPRINT.md .divan/progress.md\n",
            "AGENTS.md": "kurallar\n", "BLUEPRINT.md": "yön\n",
            ".divan/progress.md": "## Sıradaki kesin adım\nDenetle.\n",
            "VERSION": "0.11.1\n", "release-manifest.json": "{}\n",
            "registry/v1-gates.json": "{}\n",
        }
        for goreli, metin in dosyalar.items():
            yol = root / goreli
            yol.parent.mkdir(parents=True, exist_ok=True)
            yol.write_text(metin, encoding="utf-8")

    def test_tam_sozlesme_gecer(self):
        with tempfile.TemporaryDirectory() as gecici:
            root = pathlib.Path(gecici)
            self.kur(root)
            self.assertEqual(devral.denetle(root), [])

    def test_eksik_ilerleme_reddedilir(self):
        with tempfile.TemporaryDirectory() as gecici:
            root = pathlib.Path(gecici)
            self.kur(root)
            (root / ".divan/progress.md").unlink()
            self.assertTrue(any("ilerleme defteri" in h for h in devral.denetle(root)))


if __name__ == "__main__":
    unittest.main()
