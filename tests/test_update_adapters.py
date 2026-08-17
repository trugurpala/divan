"""What the update adapters may and may not do to this host.

The governor decides; these adapters only observe. The tests that matter most
here are the ones about restraint: nothing installs, nothing upgrades, and a
check that could not be run is never reported as a pass.
"""
from __future__ import annotations

import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "plugins" / "sadrazam"))

from divan_runtime.quality_factory import GateState  # noqa: E402
from divan_runtime.update_adapters import (  # noqa: E402
    PROBE_TIMEOUT_SECONDS,
    Observation,
    _first_version,
    candidate_version,
    certify,
    discover,
)
from divan_runtime.update_governor import MANAGED_TOOLS  # noqa: E402
from divan_runtime.update_pipeline import CONTRACT_SMOKE_CHECKS  # noqa: E402


class ObservationTests(unittest.TestCase):
    def _seen(self, installed, candidate):
        return Observation("codex", installed, candidate, "npm", "probe")

    def test_the_same_version_is_not_a_candidate(self):
        self.assertFalse(self._seen("1.0.0", "1.0.0").has_candidate)

    def test_a_different_version_is_a_candidate(self):
        self.assertTrue(self._seen("1.0.0", "1.0.1").has_candidate)

    def test_an_unreadable_installation_offers_no_candidate(self):
        # Nothing may be offered as an upgrade to something that is not there.
        self.assertFalse(self._seen(None, "1.0.1").has_candidate)
        self.assertFalse(self._seen(None, "1.0.1").known)

    def test_no_candidate_is_not_a_candidate(self):
        self.assertFalse(self._seen("1.0.0", None).has_candidate)

    def test_the_record_carries_a_schema_version(self):
        self.assertEqual(self._seen("1.0.0", None).to_dict()["schema_version"], 1)


class VersionReadingTests(unittest.TestCase):
    def test_it_reads_the_version_out_of_a_sentence(self):
        self.assertEqual(_first_version("codex-cli 0.147.0"), "0.147.0")
        self.assertEqual(_first_version("2.1.229 (Claude Code)"), "2.1.229")
        self.assertEqual(_first_version("Version 1.62.1"), "1.62.1")

    def test_it_reports_nothing_rather_than_guessing(self):
        self.assertIsNone(_first_version("not installed"))
        self.assertIsNone(_first_version(""))


class RestraintTests(unittest.TestCase):
    def test_discovery_never_runs_an_install_command(self):
        seen_argv = []

        def record(argv, **_kwargs):
            seen_argv.append(list(argv))
            return 0, "1.0.0"

        with mock.patch("divan_runtime.update_adapters._run", side_effect=record):
            discover("codex")

        flat = " ".join(word for argv in seen_argv for word in argv).casefold()
        for forbidden in ("install", "update", "upgrade", "--global", "-g"):
            with self.subTest(word=forbidden):
                self.assertNotIn(forbidden, flat)

    def test_every_probe_is_bounded(self):
        self.assertLessEqual(PROBE_TIMEOUT_SECONDS, 300)

    def test_chromium_has_no_registry_of_its_own(self):
        # Playwright decides which build it wants, so chromium must not be
        # discovered as an independently upgradeable package.
        version, detail = candidate_version("chromium")

        self.assertIsNone(version)
        self.assertIn("no version of its own", detail)


class CertificationTests(unittest.TestCase):
    def test_an_absent_tool_fails_version_and_leaves_the_rest_unknown(self):
        with mock.patch(
            "divan_runtime.update_adapters.installed_version",
            return_value=(None, "not on the path"),
        ):
            states = certify("codex", pathlib.Path("."))

        self.assertIs(states["version"], GateState.FAIL)
        others = [state for name, state in states.items() if name != "version"]
        self.assertTrue(all(state is GateState.UNKNOWN for state in others))

    def test_every_contract_check_is_answered_for(self):
        with mock.patch(
            "divan_runtime.update_adapters.installed_version",
            return_value=(None, "not on the path"),
        ):
            states = certify("codex", pathlib.Path("."))

        self.assertEqual(set(states), set(CONTRACT_SMOKE_CHECKS))

    def test_a_check_that_could_not_run_is_never_a_pass(self):
        with mock.patch(
            "divan_runtime.update_adapters.installed_version",
            return_value=(None, "not on the path"),
        ):
            states = certify("claude", pathlib.Path("."))

        self.assertNotIn(GateState.PASS, [s for n, s in states.items() if n != "version"])


class RosterTests(unittest.TestCase):
    def test_the_adapters_cover_every_managed_tool(self):
        for tool in MANAGED_TOOLS:
            with self.subTest(tool=tool):
                with mock.patch(
                    "divan_runtime.update_adapters._run", return_value=(1, "absent")
                ):
                    seen = discover(tool)
                self.assertEqual(seen.tool_id, tool)


if __name__ == "__main__":
    unittest.main()
