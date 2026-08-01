from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class VibeProgressContractTests(unittest.TestCase):
    def test_sadrazam_translates_work_into_plain_progress(self) -> None:
        skill = (
            ROOT / "plugins" / "sadrazam" / "skills" / "sadrazam" / "SKILL.md"
        ).read_text(encoding="utf-8")
        contract = (
            ROOT
            / "plugins"
            / "sadrazam"
            / "skills"
            / "sadrazam"
            / "references"
            / "vibe-progress.md"
        ).read_text(encoding="utf-8")

        self.assertIn("references/vibe-progress.md", skill)
        self.assertIn("single\nsource", skill)

        required = (
            "# Vibe Progress Protocol",
            "Şu anda",
            "Current",
            "Ne öğrendim",
            "What I learned",
            "Sırada",
            "Next",
            "45–60",
            "Görev alındı",
            "Task received",
            "İnceleniyor",
            "Inspecting",
            "Uygulanıyor",
            "Implementing",
            "Doğrulanıyor",
            "Verifying",
            "Yayınlanıyor",
            "Publishing",
            "Completed",
            "Engel var",
            "Blocked",
            "user's\nlanguage",
            "Never mix languages",
            "Kod hazır",
            "Code ready",
            "Test edildi",
            "Tested",
            "GitHub'a gönderildi",
            "Sent to GitHub",
            "main'e birleşti",
            "Merged to main",
            "Published",
            "Canlı ortamda doğrulandı",
            "Live-verified",
            "Henüz doğrulanmadı",
            "Not yet verified",
            "chain-of-thought",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, contract)

    def test_entry_commands_apply_the_same_progress_contract(self) -> None:
        for relative in (
            "plugins/sadrazam/commands/divan.md",
            "plugins/sadrazam/commands/ferman.md",
            "plugins/sadrazam/commands/sefer.md",
            "plugins/sadrazam/commands/teftis.md",
            "plugins/sadrazam/commands/yayin.md",
            "plugins/sadrazam/commands/defter.md",
            "plugins/sadrazam/commands/vezir.md",
        ):
            with self.subTest(relative=relative):
                command = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("Vibe progress", command)
                self.assertIn("vibe-progress.md", command)
                self.assertIn("meaningful phase", command)
                self.assertIn("${CLAUDE_PLUGIN_ROOT}", command)
                self.assertIn("loaded-plugin root", command)
                self.assertIn("current working directory", command)
                self.assertNotIn("Şu anda", command)
                self.assertNotIn("Çıktıyı aynen göster", command)

        manifest = (ROOT / "release-manifest.json").read_text(encoding="utf-8")
        self.assertIn('"defter-command"', manifest)
        self.assertIn('"vezir-command"', manifest)

    def test_public_surfaces_explain_the_user_benefit(self) -> None:
        readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_en_alias = (ROOT / "README.en.md").read_text(encoding="utf-8")
        readme_tr = (ROOT / "README.tr.md").read_text(encoding="utf-8")
        value_guide = (ROOT / "docs" / "Vibe-Coder-Icin-Deger.md").read_text(
            encoding="utf-8"
        )
        quick_start = (ROOT / "docs" / "Hizli-Baslangic.md").read_text(
            encoding="utf-8"
        )
        install_guide = (ROOT / "docs" / "Kurulum.md").read_text(encoding="utf-8")
        pages = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        site = (ROOT / "site" / "index.html").read_text(encoding="utf-8")

        self.assertEqual(readme_en, readme_en_alias)
        self.assertIn("Plain-language progress", readme_en)
        self.assertIn("Sade ilerleme", readme_tr)
        self.assertIn("no repository checkout", readme_en)
        self.assertIn("repo klonlamadan", readme_tr)
        self.assertIn("divan.pyz.sha256", readme_en)
        self.assertIn("divan.pyz.sha256", readme_tr)
        self.assertIn("Önde sakin ve anlaşılır Divan", value_guide)
        self.assertIn("gerçek-ajan A/B sonucu", value_guide)
        self.assertEqual(pages, site)
        self.assertIn("İlerleme dili", pages)
        self.assertIn("Yerel Seyir", pages)
        self.assertIn("scripts/divan.py status", pages)
        for name, surface in (
            ("readme-en", readme_en),
            ("readme-tr", readme_tr),
            ("value-guide", value_guide),
        ):
            with self.subTest(name=name):
                self.assertIn("scripts/divan.py status", surface)
                self.assertNotIn("127.0.0.1:49152", surface)
        current = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        progress = (ROOT / ".divan" / "progress.md").read_text(encoding="utf-8")
        prefix = "- Latest published release: v"
        published = next(
            line.removeprefix(prefix)
            for line in progress.splitlines()
            if line.startswith(prefix)
        )
        normalized_turkish_surfaces = tuple(
            " ".join(surface.split())
            for surface in (readme_tr, quick_start, install_guide)
        )
        normalized_pages = " ".join(pages.split())
        if current == published:
            self.assertIn("İlk kez kuruyorum", pages)
            self.assertIn("Divan zaten kurulu", pages)
            self.assertIn("önizlemeyi, sonra uygulamayı", pages)
            self.assertNotIn("yalnız tag/Release sonrası kullan", pages)
            self.assertNotIn(
                "only after its tag and GitHub Release are visible", readme_en
            )
            for surface in normalized_turkish_surfaces:
                self.assertNotIn(
                    "yalnız tag ve GitHub Release sayfası görünür olduktan sonra",
                    surface,
                )
        else:
            self.assertIn("Yayın durumu · değişmez tag ve GitHub Release ile doğrulanır", pages)
            self.assertIn("Komutlar Windows, macOS ve Linux'ta aynıdır", normalized_pages)
            self.assertIn("--ref vX.Y.Z", pages)
            self.assertNotIn(f"--ref v{current}", pages)
            self.assertIn(
                f"use v{current} only after its tag and GitHub Release are visible",
                readme_en,
            )
            for surface in normalized_turkish_surfaces:
                self.assertIn(
                    f"v{current}'i yalnız tag ve GitHub Release sayfası görünür "
                    "olduktan sonra",
                    surface,
                )

    def test_english_readme_keeps_critical_paths_in_english(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        alias = (ROOT / "README.en.md").read_text(encoding="utf-8")

        self.assertEqual(readme, alias)
        for heading in (
            "## Host compatibility",
            "## Follow progress locally",
            "## Install",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, readme)
        self.assertIn(
            "**Host compatibility:** [English guide](#host-compatibility)",
            readme,
        )
        self.assertIn(
            "**Local progress:** [Seyir](#follow-progress-locally)",
            readme,
        )
        self.assertNotIn("(docs/Host-Uyumlulugu.md)", readme)
        self.assertNotIn("[installation options](docs/Kurulum.md)", readme)


if __name__ == "__main__":
    unittest.main()
