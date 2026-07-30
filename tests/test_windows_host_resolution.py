from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import host_probe  # noqa: E402


class WindowsHostResolutionTests(unittest.TestCase):
    def test_cmd_is_found_from_npm_home_when_path_contains_only_ps1(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-path-") as temporary:
            root = pathlib.Path(temporary)
            stale = root / "stale"
            npm = root / "profile" / "npm"
            stale.mkdir()
            npm.mkdir(parents=True)
            (stale / "codex.ps1").write_text("throw 'blocked'", encoding="utf-8")
            expected = npm / "codex.cmd"
            expected.write_text("@echo off\r\n", encoding="utf-8")

            actual = host_probe.resolve_executable(
                "codex",
                {"PATH": str(stale), "APPDATA": str(root / "profile")},
                windows=True,
            )

        self.assertEqual(actual, str(expected))

    def test_ps1_is_never_selected_as_a_host_executable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-path-") as temporary:
            root = pathlib.Path(temporary)
            (root / "codex.ps1").write_text("throw 'blocked'", encoding="utf-8")

            actual = host_probe.resolve_executable(
                "codex",
                {"PATH": str(root), "APPDATA": str(root / "missing")},
                windows=True,
            )

        self.assertIsNone(actual)


if __name__ == "__main__":
    unittest.main()
