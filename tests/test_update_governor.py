from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.quality_factory import GateResult, GateState
from divan_runtime.update_governor import (
    HARD_OWNER_GATES,
    LessonCandidate,
    LessonOutcome,
    PipelineStage,
    RollbackMechanism,
    ToolStatus,
    ToolVersionRecord,
    UpdateMode,
    promote,
    promotion_decision,
    reenter_candidate,
)
from divan_runtime.update_pipeline import (
    CONTRACT_SMOKE_CHECKS,
    STAGE_ORDER,
    CertificationResult,
    StageEvidence,
    advance,
    certification_from_states,
    next_stage,
)


def record(
    stage: PipelineStage = PipelineStage.DISCOVER,
    *,
    status: ToolStatus = ToolStatus.CANDIDATE,
    rollback: RollbackMechanism = RollbackMechanism.UNTESTED,
    candidate: str | None = "0.148.0",
    rejection_reason: str | None = None,
) -> ToolVersionRecord:
    return ToolVersionRecord(
        tool_id="codex",
        installed_version="0.147.0",
        candidate_version=candidate,
        source="npm:@openai/codex sha256:abc",
        discovered_at="2026-08-17T10:00:00Z",
        status=status,
        stage=stage,
        last_good_version="0.146.0",
        rejection_reason=rejection_reason,
        rollback_mechanism=rollback,
        host="win11-desk",
    )


def passed(stage: PipelineStage) -> StageEvidence:
    return StageEvidence(stage, GateState.PASS, evidence_ref=f"ev/{stage.value}")


def promotable(**overrides: object) -> dict[str, object]:
    flags: dict[str, object] = {
        "active_attempts": 0,
        "contract_smoke_passed": True,
        "security_ok": True,
        "rollback_proven": True,
    }
    flags.update(overrides)
    return flags


class RecordTests(unittest.TestCase):
    def test_rollback_defaults_to_untested_never_proven(self) -> None:
        item = ToolVersionRecord(
            tool_id="claude",
            installed_version="2.1.229",
            candidate_version=None,
            source="npm",
            discovered_at="",
        )

        self.assertIs(item.rollback_mechanism, RollbackMechanism.UNTESTED)
        self.assertFalse(item.rollback_proven)

    def test_from_dict_without_rollback_field_is_untested(self) -> None:
        payload = record().to_dict()
        del payload["rollback_mechanism"]

        restored = ToolVersionRecord.from_dict(payload)

        self.assertIs(restored.rollback_mechanism, RollbackMechanism.UNTESTED)

    def test_round_trip_keeps_every_field_and_schema_version(self) -> None:
        item = record(PipelineStage.CANARY, status=ToolStatus.CERTIFIED,
                      rollback=RollbackMechanism.PROVEN)
        payload = item.to_dict()

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "certified")
        self.assertEqual(payload["stage"], "canary")
        self.assertTrue(payload["rollback_proven"])
        self.assertEqual(ToolVersionRecord.from_dict(payload), item)

    def test_a_forged_rollback_value_is_refused(self) -> None:
        payload = record().to_dict()
        payload["rollback_mechanism"] = "trust-me"

        with self.assertRaises(ValueError):
            ToolVersionRecord.from_dict(payload)

    def test_a_record_needs_provenance(self) -> None:
        with self.assertRaises(ValueError):
            ToolVersionRecord(
                tool_id="codex", installed_version=None, candidate_version="1",
                source="  ", discovered_at="",
            )

    def test_a_rejected_record_must_say_why(self) -> None:
        with self.assertRaises(ValueError):
            record(status=ToolStatus.REJECTED)


