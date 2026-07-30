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
        pages = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        site = (ROOT / "site" / "index.html").read_text(encoding="utf-8")

        self.assertEqual(readme_en, readme_en_alias)
        self.assertIn("Plain-language progress", readme_en)
        self.assertIn("Sade ilerleme", readme_tr)
        self.assertIn("Önde sakin ve anlaşılır Divan", value_guide)
        self.assertIn("gerçek-ajan A/B sonucu", value_guide)
        self.assertEqual(pages, site)
        self.assertIn("İlerleme dili", pages)
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
        if current == published:
            self.assertIn("Güncel yayın · yazmayan önizleme", pages)
            self.assertNotIn("yalnız tag/Release sonrası kullan", pages)
        else:
            self.assertIn("yalnız tag/Release sonrası kullan", pages)


if __name__ == "__main__":
    unittest.main()
