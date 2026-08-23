from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field

from pusula.domain.runner_policy import RunnerBackend, TrustLevel
from pusula.integrations.runner.contract import (
    IsolationClass,
    RunnerCapabilities,
    RunnerEvidence,
    RunnerLease,
    RunnerSpec,
)


def _opaque_id(prefix: str, run_id: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.sha256(f"{run_id}:{salt}".encode()).hexdigest()[:24]
    return f"{prefix}-{digest}"


def _enforce_capacity(spec: RunnerSpec, capabilities: RunnerCapabilities) -> None:
    limits = spec.limits
    if limits.cpu_cores > capabilities.max_cpu_cores:
        raise ValueError("requested CPU exceeds runner capability")
    if limits.memory_mb > capabilities.max_memory_mb:
        raise ValueError("requested memory exceeds runner capability")
    if limits.disk_mb > capabilities.max_disk_mb:
        raise ValueError("requested disk exceeds runner capability")
    if limits.timeout_seconds > capabilities.max_timeout_seconds:
        raise ValueError("requested timeout exceeds runner capability")


class _LeaseRegistry:
    _active: dict[str, RunnerLease]

    def _record(self, lease: RunnerLease) -> RunnerLease:
        if lease.run_id in self._active:
            raise RuntimeError("run already has an active runner lease")
        self._active[lease.run_id] = lease
        return lease

    def _revoke(self, lease: RunnerLease) -> None:
        current = self._active.get(lease.run_id)
        if current != lease:
            raise RuntimeError("runner lease is not active")
        del self._active[lease.run_id]

    def workspace_active(self, workspace_id: str) -> bool:
        return any(lease.workspace_id == workspace_id for lease in self._active.values())

    def credential_scope_active(self, credential_scope_id: str) -> bool:
        return any(
            lease.credential_scope_id == credential_scope_id
            for lease in self._active.values()
        )


@dataclass(slots=True)
class TrustedLocalRunnerProvider(_LeaseRegistry):
    name: str = "trusted-local"
    _active: dict[str, RunnerLease] = field(default_factory=dict, init=False, repr=False)

    def capabilities(self) -> RunnerCapabilities:
        return RunnerCapabilities(
            backend=RunnerBackend.LOCAL,
            isolation_class=IsolationClass.CONTAINER,
            supports_untrusted=False,
            disposable_workspace=True,
            ephemeral_credentials=True,
            tenant_isolation=False,
            network_restrictions=True,
            evidence=True,
            hardware_virtualization=False,
            max_cpu_cores=8,
            max_memory_mb=16384,
            max_disk_mb=32768,
            max_timeout_seconds=3600,
        )

    def allocate(self, spec: RunnerSpec) -> RunnerLease:
        spec.validate()
        if spec.trust is TrustLevel.UNTRUSTED:
            raise PermissionError("trusted-local provider cannot run untrusted code")
        _enforce_capacity(spec, self.capabilities())
        return self._record(
            RunnerLease(
                provider=self.name,
                run_id=spec.run_id,
                tenant_id=spec.tenant_id,
                source_sha=spec.source_sha,
                workspace_id=_opaque_id("workspace", spec.run_id),
                credential_scope_id=_opaque_id("credential", spec.run_id),
                isolation_class=IsolationClass.CONTAINER,
            )
        )

    def destroy(self, lease: RunnerLease) -> RunnerEvidence:
        self._revoke(lease)
        return RunnerEvidence(
            provider=self.name,
            run_id=lease.run_id,
            source_sha=lease.source_sha,
            workspace_id=lease.workspace_id,
            isolation_class=lease.isolation_class,
            allocated=True,
            execution_observed=False,
            destroyed=True,
            exit_code=None,
        )


@dataclass(slots=True)
class FirecrackerCandidateProvider(_LeaseRegistry):
    """Contract-level KVM/microVM candidate; does not execute guest code.

    Production availability requires a separate worker host with KVM,
    Firecracker jailer, default seccomp filtering and per-run resource/network
    isolation. Until those facts are independently probed, allocation fails
    closed.
    """

    kvm_available: bool = False
    jailer_enabled: bool = False
    seccomp_enabled: bool = True
    dedicated_worker_host: bool = False
    name: str = "firecracker-candidate"
    _active: dict[str, RunnerLease] = field(default_factory=dict, init=False, repr=False)

    def capabilities(self) -> RunnerCapabilities:
        hardened = (
            self.kvm_available
            and self.jailer_enabled
            and self.seccomp_enabled
            and self.dedicated_worker_host
        )
        return RunnerCapabilities(
            backend=RunnerBackend.ISOLATED,
            isolation_class=IsolationClass.MICROVM,
            supports_untrusted=hardened,
            disposable_workspace=True,
            ephemeral_credentials=True,
            tenant_isolation=True,
            network_restrictions=True,
            evidence=True,
            hardware_virtualization=True,
            max_cpu_cores=8,
            max_memory_mb=16384,
            max_disk_mb=32768,
            max_timeout_seconds=3600,
        )

    def allocate(self, spec: RunnerSpec) -> RunnerLease:
        spec.validate()
        if spec.trust is not TrustLevel.UNTRUSTED:
            raise ValueError("firecracker candidate is reserved for untrusted workloads")
        capabilities = self.capabilities()
        if not capabilities.supports_untrusted:
            raise RuntimeError("Firecracker candidate is not hardened/available")
        if spec.network_enabled:
            raise PermissionError(
                "untrusted network access remains disabled until restricted egress is implemented"
            )
        _enforce_capacity(spec, capabilities)
        return self._record(
            RunnerLease(
                provider=self.name,
                run_id=spec.run_id,
                tenant_id=spec.tenant_id,
                source_sha=spec.source_sha,
                workspace_id=_opaque_id("microvm-workspace", spec.run_id),
                credential_scope_id=_opaque_id("microvm-credential", spec.run_id),
                isolation_class=IsolationClass.MICROVM,
            )
        )

    def destroy(self, lease: RunnerLease) -> RunnerEvidence:
        self._revoke(lease)
        return RunnerEvidence(
            provider=self.name,
            run_id=lease.run_id,
            source_sha=lease.source_sha,
            workspace_id=lease.workspace_id,
            isolation_class=lease.isolation_class,
            allocated=True,
            execution_observed=False,
            destroyed=True,
            exit_code=None,
        )
