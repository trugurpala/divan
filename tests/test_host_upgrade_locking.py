from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest

from tests.test_host_upgrade import HOSTS, ROOT, SOURCE, TARGET_REF, UpgradeRunner

CHILD = """
import os
import pathlib
import sys
import time
sys.path.insert(0, sys.argv[1])
from host_journal import UpgradeLock
lock = UpgradeLock(pathlib.Path(sys.argv[2]))
lock.__enter__()
if len(sys.argv) == 4:
    print("ready", flush=True)
    time.sleep(30)
os._exit(0)
"""


class HostUpgradeLockingTests(unittest.TestCase):
    def options(self, state_dir: pathlib.Path) -> object:
        return HOSTS.Options(
            host="codex",
            source=SOURCE,
            ref=TARGET_REF,
            execute=True,
            migrate_legacy=False,
            state_dir=state_dir,
            upgrade=True,
        )

    def _journal(self, runner: UpgradeRunner) -> pathlib.Path:
        return next(runner.state_dir.glob("upgrade-*.json"))

    def _child(self, state_dir: pathlib.Path, *, live: bool) -> subprocess.Popen[str]:
        command = [
            sys.executable,
            "-c",
            CHILD,
            str(ROOT / "scripts"),
            str(state_dir),
        ]
        if live:
            command.append("live")
        return subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

    def test_dead_process_lock_does_not_block_transaction_recovery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-lock-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary))
            HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
            path = self._journal(runner)
            child = self._child(runner.state_dir, live=False)
            output, errors = child.communicate(timeout=10)
            self.assertEqual((child.returncode, output, errors), (0, "", ""))
            runner.commands.clear()

            try:
                recovered = HOSTS.rollback_transaction(path, runner=runner)
            except HOSTS.InstallError as exc:
                self.fail(f"dead process left an unrecoverable lock: {exc}")

        self.assertEqual(recovered["status"], "recovered")

    def test_live_process_lock_blocks_before_runner_call(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-lock-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary))
            HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
            path = self._journal(runner)
            child = self._child(runner.state_dir, live=True)
            assert child.stdout is not None
            self.assertEqual(child.stdout.readline().strip(), "ready")
            runner.commands.clear()
            try:
                with self.assertRaisesRegex(HOSTS.InstallError, "lock|active"):
                    HOSTS.rollback_transaction(path, runner=runner)
            finally:
                child.terminate()
                child.communicate(timeout=10)

        self.assertEqual(runner.commands, [])


if __name__ == "__main__":
    unittest.main()
