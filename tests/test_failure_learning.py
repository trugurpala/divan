from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.attempt_contract import AttemptRecord, AttemptState, FailureClass
from divan_runtime.failure_learning import (
    SUMMARY_LIMIT,
    FailureSource,
    LessonCandidate,
    lesson_from_attempt,
    lesson_from_gate,
    lesson_from_review,
    record_candidate,
    should_record,
)
from divan_runtime.knowledge_contract import KnowledgeKind, KnowledgeStatus
from divan_runtime.knowledge_store import KnowledgeStore

T0 = "2026-08-16T12:00:00+00:00"
T1 = "2026-08-16T12:05:00+00:00"
T2 = "2026-08-16T12:10:00+00:00"
_HOME_PATH = "C:/Users/User/Desktop/Projeler/Divan/apps/web/src/main.ts"
_TOKEN = "sk-abcdef1234567890"


def running(**overrides: Any) -> AttemptRecord:
    payload: dict[str, Any] = {
        "attempt_id": "DIV-7-A001",
        "task_id": "DIV-7",
        "worker_id": "worker-1",
        "provider": "codex",
        "agent": "codex",
        "started_at": T0,
        "worktree": "C:/tmp/wt/DIV-7",
        "pid": 4242,
    }
    payload.update(overrides)
    return AttemptRecord(**payload)


def rejected(reason: str = "review found the migration drops a column") -> AttemptRecord:
    return running().transition(
        AttemptState.FAILED,
        reason,
        at=T1,
        failure_class=FailureClass.WORK_REJECTED,
        exit_code=1,
    )


def orphaned(reason: str = "worker process 4242 is gone") -> AttemptRecord:
    return running().transition(AttemptState.ORPHANED, reason, at=T1)


def replaced() -> AttemptRecord:
    return (
        orphaned()
        .transition(AttemptState.RECOVERY_PENDING, "divan took ownership", at=T1)
        .transition(AttemptState.REPLACED, "replaced by DIV-7-A002", at=T2)
    )


class AttemptLessonTests(unittest.TestCase):
    """Each real failure outcome yields one bounded candidate; nothing else does."""

    def test_a_work_rejected_attempt_yields_a_candidate(self) -> None:
        candidate = lesson_from_attempt(rejected())

        assert candidate is not None
        self.assertIs(candidate.source, FailureSource.WORK_REJECTED)
        self.assertIs(candidate.failure_class, FailureClass.WORK_REJECTED)
        self.assertEqual(candidate.task_id, "DIV-7")
        self.assertEqual(candidate.attempt_id, "DIV-7-A001")
        self.assertEqual(candidate.worker, "worker-1")
        self.assertEqual(candidate.provider, "codex")
        self.assertEqual(candidate.observed_at, T1)
        self.assertIn("migration drops a column", candidate.summary)

    def test_an_orphaned_attempt_yields_a_candidate(self) -> None:
        candidate = lesson_from_attempt(orphaned())

        assert candidate is not None
        self.assertIs(candidate.source, FailureSource.ORPHANED)
        # Reaching ORPHANED names WORKER_LOST; the candidate carries that name.
        self.assertIs(candidate.failure_class, FailureClass.WORKER_LOST)
        self.assertIn("process 4242 is gone", candidate.summary)

    def test_a_replaced_attempt_yields_a_candidate(self) -> None:
        candidate = lesson_from_attempt(replaced())

        assert candidate is not None
        self.assertIs(candidate.source, FailureSource.REPLACED)
        self.assertEqual(candidate.observed_at, T2)
        self.assertIn("replaced by DIV-7-A002", candidate.summary)

    def test_a_completed_attempt_yields_nothing(self) -> None:
        completed = running().transition(
            AttemptState.COMPLETED, "merged", at=T1, result_commit="abc123"
        )

        self.assertIsNone(lesson_from_attempt(completed))

    def test_a_running_attempt_yields_nothing(self) -> None:
        self.assertIsNone(lesson_from_attempt(running()))

    def test_a_failure_that_says_nothing_about_the_work_yields_nothing(self) -> None:
        # A provider outage is a fact about the provider, not about the change.
        outage = running().transition(
            AttemptState.FAILED,
            "provider returned 503",
            at=T1,
            failure_class=FailureClass.PROVIDER_UNAVAILABLE,
        )

        self.assertIsNone(lesson_from_attempt(outage))


