import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.divan_v2_validate import validate_repository

ROOT = Path(__file__).resolve().parents[1]


def write_minimal_repo(repo: Path, *, skill_folder: str = "divan", skill_name: str = "divan", mcp: bool = False) -> None:
    plugin_root = repo / "plugins" / "divan"
    (plugin_root / ".codex-plugin").mkdir(parents=True)
    (plugin_root / "skills" / skill_folder).mkdir(parents=True)
    (repo / ".agents" / "plugins").mkdir(parents=True)

    manifest = {
        "name": "divan",
        "version": "2.0.0-alpha.1",
        "description": "x",
        "skills": "./skills/",
        "requires_local_executor": True,
        "interface": {
            "displayName": "Divan",
            "shortDescription": "Vibe coding, engineered.",
            "longDescription": "Engineering workflows.",
            "developerName": "Ugur Pala",
            "category": "Developer Tools",
            "capabilities": ["Review code"],
            "defaultPrompt": ["Review this repository."],
        },
    }
    if mcp:
        manifest["mcpServers"] = "./.mcp.json"
    (plugin_root / ".codex-plugin" / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    (plugin_root / "skills" / skill_folder / "SKILL.md").write_text(
        f"---\nname: {skill_name}\ndescription: Route Divan work.\n---\n\n# Divan\n\nDo work.\n",
        encoding="utf-8",
    )
    license_bytes = (ROOT / "plugins/divan/LICENSE").read_bytes()
    (plugin_root / "LICENSE").write_bytes(license_bytes)
    (plugin_root / "skills" / skill_folder / "LICENSE").write_bytes(license_bytes)
    marketplace = {
        "name": "divan",
        "interface": {"displayName": "Divan"},
        "plugins": [{"name": "divan", "source": {"source": "local", "path": "./plugins/divan"}}],
    }
    (repo / ".agents" / "plugins" / "marketplace.json").write_text(json.dumps(marketplace), encoding="utf-8")


class DivanV2ValidationTests(unittest.TestCase):
    def copy_repository(self, destination):
        shutil.copytree(ROOT / "plugins", destination / "plugins")
        shutil.copytree(ROOT / ".agents", destination / ".agents")
        return destination

    def test_reference_package_is_valid(self):
        self.assertEqual(validate_repository(ROOT), [])

    def test_rejects_missing_or_disabled_local_executor_requirement(self):
        for value in (None, False):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                repo = self.copy_repository(Path(tmp) / "repo")
                manifest_path = repo / "plugins/divan/.codex-plugin/plugin.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if value is None:
                    manifest.pop("requires_local_executor", None)
                else:
                    manifest["requires_local_executor"] = value
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                errors = validate_repository(repo)

                self.assertIn("requires_local_executor must be true", errors)

    def test_rejects_missing_or_changed_skill_license(self):
        skills = sorted(path.name for path in (ROOT / "plugins/divan/skills").iterdir() if path.is_dir())
        for skill in skills:
            for mutation in ("missing", "changed"):
                with self.subTest(skill=skill, mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                    repo = self.copy_repository(Path(tmp) / "repo")
                    notice = repo / "plugins/divan/skills" / skill / "LICENSE"
                    if mutation == "missing":
                        notice.unlink(missing_ok=True)
                    else:
                        notice.write_text("License notice with the copyright removed.\n", encoding="utf-8")

                    errors = validate_repository(repo)

                    self.assertEqual(len(errors), 1, errors)
                    self.assertIn(f"skills/{skill}/LICENSE", errors[0])

    def test_rejects_missing_or_empty_canonical_plugin_license(self):
        for mutation in ("missing", "empty"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                repo = self.copy_repository(Path(tmp) / "repo")
                notice = repo / "plugins/divan/LICENSE"
                if mutation == "missing":
                    notice.unlink()
                else:
                    notice.write_bytes(b"")

                errors = validate_repository(repo)

                self.assertEqual(len(errors), 1, errors)
                self.assertIn("plugin LICENSE", errors[0])

    def test_rejects_missing_local_markdown_references(self):
        for relative in ("SKILL.md", "references/guide.md"):
            with self.subTest(source=relative), tempfile.TemporaryDirectory() as tmp:
                repo = self.copy_repository(Path(tmp) / "repo")
                source = repo / "plugins/divan/skills/divan" / relative
                source.parent.mkdir(parents=True, exist_ok=True)
                with source.open("a", encoding="utf-8") as handle:
                    handle.write("\n[Missing reference](missing.md)\n")

                errors = validate_repository(repo)

                self.assertEqual(len(errors), 1, errors)
                self.assertIn("missing local Markdown reference", errors[0])
                self.assertIn("missing.md", errors[0])

    def test_rejects_local_references_outside_plugin_even_when_file_exists(self):
        for target in ("../../../../outside.md", "%2e%2e/%2e%2e/%2e%2e/%2e%2e/outside.md"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                repo = self.copy_repository(Path(tmp) / "repo")
                (repo / "outside.md").write_text("Outside the publishable plugin.\n", encoding="utf-8")
                source = repo / "plugins/divan/skills/divan/SKILL.md"
                with source.open("a", encoding="utf-8") as handle:
                    handle.write(f"\n[Outside reference]({target})\n")

                errors = validate_repository(repo)

                self.assertEqual(len(errors), 1, errors)
                self.assertIn("outside plugin", errors[0])

    def test_accepts_existing_local_external_and_anchor_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.copy_repository(Path(tmp) / "repo")
            skill = repo / "plugins/divan/skills/divan"
            guide = skill / "references/guide name.md"
            guide.parent.mkdir(parents=True, exist_ok=True)
            guide.write_text("[Skill](../SKILL.md#divan)\n", encoding="utf-8")
            with (skill / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write(
                    "\n[Guide](references/guide%20name.md?view=full#section)\n"
                    "[Angle destination](<references/guide name.md>)\n"
                    "[Anchor](#divan)\n"
                    "[HTTPS](https://example.com/missing.md)\n"
                    "[HTTP](http://example.com/missing.md)\n"
                    "[Email](mailto:example@example.com)\n"
                )

            self.assertEqual(validate_repository(repo), [])

    def test_ignores_markdown_links_inside_code_examples(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.copy_repository(Path(tmp) / "repo")
            source = repo / "plugins/divan/skills/divan/SKILL.md"
            with source.open("a", encoding="utf-8") as handle:
                handle.write(
                    "\n`[Inline example](missing.md)`\n"
                    "``[Example with ` inside](missing.md)``\n"
                    "```markdown\n[Code fence example](missing.md)\n```\n"
                    "~~~markdown\n[Other fence example](missing.md)\n~~~\n"
                    "    [Indented example](missing.md)\n"
                    "[Real link after examples](SKILL.md)\n"
                )

            self.assertEqual(validate_repository(repo), [])

    def test_rejects_forbidden_mcp_in_skills_only_plugin(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_minimal_repo(repo, mcp=True)
            self.assertTrue(any("skills-only" in error for error in validate_repository(repo)))

    def test_rejects_skill_name_folder_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_minimal_repo(repo, skill_folder="wrong-folder", skill_name="right-name")
            errors = validate_repository(repo)
            self.assertTrue(any("folder" in error and "right-name" in error for error in errors))

    def test_rejects_discovery_budget_over_soft_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_minimal_repo(repo)
            skills_root = repo / "plugins" / "divan" / "skills"
            for i in range(12):
                name = f"skill-{i}"
                folder = skills_root / name
                folder.mkdir()
                description = ("Detailed repository engineering review and implementation guidance. " * 12).strip()
                (folder / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\nDo work.\n",
                    encoding="utf-8",
                )
                (folder / "LICENSE").write_bytes((repo / "plugins/divan/LICENSE").read_bytes())
            self.assertTrue(any("discovery soft budget" in error for error in validate_repository(repo)))

    def test_rejects_wrong_skill_count_for_alpha(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns("dist", "__pycache__"))
            shutil.rmtree(repo / "plugins" / "divan" / "skills" / "project-contract")
            self.assertTrue(any("exactly 7 skills" in error for error in validate_repository(repo)))

    def test_rejects_published_hook_or_mcp_artifacts_in_alpha(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns("dist", "__pycache__"))
            (repo / "plugins" / "divan" / "hooks").mkdir()
            (repo / "plugins" / "divan" / "hooks" / "hooks.json").write_text('{"hooks": {}}', encoding="utf-8")
            (repo / "plugins" / "divan" / ".mcp.json").write_text("{}", encoding="utf-8")
            self.assertTrue(any("published alpha must not contain" in error for error in validate_repository(repo)))

    def test_marketplace_requires_user_facing_display_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns("dist", "__pycache__"))
            path = repo / ".agents" / "plugins" / "marketplace.json"
            market = json.loads(path.read_text(encoding="utf-8"))
            market.pop("interface", None)
            path.write_text(json.dumps(market), encoding="utf-8")
            self.assertTrue(any("marketplace interface.displayName" in error for error in validate_repository(repo)))


if __name__ == "__main__":
    unittest.main()
