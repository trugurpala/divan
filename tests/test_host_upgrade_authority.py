from __future__ import annotations

import copy
import json
import pathlib
import subprocess
import tempfile
import unittest
from typing import Any
from unittest import mock

from tests.test_host_install import FakeRunner
from tests.test_host_upgrade import (
    HOSTS,
    OLD_REF,
    ROOT,
    SOURCE,
    TARGET_REF,
    TARGET_VERSIONS,
    UpgradeRunner,
)

CODEX_ADD_CORE = ("codex", "plugin", "add", "core-pack@divan", "--json")
CODEX_RESTORE_MARKETPLACE = (
    "codex",
    "plugin",
    "marketplace",
    "add",
    SOURCE,
    "--ref",
    OLD_REF,
    "--json",
)


def _write_catalog(root: pathlib.Path, versions: dict[str, str]) -> None:
    path = root / ".agents" / "plugins" / "marketplace.json"
    path.parent.mkdir(parents=True)
    rows = [
        {
            "name": package,
            "version": version,
            "source": {"source": "local", "path": f"./plugins/{package}"},
        }
        for package, version in versions.items()
    ]
    path.write_text(json.dumps({"name": "divan", "plugins": rows}), encoding="utf-8")


class RawSourceMismatchRunner(UpgradeRunner):
    def _marketplace_row(self, host: str) -> dict[str, object] | None:
        row = super()._marketplace_row(host)
        if row is None:
            return None
        if host == "claude":
            row["url"] = "https://github.com/foreign/divan.git"
        else:
            row["marketplaceSource"] = {
                "sourceType": "git",
                "source": "https://github.com/foreign/divan.git",
            }
        return row


class RestoreMarketplaceMismatchRunner(UpgradeRunner):
    def __init__(self, root: pathlib.Path) -> None:
        super().__init__(root)
        self.replacement = root / "replacement-old-codex"
        _write_catalog(self.replacement, self.old_versions["codex"])

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        result = super().__call__(command)
        if tuple(command) == CODEX_RESTORE_MARKETPLACE:
            self.roots["codex"] = self.replacement
        return result


class LocalRawAliasRunner(UpgradeRunner):
    COMMIT = "b" * 40

    def __init__(self, root: pathlib.Path) -> None:
        super().__init__(root, current_ref=self.COMMIT)
        self.refs = {"codex": self.COMMIT}
        self.sources = {"codex": str(ROOT)}
        self.roots = {"codex": ROOT}
        self.plugins = {
            "codex": {
                **{
                    f"{package}@divan": version
                    for package, version in TARGET_VERSIONS.items()
                },
                "unrelated@codex": "9.9.9",
            }
        }

    def _marketplace_row(self, host: str) -> dict[str, object] | None:
        row = super()._marketplace_row(host)
        if row is not None:
            row["marketplaceSource"] = {
                "sourceType": "local",
                "source": str(ROOT) + ".git",
            }
        return row

    def _git(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        if "get-url" in command:
            return subprocess.CompletedProcess(command, 2, "", "origin is absent")
        if "status" in command:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 0, self.COMMIT + "\n", "")


