import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("divan_prose", ROOT / "scripts" / "prose.py")
PROSE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(PROSE)


class ProseGateTests(unittest.TestCase):
    def test_html_code_blocks_allow_whitespace_in_closing_tags(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-prose-html-") as temporary:
            root = pathlib.Path(temporary)
            page = root / "index.html"
            page.write_text(
                "<script>\nconst bad  spacing = true !\n</script\t\n bar>\n"
                "<style>\n.bad  spacing { color: red !important; }\n"
                "</style data-x>\n"
                "<p>Temiz metin.</p>\n",
                encoding="utf-8",
            )

            errors, warnings = PROSE._inspect_file(root, page)

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_safe_turkish_errors_and_mojibake_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            path = root / "README.tr.md"
            path.write_text(
                "# Başlık\n\nHerşey  hazır ! T\u00c3\u00bcrk\u00c3\u00a7e\n",
                encoding="utf-8",
            )
            report = PROSE.inspect(root, (path,))
        codes = {finding.code for finding in report.errors}
        self.assertTrue({"TR_SPELLING", "MOJIBAKE", "PUNCTUATION_SPACE", "REPEATED_SPACE"}.issubset(codes))

    def test_context_sensitive_particles_are_not_blindly_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            path = root / "README.tr.md"
            path.write_text(
                "# Doğal Türkçe\n\nProjede de kanıt var mı diye bakın ki karar verebilin.\n",
                encoding="utf-8",
            )
            report = PROSE.inspect(root, (path,))
        self.assertFalse(report.errors)

    def test_broken_relative_link_and_heading_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            path = root / "README.md"
            path.write_text("#Broken\n\n[Missing](docs/missing.md)\n", encoding="utf-8")
            report = PROSE.inspect(root, (path,))
        self.assertEqual(
            {finding.code for finding in report.errors},
            {"MARKDOWN_HEADING", "BROKEN_LINK"},
        )

    def test_readme_alias_must_be_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "README.md").write_text("# Divan\n", encoding="utf-8")
            (root / "README.en.md").write_text("# Other\n", encoding="utf-8")
            report = PROSE.inspect(
                root, (root / "README.md", root / "README.en.md")
            )
        self.assertIn("README_ALIAS_DRIFT", {finding.code for finding in report.errors})

    def test_warnings_do_not_fail_json_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            path = root / "README.md"
            path.write_text(
                "# Divan\n\n" + "This product is optimized for value. " * 22 + "\n",
                encoding="utf-8",
            )
            report = PROSE.inspect(root, (path,))
            payload = json.loads(PROSE.to_json(report))
            self.assertEqual(payload["status"], "warning")
            self.assertGreater(payload["warning_count"], 0)
            self.assertEqual(payload["error_count"], 0)

    def test_prohibited_marketing_language_does_not_warn(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            path = root / "README.tr.md"
            path.write_text("Dünya standardı iddiası yazmayın.\n", encoding="utf-8")
            errors, warnings = PROSE._inspect_file(root, path)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_repository_prose_contract_is_clean(self):
        report = PROSE.inspect(ROOT, PROSE.public_files(ROOT))
        self.assertFalse(report.errors, report.errors)

    def test_public_inventory_matches_the_writing_contract(self):
        relative = {
            path.relative_to(ROOT).as_posix()
            for path in PROSE.public_files(ROOT)
        }
        required = {
            "README.md",
            "README.en.md",
            "README.tr.md",
            "BLUEPRINT.md",
            "CHANGELOG.md",
            "docs/Home.md",
            "docs/index.html",
            "site/index.html",
            ".github/PULL_REQUEST_TEMPLATE.md",
            ".github/ISSUE_TEMPLATE/bug.yml",
            ".github/ISSUE_TEMPLATE/feature.yml",
            ".github/ISSUE_TEMPLATE/docs.yml",
            ".github/ISSUE_TEMPLATE/new-skill.yml",
            ".github/ISSUE_TEMPLATE/source-candidate.yml",
            ".github/ISSUE_TEMPLATE/kabul-kaniti.yml",
        }
        self.assertTrue(required.issubset(relative))
        self.assertEqual(
            {path.relative_to(ROOT).as_posix() for path in ROOT.glob("docs/*.md")},
            {path for path in relative if path.startswith("docs/") and path.endswith(".md")},
        )

    def test_verify_and_quality_gate_include_prose(self):
        verify = (ROOT / "scripts" / "verify.py").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "quality-gate.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn('(\"scripts/prose.py\", \"--check\")', verify)
        self.assertIn("python scripts/prose.py --check", workflow)


if __name__ == "__main__":
    unittest.main()