class StageMachineTests(unittest.TestCase):
    def test_pass_walks_every_stage_in_order(self) -> None:
        item = record()
        for stage, following in zip(STAGE_ORDER, STAGE_ORDER[1:]):
            self.assertIs(item.stage, stage)
            item = advance(item, passed(stage))
            self.assertIs(item.stage, following)
        self.assertIs(item.stage, PipelineStage.PROMOTE)
        self.assertIs(item.status, ToolStatus.CERTIFIED)
        self.assertEqual(len(item.certification_evidence), len(STAGE_ORDER) - 1)

    def test_status_follows_stage(self) -> None:
        item = record()
        expected = {
            PipelineStage.VERIFY_SOURCE: ToolStatus.CANDIDATE,
            PipelineStage.STAGE: ToolStatus.CANDIDATE,
            PipelineStage.ISOLATED_TEST: ToolStatus.TESTING,
            PipelineStage.CERTIFY: ToolStatus.TESTING,
            PipelineStage.CANARY: ToolStatus.CERTIFIED,
            PipelineStage.PROMOTE: ToolStatus.CERTIFIED,
        }
        for stage in STAGE_ORDER[:-1]:
            item = advance(item, passed(stage))
            self.assertIs(item.status, expected[item.stage], item.stage)

    def test_unknown_evidence_holds_and_never_promotes(self) -> None:
        for state in (GateState.UNKNOWN, GateState.SKIPPED, GateState.TIMEOUT,
                      GateState.BLOCKED, GateState.NOT_INSTALLED):
            item = record(PipelineStage.CANARY, status=ToolStatus.CERTIFIED)
            transition = next_stage(item, StageEvidence(PipelineStage.CANARY, state, "no run"))
            self.assertIs(transition.to_stage, PipelineStage.HOLD, state)
            self.assertFalse(transition.advanced)
            self.assertIs(advance(item, StageEvidence(PipelineStage.CANARY, state, "no run")).status,
                          ToolStatus.HOLD)

    def test_fail_before_the_live_slot_rejects_with_the_reason(self) -> None:
        item = record(PipelineStage.ISOLATED_TEST, status=ToolStatus.TESTING)

        item = advance(item, StageEvidence(PipelineStage.ISOLATED_TEST, GateState.FAIL, "smoke exit 1"))

        self.assertIs(item.stage, PipelineStage.REJECT)
        self.assertIs(item.status, ToolStatus.REJECTED)
        self.assertEqual(item.rejection_reason, "smoke exit 1")

    def test_canary_fail_rejects_because_nothing_is_live_yet(self) -> None:
        item = record(PipelineStage.CANARY, status=ToolStatus.CERTIFIED,
                      rollback=RollbackMechanism.PROVEN)

        item = advance(item, StageEvidence(PipelineStage.CANARY, GateState.FAIL, "canary crashed"))

        self.assertIs(item.stage, PipelineStage.REJECT)
        self.assertEqual(item.installed_version, "0.147.0")
        self.assertEqual(item.rejection_reason, "canary crashed")

    def test_a_live_regression_rolls_back_only_when_rollback_is_proven(self) -> None:
        proven = promote(record(PipelineStage.PROMOTE, status=ToolStatus.CERTIFIED,
                                rollback=RollbackMechanism.PROVEN))
        untested = promote(record(PipelineStage.PROMOTE, status=ToolStatus.CERTIFIED))
        failure = StageEvidence(PipelineStage.PROMOTE, GateState.FAIL, "regression after promote")

        rolled = advance(proven, failure)
        held = advance(untested, failure)

        self.assertIs(rolled.stage, PipelineStage.ROLLBACK)
        self.assertIs(rolled.status, ToolStatus.DEGRADED)
        self.assertEqual(rolled.installed_version, "0.147.0")
        self.assertEqual(rolled.candidate_version, "0.148.0")
        self.assertIs(held.stage, PipelineStage.HOLD)
        self.assertIs(held.status, ToolStatus.DEGRADED)
        self.assertEqual(held.installed_version, "0.148.0")
        self.assertIn("untested", next_stage(untested, failure).reason)

    def test_evidence_for_the_wrong_stage_holds(self) -> None:
        item = record(PipelineStage.STAGE)

        transition = next_stage(item, passed(PipelineStage.CANARY))

        self.assertIs(transition.to_stage, PipelineStage.HOLD)
        self.assertIn("canary", transition.reason)

    def test_terminal_stages_do_not_advance_on_any_evidence(self) -> None:
        for stage in (PipelineStage.HOLD, PipelineStage.REJECT, PipelineStage.ROLLBACK):
            item = record(stage, status=ToolStatus.HOLD)
            transition = next_stage(item, StageEvidence(stage, GateState.PASS))
            self.assertIs(transition.to_stage, stage)
            self.assertFalse(transition.advanced)

    def test_promote_pass_is_the_end_and_keeps_the_live_status(self) -> None:
        live = promote(record(PipelineStage.PROMOTE, status=ToolStatus.CERTIFIED))

        after = advance(live, passed(PipelineStage.PROMOTE))

        self.assertIs(after.stage, PipelineStage.PROMOTE)
        self.assertIs(after.status, ToolStatus.CURRENT_CERTIFIED)
        self.assertEqual(after.certification_evidence[-1], "ev/promote")

    def test_unknown_evidence_on_a_live_tool_holds_without_calling_it_degraded(self) -> None:
        live = promote(record(PipelineStage.PROMOTE, status=ToolStatus.CERTIFIED))

        item = advance(live, StageEvidence(PipelineStage.PROMOTE, GateState.TIMEOUT, "probe hung"))

        self.assertIs(item.stage, PipelineStage.HOLD)
        self.assertIs(item.status, ToolStatus.HOLD)
        self.assertEqual(item.installed_version, "0.148.0")

    def test_a_failure_at_promote_before_the_swap_rejects_not_rolls_back(self) -> None:
        eligible = record(PipelineStage.PROMOTE, status=ToolStatus.CERTIFIED,
                          rollback=RollbackMechanism.PROVEN)

        item = advance(eligible, StageEvidence(PipelineStage.PROMOTE, GateState.FAIL, "last check"))

        self.assertIs(item.stage, PipelineStage.REJECT)
        self.assertEqual(item.installed_version, "0.147.0")

    def test_transition_serialises_with_schema_version(self) -> None:
        payload = next_stage(record(), passed(PipelineStage.DISCOVER)).to_dict()

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["to_stage"], "verify-source")
        self.assertTrue(payload["advanced"])

    def test_non_pass_evidence_must_carry_a_detail(self) -> None:
        with self.assertRaises(ValueError):
            StageEvidence(PipelineStage.STAGE, GateState.TIMEOUT)


