from __future__ import annotations

import json
import os
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.project_readiness import InstalledApp, discover_tools


class ProjectReadinessTests(unittest.TestCase):
    def test_git_is_the_only_required_local_tool_for_readiness(self):
        paths = {"git": "C:/Git/bin/git.exe", "codex": "C:/bin/codex.exe"}

        def runner(argv, timeout):
            if argv[0].endswith("codex.exe") and tuple(argv[1:]) == ("login", "status"):
                return 0, "Logged in using ChatGPT", ""
            return 0, "1.0.0", ""

        result = discover_tools(
            paths.get,
            runner=runner,
            env={},
            installed_apps=(),
        )
        self.assertTrue(result.ready)
        by_id = {tool.id: tool for tool in result.tools}
        self.assertTrue(by_id["git"].required)
        self.assertFalse(by_id["orca"].required)
        self.assertTrue(by_id["codex"].available)
        self.assertEqual(by_id["codex"].auth, "connected")
        self.assertEqual(by_id["codex"].auth_detail, "chatgpt")
        self.assertTrue(by_id["codex"].subscription_supported)

    def test_missing_git_marks_not_ready_but_desktop_app_is_discovered(self):
        result = discover_tools(
            lambda _: None,
            runner=lambda argv, timeout: (127, "", ""),
            env={},
            installed_apps=(InstalledApp("Cursor", "2.0", "C:/Cursor"),),
        )
        self.assertFalse(result.ready)
        by_id = {tool.id: tool for tool in result.tools}
        self.assertFalse(by_id["cursor-agent"].available)
        self.assertTrue(by_id["cursor-agent"].app_installed)
        self.assertFalse(by_id["cursor-agent"].path)

    def test_api_key_presence_is_boolean_only(self):
        result = discover_tools(
            lambda name: "C:/codex.exe" if name == "codex" else ("C:/git.exe" if name == "git" else None),
            runner=lambda argv, timeout: (0, "1.0", ""),
            env={"OPENAI_API_KEY": "secret-value-must-not-leak"},
            installed_apps=(),
        )
        codex = {tool.id: tool for tool in result.tools}["codex"]
        self.assertTrue(codex.api_key_configured)
        self.assertEqual(codex.auth, "unknown")
        self.assertEqual(codex.auth_detail, "api-key-configured")
        self.assertNotIn("secret-value", repr(codex))

    def test_explicit_empty_env_does_not_read_process_api_keys(self):
        paths = {"git": "C:/git.exe", "codex": "C:/codex.exe"}

        def runner(argv, timeout):
            if argv[0].endswith("codex.exe") and tuple(argv[1:]) == ("login", "status"):
                return 1, "Not logged in", ""
            return 0, "1.0", ""

        with patch.dict(os.environ, {"OPENAI_API_KEY": "must-not-be-read"}, clear=False):
            result = discover_tools(
                paths.get,
                runner=runner,
                env={},
                installed_apps=(),
            )
        codex = {tool.id: tool for tool in result.tools}["codex"]
        self.assertFalse(codex.api_key_configured)
        self.assertEqual(codex.auth, "not-connected")
        self.assertEqual(codex.auth_detail, "login-required")

    def test_claude_auth_status_requires_an_explicit_logged_in_result(self):
        paths = {"git": "C:/git.exe", "claude": "C:/claude.exe"}

        def runner(argv, timeout):
            if argv[0].endswith("claude.exe") and tuple(argv[1:]) == ("auth", "status"):
                return 0, json.dumps({"loggedIn": False}), ""
            return 0, "1.0", ""

        result = discover_tools(paths.get, runner=runner, env={}, installed_apps=())
        claude = {tool.id: tool for tool in result.tools}["claude"]
        self.assertTrue(claude.available)
        self.assertEqual(claude.auth, "not-connected")
        self.assertEqual(claude.auth_detail, "login-required")

    def test_failed_codex_probe_cannot_be_reported_as_connected(self):
        paths = {"git": "C:/git.exe", "codex": "C:/codex.exe"}

        def runner(argv, timeout):
            if argv[0].endswith("codex.exe") and tuple(argv[1:]) == ("login", "status"):
                return 1, "Logged in using ChatGPT", "probe failed"
            return 0, "1.0", ""

        result = discover_tools(paths.get, runner=runner, env={}, installed_apps=())
        codex = {tool.id: tool for tool in result.tools}["codex"]
        self.assertEqual(codex.auth, "unknown")
        self.assertEqual(codex.auth_detail, "probe-failed")

    def test_failed_claude_probe_cannot_be_reported_as_connected(self):
        paths = {"git": "C:/git.exe", "claude": "C:/claude.exe"}

        def runner(argv, timeout):
            if argv[0].endswith("claude.exe") and tuple(argv[1:]) == ("auth", "status"):
                return 1, json.dumps({"loggedIn": True}), "probe failed"
            return 0, "1.0", ""

        result = discover_tools(paths.get, runner=runner, env={}, installed_apps=())
        claude = {tool.id: tool for tool in result.tools}["claude"]
        self.assertEqual(claude.auth, "unknown")
        self.assertEqual(claude.auth_detail, "probe-failed")


if __name__ == "__main__":
    unittest.main()
