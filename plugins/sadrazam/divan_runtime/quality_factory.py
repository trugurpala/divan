"""Decide what "verified" means for one project, and refuse to fake it.

One passing test run is not a quality system. A project's profile decides
which gates it actually owes, and a gate that did not run is never a gate
that passed: SKIPPED, TIMEOUT, NOT_INSTALLED and UNKNOWN all fail closed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Iterable, Mapping

QUALITY_SCHEMA_VERSION = 1


class QualityProfile(StrEnum):
    DESKTOP_WINDOWS = "DESKTOP_WINDOWS"
    WEB_STANDARD = "WEB_STANDARD"
    WEB_PAYMENT = "WEB_PAYMENT"
    BACKEND_API = "BACKEND_API"
    INTERNAL_TOOL = "INTERNAL_TOOL"
    HIGH_SECURITY = "HIGH_SECURITY"


class GateState(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    NOT_INSTALLED = "NOT_INSTALLED"
    UNKNOWN = "UNKNOWN"
    #: Recorded so a skipped gate is visible, never so it can count as passing.
    SKIPPED = "SKIPPED"
    TIMEOUT = "TIMEOUT"


#: The only state that satisfies a required gate. Everything else fails closed.
PASSING_STATES = frozenset({GateState.PASS})

#: Gates every project owes, whatever it is.
BASELINE_GATES: tuple[str, ...] = (
    "native-tests",
    "ruff",
    "mypy",
    "clean-code",
    "independent-review",
    "evidence-manifest",
)

_PROFILE_GATES: dict[QualityProfile, tuple[str, ...]] = {
    QualityProfile.DESKTOP_WINDOWS: (
        "build",
        "frontend-render",
        "installer-smoke",
        "restart-persistence",
    ),
    QualityProfile.WEB_STANDARD: (
        "build",
        "frontend-render",
        "browser-e2e",
        "accessibility",
    ),
    QualityProfile.WEB_PAYMENT: (
        "build",
        "frontend-render",
        "browser-e2e",
        "accessibility",
        "authz-negative",
        "secret-scan",
        "dependency-scan",
    ),
    QualityProfile.BACKEND_API: (
        "build",
        "authz-negative",
        "migration-verification",
        "dependency-scan",
    ),
    QualityProfile.INTERNAL_TOOL: ("build",),
    QualityProfile.HIGH_SECURITY: (
        "build",
        "authz-negative",
        "secret-scan",
        "dependency-scan",
        "sast",
    ),
}


def required_gates(profile: QualityProfile) -> tuple[str, ...]:
    """Return every gate this profile owes. A profile may only ever add."""
    return BASELINE_GATES + _PROFILE_GATES[profile]


@dataclass(frozen=True)
class GateResult:
    name: str
    state: GateState
    summary: str = ""
    #: Why a gate could not run. Required for anything that is not PASS or FAIL.
    reason: str | None = None
    command: str | None = None
    exit_code: int | None = None
    duration_ms: int | None = None
    evidence_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("gate name is required")
        if self.state not in {GateState.PASS, GateState.FAIL} and not self.reason:
            raise ValueError(
                f"gate {self.name} is {self.state.value} and must record a reason"
            )

    @property
    def satisfies(self) -> bool:
        return self.state in PASSING_STATES

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        payload["satisfies"] = self.satisfies
        return payload


@dataclass(frozen=True)
class QualityVerdict:
    profile: QualityProfile
    results: tuple[GateResult, ...]
    missing: tuple[str, ...]
    failing: tuple[str, ...]
    blocked: tuple[str, ...]

    @property
    def ready(self) -> bool:
        """True only when every required gate actually passed."""
        return not self.missing and not self.failing and not self.blocked

    @property
    def status(self) -> str:
        if self.ready:
            return "READY"
        if self.failing:
            return "FAILED"
        return "BLOCKED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": QUALITY_SCHEMA_VERSION,
            "profile": self.profile.value,
            "status": self.status,
            "ready": self.ready,
            "required_gates": list(required_gates(self.profile)),
            "results": [item.to_dict() for item in self.results],
            "missing_gates": list(self.missing),
            "failing_gates": list(self.failing),
            "blocked_gates": list(self.blocked),
        }


def evaluate(
    profile: QualityProfile, results: Iterable[GateResult]
) -> QualityVerdict:
    """Judge one run against everything the profile requires.

    A gate that was never reported counts as missing, not as passing, so a
    forgotten gate can never be mistaken for a satisfied one.
    """
    seen: dict[str, GateResult] = {}
    for result in results:
        # A gate reported twice keeps its worst outcome.
        existing = seen.get(result.name)
        if existing is None or (existing.satisfies and not result.satisfies):
            seen[result.name] = result

    required = required_gates(profile)
    missing = tuple(name for name in required if name not in seen)
    failing = tuple(
        name
        for name in required
        if name in seen and seen[name].state is GateState.FAIL
    )
    blocked = tuple(
        name
        for name in required
        if name in seen and not seen[name].satisfies and seen[name].state is not GateState.FAIL
    )
    return QualityVerdict(
        profile=profile,
        results=tuple(seen[name] for name in sorted(seen)),
        missing=missing,
        failing=failing,
        blocked=blocked,
    )


@dataclass(frozen=True)
class EvidenceManifest:
    """Everything needed to reconstruct one attempt's result later."""

    project_id: str
    goal_id: str | None
    task_id: str
    attempt_id: str
    worker: str
    provider: str
    base_commit: str | None = None
    result_commit: str | None = None
    worktree: str | None = None
    changed_files: tuple[str, ...] = ()
    diff_sha256: str | None = None
    commands: tuple[Mapping[str, Any], ...] = ()
    gate_results: tuple[GateResult, ...] = ()
    reviewer: str | None = None
    review_verdict: str | None = None
    reports: tuple[str, ...] = ()
    policy_decisions: tuple[str, ...] = ()
    memory_observations: tuple[str, ...] = ()
    started_at: str = ""
    finished_at: str | None = None
    token_confidence: str = "unknown"
    tokens: int | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name in ("project_id", "task_id", "attempt_id", "worker", "provider"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"evidence manifest {name} is required")

    def verdict(self, profile: QualityProfile) -> QualityVerdict:
        return evaluate(profile, self.gate_results)

    def to_dict(self, profile: QualityProfile) -> dict[str, Any]:
        verdict = self.verdict(profile)
        payload = asdict(self)
        payload["gate_results"] = [item.to_dict() for item in self.gate_results]
        payload["commands"] = [dict(command) for command in self.commands]
        # A manifest is meant to be serialised, so sequences travel as lists.
        for name in (
            "changed_files",
            "reports",
            "policy_decisions",
            "memory_observations",
            "notes",
        ):
            payload[name] = list(getattr(self, name))
        payload.update(
            {
                "schema_version": QUALITY_SCHEMA_VERSION,
                "quality": verdict.to_dict(),
                # A worker calling itself successful is not a verdict.
                "delivery_state": "READY" if verdict.ready else verdict.status,
            }
        )
        return payload
