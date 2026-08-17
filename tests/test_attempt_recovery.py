from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.attempt_contract import (
    AttemptRecord,
    AttemptState,
    AttemptTransitionError,
    FailureClass,
)
from divan_runtime.attempt_store import (
    AttemptStore,
    attempt_summary,
    classify_quiet_attempt,
    next_attempt_id,
    process_start_token,
    recovery_decision,
    worker_is_live,
)

NOW = datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc)


def attempt(**overrides) -> AttemptRecord:
    payload = {
        "attempt_id": "DIV-1-A001",
        "task_id": "DIV-1",
        "worker_id": "worker-1",
        "provider": "codex",
        "agent": "codex",
        "started_at": (NOW - timedelta(minutes=1)).isoformat(),
        "heartbeat_at": (NOW - timedelta(seconds=20)).isoformat(),
        "last_progress_at": (NOW - timedelta(seconds=20)).isoformat(),
        "worktree": "C:/tmp/wt/DIV-1",
        "pid": None,
    }
    payload.update(overrides)
    return AttemptRecord(**payload)


class AttemptLifecycleTests(unittest.TestCase):
    def test_a_task_and_an_attempt_are_not_the_same_thing(self) -> None:
        first = attempt()
        second = attempt(attempt_id="DIV-1-A002", worker_id="worker-2", provider="claude")

        # Two attempts, one task, one acceptance contract.
        self.assertNotEqual(first.attempt_id, second.attempt_id)
        self.assertEqual(first.task_id, second.task_id)

    def test_the_lifecycle_refuses_impossible_moves(self) -> None:
        running = attempt()
        with self.assertRaises(AttemptTransitionError):
            running.transition(AttemptState.RESUMED, "skip", at=NOW.isoformat())
        completed = running.transition(
            AttemptState.COMPLETED, "done", at=NOW.isoformat()
        )
        with self.assertRaises(AttemptTransitionError):
            completed.transition(AttemptState.RUNNING, "again", at=NOW.isoformat())

    def test_history_is_appended_and_never_rewritten(self) -> None:
        stalled = attempt().transition(
            AttemptState.SUSPECTED_STALLED, "quiet", at=NOW.isoformat()
        )
        orphaned = stalled.transition(
            AttemptState.ORPHANED,
            "process gone",
            at=NOW.isoformat(),
            failure_class=FailureClass.WORKER_LOST,
        )

        self.assertEqual(len(orphaned.history), 2)
        self.assertEqual(orphaned.history[0]["to"], "suspected-stalled")
        self.assertEqual(orphaned.history[1]["failure_class"], "worker-lost")
        self.assertEqual(orphaned.failure_class, FailureClass.WORKER_LOST)

    def test_records_round_trip_through_the_store(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = AttemptStore(pathlib.Path(directory) / "attempts")
            record = attempt().transition(
                AttemptState.SUSPECTED_STALLED, "quiet", at=NOW.isoformat()
            )
            store.save(record)

            loaded = store.load(record.attempt_id)
            self.assertEqual(loaded, record)
            self.assertEqual(store.open_attempt("DIV-1").attempt_id, record.attempt_id)


class StallPolicyTests(unittest.TestCase):
    """A slow worker must never be mistaken for a dead one."""

    def test_a_live_worker_that_just_spoke_is_simply_running(self) -> None:
        state = classify_quiet_attempt(attempt(), now=NOW, live=True)
        self.assertEqual(state, AttemptState.RUNNING)

    def test_a_live_worker_gone_quiet_is_only_suspected_first(self) -> None:
        quiet = attempt(
            heartbeat_at=(NOW - timedelta(minutes=5)).isoformat(),
            last_progress_at=(NOW - timedelta(minutes=5)).isoformat(),
        )
        self.assertEqual(
            classify_quiet_attempt(quiet, now=NOW, live=True),
            AttemptState.SUSPECTED_STALLED,
        )

    def test_a_live_worker_past_the_stall_limit_becomes_recoverable(self) -> None:
        stuck = attempt(
            heartbeat_at=(NOW - timedelta(minutes=30)).isoformat(),
            last_progress_at=(NOW - timedelta(minutes=30)).isoformat(),
        )
        self.assertEqual(
            classify_quiet_attempt(stuck, now=NOW, live=True),
            AttemptState.RECOVERY_PENDING,
        )

    def test_heartbeat_alone_does_not_prove_progress(self) -> None:
        # Alive and beating, but nothing has actually advanced in 30 minutes.
        beating_but_stuck = attempt(
            heartbeat_at=NOW.isoformat(),
            last_progress_at=(NOW - timedelta(minutes=30)).isoformat(),
        )
        self.assertEqual(
            classify_quiet_attempt(beating_but_stuck, now=NOW, live=True),
            AttemptState.RECOVERY_PENDING,
        )

    def test_a_dead_process_is_orphaned_regardless_of_timers(self) -> None:
        fresh_but_dead = attempt(last_progress_at=NOW.isoformat())
        self.assertEqual(
            classify_quiet_attempt(fresh_but_dead, now=NOW, live=False),
            AttemptState.ORPHANED,
        )


class RecoveryDecisionTests(unittest.TestCase):
    def test_a_lost_worker_with_a_checkpoint_resumes(self) -> None:
        lost = attempt(
            failure_class=FailureClass.WORKER_LOST, checkpoint_ref="ckpt-1"
        )
        action, _ = recovery_decision(lost, prior_attempts=1, resume_supported=True)
        self.assertEqual(action, "resume")

    def test_a_lost_worker_without_a_checkpoint_is_replaced(self) -> None:
        lost = attempt(failure_class=FailureClass.WORKER_LOST)
        action, _ = recovery_decision(lost, prior_attempts=1, resume_supported=True)
        self.assertEqual(action, "replace")

    def test_an_orphan_is_recoverable_without_anyone_naming_the_failure(self) -> None:
        # A supervisor that finds a dead process knows the state, not a class.
        # Leaving the failure unnamed made recovery read it as unknown and
        # refuse to retry the one case the contract calls safe to replace.
        running = attempt()
        orphaned = running.transition(
            AttemptState.ORPHANED, "the process is gone", at=NOW.isoformat()
        )

        self.assertIs(orphaned.failure_class, FailureClass.WORKER_LOST)
        action, _ = recovery_decision(
            orphaned, prior_attempts=1, resume_supported=False
        )
        self.assertEqual(action, "replace")

    def test_the_named_failure_survives_the_move_into_recovery(self) -> None:
        orphaned = attempt().transition(
            AttemptState.ORPHANED, "the process is gone", at=NOW.isoformat()
        )
        pending = orphaned.transition(
            AttemptState.RECOVERY_PENDING, "Divan owns the wreckage", at=NOW.isoformat()
        )

        self.assertIs(pending.failure_class, FailureClass.WORKER_LOST)
        action, _ = recovery_decision(pending, prior_attempts=1, resume_supported=False)
        self.assertEqual(action, "replace")

    def test_a_stall_names_itself_too(self) -> None:
        stalled = attempt().transition(
            AttemptState.SUSPECTED_STALLED, "it went quiet", at=NOW.isoformat()
        )

        self.assertIs(stalled.failure_class, FailureClass.WORKER_STALLED)

    def test_an_explicit_failure_class_still_wins(self) -> None:
        # The state implies a default; it does not overrule a caller who knows.
        orphaned = attempt().transition(
            AttemptState.ORPHANED,
            "the provider went away",
            at=NOW.isoformat(),
            failure_class=FailureClass.PROVIDER_UNAVAILABLE,
        )

        self.assertIs(orphaned.failure_class, FailureClass.PROVIDER_UNAVAILABLE)

    def test_rejected_work_is_never_blindly_retried(self) -> None:
        rejected = attempt(failure_class=FailureClass.WORK_REJECTED)
        action, reason = recovery_decision(
            rejected, prior_attempts=1, resume_supported=True
        )
        self.assertEqual(action, "fail")
        self.assertIn("not safe to retry", reason)

    def test_the_attempt_budget_stops_an_endless_retry_loop(self) -> None:
        lost = attempt(failure_class=FailureClass.WORKER_LOST)
        action, reason = recovery_decision(
            lost, prior_attempts=3, resume_supported=False, max_attempts=3
        )
        self.assertEqual(action, "fail")
        self.assertIn("budget", reason)


class FaultInjectionTests(unittest.TestCase):
    """Prove recovery against a real killed process, not a mocked transition."""

    def _spawn_disposable_worker(self) -> subprocess.Popen[bytes]:
        # A disposable child that only sleeps. It never touches the repository.
        return subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(300)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def test_a_killed_worker_is_orphaned_replaced_and_keeps_its_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = AttemptStore(pathlib.Path(directory) / "attempts")
            worker = self._spawn_disposable_worker()
            try:
                first = attempt(
                    attempt_id=next_attempt_id("DIV-1", store.for_task("DIV-1")),
                    pid=worker.pid,
                    process_start_token=process_start_token(worker.pid),
                    worktree="C:/tmp/wt/DIV-1",
                    base_commit="a" * 40,
                    evidence_refs=("evidence-1",),
                )
                store.save(first)
                # 1. The attempt is genuinely running.
                self.assertTrue(worker_is_live(first))
                self.assertEqual(
                    classify_quiet_attempt(first, now=NOW), AttemptState.RUNNING
                )

                # 2. Kill the worker mid-flight.
                worker.kill()
                worker.wait(timeout=30)
            finally:
                if worker.poll() is None:  # pragma: no cover - cleanup only
                    worker.kill()

            # 3. Divan notices the process is gone, not merely quiet.
            self.assertFalse(worker_is_live(first))
            self.assertEqual(
                classify_quiet_attempt(first, now=NOW), AttemptState.ORPHANED
            )

            orphaned = first.transition(
                AttemptState.ORPHANED,
                "worker process disappeared",
                at=NOW.isoformat(),
                failure_class=FailureClass.WORKER_LOST,
            ).transition(
                AttemptState.RECOVERY_PENDING, "divan owns the wreckage", at=NOW.isoformat()
            )
            store.save(orphaned)

            # 4. A replacement is chosen, and it may be a different provider.
            action, _ = recovery_decision(
                orphaned, prior_attempts=1, resume_supported=False
            )
            self.assertEqual(action, "replace")
            store.save(
                orphaned.transition(
                    AttemptState.REPLACED, "replacement attempt created", at=NOW.isoformat()
                )
            )

            second = AttemptRecord(
                attempt_id=next_attempt_id("DIV-1", store.for_task("DIV-1")),
                task_id=first.task_id,
                worker_id="worker-2",
                provider="claude",
                agent="claude",
                started_at=NOW.isoformat(),
                worktree=first.worktree,
                base_commit=first.base_commit,
                replaces_attempt_id=first.attempt_id,
            )
            store.save(second)

            # 5. Same task contract, fresh attempt identity.
            self.assertEqual(second.task_id, first.task_id)
            self.assertNotEqual(second.attempt_id, first.attempt_id)
            self.assertEqual(second.replaces_attempt_id, first.attempt_id)
            self.assertNotEqual(second.provider, first.provider)

            # 6. The old evidence and history survive the replacement.
            preserved = store.load(first.attempt_id)
            self.assertEqual(preserved.state, AttemptState.REPLACED)
            self.assertEqual(preserved.evidence_refs, ("evidence-1",))
            self.assertEqual(preserved.failure_class, FailureClass.WORKER_LOST)
            self.assertGreaterEqual(len(preserved.history), 3)

            # 7. The task can now complete under the replacement attempt.
            store.save(
                second.transition(
                    AttemptState.COMPLETED, "work delivered", at=NOW.isoformat(), exit_code=0
                )
            )
            summary = attempt_summary(store.for_task("DIV-1"))
            self.assertEqual(summary["total"], 2)
            self.assertEqual(summary["open"], 0)
            self.assertEqual(summary["completed"], 1)
            self.assertEqual(summary["providers"], ["claude", "codex"])

    def test_pid_reuse_cannot_make_a_dead_attempt_look_alive(self) -> None:
        worker = self._spawn_disposable_worker()
        pid = worker.pid
        token = process_start_token(pid)
        worker.kill()
        worker.wait(timeout=30)

        # A recorded token from a different process must not validate this pid.
        forged = attempt(pid=pid, process_start_token="not-the-same-token")
        self.assertFalse(worker_is_live(forged))
        if token != "unavailable":
            self.assertNotEqual(token, "not-the-same-token")


if __name__ == "__main__":
    unittest.main()