class PromotionTests(unittest.TestCase):
    def _ready(self, rollback: RollbackMechanism = RollbackMechanism.PROVEN) -> ToolVersionRecord:
        return record(PipelineStage.PROMOTE, status=ToolStatus.CERTIFIED, rollback=rollback)

    def test_balanced_promotes_when_compatible_secure_and_reversible(self) -> None:
        action, reason = promotion_decision(self._ready(), UpdateMode.BALANCED, **promotable())

        self.assertEqual(action, "promote")
        self.assertIn("reversible", reason)

    def test_no_promotion_while_attempts_are_running(self) -> None:
        for mode in UpdateMode:
            action, reason = promotion_decision(
                self._ready(), mode, **promotable(active_attempts=2)
            )
            self.assertEqual(action, "hold", mode)
            self.assertIn("2 attempt(s) still running", reason)

    def test_controlled_never_auto_promotes(self) -> None:
        action, reason = promotion_decision(self._ready(), UpdateMode.CONTROLLED, **promotable())

        self.assertEqual(action, "hold")
        self.assertIn("owner decides", reason)

    def test_balanced_refuses_without_rollback_proof(self) -> None:
        by_flag = promotion_decision(
            self._ready(), UpdateMode.BALANCED, **promotable(rollback_proven=False)
        )
        by_record = promotion_decision(
            self._ready(RollbackMechanism.UNTESTED), UpdateMode.BALANCED, **promotable()
        )

        self.assertEqual(by_flag[0], "hold")
        self.assertEqual(by_record[0], "hold")
        self.assertIn("untested", by_record[1])

    def test_balanced_refuses_when_smoke_or_security_fails(self) -> None:
        smoke = promotion_decision(
            self._ready(), UpdateMode.BALANCED, **promotable(contract_smoke_passed=False)
        )
        security = promotion_decision(
            self._ready(), UpdateMode.BALANCED, **promotable(security_ok=False)
        )

        self.assertEqual((smoke[0], security[0]), ("hold", "hold"))
        self.assertIn("compatible", smoke[1])
        self.assertIn("secure", security[1])

    def test_full_auto_documents_the_owner_gates_it_cannot_bypass(self) -> None:
        action, reason = promotion_decision(self._ready(), UpdateMode.FULL_AUTO, **promotable())

        self.assertEqual(action, "promote")
        for gate in HARD_OWNER_GATES:
            self.assertIn(gate, reason)
        self.assertEqual(
            HARD_OWNER_GATES,
            ("credentials", "paid-purchase", "security-weakening", "public-release", "production"),
        )

    def test_full_auto_still_holds_on_technical_failure(self) -> None:
        action, _ = promotion_decision(
            self._ready(), UpdateMode.FULL_AUTO, **promotable(security_ok=False)
        )

        self.assertEqual(action, "hold")

    def test_a_candidate_that_has_not_reached_promote_holds(self) -> None:
        early = record(PipelineStage.CERTIFY, status=ToolStatus.TESTING,
                       rollback=RollbackMechanism.PROVEN)

        action, reason = promotion_decision(early, UpdateMode.FULL_AUTO, **promotable())

        self.assertEqual(action, "hold")
        self.assertIn("certify", reason)

    def test_promote_swaps_versions_and_remembers_the_last_good(self) -> None:
        live = promote(self._ready())

        self.assertEqual(live.installed_version, "0.148.0")
        self.assertEqual(live.last_good_version, "0.147.0")
        self.assertIsNone(live.candidate_version)
        self.assertIs(live.status, ToolStatus.CURRENT_CERTIFIED)

    def test_promote_refuses_a_record_that_is_not_ready(self) -> None:
        with self.assertRaises(ValueError):
            promote(record(PipelineStage.CANARY, status=ToolStatus.CERTIFIED))
        with self.assertRaises(ValueError):
            promote(self._ready().__class__.from_dict({**self._ready().to_dict(), "candidate_version": None}))


