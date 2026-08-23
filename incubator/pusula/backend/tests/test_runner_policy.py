from __future__ import annotations

import unittest

from pusula.domain.runner_policy import (
    RunnerBackend,
    RunnerLimits,
    RunnerRequest,
    TrustLevel,
    evaluate_runner,
    select_backend,
)


def valid_request(**overrides: object) -> RunnerRequest:
    values: dict[str, object] = {
        "trust": TrustLevel.UNTRUSTED,
        "backend": RunnerBackend.ISOLATED,
        "limits": RunnerLimits(
            cpu_cores=2,
            memory_mb=1024,
            disk_mb=2048,
            timeout_seconds=900,
        ),
        "disposable_workspace": True,
        "ephemeral_credentials": True,
        "tenant_isolated": True,
        "network_restricted": True,
        "evidence_enabled": True,
    }
    values.update(overrides)
    return RunnerRequest(**values)  # type: ignore[arg-type]


class RunnerPolicyTests(unittest.TestCase):
    def test_untrusted_isolated_request_is_allowed(self) -> None:
        self.assertTrue(evaluate_runner(valid_request()).allowed)

    def test_untrusted_local_backend_is_blocked(self) -> None:
        decision = evaluate_runner(valid_request(backend=RunnerBackend.LOCAL))
        self.assertFalse(decision.allowed)
        self.assertIn(
            "untrusted code cannot run on the local/control-plane backend",
            decision.reasons,
        )

    def test_untrusted_requires_disposable_workspace(self) -> None:
        self.assertFalse(evaluate_runner(valid_request(disposable_workspace=False)).allowed)

    def test_untrusted_requires_ephemeral_credentials(self) -> None:
        self.assertFalse(evaluate_runner(valid_request(ephemeral_credentials=False)).allowed)

    def test_untrusted_requires_tenant_isolation(self) -> None:
        self.assertFalse(evaluate_runner(valid_request(tenant_isolated=False)).allowed)

    def test_untrusted_requires_network_restrictions(self) -> None:
        self.assertFalse(evaluate_runner(valid_request(network_restricted=False)).allowed)

    def test_evidence_is_required_for_every_runner(self) -> None:
        request = valid_request(
            trust=TrustLevel.TRUSTED,
            backend=RunnerBackend.LOCAL,
            evidence_enabled=False,
        )
        self.assertFalse(evaluate_runner(request).allowed)

    def test_invalid_cpu_limit_is_blocked(self) -> None:
        limits = RunnerLimits(
            cpu_cores=0,
            memory_mb=1024,
            disk_mb=2048,
            timeout_seconds=900,
        )
        self.assertFalse(evaluate_runner(valid_request(limits=limits)).allowed)

    def test_invalid_memory_limit_is_blocked(self) -> None:
        limits = RunnerLimits(
            cpu_cores=1,
            memory_mb=64,
            disk_mb=2048,
            timeout_seconds=900,
        )
        self.assertFalse(evaluate_runner(valid_request(limits=limits)).allowed)

    def test_untrusted_prefers_isolated_backend(self) -> None:
        backend = select_backend(
            trust=TrustLevel.UNTRUSTED,
            isolated_available=True,
            external_available=True,
        )
        self.assertIs(backend, RunnerBackend.ISOLATED)

    def test_untrusted_can_use_external_when_isolated_is_missing(self) -> None:
        backend = select_backend(
            trust=TrustLevel.UNTRUSTED,
            isolated_available=False,
            external_available=True,
        )
        self.assertIs(backend, RunnerBackend.EXTERNAL)

    def test_untrusted_never_falls_back_to_local(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "no isolated runner backend"):
            select_backend(
                trust=TrustLevel.UNTRUSTED,
                isolated_available=False,
                external_available=False,
            )
