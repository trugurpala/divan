from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.agencybench import (
    ACCEPTANCE_GATES,
    TURNKEY_BLOCKED,
    TURNKEY_READY,
    offline_workers,
    run_bench,
)
from divan_runtime.doctor import CapabilityReport, CapabilityState, DoctorReport
from divan_runtime.doctor_checks import build_report

FERMAN = """Yerel Operasyon Vaka Sistemi yap.
4 kullanıcı rolü olsun. Şirket izolasyonu olsun. Vaka kuyruğu ve atomik
sahiplenme olsun. Audit edilebilir kayıt olsun. Belge yetkilendirmesi olsun.
CSV raporu olsun. Backup ve restore olsun. Tek komutla local çalışsın."""

SPECIFICATION = {
    "ferman": FERMAN,
    "outcome": "Bir ekip vakaları rollere göre yönetip denetlenebilir kayıt tutabilsin.",
    "quality_profile": "WEB_STANDARD",
    "stories": [
        {
            "id": "roles",
            "title": "Roller ve kiracı izolasyonu",
            "priority": "P1",
            "narrative": "Her kullanıcı yalnız kendi şirketinin verisini görür.",
            "acceptance": [
                "Dört rol tanımlıdır.",
                "Bir şirketin kullanıcısı diğerinin vakasını göremez.",
            ],
        },
        {
            "id": "queue",
            "title": "Vaka kuyruğu ve atomik sahiplenme",
            "priority": "P1",
            "narrative": "Bir vaka aynı anda yalnız bir operatöre atanır.",
            "acceptance": ["İki operatör aynı vakayı aynı anda alamaz."],
        },
        {
            "id": "ledger",
            "title": "Denetlenebilir kayıt",
            "priority": "P2",
            "narrative": "Finansal benzeri kayıt sonradan değiştirilemez.",
            "acceptance": ["Aynı işlem iki kez yazılmaz."],
        },
        {
            "id": "report",
            "title": "CSV raporu",
            "priority": "P3",
            "narrative": "Yönetici dönemsel raporu dışa aktarır.",
            "acceptance": ["Rapor yalnız yetkili şirketin verisini içerir."],
        },
    ],
    "requirements": [
        "Yetki denetimi sunucu tarafındadır.",
        "Gerçek ödeme veya banka entegrasyonu kullanılmaz.",
    ],
    "measurable_outcomes": [
        "Bir vaka üç tıklamada sahiplenilir.",
        "Rapor 5 saniyeden kısa sürede üretilir.",
    ],
    "entities": ["Company", "User", "Case", "LedgerEntry", "Document"],
    "edge_cases": ["Operatör silinirse vaka sahipsiz kalmamalı."],
    "assumptions": ["Tek makinede yerel çalışma, sentetik veri."],
}


def doctor_with(**states: CapabilityState) -> DoctorReport:
    reports = []
    for capability_id, state in states.items():
        reports.append(
            CapabilityReport(
                capability_id=capability_id,
                display_name=capability_id,
                state=state,
                affects="Kod yazan çalışan.",
                code=None if state is CapabilityState.CERTIFIED else "TOOL_NOT_INSTALLED",
            )
        )
    return DoctorReport(tuple(reports))


