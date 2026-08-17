from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.attempt_store import process_start_token
from divan_runtime.verification_guard import (
    LOCK_NAME,
    GuardLease,
    GuardState,
    LockHolder,
    VerificationGuardError,
    acquire,
    check,
    held,
    lock_path_for,
    release,
    try_acquire,
)


def _write_lock(tree: pathlib.Path, **overrides: object) -> pathlib.Path:
    """Write a lock file by hand, the way a foreign or dead holder would leave it."""
    payload: dict[str, object] = {
        "schema_version": 1,
        "pid": 1,
        "process_start_token": "unavailable",
        "acquired_at": "2026-08-16T12:00:00+00:00",
        "purpose": "test",
        "tree_digest": "sha256:" + "0" * 64,
    }
    payload.update(overrides)
    path = lock_path_for(tree)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class GuardTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.tree = pathlib.Path(self._directory.name) / "tree"
        self.tree.mkdir()
        # A tracked-looking file that the guard must never touch.
        self.source = self.tree / "module.py"
        self.source.write_text("print('hello')\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._directory.cleanup()

    def _spawn_sleeper(self) -> subprocess.Popen[bytes]:
        # A disposable child that only sleeps. It never touches the tree.
        return subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _stop(self, worker: subprocess.Popen[bytes]) -> None:
        if worker.poll() is None:
            worker.kill()
        worker.wait(timeout=30)


class AcquireTests(GuardTestCase):
    def test_acquire_takes_a_free_tree_and_writes_only_its_lock(self) -> None:
        before = self.source.read_bytes()

        lease = acquire(self.tree, "pytest canonical")

        self.assertIsNotNone(lease)
        assert lease is not None
        self.assertEqual(lease.lock_path, self.tree / ".divan" / LOCK_NAME)
        self.assertTrue(lease.lock_path.is_file())
        self.assertIsNone(lease.recovered)
        self.assertEqual(lease.holder.pid, os.getpid())
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.tree.iterdir()), [".divan", "module.py"])
        self.assertEqual([p.name for p in (self.tree / ".divan").iterdir()], [LOCK_NAME])

    def test_lock_file_carries_the_documented_fields(self) -> None:
        lease = acquire(self.tree, "pytest canonical")
        assert lease is not None

        payload = json.loads(lease.lock_path.read_text(encoding="utf-8"))

        self.assertEqual(
            set(payload),
            {"schema_version", "pid", "process_start_token", "acquired_at", "purpose", "tree_digest"},
        )
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["pid"], os.getpid())
        self.assertEqual(payload["process_start_token"], process_start_token(os.getpid()))
        self.assertEqual(payload["purpose"], "pytest canonical")
        self.assertTrue(payload["tree_digest"].startswith("sha256:"))
        self.assertNotIn(str(self.tree), json.dumps(payload))

    def test_second_acquire_is_refused_while_the_holder_is_live(self) -> None:
        worker = self._spawn_sleeper()
        try:
            _write_lock(
                self.tree,
                pid=worker.pid,
                process_start_token=process_start_token(worker.pid),
                purpose="another verification",
            )

            result = try_acquire(self.tree, "an edit")

            self.assertIsNone(result.lease)
            self.assertIn("held by live process", result.reason)
            assert result.refused_by is not None
            self.assertIs(result.refused_by.state, GuardState.HELD_LIVE)
            assert result.refused_by.holder is not None
            self.assertEqual(result.refused_by.holder.pid, worker.pid)
            self.assertIsNone(acquire(self.tree, "an edit"))
            # The live holder's lock is untouched.
            on_disk = json.loads(lock_path_for(self.tree).read_text(encoding="utf-8"))
            self.assertEqual(on_disk["pid"], worker.pid)
            self.assertEqual(on_disk["purpose"], "another verification")
        finally:
            self._stop(worker)

    def test_own_second_acquire_is_refused_because_this_process_is_live(self) -> None:
        first = acquire(self.tree, "first")
        assert first is not None

        second = try_acquire(self.tree, "second")

        self.assertIsNone(second.lease)
        self.assertIn("held by live process", second.reason)
        self.assertTrue(release(first).released)

    def test_stale_lock_from_a_dead_pid_is_recovered(self) -> None:
        worker = self._spawn_sleeper()
        pid = worker.pid
        token = process_start_token(pid)
        self._stop(worker)
        _write_lock(self.tree, pid=pid, process_start_token=token, purpose="died")

        result = try_acquire(self.tree, "recover")

        assert result.lease is not None
        self.assertIn("recovered a stale lock", result.reason)
        assert result.lease.recovered is not None
        self.assertIs(result.lease.recovered.state, GuardState.STALE)
        assert result.lease.recovered.holder is not None
        self.assertEqual(result.lease.recovered.holder.pid, pid)
        self.assertEqual(result.lease.recovered.holder.purpose, "died")
        on_disk = json.loads(lock_path_for(self.tree).read_text(encoding="utf-8"))
        self.assertEqual(on_disk["pid"], os.getpid())

    def test_pid_reuse_is_treated_as_stale_not_live(self) -> None:
        worker = self._spawn_sleeper()
        try:
            # Same pid, alive right now, but a start token from a different life.
            _write_lock(
                self.tree,
                pid=worker.pid,
                process_start_token="windows-filetime:1",
                purpose="previous owner of this pid",
            )
            self.assertNotEqual(process_start_token(worker.pid), "windows-filetime:1")

            status = check(self.tree)
            result = try_acquire(self.tree, "recover")
        finally:
            self._stop(worker)

        self.assertIs(status.state, GuardState.STALE)
        assert result.lease is not None
        assert result.lease.recovered is not None
        self.assertIs(result.lease.recovered.state, GuardState.STALE)

    def test_malformed_lock_is_treated_as_stale_and_recorded(self) -> None:
        path = lock_path_for(self.tree)
        path.parent.mkdir(parents=True)
        path.write_text("{not json", encoding="utf-8")

        result = try_acquire(self.tree, "recover")

        assert result.lease is not None
        self.assertIn("recovered a malformed lock", result.reason)
        assert result.lease.recovered is not None
        self.assertIs(result.lease.recovered.state, GuardState.MALFORMED)
        self.assertIsNone(result.lease.recovered.holder)
        self.assertEqual(
            json.loads(path.read_text(encoding="utf-8"))["pid"], os.getpid()
        )

    def test_valid_json_with_the_wrong_shape_is_malformed(self) -> None:
        _write_lock(self.tree, pid="not-a-pid")

        self.assertIs(check(self.tree).state, GuardState.MALFORMED)


