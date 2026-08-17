"""The two capabilities that carry Divan to a machine.

The canonical report claimed fifteen capabilities for a product with
seventeen: the installer and the update governor were proved during the
delivery campaign and never asked about afterwards.

The governor's check drives the decision rather than importing the module,
because an import would have passed on the day the governor promoted an
unproven candidate.
"""
from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "plugins" / "sadrazam"))

from divan_runtime.doctor import CapabilityState  # noqa: E402
from divan_runtime.doctor_checks import build_report, trusted_state_root  # noqa: E402
from divan_runtime.doctor_delivery import (  # noqa: E402
    installer_capability,
    update_governor_capability,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]


class InstallerCapabilityTests(unittest.TestCase):
    def test_a_tree_without_the_runtime_contract_is_offline(self):
        with tempfile.TemporaryDirectory() as raw:
            report = installer_capability(pathlib.Path(raw))

        self.assertIs(report.state, CapabilityState.OFFLINE)
        self.assertEqual(report.code, "INSTALLER_TREE_ABSENT")

    def test_a_contract_with_no_sidecar_is_degraded_not_broken(self):
        # Not having built the package yet is not a defect in the installer.
        with tempfile.TemporaryDirectory() as raw:
            tree = pathlib.Path(raw)
            runtime = tree / "plugins" / "sadrazam" / "divan_runtime"
            runtime.mkdir(parents=True)
            (runtime / "modules.json").write_text(
                '{"modules": [{"python_modules": ["kernel"]}]}', encoding="utf-8"
            )

            report = installer_capability(tree)

        self.assertIs(report.state, CapabilityState.DEGRADED)
        self.assertEqual(report.code, "SIDECAR_NOT_BUILT")

    def test_it_names_the_artefact_when_one_was_built(self):
        report = installer_capability(ROOT)

        if report.state is CapabilityState.CERTIFIED:
            self.assertIn("setup.exe", (report.evidence or "").casefold())
        else:
            self.assertIn(report.code, {"SIDECAR_NOT_BUILT", "BUNDLE_NOT_BUILT"})


class UpdateGovernorCapabilityTests(unittest.TestCase):
    def test_the_governor_refuses_an_unproven_rollback(self):
        report = update_governor_capability()

        self.assertIs(report.state, CapabilityState.CERTIFIED)
        self.assertIn("geri alma", report.evidence or "")

    def test_the_evidence_counts_the_managed_tools_and_the_smoke(self):
        from divan_runtime.update_governor import MANAGED_TOOLS
        from divan_runtime.update_pipeline import CONTRACT_SMOKE_CHECKS

        evidence = update_governor_capability().evidence or ""

        self.assertIn(str(len(MANAGED_TOOLS)), evidence)
        self.assertIn(str(len(CONTRACT_SMOKE_CHECKS)), evidence)


class CanonicalReportTests(unittest.TestCase):
    def _disposable_database(self) -> pathlib.Path:
        """A knowledge database outside the checkout.

        The doctor creates this file when it looks at it. Pointing it inside the
        repository left an untracked database behind, which dirtied the checkout
        and made every later Project OS test fail closed on a guard that was
        working exactly as intended.
        """
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        return pathlib.Path(holder.name) / "knowledge.sqlite3"

    def test_the_report_carries_both_new_capabilities(self):
        report = build_report(
            state_root=trusted_state_root(),
            knowledge_database=self._disposable_database(),
        )
        named = {item.capability_id for item in report.capabilities}

        self.assertIn("installer", named)
        self.assertIn("update-governor", named)

    def test_the_report_covers_seventeen_capabilities(self):
        report = build_report(
            state_root=trusted_state_root(),
            knowledge_database=self._disposable_database(),
        )

        self.assertGreaterEqual(len(report.capabilities), 17)


if __name__ == "__main__":
    unittest.main()
