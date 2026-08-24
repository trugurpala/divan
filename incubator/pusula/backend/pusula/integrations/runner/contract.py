from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from pusula.domain.runner_policy import RunnerBackend, RunnerLimits, TrustLevel


class IsolationClass(StrEnum):
    PROCESS = "process"
    CONTAINER = "container"
    MICROVM = "microvm"
    REMOTE_VM = "remote_vm"


@dataclass(frozen=True, slots=True)
class RunnerCapabilities:
    backend: RunnerBackend
    isolation_class: IsolationClass
    supports_untrusted: bool
    disposable_workspace: bool
    ephemeral_credentials: bool
    tenant_isolation: bool
    network_restrictions: bool
    evidence: bool
    hardware_virtualization: bool
    max_cpu_cores: int
    max_memory_mb: int
    max_disk_mb: int
    max_timeout_seconds: int


@dataclass(frozen=True, slots=True)
class RunnerSpec:
    run_id: str
    tenant_id: str
    trust: TrustLevel
    limits: RunnerLimits
    source_sha: str
    network_enabled: bool = False

    def validate(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if len(self.source_sha) != 40 or any(
            ch not in "0123456789abcdef" for ch in self.source_sha.lower()
        ):
            raise ValueError("source_sha must be a 40-character hexadecimal Git SHA")
        self.limits.validate()


@dataclass(frozen=True, slots=True)
class RunnerLease:
    provider: str
    run_id: str
    tenant_id: str
    source_sha: str
    workspace_id: str
    credential_scope_id: str
    isolation_class: IsolationClass


@dataclass(frozen=True, slots=True)
class RunnerEvidence:
    provider: str
    run_id: str
    source_sha: str
    workspace_id: str
    isolation_class: IsolationClass
    allocated: bool
    execution_observed: bool
    destroyed: bool
    exit_code: int | None


class RunnerProvider(Protocol):
    name: str

    def capabilities(self) -> RunnerCapabilities: ...

    def allocate(self, spec: RunnerSpec) -> RunnerLease: ...

    def destroy(self, lease: RunnerLease) -> RunnerEvidence: ...