class HostUpgradeAuthorityTests(unittest.TestCase):
    def test_claude_directory_marketplace_uses_local_path_authority(self) -> None:
        row = {
            "name": "divan",
            "source": "directory",
            "path": str(ROOT),
            "installLocation": str(ROOT),
        }
        checkout = {"root": str(ROOT), "ref": TARGET_REF}

        with mock.patch.object(
            HOSTS._host_upgrade.host_state, "checkout_evidence", return_value=checkout
        ) as evidence:
            self.assertEqual(
                HOSTS._host_upgrade.host_state.marketplace_evidence(
                    "claude",
                    row,
                    str(ROOT),
                    TARGET_REF,
                    lambda _command: "",
                    HOSTS._normalize_source,
                ),
                checkout,
            )
            evidence.assert_called_once()

        with mock.patch.object(HOSTS._host_upgrade.host_state, "checkout_evidence") as evidence:
            with self.assertRaisesRegex(HOSTS._host_upgrade.host_state.StateError, "source"):
                HOSTS._host_upgrade.host_state.marketplace_evidence(
                    "claude",
                    row,
                    SOURCE,
                    TARGET_REF,
                    lambda _command: "",
                    HOSTS._normalize_source,
                )
            evidence.assert_not_called()

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

    def _successful_record(self, runner: UpgradeRunner) -> tuple[pathlib.Path, dict[str, Any]]:
        HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
        path = self._journal(runner)
        return path, json.loads(path.read_text(encoding="utf-8"))

    def test_transition_tampering_is_rejected_before_runner_call(self) -> None:
        mutators = {
            "install-without-marketplace": _install_without_marketplace,
            "remove-unowned-plugin": _remove_unowned_plugin,
            "remove-unowned-marketplace": _remove_unowned_marketplace,
            "restore-unaffected-host": _restore_unaffected_host,
            "forward-and-recovery-pending": _both_pending,
            "verified-with-forward-pending": _verified_with_pending,
            "created-plugin-order": _swap_created_plugins,
            "created-plugin-prefix": _skip_created_plugin,
            "created-marketplace-prerequisite": _drop_removed_marketplace,
            "created-plugin-prerequisite": _drop_removed_plugin,
            "pending-marketplace-prerequisite": _add_marketplace_too_early,
        }
        for name, mutate in mutators.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix="divan-upgrade-authority-"
            ) as temporary:
                runner = UpgradeRunner(pathlib.Path(temporary))
                path, record = self._successful_record(runner)
                mutate(record)
                path.write_text(json.dumps(record), encoding="utf-8")
                runner.commands.clear()

                with self.assertRaises(HOSTS.InstallError):
                    HOSTS.rollback_transaction(path, runner=runner)

                self.assertEqual(runner.commands, [])

    def test_verified_snapshot_tampering_is_rejected_before_runner_call(self) -> None:
        mutators = {
            "missing-host": lambda record: record.__setitem__("verified", {}),
            "empty-snapshot": lambda record: record["verified"].__setitem__("codex", {}),
            "target-evidence": _break_verified_commit,
            "contract": _break_verified_contract,
            "plugin-fingerprint": _break_verified_plugin_fingerprint,
        }
        for name, mutate in mutators.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix="divan-upgrade-authority-"
            ) as temporary:
                runner = UpgradeRunner(pathlib.Path(temporary))
                path, record = self._successful_record(runner)
                mutate(record)
                path.write_text(json.dumps(record), encoding="utf-8")
                runner.commands.clear()

                with self.assertRaises(HOSTS.InstallError):
                    HOSTS.rollback_transaction(path, runner=runner)

                self.assertEqual(runner.commands, [])

    def test_schema_tamper_blocks_recovery_and_later_upgrade_before_runner(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-authority-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary))
            path, record = self._successful_record(runner)
            record["schema"] = 1
            record["before"] = {
                "codex": {"marketplaces": ["community-codex"], "plugins": []}
            }
            record["created"] = {"marketplaces": [], "plugins": []}
            path.write_text(json.dumps(record), encoding="utf-8")
            runner.commands.clear()

            with self.assertRaises(HOSTS.InstallError):
                HOSTS.rollback_transaction(path, runner=runner)
            self.assertEqual(runner.commands, [])

            with self.assertRaises(HOSTS.InstallError):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
            self.assertEqual(runner.commands, [])

    def test_local_source_alias_tamper_is_rejected_before_runner_call(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-authority-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary))
            path, record = self._successful_record(runner)
            _make_local_alias_tamper(record)
            path.write_text(json.dumps(record), encoding="utf-8")
            runner.commands.clear()

            with self.assertRaises(HOSTS.InstallError):
                HOSTS.rollback_transaction(path, runner=runner)

            self.assertEqual(runner.commands, [])

    def test_early_safe_schema1_rollback_does_not_block_later_upgrade(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-authority-") as temporary:
            fixture_root = pathlib.Path(temporary)
            state_dir = fixture_root / "state"
            install_runner = FakeRunner(
                fail_on=("claude", "plugin", "marketplace", "list", "--json")
            )
            install_options = HOSTS.Options(
                host="both",
                source=SOURCE,
                ref=OLD_REF,
                execute=True,
                migrate_legacy=False,
                state_dir=state_dir,
                upgrade=False,
            )
            with self.assertRaises(HOSTS.InstallError):
                HOSTS.install(install_options, runner=install_runner, root=ROOT)
            install_path = next(state_dir.glob("install-*.json"))
            install_record = json.loads(install_path.read_text(encoding="utf-8"))
            self.assertEqual(install_record["status"], "rolled-back")
            self.assertEqual(install_record["before"], {})

            upgrade_runner = UpgradeRunner(fixture_root)
            upgraded = HOSTS.upgrade(
                self.options(state_dir), runner=upgrade_runner, root=ROOT
            )

        self.assertEqual(upgraded["status"], "verified")

    def test_fingerprinted_schema1_terminal_allows_later_upgrade(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-authority-") as temporary:
            fixture_root = pathlib.Path(temporary)
            state_dir = fixture_root / "state"
            installed = HOSTS.install(
                HOSTS.Options(
                    host="codex",
                    source=SOURCE,
                    ref=OLD_REF,
                    execute=True,
                    migrate_legacy=False,
                    state_dir=state_dir,
                    upgrade=False,
                ),
                runner=FakeRunner(),
                root=ROOT,
            )
            self.assertEqual(installed["status"], "verified")

            runner = UpgradeRunner(fixture_root)
            try:
                upgraded = HOSTS.upgrade(
                    self.options(state_dir), runner=runner, root=ROOT
                )
            except Exception as exc:
                self.fail(f"fingerprinted terminal install blocked upgrade: {exc}")

        self.assertEqual(upgraded["status"], "verified")

    def test_schema1_terminal_subset_rejects_malformed_or_uncaptured_rows(self) -> None:
        mutators = {
            "extra-before-field": lambda record: record["before"]["claude"].__setitem__(
                "unexpected", []
            ),
            "duplicate-before-row": lambda record: record["before"]["claude"][
                "marketplaces"
            ].append("community-claude"),
            "uncaptured-created-host": lambda record: record["created"][
                "marketplaces"
            ].append("codex"),
        }
        for name, mutate in mutators.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix="divan-upgrade-authority-"
            ) as temporary:
                runner = UpgradeRunner(pathlib.Path(temporary))
                runner.state_dir.mkdir()
                path = runner.state_dir / "install-safe-rollback.json"
                record = {
                    "schema": 1,
                    "status": "rolled-back",
                    "transaction_path": str(path.resolve()),
                    "hosts": ["claude", "codex"],
                    "pending": None,
                    "before": {
                        "claude": {
                            "marketplaces": ["community-claude"],
                            "plugins": ["unrelated@claude"],
                        }
                    },
                    "created": {"marketplaces": [], "plugins": []},
                }
                mutate(record)
                path.write_text(json.dumps(record), encoding="utf-8")

                with self.assertRaises(HOSTS.InstallError):
                    HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

                self.assertEqual(runner.commands, [])

    def test_restore_marketplace_is_verified_before_any_plugin_install(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-authority-") as temporary:
            runner = RestoreMarketplaceMismatchRunner(pathlib.Path(temporary))
            runner.fail_on = CODEX_ADD_CORE

            with self.assertRaises(HOSTS.InstallError):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

        restore_index = runner.mutations.index(CODEX_RESTORE_MARKETPLACE)
        plugin_installs = [
            command
            for command in runner.mutations[restore_index + 1 :]
            if command[:3] == ("codex", "plugin", "add")
        ]
        self.assertEqual(plugin_installs, [])

    def test_same_source_ref_before_snapshots_must_have_one_contract(self) -> None:
        versions = {
            "claude": {package: f"1.0.{index}" for index, package in enumerate(TARGET_VERSIONS)},
            "codex": {package: f"2.0.{index}" for index, package in enumerate(TARGET_VERSIONS)},
        }
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-authority-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary), old_versions=versions)

            with self.assertRaisesRegex(HOSTS.InstallError, "snapshot|contract|digest"):
                HOSTS.upgrade(
                    self.options(runner.state_dir, host="both"), runner=runner, root=ROOT
                )

        self.assertEqual(runner.mutations, [])
        self.assertFalse(runner.state_dir.exists())

    def test_raw_host_source_mismatch_fails_before_journal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-authority-") as temporary:
            runner = RawSourceMismatchRunner(pathlib.Path(temporary))

            with self.assertRaisesRegex(HOSTS.InstallError, "source"):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

        self.assertEqual(runner.mutations, [])
        self.assertFalse(runner.state_dir.exists())

    def test_local_raw_source_requires_resolved_path_identity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-authority-") as temporary:
            runner = LocalRawAliasRunner(pathlib.Path(temporary))
            options = self.options(
                runner.state_dir, source=str(ROOT), ref=LocalRawAliasRunner.COMMIT
            )

            with self.assertRaisesRegex(HOSTS.InstallError, "source"):
                HOSTS.upgrade(options, runner=runner, root=ROOT)

        self.assertEqual(runner.mutations, [])
        self.assertFalse(runner.state_dir.exists())

    def test_unreadable_or_malformed_transaction_scan_fails_closed(self) -> None:
        rows = {
            "install-unreadable.json": "{",
            "upgrade-unreadable.json": "{",
            "install-terminal.json": '{"schema": 1, "status": "verified"}',
            "upgrade-terminal.json": '{"schema": 2, "status": "verified"}',
        }
        for name, payload in rows.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix="divan-upgrade-authority-"
            ) as temporary:
                runner = UpgradeRunner(pathlib.Path(temporary))
                runner.state_dir.mkdir()
                (runner.state_dir / name).write_text(payload, encoding="utf-8")

                with self.assertRaisesRegex(HOSTS.InstallError, "journal|transaction"):
                    HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

                self.assertEqual(runner.commands, [])

    def test_validated_terminal_upgrade_journal_allows_a_later_no_op(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-authority-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary))
            first = HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

            second = HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

        self.assertEqual((first["status"], second["status"]), ("verified", "no-op"))

    def test_catalog_rejects_duplicate_empty_and_invalid_source_rows(self) -> None:
        base = [
            {
                "name": package,
                "version": version,
                "source": {"source": "local", "path": f"./plugins/{package}"},
            }
            for package, version in TARGET_VERSIONS.items()
        ]
        cases = {
            "duplicate": [*base, copy.deepcopy(base[0])],
            "empty-version": [
                {**row, "version": ""} if row["name"] == "sadrazam" else row
                for row in copy.deepcopy(base)
            ],
            "invalid-source": [
                {**row, "source": {"source": "local", "path": "../foreign"}}
                if row["name"] == "sadrazam"
                else row
                for row in copy.deepcopy(base)
            ],
        }
        for name, rows in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix="divan-upgrade-authority-"
            ) as temporary:
                root = pathlib.Path(temporary)
                path = root / ".agents" / "plugins" / "marketplace.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({"plugins": rows}), encoding="utf-8")

                with self.assertRaises(HOSTS._host_upgrade.host_state.StateError):
                    HOSTS._host_upgrade.host_state._catalog(root)