class ReleaseTests(GuardTestCase):
    def test_holder_releases_and_the_tree_is_free_again(self) -> None:
        lease = acquire(self.tree, "pytest")
        assert lease is not None

        report = release(lease)

        self.assertTrue(report.released)
        self.assertFalse(lease.lock_path.exists())
        self.assertIs(check(self.tree).state, GuardState.FREE)

    def test_a_lease_from_another_process_cannot_release(self) -> None:
        lease = acquire(self.tree, "pytest")
        assert lease is not None
        forged = GuardLease(
            tree=lease.tree,
            lock_path=lease.lock_path,
            holder=LockHolder(
                pid=lease.holder.pid + 1,
                process_start_token=lease.holder.process_start_token,
                acquired_at=lease.holder.acquired_at,
                purpose="impostor",
                tree_digest=lease.holder.tree_digest,
            ),
        )

        report = release(forged)

        self.assertFalse(report.released)
        self.assertIn("another process", report.reason)
        self.assertTrue(lease.lock_path.is_file())
        self.assertTrue(release(lease).released)

    def test_release_is_refused_when_the_lock_now_belongs_to_someone_else(self) -> None:
        lease = acquire(self.tree, "pytest")
        assert lease is not None
        # Simulate a takeover: the lock on disk is now another holder's.
        _write_lock(self.tree, pid=os.getpid() + 1, process_start_token="windows-filetime:2")

        report = release(lease)

        self.assertFalse(report.released)
        self.assertIn("held by process", report.reason)
        on_disk = json.loads(lease.lock_path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["pid"], os.getpid() + 1)

    def test_release_with_no_lock_on_disk_is_reported_not_silent(self) -> None:
        lease = acquire(self.tree, "pytest")
        assert lease is not None
        lease.lock_path.unlink()

        report = release(lease)

        self.assertFalse(report.released)
        self.assertIn("no lock on disk", report.reason)


