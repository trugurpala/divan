from __future__ import annotations

import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from tests.test_host_upgrade import (
    HOSTS,
    OLD_REF,
    ROOT,
    SOURCE,
    TARGET_REF,
    TARGET_VERSIONS,
    UpgradeRunner,
)

CODEX_ADD_SADRAZAM = ("codex", "plugin", "add", "sadrazam@divan", "--json")
CODEX_ADD_CORE = ("codex", "plugin", "add", "core-pack@divan", "--json")
CODEX_REMOVE_SADRAZAM = ("codex", "plugin", "remove", "sadrazam@divan", "--json")
CODEX_REMOVE_CORE = ("codex", "plugin", "remove", "core-pack@divan", "--json")
CODEX_REMOVE_ZANAAT = ("codex", "plugin", "remove", "zanaat-pack@divan", "--json")
CODEX_REMOVE_MARKETPLACE = (
    "codex",
    "plugin",
    "marketplace",
    "remove",
    "divan",
    "--json",
)
CODEX_ADD_MARKETPLACE = (
    "codex",
    "plugin",
    "marketplace",
    "add",
    SOURCE,
    "--ref",
    TARGET_REF,
    "--json",
)


class SequencedInterruptRunner(UpgradeRunner):
    def __init__(self, root: pathlib.Path, events: list[tuple[str, tuple[str, ...]]], **kw: object):
        super().__init__(root, **kw)
        self.events = list(events)

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        argv = tuple(command)
        if self.events and self.events[0] == ("before", argv):
            self.events.pop(0)
            self.commands.append(argv)
            self._observe_journal(argv)
            self.mutations.append(argv)
            raise KeyboardInterrupt
        result = super().__call__(command)
        if self.events and self.events[0] == ("after", argv):
            self.events.pop(0)
            raise KeyboardInterrupt
        return result


class NthInterruptRunner(UpgradeRunner):
    def __init__(
        self,
        root: pathlib.Path,
        command: tuple[str, ...],
        occurrence: int,
        **kw: object,
    ) -> None:
        super().__init__(root, **kw)
        self.interrupt_command = command
        self.interrupt_occurrence = occurrence
        self.occurrences = 0

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        argv = tuple(command)
        if argv == self.interrupt_command:
            self.occurrences += 1
            if self.occurrences == self.interrupt_occurrence:
                self.commands.append(argv)
                self._observe_journal(argv)
                self.mutations.append(argv)
                raise KeyboardInterrupt
        return super().__call__(command)