def _install_without_marketplace(record: dict[str, Any]) -> None:
    record["status"] = "in-progress"
    record["created"] = {"marketplaces": [], "plugins": []}
    record["pending"] = {
        "phase": "forward",
        "action": "install-plugin",
        "host": "codex",
        "id": "sadrazam@divan",
    }


def _break_verified_commit(record: dict[str, Any]) -> None:
    record["verified"]["codex"]["commit"] = "b" * 40


def _break_verified_contract(record: dict[str, Any]) -> None:
    record["verified"]["codex"]["contract"]["sadrazam"] = "9.9.9"


def _break_verified_plugin_fingerprint(record: dict[str, Any]) -> None:
    row = record["verified"]["codex"]["plugins"]["sadrazam@divan"]
    row["installPath"] = "foreign-root/plugins/sadrazam"
    row["source"] = {"path": "foreign-root/plugins/sadrazam"}


def _make_local_alias_tamper(record: dict[str, Any]) -> None:
    local = str(ROOT)
    alias = local + ".git"
    record["target"]["source"] = local
    before = record["before_rows"]["codex"]
    before["source"] = alias
    before["marketplace"]["marketplaceSource"]["source"] = alias
    record["created"]["marketplaces"][0]["source"] = local
    verified = record["verified"]["codex"]
    verified["source"] = local
    verified["marketplace"]["marketplaceSource"]["source"] = local


