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
    marketplace = {
        "name": "divan",
        "interface": {"displayName": "Divan"},
        "plugins": [{"name": "divan", "source": {"source": "local", "path": "./plugins/divan"}}],
    }
    (repo / ".agents" / "plugins" / "marketplace.json").write_text(json.dumps(marketplace), encoding="utf-8")


class DivanV2ValidationTests(unittest.TestCase):
    def test_reference_package_is_valid(self):
        self.assertEqual(validate_repository(ROOT), [])

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
