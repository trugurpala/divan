import json
import tempfile
import unittest
from pathlib import Path

from scripts.divan_v2_validate import validate_repository

class DivanV2ValidationTests(unittest.TestCase):
    def _repo(self, tmp, manifest, skill_folder="divan", skill_name="divan", description="Route Divan work."):
        repo = Path(tmp); plugin_root = repo / "plugins" / "divan"
        (plugin_root / ".codex-plugin").mkdir(parents=True); (plugin_root / "skills" / skill_folder).mkdir(parents=True); (repo / ".agents" / "plugins").mkdir(parents=True)
        (plugin_root / ".codex-plugin" / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_root / "skills" / skill_folder / "SKILL.md").write_text(f"---\nname: {skill_name}\ndescription: {description}\n---\n\n# Skill\n\nDo work.\n", encoding="utf-8")
        (repo / ".agents" / "plugins" / "marketplace.json").write_text(json.dumps({"name":"divan","plugins":[{"name":"divan","source":{"source":"local","path":"./plugins/divan"}}]}), encoding="utf-8")
        return repo
    def _manifest(self):
        return {"name":"divan","version":"2.0.0-alpha.1","description":"x","skills":"./skills/","interface":{"displayName":"Divan","shortDescription":"Vibe coding, engineered.","longDescription":"Engineering workflows.","developerName":"Ugur Pala","category":"Developer Tools","capabilities":["Review code"],"defaultPrompt":["Review this repository."]}}
    def test_reference_package_is_valid(self): self.assertEqual(validate_repository(Path(__file__).resolve().parents[1]), [])
    def test_rejects_forbidden_mcp_in_skills_only_plugin(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest=self._manifest(); manifest["mcpServers"]="./.mcp.json"; errors=validate_repository(self._repo(tmp,manifest)); self.assertTrue(any("skills-only" in e for e in errors))
    def test_rejects_skill_name_folder_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors=validate_repository(self._repo(tmp,self._manifest(),"wrong-folder","right-name","Review code after implementation.")); self.assertTrue(any("folder" in e and "right-name" in e for e in errors))
    def test_rejects_discovery_budget_over_soft_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp); plugin_root=repo/"plugins"/"divan"; (plugin_root/".codex-plugin").mkdir(parents=True); (repo/".agents"/"plugins").mkdir(parents=True); skills_root=plugin_root/"skills"; skills_root.mkdir(parents=True)
            (plugin_root/".codex-plugin"/"plugin.json").write_text(json.dumps(self._manifest()),encoding="utf-8")
            for i in range(12):
                name=f"skill-{i}"; d=skills_root/name; d.mkdir(); description=("Use this skill for detailed repository engineering review and implementation work. "*9).strip(); (d/"SKILL.md").write_text(f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\nDo work.\n",encoding="utf-8")
            (repo/".agents"/"plugins"/"marketplace.json").write_text(json.dumps({"name":"divan","plugins":[{"name":"divan","source":{"source":"local","path":"./plugins/divan"}}]}),encoding="utf-8")
            errors=validate_repository(repo); self.assertTrue(any("discovery soft budget" in e for e in errors))

if __name__ == "__main__": unittest.main()