def _remove_unowned_plugin(record: dict[str, Any]) -> None:
    record["status"] = "rollback-incomplete"
    record["created"]["plugins"] = [
        row for row in record["created"]["plugins"] if row["id"] != "sadrazam@divan"
    ]
    record["recovery_pending"] = {
        "phase": "recovery",
        "action": "remove-target-plugin",
        "host": "codex",
        "id": "sadrazam@divan",
    }


def _remove_unowned_marketplace(record: dict[str, Any]) -> None:
    record["status"] = "rollback-incomplete"
    record["created"] = {"marketplaces": [], "plugins": []}
    record["recovery_pending"] = {
        "phase": "recovery",
        "action": "remove-target-marketplace",
        "host": "codex",
    }


def _restore_unaffected_host(record: dict[str, Any]) -> None:
    record["status"] = "rollback-incomplete"
    record["created"] = {"marketplaces": [], "plugins": []}
    record["removed"] = []
    record["recovery_pending"] = {
        "phase": "recovery",
        "action": "restore-marketplace",
        "host": "codex",
    }


def _both_pending(record: dict[str, Any]) -> None:
    record["status"] = "rollback-incomplete"
    record["pending"] = {
        "phase": "forward",
        "action": "install-plugin",
        "host": "codex",
        "id": "zanaat-pack@divan",
    }
    record["recovery_pending"] = {
        "phase": "recovery",
        "action": "restore-marketplace",
        "host": "codex",
    }


