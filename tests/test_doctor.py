from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.doctor import (
    LOCAL_STATE_DACL_POLICY,
    CapabilityReport,
    CapabilityState,
    DoctorReport,
    human_lines,
    run_checks,
)
from divan_runtime.doctor_checks import build_report, report_payload


def report(**overrides) -> CapabilityReport:
    payload = {
        "capability_id": "codex",
        "display_name": "Codex",
        "state": CapabilityState.CERTIFIED,
        "affects": "Kod yazan çalışanlardan biri.",
    }
    payload.update(overrides)
    return CapabilityReport(**payload)


class CapabilityContractTests(unittest.TestCase):
    def test_a_non_certified_capability_must_carry_a_code(self) -> None:
        for state in (
            CapabilityState.DEGRADED,
            CapabilityState.OFFLINE,
            CapabilityState.INCOMPATIBLE,
            CapabilityState.BLOCKED,
        ):
            with self.assertRaises(ValueError, msg=state.value):
                report(state=state)
            # With a code it is recordable, which is separate from usable.
            self.assertTrue(report(state=state, code="X").code)

    def test_every_capability_must_say_what_it_affects(self) -> None:
        with self.assertRaises(ValueError):
            report(affects="   ")

    def test_only_certified_and_degraded_let_the_function_run(self) -> None:
        self.assertTrue(report().usable)
        self.assertTrue(report(state=CapabilityState.DEGRADED, code="X").usable)
        for state in (
            CapabilityState.OFFLINE,
            CapabilityState.INCOMPATIBLE,
            CapabilityState.BLOCKED,
        ):
            self.assertFalse(report(state=state, code="X").usable, state.value)

    def test_a_probe_that_raises_becomes_a_finding_not_a_crash(self) -> None:
        def broken() -> CapabilityReport:
            raise RuntimeError("probe exploded")

        result = run_checks([broken])

        self.assertEqual(len(result.capabilities), 1)
        self.assertEqual(result.capabilities[0].code, "PROBE_FAILED")
        self.assertFalse(result.healthy)


class HumanSummaryTests(unittest.TestCase):
    def test_one_missing_capability_does_not_read_as_a_dead_product(self) -> None:
        lines = human_lines(
            DoctorReport(
                (
                    report(),
                    report(
                        capability_id="claude",
                        display_name="Claude Code",
                        state=CapabilityState.OFFLINE,
                        code="TOOL_NOT_INSTALLED",
                        detail="claude bulunamadı",
                    ),
                )
            )
        )
        joined = " ".join(lines)

        self.assertIn("Codex hazır.", lines)
        self.assertIn("Claude Code kurulu değil.", lines)
        self.assertIn("geliştirme çalışmaya devam eder", joined)
        self.assertNotIn("Divan hazır.", lines)

    def test_a_fully_certified_machine_says_divan_is_ready(self) -> None:
        lines = human_lines(DoctorReport((report(),)))
        self.assertIn("Divan hazır.", lines)


class RealMachineDoctorTests(unittest.TestCase):
    """The doctor must describe this machine, not an idealised one."""

    def _payload(self, state_root: pathlib.Path):
        with tempfile.TemporaryDirectory() as directory:
            return report_payload(
                build_report(
                    state_root=state_root,
                    knowledge_database=pathlib.Path(directory) / "knowledge.sqlite3",
                )
            )

    def test_the_core_and_its_own_capabilities_are_certified(self) -> None:
        payload = self._payload(pathlib.Path(tempfile.gettempdir()))
        states = {item["capability_id"]: item["state"] for item in payload["capabilities"]}

        for capability in (
            "divan-core",
            "spec-compiler",
            "memory-store",
            "memory-recall",
            "plugin-trust",
            "context-compiler",
            "attempt-recovery",
            "quality-factory",
            "evidence",
            "agency-status",
        ):
            self.assertEqual(states[capability], "CERTIFIED", capability)

    def test_a_resolved_executable_that_needs_a_session_is_degraded(self) -> None:
        # Finding a binary is not proof it is authenticated, so a tool that has
        # a session to verify must not be reported as fully ready on the
        # strength of being found. Asserted on the check itself rather than on
        # whichever tool happens to be installed on the machine running this.
        from divan_runtime.doctor_checks import _tool_check

        report = _tool_check(
            "probe", "Probe", "nothing", "probe", lambda _name: "C:/probe/probe.exe"
        )

        self.assertIs(report.state, CapabilityState.DEGRADED)
        self.assertEqual(report.code, "AUTH_NOT_VERIFIED")

    def test_a_tool_with_no_session_is_certified_when_it_is_found(self) -> None:
        # Git has no credential to verify. Reporting it degraded for a session
        # it never has told the owner something was wrong when nothing was.
        from divan_runtime.doctor_checks import _tool_check

        report = _tool_check(
            "probe",
            "Probe",
            "nothing",
            "probe",
            lambda _name: "C:/probe/probe.exe",
            needs_session=False,
        )

        self.assertIs(report.state, CapabilityState.CERTIFIED)
        self.assertIsNone(report.code)

    def test_a_tool_that_is_absent_is_offline_either_way(self) -> None:
        from divan_runtime.doctor_checks import _tool_check

        for needs_session in (True, False):
            with self.subTest(needs_session=needs_session):
                report = _tool_check(
                    "probe",
                    "Probe",
                    "nothing",
                    "probe",
                    lambda _name: None,
                    needs_session=needs_session,
                )

                self.assertIs(report.state, CapabilityState.OFFLINE)
                self.assertEqual(report.code, "TOOL_NOT_INSTALLED")

    @unittest.skipUnless(os.name == "nt", "Windows local state policy")
    def test_the_windows_state_policy_is_reported_blocked_and_never_repaired(self) -> None:
        # This machine's AppData carries a capability SID. Divan must say so
        # rather than pass the gate, and must not touch the ACL.
        payload = self._payload(
            pathlib.Path(os.environ["LOCALAPPDATA"]) / "Divan" / "project-init"
        )
        security = next(
            c for c in payload["capabilities"] if c["capability_id"] == "local-state-security"
        )

        self.assertEqual(security["state"], "BLOCKED")
        self.assertEqual(security["code"], LOCAL_STATE_DACL_POLICY)
        self.assertFalse(security["usable"])
        self.assertIn(LOCAL_STATE_DACL_POLICY, payload["blocked_codes"])
        # It blocks final local evidence, not development itself.
        self.assertIn("geliştirme durmaz", security["affects"])

    def test_the_payload_is_one_model_with_a_human_summary(self) -> None:
        payload = self._payload(pathlib.Path(tempfile.gettempdir()))

        self.assertEqual(payload["schema_version"], 1)
        self.assertTrue(payload["human_summary"])
        self.assertEqual(
            len(payload["capabilities"]),
            len({item["capability_id"] for item in payload["capabilities"]}),
        )


if __name__ == "__main__":
    unittest.main()