class CertificationTests(unittest.TestCase):
    def _all(self, state: GateState = GateState.PASS, reason: str = "") -> list[tuple[str, GateState, str]]:
        return [(name, state, reason) for name in CONTRACT_SMOKE_CHECKS]

    def test_checklist_names_every_capability_in_order(self) -> None:
        self.assertEqual(
            CONTRACT_SMOKE_CHECKS,
            ("version", "auth", "headless", "cwd", "git-worktree", "cancel",
             "timeout", "diff", "evidence", "review-mode"),
        )

    def test_certified_only_when_every_check_passes(self) -> None:
        result = certification_from_states("codex", "0.148.0", self._all())

        self.assertTrue(result.certified)
        self.assertIs(result.as_evidence().state, GateState.PASS)
        self.assertIs(result.as_evidence().stage, PipelineStage.CERTIFY)

    def test_a_missing_check_is_not_certified(self) -> None:
        result = certification_from_states("codex", "0.148.0", self._all()[:-1])

        self.assertFalse(result.certified)
        self.assertEqual(result.missing, ("review-mode",))
        self.assertIs(result.as_evidence().state, GateState.UNKNOWN)

    def test_a_skipped_check_holds_rather_than_fails(self) -> None:
        rows = self._all()
        rows[3] = ("cwd", GateState.SKIPPED, "not run on this host")

        evidence = certification_from_states("codex", "0.148.0", rows).as_evidence()

        self.assertIs(evidence.state, GateState.SKIPPED)
        self.assertIs(next_stage(record(PipelineStage.CERTIFY), evidence).to_stage, PipelineStage.HOLD)

    def test_any_failed_check_fails_the_certification(self) -> None:
        rows = self._all()
        rows[5] = ("cancel", GateState.FAIL, "")
        rows[6] = ("timeout", GateState.TIMEOUT, "hung")

        evidence = certification_from_states("codex", "0.148.0", rows).as_evidence(evidence_ref="ev/1")

        self.assertIs(evidence.state, GateState.FAIL)
        self.assertIn("cancel", evidence.detail)
        self.assertEqual(evidence.evidence_ref, "ev/1")

    def test_a_check_reported_twice_keeps_its_worst_outcome(self) -> None:
        rows = self._all() + [("auth", GateState.FAIL, "")]

        result = certification_from_states("claude", "2.1.229", rows)

        self.assertIs(result.states["auth"], GateState.FAIL)
        self.assertFalse(result.certified)

    def test_unknown_check_names_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            CertificationResult("codex", "1", (GateResult(name="git_worktree", state=GateState.PASS),))

    def test_to_dict_carries_schema_and_verdict(self) -> None:
        payload = certification_from_states("codex", "0.148.0", self._all()).to_dict()

        self.assertEqual(payload["schema_version"], 1)
        self.assertTrue(payload["certified"])
        self.assertEqual(payload["required_checks"], list(CONTRACT_SMOKE_CHECKS))


