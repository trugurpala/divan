"""Run one Ferman through Divan's own pipeline and report what really happened.

AgencyBench measures Divan, not a human. It drives the real Spec Compiler,
work package graph, quality profile, context compiler and attempt model, and
stops at the first capability the machine cannot supply.

The verdict is deliberately blunt. TURNKEY_READY requires every acceptance
gate to have actually passed; anything else is TURNKEY_BLOCKED with the
reason. A benchmark that reports READY because a human wrote the code would
measure nothing.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from .context_compiler import build_candidates, compile_context
from .doctor import CapabilityState, DoctorReport
from .quality_factory import GateResult, GateState, QualityProfile, evaluate
from .spec_compiler import compile_specification
from .spec_contract import CompiledSpecification

BENCH_SCHEMA_VERSION = 1

#: Capabilities that must be usable before any code can be written at all.
WORKER_CAPABILITIES = ("codex", "claude")

TURNKEY_READY = "TURNKEY_READY"
TURNKEY_BLOCKED = "TURNKEY_BLOCKED"

#: Everything the benchmark application must prove before it may be called
#: turnkey. Named up front so a later run cannot quietly shorten the list.
ACCEPTANCE_GATES: tuple[str, ...] = (
    "clean-start",
    "database-init",
    "four-roles",
    "tenant-isolation",
    "queue",
    "atomic-claim",
    "ledger-idempotency",
    "document-authorization",
    "admin-correction",
    "report-csv",
    "browser-acceptance",
    "security-checks",
    "backup-creation",
    "restore-smoke",
    "restart-persistence",
    "independent-review",
    "evidence-manifest",
)


@dataclass(frozen=True)
class BenchMetrics:
    total_work_packages: int = 0
    attempts: int = 0
    codex_attempts: int = 0
    claude_attempts: int = 0
    retries: int = 0
    stalls: int = 0
    worker_replacements: int = 0
    review_findings: int = 0
    auto_repaired_findings: int = 0
    tests_fixed: int = 0
    browser_findings_fixed: int = 0
    security_findings_fixed: int = 0
    human_questions: int = 0
    hard_gate_questions: int = 0
    human_intervention_count: int = 0
    token_confidence: str = "unknown"
    estimated_tokens: int = 0
    wall_clock_seconds: float | None = None


@dataclass(frozen=True)
class BenchResult:
    verdict: str
    reason: str | None
    stage_reached: str
    specification: CompiledSpecification | None
    metrics: BenchMetrics
    gate_results: tuple[GateResult, ...]
    blocked_capabilities: tuple[str, ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ready(self) -> bool:
        return self.verdict == TURNKEY_READY

    def to_dict(self) -> dict[str, Any]:
        verdict = evaluate(QualityProfile.WEB_STANDARD, self.gate_results)
        return {
            "schema_version": BENCH_SCHEMA_VERSION,
            "verdict": self.verdict,
            "reason": self.reason,
            "stage_reached": self.stage_reached,
            "ready": self.ready,
            "metrics": asdict(self.metrics),
            "acceptance_gates": list(ACCEPTANCE_GATES),
            "gate_matrix": [item.to_dict() for item in self.gate_results],
            "quality": verdict.to_dict(),
            "blocked_capabilities": list(self.blocked_capabilities),
            "specification_compiled": self.specification is not None,
            "work_packages": (
                []
                if self.specification is None
                else [
                    node.package_id for node in self.specification.work_packages.nodes
                ]
            ),
            "notes": list(self.notes),
        }


def _blocked_gates(reason: str) -> tuple[GateResult, ...]:
    """Every acceptance gate is BLOCKED, each saying why. None may read as passed."""
    return tuple(
        GateResult(name=name, state=GateState.BLOCKED, reason=reason)
        for name in ACCEPTANCE_GATES
    )


def offline_workers(report: DoctorReport) -> tuple[str, ...]:
    """Return the worker capabilities this machine cannot supply."""
    states = {item.capability_id: item for item in report.capabilities}
    return tuple(
        name
        for name in WORKER_CAPABILITIES
        if name not in states or states[name].state is CapabilityState.OFFLINE
    )


def run_bench(
    *,
    ferman: str,
    specification_payload: Mapping[str, Any],
    doctor: DoctorReport,
    context_budget_tokens: int = 8_000,
) -> BenchResult:
    """Drive the pipeline as far as this machine honestly allows."""
    compilation = compile_specification(specification_payload)
    if not compilation.ok:
        return BenchResult(
            verdict=TURNKEY_BLOCKED,
            reason="SPECIFICATION_INVALID",
            stage_reached="spec-compiler",
            specification=None,
            metrics=BenchMetrics(),
            gate_results=_blocked_gates("specification did not compile"),
            notes=tuple(issue.code for issue in compilation.issues),
        )

    specification = compilation.specification
    assert specification is not None
    packages = specification.work_packages.nodes

    # Context is compiled per package, so the benchmark exercises the real
    # bounded-context path rather than assuming it works.
    estimated = 0
    for node in packages:
        pack = compile_context(
            node.package_id,
            build_candidates(
                task_contract={
                    "title": node.title,
                    "summary": node.title,
                    "acceptance": [
                        line
                        for story in specification.project.stories
                        if story.story_id == node.story_id
                        for line in story.acceptance
                    ],
                },
                project_contract={"outcome": specification.project.outcome},
                ux_contract={
                    "measurable_outcomes": list(specification.ux.measurable_outcomes)
                },
                architecture_decisions=[
                    asdict(item) for item in specification.architecture
                ],
            ),
            budget_tokens=context_budget_tokens,
        )
        estimated += pack.estimated_tokens

    missing = offline_workers(doctor)
    metrics = BenchMetrics(
        total_work_packages=len(packages),
        token_confidence="estimated",
        estimated_tokens=estimated,
        # No human answered a technical question: the run stopped on a machine
        # fact, not on a request for help.
        human_questions=0,
        hard_gate_questions=1 if missing else 0,
        human_intervention_count=0,
    )

    if missing:
        return BenchResult(
            verdict=TURNKEY_BLOCKED,
            reason="WORKERS_OFFLINE",
            stage_reached="worker-assignment",
            specification=specification,
            metrics=metrics,
            gate_results=_blocked_gates(
                "no coding worker is installed on this machine"
            ),
            blocked_capabilities=missing,
            notes=(
                "Ferman: " + ferman.strip().splitlines()[0],
                "Specification compiled and the work package graph was produced.",
                "Execution needs an installed and authenticated coding worker.",
            ),
        )

    # Reaching here means workers exist; the run would continue into execution.
    return BenchResult(
        verdict=TURNKEY_BLOCKED,
        reason="EXECUTION_NOT_RUN",
        stage_reached="execution",
        specification=specification,
        metrics=metrics,
        gate_results=_blocked_gates("execution has not been run yet"),
    )