class BenchPipelineTests(unittest.TestCase):
    def test_the_ferman_compiles_into_a_real_work_package_graph(self) -> None:
        result = run_bench(
            ferman=FERMAN,
            specification_payload=SPECIFICATION,
            doctor=doctor_with(codex=CapabilityState.OFFLINE, claude=CapabilityState.OFFLINE),
        )

        self.assertIsNotNone(result.specification)
        payload = result.to_dict()
        self.assertTrue(payload["specification_compiled"])
        self.assertEqual(payload["metrics"]["total_work_packages"], 4)
        # P1 stories are independent; lower bands wait for them.
        self.assertEqual(len(payload["work_packages"]), 4)

    def test_context_is_compiled_per_package_with_an_estimated_cost(self) -> None:
        result = run_bench(
            ferman=FERMAN,
            specification_payload=SPECIFICATION,
            doctor=doctor_with(codex=CapabilityState.OFFLINE, claude=CapabilityState.OFFLINE),
        )

        self.assertEqual(result.metrics.token_confidence, "estimated")
        self.assertGreater(result.metrics.estimated_tokens, 0)

    def test_an_invalid_specification_blocks_before_any_planning(self) -> None:
        broken = dict(SPECIFICATION)
        broken["outcome"] = "Raporlama [NEEDS CLARIFICATION: hangi aralık?]"

        result = run_bench(
            ferman=FERMAN,
            specification_payload=broken,
            doctor=doctor_with(codex=CapabilityState.CERTIFIED, claude=CapabilityState.CERTIFIED),
        )

        self.assertEqual(result.verdict, TURNKEY_BLOCKED)
        self.assertEqual(result.reason, "SPECIFICATION_INVALID")
        self.assertEqual(result.stage_reached, "spec-compiler")


class TurnkeyVerdictTests(unittest.TestCase):
    """A benchmark that can report READY without evidence measures nothing."""

    def test_offline_workers_block_the_run_and_every_gate(self) -> None:
        result = run_bench(
            ferman=FERMAN,
            specification_payload=SPECIFICATION,
            doctor=doctor_with(codex=CapabilityState.OFFLINE, claude=CapabilityState.OFFLINE),
        )

        self.assertEqual(result.verdict, TURNKEY_BLOCKED)
        self.assertEqual(result.reason, "WORKERS_OFFLINE")
        self.assertEqual(result.blocked_capabilities, ("codex", "claude"))
        self.assertFalse(result.ready)

        payload = result.to_dict()
        self.assertEqual(len(payload["gate_matrix"]), len(ACCEPTANCE_GATES))
        for gate in payload["gate_matrix"]:
            self.assertEqual(gate["state"], "BLOCKED", gate["name"])
            self.assertFalse(gate["satisfies"], gate["name"])
            self.assertTrue(gate["reason"], gate["name"])

    def test_no_path_reports_ready_without_a_completed_execution(self) -> None:
        # Even with both workers certified, nothing has been built yet.
        result = run_bench(
            ferman=FERMAN,
            specification_payload=SPECIFICATION,
            doctor=doctor_with(codex=CapabilityState.CERTIFIED, claude=CapabilityState.CERTIFIED),
        )

        self.assertNotEqual(result.verdict, TURNKEY_READY)
        self.assertEqual(result.reason, "EXECUTION_NOT_RUN")

    def test_the_run_does_not_burn_owner_attention_on_a_machine_fact(self) -> None:
        result = run_bench(
            ferman=FERMAN,
            specification_payload=SPECIFICATION,
            doctor=doctor_with(codex=CapabilityState.OFFLINE, claude=CapabilityState.OFFLINE),
        )

        self.assertEqual(result.metrics.human_questions, 0)
        self.assertEqual(result.metrics.human_intervention_count, 0)
        # A missing installed worker is an owner gate, and is counted as one.
        self.assertEqual(result.metrics.hard_gate_questions, 1)


class RealMachineBenchTests(unittest.TestCase):
    def test_this_machine_reports_its_true_worker_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = build_report(
                state_root=pathlib.Path(directory),
                knowledge_database=pathlib.Path(directory) / "knowledge.sqlite3",
            )
        missing = offline_workers(report)

        # Whatever this machine has, the benchmark must agree with the doctor.
        states = {c.capability_id: c.state for c in report.capabilities}
        for name in ("codex", "claude"):
            if states[name] is CapabilityState.OFFLINE:
                self.assertIn(name, missing)
            else:
                self.assertNotIn(name, missing)


if __name__ == "__main__":
    unittest.main()
