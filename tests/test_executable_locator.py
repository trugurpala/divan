from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import executable_locator


class ExecutableLocatorTests(unittest.TestCase):
    def test_windows_user_shim_is_found_outside_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            appdata = pathlib.Path(temp_dir) / "Roaming"
            shim_root = appdata / "npm"
            shim_root.mkdir(parents=True)
            candidate = shim_root / "divan-test-agent.cmd"
            candidate.write_text("@echo off\n", encoding="utf-8")
            env = {"APPDATA": str(appdata), "PATHEXT": ".CMD;.EXE"}

            with patch.object(executable_locator.sys, "platform", "win32"):
                found = executable_locator.locate_executable(
                    ("divan-test-agent",),
                    env=env,
                )

            self.assertEqual(found, str(candidate.resolve()))

    def test_injected_resolver_does_not_fall_back_to_user_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            appdata = pathlib.Path(temp_dir) / "Roaming"
            shim_root = appdata / "npm"
            shim_root.mkdir(parents=True)
            (shim_root / "divan-test-agent.cmd").write_text(
                "@echo off\n",
                encoding="utf-8",
            )
            env = {"APPDATA": str(appdata), "PATHEXT": ".CMD;.EXE"}

            with patch.object(executable_locator.sys, "platform", "win32"):
                found = executable_locator.locate_executable(
                    ("divan-test-agent",),
                    which=lambda _: None,
                    env=env,
                )

            self.assertIsNone(found)


if __name__ == "__main__":
    unittest.main()
