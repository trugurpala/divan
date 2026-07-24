import importlib.util
import pathlib
import tempfile
import unittest

KOK = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("handoff", KOK / "scripts" / "handoff.py")
devral = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(devral)


class DevralTesti(unittest.TestCase):
    PUBLISHED_COMMIT = "a" * 40

    def kur(self, root: pathlib.Path) -> None:
        dosyalar = {
            "CLAUDE.md": "AGENTS.md BLUEPRINT.md .divan/progress.md\n",
            "AGENTS.md": "kurallar\n", "BLUEPRINT.md": "yön\n",
            ".divan/progress.md": (
                "## Yayın durumu\n"
                "- Latest published release: v0.11.0\n"
                f"- Published commit: {self.PUBLISHED_COMMIT}\n"
                "- Publication evidence: .divan/evidence/v011.md\n\n"
                "## Sıradaki kesin adım\n"
                "Denetle v0.11.1 adayını.\n"
            ),
            ".divan/evidence/v011.md": (
                "# Publication evidence\n\n"
                "- Version: v0.11.0\n"
                f"- Source commit: {self.PUBLISHED_COMMIT}\n"
            ),
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

    def test_yayimlanmis_surumu_yeniden_yayinlayan_adim_reddedilir(self):
        with tempfile.TemporaryDirectory() as gecici:
            root = pathlib.Path(gecici)
            self.kur(root)
            (root / "VERSION").write_text("0.16.0\n", encoding="utf-8")
            (root / ".divan/progress.md").write_text(
                "## Yayın durumu\n"
                "- Latest published release: v0.16.0\n"
                f"- Published commit: {self.PUBLISHED_COMMIT}\n"
                "- Publication evidence: .divan/evidence/v011.md\n\n"
                "## Sıradaki kesin adım\n"
                "Run v0.16.0 gates, push the release branch, and open a ready PR.\n",
                encoding="utf-8",
            )
            (root / ".divan/evidence/v011.md").write_text(
                "# Publication evidence\n\n"
                "- Version: v0.16.0\n"
                f"- Source commit: {self.PUBLISHED_COMMIT}\n",
                encoding="utf-8",
            )

            self.assertTrue(
                any("zaten yayımlanmış sürümü" in hata for hata in devral.denetle(root))
            )

    def test_yayin_kaniti_surume_ve_commite_bagli_olmalidir(self):
        with tempfile.TemporaryDirectory() as gecici:
            root = pathlib.Path(gecici)
            self.kur(root)
            evidence = root / ".divan/evidence/v011.md"
            evidence.write_text(
                "# Publication evidence\n\n"
                "- Version: v0.10.0\n"
                f"- Source commit: {'b' * 40}\n",
                encoding="utf-8",
            )

            hatalar = devral.denetle(root)

            self.assertTrue(any("yayın kanıtı sürümü" in hata for hata in hatalar))
            self.assertTrue(any("yayın kanıtı commit'i" in hata for hata in hatalar))

    def test_yayin_kaniti_repo_disina_cikamaz(self):
        with tempfile.TemporaryDirectory() as gecici:
            root = pathlib.Path(gecici)
            self.kur(root)
            progress = root / ".divan/progress.md"
            progress.write_text(
                progress.read_text(encoding="utf-8").replace(
                    ".divan/evidence/v011.md", "../outside.md"
                ),
                encoding="utf-8",
            )

            self.assertTrue(
                any("repo içinde göreli" in hata for hata in devral.denetle(root))
            )


if __name__ == "__main__":
    unittest.main()
