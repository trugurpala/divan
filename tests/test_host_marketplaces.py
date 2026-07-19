from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "divan_host_marketplaces", ROOT / "scripts" / "host_marketplaces.py"
)
assert SPEC and SPEC.loader
HOST_MARKETPLACES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOST_MARKETPLACES)


class HostMarketplaceTests(unittest.TestCase):
    def test_repository_marketplaces_match(self) -> None:
        errors, packages, skills = HOST_MARKETPLACES.check(ROOT)

        self.assertEqual(errors, [])
        self.assertEqual((packages, skills), (5, 41))
        for manifest_path in ROOT.glob("plugins/*/.codex-plugin/plugin.json"):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["skills"], "./skills/")

    def test_reports_version_and_source_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-marketplaces-") as temporary:
            root = pathlib.Path(temporary)
            (root / ".claude-plugin").mkdir(parents=True)
            (root / ".agents" / "plugins").mkdir(parents=True)
            (root / "plugins" / "sample" / ".claude-plugin").mkdir(parents=True)
            (root / "plugins" / "sample" / ".codex-plugin").mkdir(parents=True)
            (root / "plugins" / "sample" / "skills" / "sample").mkdir(parents=True)
            (root / "plugins" / "sample" / "skills" / "sample" / "SKILL.md").write_text(
                "---\nname: sample\ndescription: sample\n---\n", encoding="utf-8"
            )
            (root / ".claude-plugin" / "marketplace.json").write_text(
                json.dumps(
                    {
                        "name": "divan",
                        "plugins": [
                            {"name": "sample", "source": "./plugins/sample", "version": "1.0.0"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (root / ".agents" / "plugins" / "marketplace.json").write_text(
                json.dumps(
                    {
                        "name": "divan",
                        "plugins": [
                            {
                                "name": "sample",
                                "source": {"source": "local", "path": "./plugins/wrong"},
                                "version": "2.0.0",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            manifest = {"name": "sample", "version": "1.0.0"}
            for host in (".claude-plugin", ".codex-plugin"):
                (root / "plugins" / "sample" / host / "plugin.json").write_text(
                    json.dumps(manifest), encoding="utf-8"
                )

            errors, packages, skills = HOST_MARKETPLACES.check(root)

            self.assertEqual((packages, skills), (1, 1))
            self.assertTrue(any("source" in error for error in errors))
            self.assertTrue(any("version" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
