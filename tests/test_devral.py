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
                "## Sıradaki kesin iş\n"
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
                "## Sıradaki kesin iş\n"
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

    def test_public_truth_matches_current_source_and_published_release(self):
        progress = (KOK / ".divan/progress.md").read_text(encoding="utf-8")
        section = devral._bolum(progress, "Yayın durumu")
        self.assertIsNotNone(section)
        version = (KOK / "VERSION").read_text(encoding="utf-8").strip()

        expected = {
            "README.md": (
                f"**Source line:** v{version}",
                "**Published packages:** [GitHub Releases]",
            ),
            "README.en.md": (
                f"**Source line:** v{version}",
                "**Published packages:** [GitHub Releases]",
            ),
            "README.tr.md": (
                f"**Kaynak hattı:** v{version}",
                "**Yayımlanan paketler:** [GitHub Releases]",
            ),
            "site/index.html": (
                f"v{version} kaynak hattı",
                "yayımlanan paketler GitHub Releases'ta",
            ),
            "docs/index.html": (
                f"v{version} kaynak hattı",
                "yayımlanan paketler GitHub Releases'ta",
            ),
            "docs/Home.md": (
                f"**Kaynak hattı:** v{version}",
                "**Yayımlanan paketler:** [GitHub Releases]",
            ),
            "docs/Durum-ve-Yol-Haritasi.md": (
                f"# Durum ve Yol Haritası · v{version}",
                "Yayımlanan paketlerin güncel listesi [GitHub Releases]",
            ),
        }
        for relative, markers in expected.items():
            text = (KOK / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                for marker in markers:
                    self.assertIn(marker, text)

    def test_blueprint_and_active_host_guide_follow_the_current_release(self):
        blueprint = (KOK / "BLUEPRINT.md").read_text(encoding="utf-8")
        current_next = blueprint.split("## Sıradaki Kesin Adım", maxsplit=1)[1]
        host_guide = (KOK / "docs/Host-Uyumlulugu.md").read_text(encoding="utf-8")

        version = (KOK / "VERSION").read_text(encoding="utf-8").strip()
        self.assertIn(f"v{version} ✓**", blueprint)
        self.assertIn("Keep v1.3.4", current_next)
        self.assertNotIn("Keep v1.0.3 immutable", current_next)
        self.assertIn(f"--ref v{version} --execute", host_guide)


if __name__ == "__main__":
    unittest.main()
