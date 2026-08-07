from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.project_readiness import discover_tools


class ProjectReadinessTests(unittest.TestCase):
    def test_git_is_the_only_required_local_tool_for_readiness(self):
        paths = {"git": "C:/Git/bin/git.exe", "codex": "C:/bin/codex.exe"}
        result = discover_tools(paths.get)
        self.assertTrue(result.ready)
        by_id = {tool.id: tool for tool in result.tools}
        self.assertTrue(by_id["git"].required)
        self.assertFalse(by_id["orca"].required)
        self.assertTrue(by_id["codex"].available)

    def test_missing_git_marks_not_ready(self):
        result = discover_tools(lambda _: None)
        self.assertFalse(result.ready)


if __name__ == "__main__":
    unittest.main()
