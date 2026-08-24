from __future__ import annotations

import unittest

from pusula.domain.runner_policy import RunnerLimits, TrustLevel
from pusula.integrations.runner.contract import IsolationClass, RunnerSpec
from pusula.integrations.runner.host_probe import MicrovmHostFacts
from pusula.integrations.runner.providers import (
    FirecrackerCandidateProvider,
    TrustedLocalRunnerProvider,
)


def spec(
    *,
    run_id: str = "run-1",
    trust: TrustLevel = TrustLevel.TRUSTED,
    network_enabled: bool = False,
    limits: RunnerLimits | None = None,
) -> RunnerSpec:
    return RunnerSpec(
        run_id=run_id,
        tenant_id="tenant-1",
        trust=trust,
        limits=limits or RunnerLimits(2, 1024, 2048, 900),
        source_sha="a" * 40,
        network_enabled=network_enabled,
    )


def hardened_facts(**overrides: object) -> MicrovmHostFacts:
    values: dict[str, object] = {
        "kvm_available": True,
        "firecracker_path": "/usr/bin/firecracker",
        "firecracker_sha256": "1" * 64,
        "jailer_path": "/usr/bin/jailer",
        "jailer_sha256": "2" * 64,
        "cgroup_v2": True,
        "network_namespace_tool": True,
        "dedicated_worker": True,
        "control_plane": False,
    }
    values.update(overrides)
    return MicrovmHostFacts(**values)  # type: ignore[arg-type]


class RunnerProviderTests(unittest.TestCase):
    def test_trusted_local_capabilities_refuse_untrusted(self) -> None:
        capabilities = TrustedLocalRunnerProvider().capabilities()
        self.assertFalse(capabilities.supports_untrusted)
        self.assertIs(capabilities.isolation_class, IsolationClass.CONTAINER)

    def test_trusted_local_allocates_trusted_workload(self) -> None:
        lease = TrustedLocalRunnerProvider().allocate(spec())
        self.assertEqual(lease.run_id, "run-1")

    def test_trusted_local_rejects_untrusted_workload(self) -> None:
        with self.assertRaises(PermissionError):
            TrustedLocalRunnerProvider().allocate(spec(trust=TrustLevel.UNTRUSTED))

    def test_provider_enforces_capacity(self) -> None:
        limits = RunnerLimits(9, 1024, 2048, 900)
        with self.assertRaisesRegex(ValueError, "CPU"):
            TrustedLocalRunnerProvider().allocate(spec(limits=limits))

    def test_firecracker_candidate_is_fail_closed_with_incomplete_facts(self) -> None:
        provider = FirecrackerCandidateProvider(
            hardened_facts(kvm_available=False, firecracker_path=None, firecracker_sha256=None)
        )
        self.assertFalse(provider.capabilities().supports_untrusted)
        with self.assertRaisesRegex(RuntimeError, "kvm_unavailable"):
            provider.allocate(spec(trust=TrustLevel.UNTRUSTED))

    def test_firecracker_candidate_requires_every_hardening_boundary(self) -> None:
        provider = FirecrackerCandidateProvider(hardened_facts())
        self.assertTrue(provider.capabilities().supports_untrusted)
        self.assertIs(provider.capabilities().isolation_class, IsolationClass.MICROVM)

    def test_control_plane_host_is_never_eligible(self) -> None:
        provider = FirecrackerCandidateProvider(hardened_facts(control_plane=True))
        self.assertFalse(provider.capabilities().supports_untrusted)
        with self.assertRaisesRegex(RuntimeError, "control_plane_host_forbidden"):
            provider.allocate(spec(trust=TrustLevel.UNTRUSTED))

    def test_firecracker_candidate_allocates_untrusted_when_hardened(self) -> None:
        provider = FirecrackerCandidateProvider(hardened_facts())
        lease = provider.allocate(spec(trust=TrustLevel.UNTRUSTED))
        self.assertEqual(lease.tenant_id, "tenant-1")

    def test_untrusted_network_is_disabled_fail_closed(self) -> None:
        provider = FirecrackerCandidateProvider(hardened_facts())
        with self.assertRaisesRegex(PermissionError, "network access remains disabled"):
            provider.allocate(
                spec(trust=TrustLevel.UNTRUSTED, network_enabled=True)
            )

    def test_cross_run_workspace_ids_are_distinct(self) -> None:
        provider = FirecrackerCandidateProvider(hardened_facts())
        a = provider.allocate(spec(run_id="run-a", trust=TrustLevel.UNTRUSTED))
        b = provider.allocate(spec(run_id="run-b", trust=TrustLevel.UNTRUSTED))
        self.assertNotEqual(a.workspace_id, b.workspace_id)

    def test_cross_run_credential_scopes_are_distinct(self) -> None:
        provider = FirecrackerCandidateProvider(hardened_facts())
        a = provider.allocate(spec(run_id="run-a", trust=TrustLevel.UNTRUSTED))
        b = provider.allocate(spec(run_id="run-b", trust=TrustLevel.UNTRUSTED))
        self.assertNotEqual(a.credential_scope_id, b.credential_scope_id)

    def test_destroy_evidence_is_bound_to_source_sha(self) -> None:
        provider = FirecrackerCandidateProvider(hardened_facts())
        lease = provider.allocate(spec(trust=TrustLevel.UNTRUSTED))
        evidence = provider.destroy(lease)
        self.assertTrue(evidence.destroyed)
        self.assertTrue(evidence.allocated)
        self.assertFalse(evidence.execution_observed)
        self.assertEqual(evidence.source_sha, "a" * 40)
        self.assertEqual(evidence.workspace_id, lease.workspace_id)

    def test_destroy_revokes_workspace_and_credential_scope(self) -> None:
        provider = FirecrackerCandidateProvider(hardened_facts())
        lease = provider.allocate(spec(trust=TrustLevel.UNTRUSTED))
        self.assertTrue(provider.workspace_active(lease.workspace_id))
        self.assertTrue(provider.credential_scope_active(lease.credential_scope_id))
        provider.destroy(lease)
        self.assertFalse(provider.workspace_active(lease.workspace_id))
        self.assertFalse(provider.credential_scope_active(lease.credential_scope_id))

    def test_destroyed_lease_cannot_be_destroyed_or_reused_again(self) -> None:
        provider = FirecrackerCandidateProvider(hardened_facts())
        lease = provider.allocate(spec(trust=TrustLevel.UNTRUSTED))
        provider.destroy(lease)
        with self.assertRaisesRegex(RuntimeError, "not active"):
            provider.destroy(lease)

    def test_invalid_source_sha_is_rejected_before_allocation(self) -> None:
        bad = RunnerSpec(
            run_id="run-bad",
            tenant_id="tenant-1",
            trust=TrustLevel.TRUSTED,
            limits=RunnerLimits(1, 512, 1024, 60),
            source_sha="not-a-sha",
        )
        with self.assertRaises(ValueError):
            TrustedLocalRunnerProvider().allocate(bad)
