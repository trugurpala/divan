import importlib.util
import pathlib
import tempfile
import unittest


KOK = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("divan_wiki", KOK / "scripts" / "wiki.py")
WIKI = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(WIKI)


class WikiTesti(unittest.TestCase):
    def test_manifest_home_ile_baslar_ve_kaynaklar_mevcuttur(self):
        sayfalar = WIKI.manifesti_oku(KOK)
        self.assertEqual(sayfalar[0]["slug"], "Home")
        self.assertGreaterEqual(len(sayfalar), 12)
        for sayfa in sayfalar:
            self.assertTrue((KOK / sayfa["source"]).is_file())

    def test_derleme_kenar_cubugu_ve_tum_sayfalari_uretir(self):
        with tempfile.TemporaryDirectory() as gecici:
            dosyalar = WIKI.derle(pathlib.Path(gecici), KOK)
            adlar = {dosya.name for dosya in dosyalar}
            self.assertIn("Home.md", adlar)
            self.assertIn("_Sidebar.md", adlar)
            self.assertIn("OpenAI-ve-Codex-Uyumlulugu.md", adlar)
            self.assertIn("Muhurdar.md", adlar)

    def test_wiki_surumu_ve_baglantilari_tutarlidir(self):
        sonuc = WIKI.denetle(KOK)
        self.assertEqual(sonuc["status"], "valid")
        self.assertEqual(sonuc["version"], (KOK / "VERSION").read_text().strip())


if __name__ == "__main__":
    unittest.main()
