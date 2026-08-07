from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.project_registry import ProjectRegistry


class ProjectRegistryTests(unittest.TestCase):
    def test_registers_git_repository_and_round_trips(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            repo = root / "demo"
            repo.mkdir()
            subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
            registry = ProjectRegistry(root / "projects.json")
            record = registry.register(str(repo))
            self.assertEqual(record.name, "demo")
            self.assertEqual(registry.get(record.project_id).root, str(repo.resolve()))
            self.assertEqual(registry.list()[0].project_id, record.project_id)

    def test_rejects_non_git_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = ProjectRegistry(pathlib.Path(directory) / "projects.json")
            with self.assertRaises(ValueError):
                registry.register(directory)


if __name__ == "__main__":
    unittest.main()