class BetweenHostDriftRunner(UpgradeRunner):
    def __init__(self, root: pathlib.Path) -> None:
        super().__init__(root)
        self.codex_marketplace_reads = 0

    def _marketplace_list(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        if command[0] == "codex":
            self.codex_marketplace_reads += 1
            if self.codex_marketplace_reads == 2 and self.refs.get("claude") == TARGET_REF:
                self.plugins["codex"]["sadrazam@divan"] = "drifted"
        return super()._marketplace_list(command)


class TargetExtraRunner(UpgradeRunner):
    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        result = super().__call__(command)
        if tuple(command) == ("codex", "plugin", "add", "zanaat-pack@divan", "--json"):
            self.plugins["codex"]["rogue@divan"] = "7.7.7"
        return result


class TargetWrongPathRunner(UpgradeRunner):
    def _plugin_row(self, host: str, selector: str) -> dict[str, object]:
        row = super()._plugin_row(host, selector)
        if self.refs.get(host) == TARGET_REF and selector == "sadrazam@divan":
            row["installPath"] = "foreign-root/plugins/sadrazam"
            row["source"] = {"path": "foreign-root/plugins/sadrazam"}
        return row


class NextPluginReplacementRunner(UpgradeRunner):
    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        result = super().__call__(command)
        if tuple(command) == CODEX_REMOVE_SADRAZAM:
            self.plugins["codex"]["core-pack@divan"] = "9.9.9"
        return result


class MarketplaceReplacementBeforeRemoveRunner(UpgradeRunner):
    def __init__(self, root: pathlib.Path) -> None:
        super().__init__(root)
        self.replacement = root / "replacement-old-codex"
        catalog = self.replacement / ".agents" / "plugins" / "marketplace.json"
        catalog.parent.mkdir(parents=True)
        catalog.write_bytes(
            (self.old_roots["codex"] / ".agents" / "plugins" / "marketplace.json").read_bytes()
        )

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        result = super().__call__(command)
        if tuple(command) == CODEX_REMOVE_ZANAAT:
            self.roots["codex"] = self.replacement
        return result


class RestoreExtraRunner(UpgradeRunner):
    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        result = super().__call__(command)
        argv = tuple(command)
        if argv == (
            "codex",
            "plugin",
            "marketplace",
            "add",
            SOURCE,
            "--ref",
            OLD_REF,
            "--json",
        ):
            self.plugins["codex"]["rogue@divan"] = "7.7.7"
        return result


class DirtyTargetRunner(UpgradeRunner):
    def _git(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        if pathlib.Path(command[2]) == ROOT and "status" in command:
            return subprocess.CompletedProcess(command, 0, " M .agents/plugins/marketplace.json\n", "")
        return super()._git(command)


class OriginlessLocalRunner(UpgradeRunner):
    COMMIT = "b" * 40

    def __init__(self, root: pathlib.Path, *, dirty: bool = False) -> None:
        super().__init__(root, current_ref=self.COMMIT)
        self.dirty = dirty
        self.refs = {"codex": self.COMMIT}
        self.sources = {"codex": str(ROOT)}
        self.roots = {"codex": ROOT}
        self.plugins = {
            "codex": {
                **{f"{package}@divan": version for package, version in TARGET_VERSIONS.items()},
                "unrelated@codex": "9.9.9",
            }
        }

    def _git(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        if "get-url" in command:
            return subprocess.CompletedProcess(command, 2, "", "origin is absent")
        if "status" in command:
            output = " M local-change\n" if self.dirty else ""
            return subprocess.CompletedProcess(command, 0, output, "")
        return subprocess.CompletedProcess(command, 0, self.COMMIT + "\n", "")


class HostUpgradeSecurityTests(unittest.TestCase):
    def options(self, state_dir: pathlib.Path, **changes: object) -> object:
        values = {
            "host": "codex",
            "source": SOURCE,
            "ref": TARGET_REF,
            "execute": True,
            "migrate_legacy": False,
            "state_dir": state_dir,
            "upgrade": True,
        }
        values.update(changes)
        return HOSTS.Options(**values)

    def _journal(self, runner: UpgradeRunner) -> pathlib.Path:
        return next(runner.state_dir.glob("upgrade-*.json"))

    def _old_versions(self) -> dict[str, dict[str, str]]:
        versions = {package: f"0.0.{index}" for index, package in enumerate(TARGET_VERSIONS)}
        return {"claude": dict(versions), "codex": dict(versions)}

    def test_plugin_forward_evidence_survives_second_recovery_interruption(self) -> None:
        for timing in ("before", "after"):
            with self.subTest(timing=timing), tempfile.TemporaryDirectory(
                prefix="divan-upgrade-security-"
            ) as temporary:
                runner = SequencedInterruptRunner(
                    pathlib.Path(temporary),
                    [("after", CODEX_ADD_SADRAZAM), (timing, CODEX_REMOVE_SADRAZAM)],
                    old_versions=self._old_versions(),
                )
                with self.assertRaises(HOSTS.InstallError):
                    HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
                path = self._journal(runner)
                interrupted = json.loads(path.read_text("utf-8"))
                self.assertTrue(interrupted["created"]["plugins"])
                self.assertIsInstance(interrupted["recovery_pending"], dict)

                runner.events.clear()
                recovered = HOSTS.rollback_transaction(path, runner=runner)

                self.assertEqual(recovered["status"], "recovered")
                self.assertEqual(runner.refs["codex"], OLD_REF)
                self.assertEqual(
                    runner.plugins["codex"]["sadrazam@divan"],
                    self._old_versions()["codex"]["sadrazam"],
                )

    def test_marketplace_forward_evidence_survives_second_recovery_interruption(self) -> None:
        for timing in ("before", "after"):
            with self.subTest(timing=timing), tempfile.TemporaryDirectory(
                prefix="divan-upgrade-security-"
            ) as temporary:
                runner = SequencedInterruptRunner(
                    pathlib.Path(temporary),
                    [("after", CODEX_ADD_MARKETPLACE), (timing, CODEX_REMOVE_MARKETPLACE)],
                )
                with self.assertRaises(HOSTS.InstallError):
                    HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
                path = self._journal(runner)
                interrupted = json.loads(path.read_text("utf-8"))
                self.assertTrue(interrupted["created"]["marketplaces"])
                self.assertIsInstance(interrupted["recovery_pending"], dict)

                runner.events.clear()
                recovered = HOSTS.rollback_transaction(path, runner=runner)

                self.assertEqual(recovered["status"], "recovered")
                self.assertEqual(runner.refs["codex"], OLD_REF)

    def test_tampered_schema_2_journal_never_reaches_runner(self) -> None:
        mutators = {
            "operation": lambda row, path: row.update(operation="install"),
            "path": lambda row, path: row.update(transaction_path=str(path.parent / "other.json")),
            "hosts": lambda row, path: row.update(hosts=["codex", "codex"]),
            "target-ref": lambda row, path: row["target"].update(ref=7),
            "versions": lambda row, path: row["target"]["versions"].pop("sadrazam"),
            "source-relation": lambda row, path: row["before_rows"]["codex"].update(
                source="https://github.com/foreign/divan.git"
            ),
            "pending": lambda row, path: row.update(
                pending={"phase": "evil", "action": "shell", "host": "codex"}
            ),
            "selector": lambda row, path: row["created"]["plugins"].append(
                {"host": "codex", "id": "evil@divan"}
            ),
            "before-version": lambda row, path: row["before_rows"]["codex"][
                "plugins"
            ]["sadrazam@divan"].update(version="9.9.9"),
            "created-version": lambda row, path: row["created"]["plugins"][0].update(
                version="9.9.9"
            ),
            "created-root": lambda row, path: row["created"]["marketplaces"][0].update(
                root=str(path.parent / "foreign")
            ),
            "verified-host": lambda row, path: row["verified"].update(evil={}),
            "removed-duplicate": lambda row, path: row["removed"].append(
                dict(row["removed"][0])
            ),
        }
        for name, mutate in mutators.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix="divan-upgrade-security-"
            ) as temporary:
                runner = UpgradeRunner(pathlib.Path(temporary))
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
                path = self._journal(runner)
                record = json.loads(path.read_text("utf-8"))
                mutate(record, path)
                path.write_text(json.dumps(record), encoding="utf-8")
                runner.commands.clear()

                with self.assertRaises(HOSTS.InstallError):
                    HOSTS.rollback_transaction(path, runner=runner)

                self.assertEqual(runner.commands, [])

    def test_active_journal_blocks_even_a_no_op_before_runner_call(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary), current_ref=TARGET_REF)
            runner.roots = {host: ROOT for host in ("claude", "codex")}
            runner.state_dir.mkdir()
            (runner.state_dir / "upgrade-stale.json").write_text(
                '{"schema": 2, "operation": "upgrade", "status": "in-progress"}',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(HOSTS.InstallError, "transaction|journal"):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

        self.assertEqual(runner.commands, [])

    def test_unowned_stale_lock_file_does_not_block_upgrade(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary))
            lock = runner.state_dir.parent / f".{runner.state_dir.name}.upgrade.lock"
            lock.write_text("occupied", encoding="utf-8")

            try:
                record = HOSTS.upgrade(
                    self.options(runner.state_dir), runner=runner, root=ROOT
                )
            except HOSTS.InstallError as exc:
                self.fail(f"stale lock file blocked upgrade: {exc}")

        self.assertEqual(record["status"], "verified")

    def test_between_host_drift_rolls_back_first_host_without_mutating_drifted_host(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = BetweenHostDriftRunner(pathlib.Path(temporary))
            with self.assertRaisesRegex(HOSTS.InstallError, "drift|contract|version"):
                HOSTS.upgrade(
                    self.options(runner.state_dir, host="both"), runner=runner, root=ROOT
                )

        codex_mutations = [command for command in runner.mutations if command[0] == "codex"]
        self.assertEqual(codex_mutations, [])
        self.assertEqual(runner.refs["claude"], OLD_REF)
        self.assertEqual(runner.plugins["codex"]["sadrazam@divan"], "drifted")

    def test_progressive_remove_refuses_replaced_next_plugin(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = NextPluginReplacementRunner(pathlib.Path(temporary))

            with self.assertRaisesRegex(HOSTS.InstallError, "drift|fingerprint|version"):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

        self.assertNotIn(CODEX_REMOVE_CORE, runner.mutations)
        self.assertNotIn(CODEX_REMOVE_MARKETPLACE, runner.mutations)
        self.assertEqual(runner.plugins["codex"]["core-pack@divan"], "9.9.9")

    def test_progressive_remove_refuses_replaced_marketplace(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = MarketplaceReplacementBeforeRemoveRunner(pathlib.Path(temporary))

            with self.assertRaisesRegex(HOSTS.InstallError, "drift|marketplace|fingerprint"):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

        self.assertNotIn(CODEX_REMOVE_MARKETPLACE, runner.mutations)
        self.assertEqual(runner.roots["codex"], runner.replacement)

    def test_recovery_refuses_replaced_plugin_with_same_selector(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = NthInterruptRunner(
                pathlib.Path(temporary), CODEX_REMOVE_SADRAZAM, 2
            )
            runner.fail_on = CODEX_ADD_CORE
            with self.assertRaises(HOSTS.InstallError):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
            path = self._journal(runner)
            runner.plugins["codex"]["sadrazam@divan"] = "9.9.9"
            runner.plugin_overrides[("codex", "sadrazam@divan")] = {
                "source": {"path": "foreign-root/plugins/sadrazam"}
            }
            runner.commands.clear()
            runner.mutations.clear()

            with self.assertRaises(HOSTS.InstallError):
                HOSTS.rollback_transaction(path, runner=runner)

        self.assertNotIn(CODEX_REMOVE_SADRAZAM, runner.mutations)
        self.assertEqual(runner.plugins["codex"]["sadrazam@divan"], "9.9.9")

    def test_recovery_refuses_replaced_marketplace_with_same_source_and_ref(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = NthInterruptRunner(
                pathlib.Path(temporary), CODEX_REMOVE_MARKETPLACE, 2
            )
            runner.fail_on = CODEX_ADD_CORE
            with self.assertRaises(HOSTS.InstallError):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
            path = self._journal(runner)
            replacement = pathlib.Path(temporary) / "replacement"
            replacement.mkdir()
            (replacement / ".agents" / "plugins").mkdir(parents=True)
            source_catalog = ROOT / ".agents" / "plugins" / "marketplace.json"
            (replacement / ".agents" / "plugins" / "marketplace.json").write_bytes(
                source_catalog.read_bytes()
            )
            runner.roots["codex"] = replacement
            runner.commands.clear()
            runner.mutations.clear()

            with self.assertRaises(HOSTS.InstallError):
                HOSTS.rollback_transaction(path, runner=runner)

        self.assertNotIn(CODEX_REMOVE_MARKETPLACE, runner.mutations)
        self.assertEqual(runner.roots["codex"], replacement)

    def test_target_verification_rejects_extra_divan_selector(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = TargetExtraRunner(pathlib.Path(temporary))
            with self.assertRaises(HOSTS.InstallError):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
            journal = json.loads(self._journal(runner).read_text("utf-8"))

        self.assertNotEqual(journal["status"], "verified")
        self.assertIn("rogue@divan", runner.plugins["codex"])

    def test_target_verification_rejects_same_version_from_foreign_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = TargetWrongPathRunner(pathlib.Path(temporary))
            with self.assertRaisesRegex(HOSTS.InstallError, "path|fingerprint|provenance"):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
            self.assertNotEqual(
                json.loads(self._journal(runner).read_text("utf-8"))["status"], "verified"
            )

    def test_restore_verification_rejects_extra_divan_selector(self) -> None:
        failure = ("codex", "plugin", "add", "ui-pack@divan", "--json")
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = RestoreExtraRunner(pathlib.Path(temporary))
            runner.fail_on = failure
            with self.assertRaises(HOSTS.InstallError):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
            journal = json.loads(self._journal(runner).read_text("utf-8"))

        self.assertEqual(journal["status"], "rollback-incomplete")
        self.assertIn("rogue@divan", runner.plugins["codex"])

    def test_same_source_ref_contract_mismatch_fails_before_journal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = UpgradeRunner(
                pathlib.Path(temporary), old_versions=self._old_versions(), current_ref=TARGET_REF
            )
            with self.assertRaisesRegex(HOSTS.InstallError, "contract|reproduc"):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

        self.assertEqual(runner.mutations, [])
        self.assertFalse(runner.state_dir.exists())

    def test_same_source_ref_catalog_digest_mismatch_fails_before_journal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary), current_ref=TARGET_REF)
            for root in runner.old_roots.values():
                path = root / ".agents" / "plugins" / "marketplace.json"
                value = json.loads(path.read_text("utf-8"))
                value["moved"] = True
                path.write_text(json.dumps(value, indent=2), encoding="utf-8")
            with self.assertRaisesRegex(HOSTS.InstallError, "digest|reproduc"):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

        self.assertEqual(runner.mutations, [])
        self.assertFalse(runner.state_dir.exists())

    def test_dirty_target_checkout_fails_before_journal_or_host_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = DirtyTargetRunner(pathlib.Path(temporary))
            with self.assertRaisesRegex(HOSTS.InstallError, "dirty|clean"):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

        self.assertEqual(runner.mutations, [])
        self.assertFalse(runner.state_dir.exists())

    def test_originless_clean_local_checkout_can_be_proven_as_no_op(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = OriginlessLocalRunner(pathlib.Path(temporary))
            options = self.options(
                runner.state_dir, source=str(ROOT), ref=OriginlessLocalRunner.COMMIT
            )
            record = HOSTS.upgrade(options, runner=runner, root=ROOT)

        self.assertEqual(record["status"], "no-op")
        self.assertFalse(any("get-url" in command for command in runner.commands))
        self.assertEqual(runner.mutations, [])

    def test_dirty_originless_local_checkout_fails_before_journal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = OriginlessLocalRunner(pathlib.Path(temporary), dirty=True)
            options = self.options(
                runner.state_dir, source=str(ROOT), ref=OriginlessLocalRunner.COMMIT
            )
            with self.assertRaisesRegex(HOSTS.InstallError, "dirty|clean"):
                HOSTS.upgrade(options, runner=runner, root=ROOT)

        self.assertEqual(runner.mutations, [])
        self.assertFalse(runner.state_dir.exists())

    def test_schema_2_records_commit_and_catalog_digest_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-security-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary))
            record = HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

        for evidence in (record["target"], record["before_rows"]["codex"]):
            self.assertRegex(evidence["commit"], r"^[0-9a-f]{40}$")
            self.assertRegex(evidence["catalog_digest"], r"^[0-9a-f]{64}$")

    def test_recovery_command_is_absolute_and_uses_current_python(self) -> None:
        path = pathlib.Path("relative journal.json")
        command = HOSTS._host_transactions.recovery_command(path)

        self.assertIn(str(path.resolve()), command)
        self.assertIn(str((ROOT / "scripts" / "divan.py").resolve()), command)
        self.assertIn("recover", command)
        self.assertIn(sys.executable, command)

    def test_rollback_equals_syntax_uses_the_recovery_parser(self) -> None:
        path = pathlib.Path("fixture-transaction.json").resolve()
        payload = {"transaction_path": str(path), "status": "recovered"}
        output, errors = io.StringIO(), io.StringIO()
        with mock.patch.object(HOSTS, "rollback_transaction", return_value=payload) as rollback:
            with redirect_stdout(output), redirect_stderr(errors):
                result = HOSTS.main([f"--rollback-transaction={path}"])

        self.assertEqual(result, 0)
        rollback.assert_called_once_with(path)
        self.assertEqual(errors.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
