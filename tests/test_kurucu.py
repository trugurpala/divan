from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_SAYISI = 41
PAKETLER = ("sadrazam", "core-pack", "ui-pack", "react-pack", "zanaat-pack")


@unittest.skipIf(os.name == "nt", "kabuk tatbikati Unix'te kosar; Windows'u CI kurucu matrisi sinar")
class KurucuTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = pathlib.Path(tempfile.mkdtemp(prefix="divan-kurucu-test-"))
        self.addCleanup(shutil.rmtree, self.temp, True)
        mockbin = self.temp / "mockbin"
        mockbin.mkdir()
        claude = mockbin / "claude"
        claude.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env bash
                printf '%s\\n' "$*" >> "$CLAUDE_LOG"
                case "$*" in
                  "plugin marketplace add"*)
                    if [ -e "$CLAUDE_STATE" ]; then exit 1; fi
                    : > "$CLAUDE_STATE" ;;
                esac
                exit 0
                """
            ),
            encoding="utf-8",
        )
        claude.chmod(0o755)
        (self.temp / "home").mkdir()
        self.env = {
            **os.environ,
            "PATH": f"{mockbin}:{os.environ['PATH']}",
            "HOME": str(self.temp / "home"),
            "CLAUDE_LOG": str(self.temp / "claude.log"),
            "CLAUDE_STATE": str(self.temp / "claude.state"),
            "DIVAN_SOURCE_DIR": str(ROOT),
            "CODEX_SKILLS_DIR": str(self.temp / "skills"),
            "DIVAN_STATE_DIR": str(self.temp / "state"),
        }

    def calistir(self, betik: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(ROOT / "scripts" / betik)],
            env=self.env,
            capture_output=True,
            text=True,
        )

    def log_satirlari(self) -> list[str]:
        yol = pathlib.Path(self.env["CLAUDE_LOG"])
        return yol.read_text(encoding="utf-8").splitlines() if yol.exists() else []

    def skill_sayisi(self) -> int:
        return len(list((self.temp / "skills").rglob("SKILL.md")))

    def test_kur_iki_hedefi_kurar_ve_kaldirma_temizler(self) -> None:
        birinci = self.calistir("kur.sh")
        self.assertEqual(birinci.returncode, 0, birinci.stdout + birinci.stderr)
        satirlar = self.log_satirlari()
        self.assertEqual(satirlar.count("plugin marketplace add trugurpala/divan"), 1)
        for paket in PAKETLER:
            self.assertIn(f"plugin install {paket}@divan --scope user", satirlar)
        self.assertEqual(self.skill_sayisi(), SKILL_SAYISI)

        kaldir = self.calistir("kaldir.sh")
        self.assertEqual(kaldir.returncode, 0, kaldir.stdout + kaldir.stderr)
        satirlar = self.log_satirlari()
        for paket in PAKETLER:
            self.assertIn(f"plugin uninstall {paket}@divan", satirlar)
        self.assertIn("plugin marketplace remove divan", satirlar)
        self.assertEqual(self.skill_sayisi(), 0)

    def test_tekrarli_kur_update_yoluna_gecer_kaldirma_yedegi_geri_yukler(self) -> None:
        self.assertEqual(self.calistir("kur.sh").returncode, 0)
        # Idempotens: pazar zaten kayitli (add exit 1) -> update yoluna gecilir.
        ikinci = self.calistir("kur.sh")
        self.assertEqual(ikinci.returncode, 0, ikinci.stdout + ikinci.stderr)
        self.assertIn("plugin marketplace update divan", self.log_satirlari())
        self.assertEqual(self.skill_sayisi(), SKILL_SAYISI)

        # Kayitli kaldirma son kurulumu geri alir: yedekteki ONCEKI kurulum
        # geri yuklenir (kur-codex yedek sozlesmesi). Ikinci kaldirma sifirlar.
        birinci_kaldir = self.calistir("kaldir.sh")
        self.assertEqual(birinci_kaldir.returncode, 0)
        self.assertEqual(self.skill_sayisi(), SKILL_SAYISI)
        ikinci_kaldir = self.calistir("kaldir.sh")
        self.assertEqual(ikinci_kaldir.returncode, 0)
        self.assertEqual(self.skill_sayisi(), 0)

    def test_arac_yokken_yol_gosterir_ve_hata_doner(self) -> None:
        dar_path = "/usr/bin:/bin"
        if shutil.which("claude", path=dar_path) or shutil.which("codex", path=dar_path):
            self.skipTest("dar PATH icinde gercek ajan var; hermetik negatif test atlandi")
        bos_home = self.temp / "bos-home"
        bos_home.mkdir()
        sonuc = subprocess.run(
            ["bash", str(ROOT / "scripts" / "kur.sh")],
            env={"PATH": dar_path, "HOME": str(bos_home)},
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(sonuc.returncode, 0)
        self.assertIn("claude.ai/install", sonuc.stdout)

    def test_kaldirilacak_bir_sey_yoksa_hata_donmez(self) -> None:
        dar_path = "/usr/bin:/bin"
        if shutil.which("claude", path=dar_path):
            self.skipTest("dar PATH icinde gercek claude var; hermetik test atlandi")
        bos_home = self.temp / "bos-home-kaldir"
        bos_home.mkdir()
        sonuc = subprocess.run(
            ["bash", str(ROOT / "scripts" / "kaldir.sh")],
            env={"PATH": dar_path, "HOME": str(bos_home)},
            capture_output=True,
            text=True,
        )
        self.assertEqual(sonuc.returncode, 0, sonuc.stdout + sonuc.stderr)
        self.assertIn("kaldirilacak bir sey yok", sonuc.stdout)


if __name__ == "__main__":
    unittest.main()