class HeldTests(GuardTestCase):
    def test_context_manager_holds_then_releases(self) -> None:
        with held(self.tree, "pytest") as lease:
            self.assertIs(check(self.tree).state, GuardState.HELD_LIVE)
            self.assertEqual(lease.holder.purpose, "pytest")

        self.assertIs(check(self.tree).state, GuardState.FREE)

    def test_context_manager_releases_on_exception(self) -> None:
        with self.assertRaises(ZeroDivisionError):
            with held(self.tree, "pytest"):
                raise ZeroDivisionError("verification blew up")

        self.assertIs(check(self.tree).state, GuardState.FREE)
        self.assertFalse(lock_path_for(self.tree).exists())

    def test_context_manager_refuses_a_live_holder(self) -> None:
        worker = self._spawn_sleeper()
        try:
            _write_lock(
                self.tree, pid=worker.pid, process_start_token=process_start_token(worker.pid)
            )
            with self.assertRaises(VerificationGuardError) as caught:
                with held(self.tree, "an edit"):
                    self.fail("must not run over a live holder")  # pragma: no cover
            self.assertIn("held by live process", str(caught.exception))
        finally:
            self._stop(worker)


class CheckTests(GuardTestCase):
    def test_check_reports_free(self) -> None:
        status = check(self.tree)

        self.assertIs(status.state, GuardState.FREE)
        self.assertTrue(status.mutation_allowed)
        self.assertIsNone(status.holder)
        self.assertFalse((self.tree / ".divan").exists(), "check() must not write")

    def test_check_reports_held_live_with_holder_details(self) -> None:
        worker = self._spawn_sleeper()
        try:
            _write_lock(
                self.tree,
                pid=worker.pid,
                process_start_token=process_start_token(worker.pid),
                purpose="canonical verify",
            )
            status = check(self.tree)
        finally:
            self._stop(worker)

        self.assertIs(status.state, GuardState.HELD_LIVE)
        self.assertFalse(status.mutation_allowed)
        assert status.holder is not None
        self.assertEqual(status.holder.pid, worker.pid)
        self.assertEqual(status.holder.purpose, "canonical verify")
        self.assertIn(str(worker.pid), status.reason)

    def test_check_reports_stale_and_leaves_the_lock_in_place(self) -> None:
        worker = self._spawn_sleeper()
        pid, token = worker.pid, process_start_token(worker.pid)
        self._stop(worker)
        path = _write_lock(self.tree, pid=pid, process_start_token=token)

        status = check(self.tree)

        self.assertIs(status.state, GuardState.STALE)
        self.assertTrue(status.mutation_allowed)
        assert status.holder is not None
        self.assertEqual(status.holder.pid, pid)
        self.assertTrue(path.is_file(), "check() is read-only")

    def test_check_reports_malformed_and_leaves_the_lock_in_place(self) -> None:
        path = lock_path_for(self.tree)
        path.parent.mkdir(parents=True)
        path.write_bytes(b"\xff\xfe garbage")

        status = check(self.tree)

        self.assertIs(status.state, GuardState.MALFORMED)
        self.assertIsNone(status.holder)
        self.assertTrue(path.is_file(), "check() is read-only")


if __name__ == "__main__":
    unittest.main()