class BoundsAndRedactionTests(unittest.TestCase):
    """A candidate is a note, not a log, and never a place a secret survives."""

    def test_the_summary_is_bounded(self) -> None:
        long_reason = "the change broke the build because " + ("very " * 200) + "badly"
        candidate = lesson_from_attempt(rejected(long_reason))

        assert candidate is not None
        self.assertLessEqual(len(candidate.summary), SUMMARY_LIMIT)
        self.assertTrue(candidate.summary.startswith("Attempt ended failed"))

    def test_a_home_path_and_a_token_are_redacted_out(self) -> None:
        reason = f"build failed at {_HOME_PATH} with OPENAI_API_KEY={_TOKEN}"
        candidate = lesson_from_attempt(rejected(reason))

        assert candidate is not None
        blob = " ".join(str(value) for value in candidate.to_dict().values())
        self.assertNotIn(_TOKEN, blob)
        self.assertNotIn("C:/Users/User", blob)
        self.assertNotIn("C:\\Users\\User", blob)
        self.assertIn("[REDACTED_SECRET]", candidate.summary)

    def test_a_candidate_never_carries_the_worktree(self) -> None:
        candidate = lesson_from_attempt(orphaned())

        assert candidate is not None
        self.assertNotIn("C:/tmp/wt", " ".join(str(v) for v in candidate.to_dict().values()))
        self.assertNotIn("worktree", candidate.to_dict())

    def test_a_candidate_cannot_be_built_over_the_bound(self) -> None:
        with self.assertRaises(ValueError):
            LessonCandidate(
                source=FailureSource.WORK_REJECTED,
                task_id="DIV-7",
                summary="x" * (SUMMARY_LIMIT + 1),
                observed_at=T1,
            )


class ReviewAndGateLessonTests(unittest.TestCase):
    def test_a_review_retry_yields_a_candidate(self) -> None:
        candidate = lesson_from_review(
            "DIV-7", "RETRY", "missing test for the empty-diff branch", "claude"
        )

        assert candidate is not None
        self.assertIs(candidate.source, FailureSource.REVIEW_FAILURE)
        self.assertIs(candidate.failure_class, FailureClass.WORK_REJECTED)
        self.assertIn("claude", candidate.summary)
        self.assertIn("empty-diff branch", candidate.summary)

    def test_a_review_pass_yields_nothing(self) -> None:
        self.assertIsNone(lesson_from_review("DIV-7", "PASS", "Review passed.", "claude"))

    def test_review_findings_are_redacted_and_bounded(self) -> None:
        findings = f"leaks token={_TOKEN} written to {_HOME_PATH} " + ("again " * 100)
        candidate = lesson_from_review("DIV-7", "retry", findings, "codex")

        assert candidate is not None
        self.assertLessEqual(len(candidate.summary), SUMMARY_LIMIT)
        self.assertNotIn(_TOKEN, candidate.summary)
        self.assertNotIn("C:/Users/User", candidate.summary)

    def test_a_failed_security_gate_yields_a_candidate(self) -> None:
        candidate = lesson_from_gate(
            "DIV-7", "secret-scan", "FAIL", "one credential in settings.example"
        )

        assert candidate is not None
        self.assertIs(candidate.source, FailureSource.SECURITY_FAILURE)
        self.assertIs(candidate.failure_class, FailureClass.WORK_REJECTED)
        self.assertIn("secret-scan", candidate.summary)

    def test_a_passing_security_gate_yields_nothing(self) -> None:
        self.assertIsNone(lesson_from_gate("DIV-7", "secret-scan", "PASS", ""))

    def test_a_gate_that_did_not_run_yields_nothing(self) -> None:
        # BLOCKED fails closed for release, but it describes the gate, not the work.
        self.assertIsNone(lesson_from_gate("DIV-7", "sast", "BLOCKED", "scanner not installed"))

    def test_a_failing_quality_gate_is_not_a_security_lesson(self) -> None:
        self.assertIsNone(lesson_from_gate("DIV-7", "ruff", "FAIL", "E501"))


