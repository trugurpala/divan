from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TrustLevel(StrEnum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


class RunnerBackend(StrEnum):
    LOCAL = "local"
    ISOLATED = "isolated"
    EXTERNAL = "external"


@dataclass(frozen=True, slots=True)
class RunnerLimits:
    cpu_cores: int
    memory_mb: int
    disk_mb: int
    timeout_seconds: int

    def validate(self) -> None:
        if self.cpu_cores < 1:
            raise ValueError("cpu_cores must be >= 1")
        if self.memory_mb < 128:
            raise ValueError("memory_mb must be >= 128")
        if self.disk_mb < 256:
            raise ValueError("disk_mb must be >= 256")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be >= 1")


@dataclass(frozen=True, slots=True)
class RunnerRequest:
    trust: TrustLevel
    backend: RunnerBackend
    limits: RunnerLimits
    disposable_workspace: bool
    ephemeral_credentials: bool
    tenant_isolated: bool
    network_restricted: bool
    evidence_enabled: bool


@dataclass(frozen=True, slots=True)
class RunnerDecision:
    allowed: bool
    reasons: tuple[str, ...]


def evaluate_runner(request: RunnerRequest) -> RunnerDecision:
    reasons: list[str] = []

    try:
        request.limits.validate()
    except ValueError as exc:
        reasons.append(str(exc))

    if not request.evidence_enabled:
        reasons.append("runner evidence must be enabled")

    if request.trust is TrustLevel.UNTRUSTED:
        if request.backend is RunnerBackend.LOCAL:
            reasons.append("untrusted code cannot run on the local/control-plane backend")
        if not request.disposable_workspace:
            reasons.append("untrusted code requires a disposable workspace")
        if not request.ephemeral_credentials:
            reasons.append("untrusted code requires ephemeral credentials")
        if not request.tenant_isolated:
            reasons.append("untrusted code requires tenant isolation")
        if not request.network_restricted:
            reasons.append("untrusted code requires network restrictions")

    return RunnerDecision(allowed=not reasons, reasons=tuple(reasons))


def select_backend(
    *,
    trust: TrustLevel,
    isolated_available: bool,
    external_available: bool,
) -> RunnerBackend:
    if trust is TrustLevel.TRUSTED:
        return RunnerBackend.LOCAL
    if isolated_available:
        return RunnerBackend.ISOLATED
    if external_available:
        return RunnerBackend.EXTERNAL
    raise RuntimeError("no isolated runner backend is available for untrusted code")