class ReentryAndMemoryTests(unittest.TestCase):
    def test_a_rejected_version_reenters_as_candidate_on_new_evidence(self) -> None:
        rejected = record(PipelineStage.REJECT, status=ToolStatus.REJECTED,
                          rejection_reason="cancel probe hung")

        again = reenter_candidate(rejected, evidence_ref="ev/upstream-fix", discovered_at="later")

        self.assertIs(again.status, ToolStatus.CANDIDATE)
        self.assertIs(again.stage, PipelineStage.DISCOVER)
        self.assertIsNone(again.rejection_reason)
        self.assertEqual(again.certification_evidence[-2:],
                         ("previous rejection: cancel probe hung", "ev/upstream-fix"))

    def test_reentry_without_new_evidence_is_refused(self) -> None:
        rejected = record(PipelineStage.REJECT, status=ToolStatus.REJECTED, rejection_reason="x")

        with self.assertRaises(ValueError):
            reenter_candidate(rejected, evidence_ref=" ", discovered_at="later")

    def test_only_rejected_held_or_rolled_back_records_reenter(self) -> None:
        with self.assertRaises(ValueError):
            reenter_candidate(record(), evidence_ref="ev", discovered_at="later")
        with self.assertRaises(ValueError):
            reenter_candidate(record(status=ToolStatus.CURRENT_CERTIFIED),
                              evidence_ref="ev", discovered_at="later")

    def test_a_rolled_back_version_can_try_again_from_discovery(self) -> None:
        live = promote(record(PipelineStage.PROMOTE, status=ToolStatus.CERTIFIED,
                              rollback=RollbackMechanism.PROVEN))
        rolled = advance(live, StageEvidence(PipelineStage.PROMOTE, GateState.FAIL, "regressed"))

        again = reenter_candidate(rolled, evidence_ref="ev/patched", discovered_at="later")

        self.assertIs(again.stage, PipelineStage.DISCOVER)
        self.assertEqual(again.installed_version, "0.147.0")
        self.assertEqual(again.candidate_version, "0.148.0")

    def test_a_lesson_never_authorises_promotion(self) -> None:
        lesson = LessonCandidate("codex", "0.148.0", "win11-desk", LessonOutcome.REJECTED,
                                 "cancel probe hung on windows")

        payload = lesson.to_dict()

        self.assertFalse(LessonCandidate.AUTHORIZES_PROMOTION)
        self.assertFalse(payload["authorizes_promotion"])
        self.assertEqual(payload["outcome"], "rejected")
        self.assertEqual(payload["schema_version"], 1)

    def test_a_lesson_needs_a_detail(self) -> None:
        with self.assertRaises(ValueError):
            LessonCandidate("codex", "1", "host", LessonOutcome.HELD, "  ")


if __name__ == "__main__":
    unittest.main()