class NoiseThresholdTests(unittest.TestCase):
    """One lesson per (source, task, failure_class); a retry loop is not five lessons."""

    def test_a_duplicate_for_the_same_task_is_refused(self) -> None:
        first = lesson_from_review("DIV-7", "RETRY", "first pass findings", "claude")
        second = lesson_from_review("DIV-7", "RETRY", "second pass, other findings", "claude")

        assert first is not None and second is not None
        self.assertTrue(should_record(first, []))
        self.assertFalse(should_record(second, [first]))

    def test_the_same_failure_on_another_task_is_still_recorded(self) -> None:
        first = lesson_from_review("DIV-7", "RETRY", "findings", "claude")
        other = lesson_from_review("DIV-8", "RETRY", "findings", "claude")

        assert first is not None and other is not None
        self.assertTrue(should_record(other, [first]))

    def test_a_different_source_on_the_same_task_is_a_different_fact(self) -> None:
        lost = lesson_from_attempt(orphaned())
        wrong = lesson_from_attempt(rejected())

        assert lost is not None and wrong is not None
        self.assertTrue(should_record(wrong, [lost]))


class CandidateOnlyTests(unittest.TestCase):
    """Failure learning writes candidates through the capture path and never promotes."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = KnowledgeStore(pathlib.Path(self.temp.name) / "knowledge.sqlite3")

    def test_candidates_carry_status_candidate(self) -> None:
        candidate = lesson_from_attempt(rejected())

        assert candidate is not None
        self.assertEqual(candidate.status, KnowledgeStatus.CANDIDATE.value)
        self.assertEqual(candidate.to_dict()["status"], "candidate")

    def test_a_candidate_cannot_be_minted_promoted(self) -> None:
        with self.assertRaises(ValueError):
            LessonCandidate(
                source=FailureSource.WORK_REJECTED,
                task_id="DIV-7",
                summary="anything",
                observed_at=T1,
                status=KnowledgeStatus.VALIDATED.value,
            )

    def test_recording_writes_a_candidate_lesson_and_never_curates(self) -> None:
        curated: list[str] = []
        original = self.store.curate

        def spy(item_id: str, **changes: Any) -> Any:
            curated.append(item_id)
            return original(item_id, **changes)

        self.store.curate = spy  # type: ignore[method-assign]
        candidate = lesson_from_attempt(rejected())
        assert candidate is not None

        item = record_candidate(candidate, self.store)
        stored = self.store.get(item.item_id)

        self.assertEqual(curated, [])
        self.assertIs(stored.kind, KnowledgeKind.LESSON)
        self.assertIs(stored.status, KnowledgeStatus.CANDIDATE)
        self.assertEqual(stored.confidence, 0.5)
        self.assertIsNone(stored.last_verified_at)
        self.assertIn("failure-source:work-rejected", stored.tags)
        self.assertIn("failure-learning", stored.tags)
        self.assertIn("DIV-7", stored.summary)
        self.assertNotIn("C:/tmp/wt", stored.summary)

    def test_recording_again_does_not_undo_curation(self) -> None:
        candidate = lesson_from_attempt(rejected())
        assert candidate is not None
        item = record_candidate(candidate, self.store)
        self.store.curate(item.item_id, status=KnowledgeStatus.VALIDATED)

        record_candidate(candidate, self.store)

        # A human promoted it; re-capture must not demote it back to candidate.
        self.assertIs(self.store.get(item.item_id).status, KnowledgeStatus.VALIDATED)


if __name__ == "__main__":
    unittest.main()