def _verified_with_pending(record: dict[str, Any]) -> None:
    record["status"] = "verified"
    record["pending"] = {
        "phase": "forward",
        "action": "remove-plugin",
        "host": "codex",
        "id": "sadrazam@divan",
    }


def _swap_created_plugins(record: dict[str, Any]) -> None:
    record["created"]["plugins"][0], record["created"]["plugins"][1] = (
        record["created"]["plugins"][1],
        record["created"]["plugins"][0],
    )


def _skip_created_plugin(record: dict[str, Any]) -> None:
    record["created"]["plugins"] = [
        record["created"]["plugins"][0], record["created"]["plugins"][2]
    ]


def _drop_removed_marketplace(record: dict[str, Any]) -> None:
    record["removed"] = [row for row in record["removed"] if row["kind"] != "marketplace"]


def _drop_removed_plugin(record: dict[str, Any]) -> None:
    record["removed"] = [
        row
        for row in record["removed"]
        if not (row["kind"] == "plugin" and row["id"] == "sadrazam@divan")
    ]


def _add_marketplace_too_early(record: dict[str, Any]) -> None:
    record["status"] = "in-progress"
    record["created"] = {"marketplaces": [], "plugins": []}
    record["removed"] = [row for row in record["removed"] if row["kind"] != "marketplace"]
    record["pending"] = {
        "phase": "forward",
        "action": "add-marketplace",
        "host": "codex",
    }


if __name__ == "__main__":
    unittest.main()
