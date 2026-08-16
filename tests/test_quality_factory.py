from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.quality_factory import (
    BASELINE_GATES,
    EvidenceManifest,
    GateResult,
    GateState,
    QualityProfile,
    evaluate,
    required_gates,
)


def passing(profile: QualityProfile) -> list[GateResult]:
    return [
        GateResult(name=name, state=GateState.PASS, summary="ok")
        for name in required_gates(profile)
    ]


class ProfileTests(unittest.TestCase):
    def test_every_profile_owes_the_baseline_gates(self) -> None:
        for profile in QualityProfile:
            gates = required_gates(profile)
            for baseline in BASELINE_GATES:
                self.assertIn(baseline, gates, profile.value)

    def test_a_profile_adds_obligations_and_never_removes_one(self) -> None:
        internal = set(required_gates(QualityProfile.INTERNAL_TOOL))
        payment = set(required_gates(QualityProfile.WEB_PAYMENT))
        security = set(required_gates(QualityProfile.HIGH_SECURITY))

        self.assertTrue(set(BASELINE_GATES) <= internal)
        self.assertIn("authz-negative", payment)
        self.assertIn("secret-scan", payment)
        self.assertIn("sast", security)
        self.assertNotIn("sast", internal)


class FailClosedTests(unittest.TestCase):
    def test_all_gates_passing_is_the_only_way_to_be_ready(self) -> None:
        verdict = evaluate(
            QualityProfile.INTERNAL_TOOL, passing(QualityProfile.INTERNAL_TOOL)
        )
        self.assertTrue(verdict.ready)
        self.assertEqual(verdict.status, "READY")

    def test_a_missing_gate_is_never_a_passing_gate(self) -> None:
        results = passing(QualityProfile.INTERNAL_TOOL)
        dropped = [item for item in results if item.name != "independent-review"]

        verdict = evaluate(QualityProfile.INTERNAL_TOOL, dropped)

        self.assertFalse(verdict.ready)
        self.assertIn("independent-review", verdict.missing)
        self.assertEqual(verdict.status, "BLOCKED")

    def test_skipped_timeout_unknown_and_not_installed_never_pass(self) -> None:
        for state in (
            GateState.SKIPPED,
            GateState.TIMEOUT,
            GateState.UNKNOWN,
            GateState.NOT_INSTALLED,
            GateState.BLOCKED,
        ):
            results = [
                item for item in passing(QualityProfile.INTERNAL_TOOL) if item.name != "ruff"
            ]
            results.append(
                GateResult(name="ruff", state=state, reason="did not run")
            )

            verdict = evaluate(QualityProfile.INTERNAL_TOOL, results)

            self.assertFalse(verdict.ready, state.value)
            self.assertIn("ruff", verdict.blocked, state.value)

    def test_a_failing_gate_reports_FAILED_not_BLOCKED(self) -> None:
        results = [
            item for item in passing(QualityProfile.INTERNAL_TOOL) if item.name != "native-tests"
        ]
        results.append(GateResult(name="native-tests", state=GateState.FAIL, summary="2 failed"))

        verdict = evaluate(QualityProfile.INTERNAL_TOOL, results)

        self.assertEqual(verdict.status, "FAILED")
        self.assertIn("native-tests", verdict.failing)

    def test_a_non_passing_gate_must_explain_itself(self) -> None:
        with self.assertRaises(ValueError):
            GateResult(name="browser-e2e", state=GateState.NOT_INSTALLED)
        # A reason makes it recordable, but still not passing.
        blocked = GateResult(
            name="browser-e2e", state=GateState.NOT_INSTALLED, reason="playwright absent"
        )
        self.assertFalse(blocked.satisfies)

    def test_a_gate_reported_twice_keeps_its_worst_outcome(self) -> None:
        results = passing(QualityProfile.INTERNAL_TOOL)
        results.append(GateResult(name="ruff", state=GateState.FAIL, summary="lint error"))

        verdict = evaluate(QualityProfile.INTERNAL_TOOL, results)

        self.assertFalse(verdict.ready)
        self.assertIn("ruff", verdict.failing)


class EvidenceManifestTests(unittest.TestCase):
    def _manifest(self, **overrides) -> EvidenceManifest:
        payload = {
            "project_id": "p-1",
            "goal_id": "goal-1",
            "task_id": "DIV-1",
            "attempt_id": "DIV-1-A002",
            "worker": "worker-2",
            "provider": "claude",
            "base_commit": "a" * 40,
            "result_commit": "b" * 40,
            "worktree": "C:/tmp/wt/DIV-1",
            "changed_files": ("app/queue.py",),
            "diff_sha256": "c" * 64,
            "commands": ({"argv": "python -m unittest", "exit_code": 0},),
            "gate_results": tuple(passing(QualityProfile.INTERNAL_TOOL)),
            "reviewer": "codex",
            "review_verdict": "PASS",
            "memory_observations": ("lesson-1",),
            "started_at": "2026-08-16T12:00:00+00:00",
            "finished_at": "2026-08-16T12:20:00+00:00",
            "token_confidence": "estimated",
            "tokens": 18_000,
        }
        payload.update(overrides)
        return EvidenceManifest(**payload)

    def test_a_manifest_binds_task_attempt_worker_diff_and_review(self) -> None:
        payload = self._manifest().to_dict(QualityProfile.INTERNAL_TOOL)

        self.assertEqual(payload["task_id"], "DIV-1")
        self.assertEqual(payload["attempt_id"], "DIV-1-A002")
        self.assertEqual(payload["provider"], "claude")
        self.assertEqual(payload["reviewer"], "codex")
        self.assertEqual(payload["diff_sha256"], "c" * 64)
        self.assertEqual(payload["memory_observations"], ["lesson-1"])
        self.assertEqual(payload["delivery_state"], "READY")

    def test_a_manifest_with_a_blocked_gate_is_not_delivery_ready(self) -> None:
        gates = [
            item
            for item in passing(QualityProfile.INTERNAL_TOOL)
            if item.name != "independent-review"
        ]
        gates.append(
            GateResult(
                name="independent-review",
                state=GateState.UNKNOWN,
                reason="reviewer unavailable",
            )
        )

        payload = self._manifest(gate_results=tuple(gates)).to_dict(
            QualityProfile.INTERNAL_TOOL
        )

        self.assertNotEqual(payload["delivery_state"], "READY")
        self.assertIn("independent-review", payload["quality"]["blocked_gates"])

    def test_identity_fields_are_required(self) -> None:
        for field_name in ("project_id", "task_id", "attempt_id", "worker", "provider"):
            with self.assertRaises(ValueError, msg=field_name):
                self._manifest(**{field_name: "  "})


if __name__ == "__main__":
    unittest.main()
