from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.worker_discovery import WorkerFinding, probe_all, probe_worker


class WorkerDiscoveryTests(unittest.TestCase):
    """Not on PATH and not installed are different findings."""

    def test_a_worker_on_path_resolves_through_the_existing_resolver(self) -> None:
        probe = probe_worker("codex", locator=lambda names: "C:/tools/codex.exe")

        self.assertIs(probe.finding, WorkerFinding.RESOLVED)
        self.assertEqual(probe.executable, "C:/tools/codex.exe")
        self.assertEqual(probe.searched, ("PATH",))

    def test_a_worker_outside_path_is_found_and_named_as_such(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "bin"
            root.mkdir()
            (root / "codex.cmd").write_text("@echo off\n", encoding="utf-8")

            probe = probe_worker(
                "codex",
                environ={"USERPROFILE": directory},
                locator=lambda names: None,
            )

        self.assertIs(probe.finding, WorkerFinding.RESOLVED)
        self.assertIn("environment boundary", " ".join(probe.notes))

    def test_absent_records_every_place_it_looked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            probe = probe_worker(
                "claude",
                environ={"USERPROFILE": directory, "LOCALAPPDATA": directory},
                locator=lambda names: None,
            )

        self.assertIs(probe.finding, WorkerFinding.ABSENT)
        # An absence claim is only meaningful with the search behind it.
        self.assertIn("PATH", probe.searched)
        self.assertGreater(len(probe.searched), 1)
        self.assertIn("not found", probe.detail or "")

    def test_an_unknown_worker_is_absent_rather_than_guessed(self) -> None:
        probe = probe_worker("gemini")
        self.assertIs(probe.finding, WorkerFinding.ABSENT)

    def test_the_probe_never_opens_a_credential_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = pathlib.Path(directory)
            secrets = home / ".claude"
            secrets.mkdir()
            (secrets / ".credentials.json").write_text("{}", encoding="utf-8")

            probe = probe_worker(
                "claude", environ={"USERPROFILE": directory}, locator=lambda names: None
            )

        self.assertNotIn(str(secrets), probe.searched)

    def test_both_workers_are_probed(self) -> None:
        self.assertEqual(set(probe_all()), {"codex", "claude"})


if __name__ == "__main__":
    unittest.main()
