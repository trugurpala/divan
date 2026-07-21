from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("divan_host_install", ROOT / "scripts" / "kur-hostlar.py")
assert SPEC and SPEC.loader
HOST_INSTALL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOST_INSTALL)
PACKAGE_VERSIONS = {
    "sadrazam": "0.9.1",
    "core-pack": "0.5.1",
    "ui-pack": "0.1.0",
    "react-pack": "0.2.1",
    "zanaat-pack": "0.1.1",
}
SOURCE = "https://github.com/trugurpala/divan.git"
REF = "v0.12.0"
COMMIT = "a" * 40
CATALOG_DIGEST = hashlib.sha256(
    (ROOT / ".agents" / "plugins" / "marketplace.json").read_bytes()
).hexdigest()
CLAUDE_ROOT = (
    pathlib.Path(tempfile.gettempdir())
    / "divan-host-fixture-home"
    / ".claude"
    / "plugins"
    / "marketplaces"
    / "divan"
)


def _fingerprinted(record: dict[str, object]) -> dict[str, object]:
    record["operation"] = "install"
    before = record.get("before")
    assert isinstance(before, dict)
    record["hosts"] = [host for host in ("claude", "codex") if host in before]
    record["fingerprint_schema"] = 1
    record["target"] = {
        "source": SOURCE,
        "ref": REF,
        "root": str(ROOT.resolve()),
        "commit": COMMIT,
        "catalog_digest": CATALOG_DIGEST,
        "versions": dict(PACKAGE_VERSIONS),
    }
    created = record["created"]
    assert isinstance(created, dict)
    markets = created["marketplaces"]
    plugins = created["plugins"]
    assert isinstance(markets, list) and isinstance(plugins, list)
    created["marketplaces"] = [
        {
            "host": host,
            "source": SOURCE,
            "ref": REF,
            "root": str((CLAUDE_ROOT if host == "claude" else ROOT).resolve()),
            "commit": COMMIT,
            "catalog_digest": CATALOG_DIGEST,
        }
        for host in markets
    ]
    created["plugins"] = [_plugin_fingerprint(row) for row in plugins]
    return record


def _plugin_fingerprint(row: object) -> dict[str, object]:
    assert isinstance(row, dict)
    host, selector = row["host"], row["id"]
    assert isinstance(host, str) and isinstance(selector, str)
    package = selector.removesuffix("@divan")
    version = PACKAGE_VERSIONS[package]
    install_path = ROOT / "plugins" / package
    marketplace_root = ROOT
    if host == "claude":
        marketplace_root = CLAUDE_ROOT
        install_path = CLAUDE_ROOT.parent.parent / "cache" / "divan" / package / version
    return {
        "host": host,
        "id": selector,
        "version": version,
        "marketplace_root": str(marketplace_root.resolve()),
        "install_path": str(install_path.resolve()),
        "native_provenance": True,
    }


def _tamper_legacy_path(record: dict[str, object], transaction: pathlib.Path) -> None:
    outside = transaction.parent.parent / "foreign-legacy.json"
    outside.write_text('{"schema": 1}\n', encoding="utf-8")
    record["legacy_migration"] = {"result": {"journal": str(outside)}}


def _tamper_legacy_identity(record: dict[str, object], transaction: pathlib.Path) -> None:
    journal = transaction.with_name("legacy-foreign.json")
    journal.write_text(
        json.dumps({"schema": 1, "kind": "fallback", "journal": str(journal.resolve())}),
        encoding="utf-8",
    )
    record["legacy_migration"] = {"result": {"journal": str(journal.resolve())}}


class FakeRunner:
    def __init__(self, fail_on: tuple[str, ...] | None = None) -> None:
        self.commands: list[tuple[str, ...]] = []
        self.fail_on = fail_on
        self.marketplaces = {
            "claude": {"claude-plugins-official"},
            "codex": {"personal"},
        }
        self.plugins = {
            "claude": {"unrelated@claude-plugins-official"},
            "codex": {"vibe-coder-standard@personal"},
        }
        self.plugin_overrides: dict[str, dict[str, object]] = {}
        catalog = CLAUDE_ROOT / ".agents" / "plugins" / "marketplace.json"
        catalog.parent.mkdir(parents=True, exist_ok=True)
        catalog.write_bytes((ROOT / ".agents" / "plugins" / "marketplace.json").read_bytes())

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        argv = tuple(command)
        self.commands.append(argv)
        if self.fail_on and self.fail_on == argv:
            return subprocess.CompletedProcess(command, 7, "", "fixture failure")

        host = command[0]
        if host == "git":
            if "status" in command:
                return subprocess.CompletedProcess(command, 0, "", "")
            if "get-url" in command:
                return subprocess.CompletedProcess(
                    command, 0, "https://github.com/trugurpala/divan.git\n", ""
                )
            if "describe" in command:
                return subprocess.CompletedProcess(command, 0, "v0.12.0\n", "")
            return subprocess.CompletedProcess(command, 0, "a" * 40 + "\n", "")
        if command[1:4] == ["plugin", "marketplace", "list"]:
            if host == "claude":
                output = [
                    {
                        "name": name,
                        "installLocation": str(CLAUDE_ROOT) if name == "divan" else name,
                    }
                    for name in sorted(self.marketplaces[host])
                ]
            else:
                output = {
                    "marketplaces": [
                        {
                            "name": name,
                            "root": str(ROOT) if name == "divan" else name,
                        }
                        for name in sorted(self.marketplaces[host])
                    ]
                }
            return subprocess.CompletedProcess(command, 0, json.dumps(output), "")
        if command[1:3] == ["plugin", "list"]:
            if host == "claude":
                output = [self._plugin_row(host, plugin) for plugin in sorted(self.plugins[host])]
            else:
                output = {
                    "installed": [
                        self._plugin_row(host, plugin) for plugin in sorted(self.plugins[host])
                    ]
                }
            return subprocess.CompletedProcess(command, 0, json.dumps(output), "")
        if command[1:4] == ["plugin", "marketplace", "add"]:
            self.marketplaces[host].add("divan")
        elif command[1:4] == ["plugin", "marketplace", "remove"]:
            self.marketplaces[host].discard(command[4])
        elif command[1:3] == ["plugin", "install"]:
            self.plugins[host].add(command[3])
        elif command[1:3] == ["plugin", "add"]:
            self.plugins[host].add(command[3])
        elif command[1:3] in (["plugin", "uninstall"], ["plugin", "remove"]):
            self.plugins[host].discard(command[3])
        return subprocess.CompletedProcess(command, 0, "{}", "")

    def _plugin_row(self, host: str, plugin: str) -> dict[str, object]:
        key = "id" if host == "claude" else "pluginId"
        row: dict[str, object] = {key: plugin, "enabled": True}
        if plugin.endswith("@divan"):
            name = plugin.removesuffix("@divan")
            version = PACKAGE_VERSIONS[name]
            install_path = str(ROOT / "plugins" / name)
            if host == "claude":
                install_path = str(
                    CLAUDE_ROOT.parent.parent / "cache" / "divan" / name / version
                )
            skills = sorted(
                path.parent.name
                for path in (ROOT / "plugins" / name / "skills").glob("*/SKILL.md")
            )
            row.update(
                {
                    "version": version,
                    "installed": True,
                    "marketplaceName": "divan",
                    "scope": "user",
                    "installPath": install_path,
                    "source": {"path": install_path},
                    "skills": skills,
                }
            )
        row.update(self.plugin_overrides.get(plugin, {}))
        return row


class JournalObservingRunner(FakeRunner):
    def __init__(self, state_dir: pathlib.Path) -> None:
        super().__init__()
        self.state_dir = state_dir
        self.saw_pending_journal = False

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        if command[1:4] == ["plugin", "marketplace", "add"]:
            journals = list(self.state_dir.glob("install-*.json"))
            if journals:
                record = json.loads(journals[0].read_text(encoding="utf-8"))
                self.saw_pending_journal = record.get("pending") == {
                    "phase": "forward",
                    "action": "add-marketplace",
                    "host": command[0],
                }
        return super().__call__(command)


class InterruptAfterMutationRunner(FakeRunner):
    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        result = super().__call__(command)
        if command[1:3] == ["plugin", "add"] and command[3] == "sadrazam@divan":
            raise KeyboardInterrupt
        return result


class PendingReplacementRunner(FakeRunner):
    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        result = super().__call__(command)
        if tuple(command) == ("codex", "plugin", "add", "sadrazam@divan", "--json"):
            self.plugin_overrides["sadrazam@divan"] = {
                "version": "9.9.9",
                "source": {"path": "foreign-root/plugins/sadrazam"},
            }
            raise KeyboardInterrupt
        return result


class InterruptOnceDuringRecoveryRunner(FakeRunner):
    def __init__(self) -> None:
        super().__init__()
        self.interrupted = False

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        result = super().__call__(command)
        if (
            not self.interrupted
            and command[1:3] in (["plugin", "uninstall"], ["plugin", "remove"])
        ):
            self.interrupted = True
            raise KeyboardInterrupt
        return result


class HostInstallTests(unittest.TestCase):
    def options(self, state_dir: pathlib.Path, **changes: object):
        values = {
            "host": "both",
            "source": "https://github.com/trugurpala/divan.git",
            "ref": "v0.12.0",
            "execute": True,
            "migrate_legacy": False,
            "state_dir": state_dir,
        }
        values.update(changes)
        return HOST_INSTALL.Options(**values)

    def test_transaction_primitives_are_extracted_with_compatibility_exports(self) -> None:
        transactions = sys.modules["host_transactions"]

        self.assertIs(HOST_INSTALL._persist_record, transactions.persist_record)
        self.assertIs(HOST_INSTALL._begin_mutation, transactions.begin_mutation)
        self.assertIs(HOST_INSTALL._finish_mutation, transactions.finish_mutation)
        self.assertIs(HOST_INSTALL._created_rows, transactions.schema1_created_rows)
        self.assertIs(HOST_INSTALL._owned_plugins, transactions.schema1_owned_plugins)

    def test_host_cli_output_is_decoded_as_utf8_not_system_locale(self) -> None:
        completed = subprocess.CompletedProcess(["tool"], 0, "Türkçe\n", "")
        with mock.patch.object(HOST_INSTALL.subprocess, "run", return_value=completed) as run:
            result = HOST_INSTALL._subprocess_runner([sys.executable, "--version"])

        self.assertEqual(result.stdout, "Türkçe\n")
        self.assertEqual(run.call_args.kwargs["encoding"], "utf-8")
        self.assertEqual(run.call_args.kwargs["errors"], "replace")

    def test_host_command_and_json_row_contracts_remain_compatible(self) -> None:
        runner = FakeRunner()

        claude_marketplaces = HOST_INSTALL._marketplace_rows("claude", runner)
        codex_marketplaces = HOST_INSTALL._marketplace_rows("codex", runner)
        claude_plugins = HOST_INSTALL._plugin_rows("claude", runner)
        codex_plugins = HOST_INSTALL._plugin_rows("codex", runner)

        self.assertEqual(
            runner.commands,
            [
                ("claude", "plugin", "marketplace", "list", "--json"),
                ("codex", "plugin", "marketplace", "list", "--json"),
                ("claude", "plugin", "list", "--json"),
                ("codex", "plugin", "list", "--json"),
            ],
        )
        self.assertIn("claude-plugins-official", claude_marketplaces)
        self.assertIn("personal", codex_marketplaces)
        self.assertIn("unrelated@claude-plugins-official", claude_plugins)
        self.assertIn("vibe-coder-standard@personal", codex_plugins)
        self.assertEqual(
            HOST_INSTALL._add_marketplace_command(
                "claude", "https://github.com/trugurpala/divan.git", "v0.12.0"
            ),
            [
                "claude",
                "plugin",
                "marketplace",
                "add",
                "https://github.com/trugurpala/divan.git#v0.12.0",
            ],
        )
        self.assertEqual(
            HOST_INSTALL._add_marketplace_command(
                "codex", "https://github.com/trugurpala/divan.git", "v0.12.0"
            ),
            [
                "codex",
                "plugin",
                "marketplace",
                "add",
                "https://github.com/trugurpala/divan.git",
                "--ref",
                "v0.12.0",
                "--json",
            ],
        )
        self.assertEqual(
            HOST_INSTALL._install_command("claude", "sadrazam"),
            ["claude", "plugin", "install", "sadrazam@divan", "--scope", "user"],
        )
        self.assertEqual(
            HOST_INSTALL._install_command("codex", "sadrazam"),
            ["codex", "plugin", "add", "sadrazam@divan", "--json"],
        )
        self.assertEqual(
            HOST_INSTALL._remove_plugin_command("claude", "sadrazam@divan"),
            [
                "claude",
                "plugin",
                "uninstall",
                "sadrazam@divan",
                "--scope",
                "user",
                "--yes",
            ],
        )
        self.assertEqual(
            HOST_INSTALL._remove_plugin_command("codex", "sadrazam@divan"),
            ["codex", "plugin", "remove", "sadrazam@divan", "--json"],
        )

    def test_adapter_owns_host_specific_plugin_provenance_and_paths(self) -> None:
        adapter = HOST_INSTALL._host_adapters

        self.assertTrue(
            adapter.plugin_provenance_valid(
                "codex", {"installed": True, "marketplaceName": "divan"}
            )
        )
        self.assertFalse(
            adapter.plugin_provenance_valid(
                "codex", {"installed": False, "marketplaceName": "divan"}
            )
        )
        self.assertEqual(
            adapter.plugin_install_path("claude", {"installPath": "claude-package"}),
            "claude-package",
        )
        self.assertEqual(
            adapter.plugin_install_path("codex", {"source": {"path": "codex-package"}}),
            "codex-package",
        )

    def test_real_host_json_paths_prove_native_versioned_install_fingerprints(self) -> None:
        fixture_dir = ROOT / "tests" / "fixtures" / "host-cli"
        cases = {
            "claude": (
                "claude-plugin-list.json",
                pathlib.Path("fixture-home/.claude/plugins/marketplaces/divan"),
                ("plugins", "cache", "divan", "sadrazam", "0.9.1"),
            ),
            "codex": (
                "codex-plugin-list.json",
                pathlib.Path("fixture-codex/divan"),
                ("divan", "plugins", "sadrazam"),
            ),
        }
        for host, (name, root, suffix) in cases.items():
            with self.subTest(host=host):
                value = json.loads((fixture_dir / name).read_text(encoding="utf-8"))
                row = HOST_INSTALL._host_adapters.plugin_rows(host, value)[
                    "sadrazam@divan"
                ]
                try:
                    fingerprint = HOST_INSTALL._host_upgrade.host_state.plugin_fingerprint(
                        host, "sadrazam@divan", row, root
                    )
                except HOST_INSTALL._host_upgrade.host_state.StateError as exc:
                    self.fail(f"real {host} plugin JSON was rejected: {exc}")

                self.assertEqual(fingerprint["version"], "0.9.1")
                self.assertEqual(
                    pathlib.Path(fingerprint["install_path"]).parts[-len(suffix) :],
                    suffix,
                )

        claude = json.loads(
            (fixture_dir / "claude-plugin-list.json").read_text(encoding="utf-8")
        )[0]
        claude["version"] = "9.9.9"
        with self.assertRaisesRegex(
            HOST_INSTALL._host_upgrade.host_state.StateError, "path|version"
        ):
            HOST_INSTALL._host_upgrade.host_state.plugin_fingerprint(
                "claude",
                "sadrazam@divan",
                claude,
                pathlib.Path("fixture-home/.claude/plugins/marketplaces/divan"),
            )

        foreign = dict(claude)
        foreign["version"] = "0.9.1"
        foreign["installPath"] = (
            "foreign-home/.claude/plugins/cache/divan/sadrazam/0.9.1"
        )
        with self.assertRaisesRegex(
            HOST_INSTALL._host_upgrade.host_state.StateError, "path|native"
        ):
            HOST_INSTALL._host_upgrade.host_state.plugin_fingerprint(
                "claude",
                "sadrazam@divan",
                foreign,
                pathlib.Path("fixture-home/.claude/plugins/marketplaces/divan"),
            )

        wrong_scope = dict(claude)
        wrong_scope["version"] = "0.9.1"
        wrong_scope["scope"] = "project"
        with self.assertRaisesRegex(
            HOST_INSTALL._host_upgrade.host_state.StateError, "provenance|scope"
        ):
            HOST_INSTALL._host_upgrade.host_state.plugin_fingerprint(
                "claude",
                "sadrazam@divan",
                wrong_scope,
                pathlib.Path("fixture-home/.claude/plugins/marketplaces/divan"),
            )

    def test_claude_local_directory_uses_config_cache_as_native_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-claude-local-path-") as temporary:
            root = pathlib.Path(temporary)
            source = root / "checkout"
            config = root / ".claude"
            source.mkdir()
            install_path = config / "plugins" / "cache" / "divan" / "sadrazam" / "0.9.1"
            row = {
                "id": "sadrazam@divan",
                "version": "0.9.1",
                "scope": "user",
                "enabled": True,
                "installPath": str(install_path),
            }

            with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(config)}):
                fingerprint = HOST_INSTALL._host_upgrade.host_state.plugin_fingerprint(
                    "claude", "sadrazam@divan", row, source, source=str(source)
                )

            self.assertEqual(
                pathlib.Path(fingerprint["install_path"]), install_path.resolve()
            )

    def test_dry_run_never_invokes_host_cli(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            runner = FakeRunner()
            record = HOST_INSTALL.install(
                self.options(pathlib.Path(temporary), execute=False), runner=runner
            )

        self.assertEqual(runner.commands, [])
        self.assertEqual(record["status"], "dry-run")
        rendered = "\n".join(" ".join(command) for command in record["planned_commands"])
        self.assertIn(
            "claude plugin marketplace add https://github.com/trugurpala/divan.git#v0.12.0",
            rendered,
        )
        self.assertIn(
            "codex plugin marketplace add https://github.com/trugurpala/divan.git --ref v0.12.0",
            rendered,
        )

    def test_installs_both_hosts_and_preserves_unrelated_plugins(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            runner = FakeRunner()
            state_dir = pathlib.Path(temporary)
            record = HOST_INSTALL.install(self.options(state_dir), runner=runner)

            self.assertEqual(record["status"], "verified")
            self.assertEqual(set(record["verified"]), {"claude", "codex"})
            for evidence in record["verified"].values():
                self.assertEqual(evidence["package_count"], 5)
                self.assertEqual(evidence["skill_count"], 41)
                self.assertEqual(evidence["ref"], "v0.12.0")
                self.assertEqual(
                    evidence["source"],
                    "https://github.com/trugurpala/divan.git",
                )
                self.assertTrue(evidence["all_enabled"])
            self.assertTrue(record["transaction_path"].startswith(str(state_dir)))
            self.assertTrue(pathlib.Path(record["transaction_path"]).is_file())
            self.assertIn("unrelated@claude-plugins-official", runner.plugins["claude"])
            self.assertIn("vibe-coder-standard@personal", runner.plugins["codex"])
            for package in HOST_INSTALL.PACKAGES:
                self.assertIn(f"{package}@divan", runner.plugins["claude"])
                self.assertIn(f"{package}@divan", runner.plugins["codex"])

    def test_install_journal_records_exact_created_fingerprints(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            runner = FakeRunner()
            record = HOST_INSTALL.install(
                self.options(pathlib.Path(temporary), host="both"), runner=runner
            )

        self.assertEqual(record.get("fingerprint_schema"), 1)
        self.assertTrue(
            all(
                isinstance(row, dict)
                and set(row)
                == {"host", "source", "ref", "root", "commit", "catalog_digest"}
                for row in record["created"]["marketplaces"]
            )
        )
        self.assertTrue(
            all(
                isinstance(row, dict)
                and set(row)
                == {
                    "host",
                    "id",
                    "version",
                    "marketplace_root",
                    "install_path",
                    "native_provenance",
                }
                for row in record["created"]["plugins"]
            )
        )
        by_host = {
            (row["host"], row["id"]): row for row in record["created"]["plugins"]
        }
        claude = by_host[("claude", "sadrazam@divan")]
        self.assertEqual(claude["version"], PACKAGE_VERSIONS["sadrazam"])
        self.assertEqual(
            pathlib.Path(claude["install_path"]).parts[-5:],
            ("plugins", "cache", "divan", "sadrazam", "0.9.1"),
        )

    def test_schema1_authority_rejects_tampering_before_any_runner_call(self) -> None:
        cases = {
            "schema": lambda row, _path: row.update(schema=2),
            "operation": lambda row, _path: row.update(operation="upgrade"),
            "status": lambda row, _path: row.update(status="unknown"),
            "hosts": lambda row, _path: row.update(hosts=["codex", "codex"]),
            "host-executable": lambda row, _path: row.update(hosts=["python"]),
            "transaction-path": lambda row, path: row.update(
                transaction_path=str(path.with_name("install-other.json"))
            ),
            "before-shape": lambda row, _path: row["before"]["codex"].update(
                marketplaces="personal"
            ),
            "created-crossfield": lambda row, _path: row["created"]["plugins"][0].update(
                host="claude"
            ),
            "pending-shape": lambda row, _path: row.update(
                status="in-progress",
                pending={"phase": "forward", "action": "install-plugin", "host": "codex"},
            ),
            "legacy-path": _tamper_legacy_path,
            "legacy-identity": _tamper_legacy_identity,
        }
        for name, tamper in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix="divan-schema1-authority-"
            ) as temporary:
                runner = FakeRunner()
                record = HOST_INSTALL.install(
                    self.options(pathlib.Path(temporary), host="codex"), runner=runner
                )
                transaction = pathlib.Path(record["transaction_path"])
                changed = copy.deepcopy(record)
                tamper(changed, transaction)
                transaction.write_text(json.dumps(changed) + "\n", encoding="utf-8")
                runner.commands.clear()

                with self.assertRaises(HOST_INSTALL.InstallError):
                    HOST_INSTALL.rollback_transaction(transaction, runner=runner)

                self.assertEqual(runner.commands, [])

    def test_execute_install_blocks_on_any_active_transaction_before_runner(self) -> None:
        for filename in ("install-active.json", "upgrade-active.json"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory(
                prefix="divan-install-active-"
            ) as temporary:
                state_dir = pathlib.Path(temporary)
                (state_dir / filename).write_text(
                    json.dumps({"schema": 1, "status": "in-progress"}),
                    encoding="utf-8",
                )
                runner = FakeRunner()

                with self.assertRaisesRegex(HOST_INSTALL.InstallError, "active|recovery"):
                    HOST_INSTALL.install(self.options(state_dir), runner=runner)

                self.assertEqual(runner.commands, [])

    def test_pending_replacement_is_not_promoted_or_removed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            state_dir = pathlib.Path(temporary)
            runner = PendingReplacementRunner()

            with self.assertRaises(HOST_INSTALL.InstallError):
                HOST_INSTALL.install(
                    self.options(state_dir, host="codex"), runner=runner
                )
            record = json.loads(
                next(state_dir.glob("install-*.json")).read_text(encoding="utf-8")
            )

        self.assertEqual(record["status"], "rollback-incomplete")
        self.assertIn("sadrazam@divan", runner.plugins["codex"])
        self.assertFalse(
            any(
                command[1:3] == ("plugin", "remove")
                and command[3] == "sadrazam@divan"
                for command in runner.commands
            )
        )

    def test_recorded_replacement_is_preserved_before_any_remove(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            state_dir = pathlib.Path(temporary)
            runner = FakeRunner()
            record = HOST_INSTALL.install(
                self.options(state_dir, host="codex"), runner=runner
            )
            transaction = pathlib.Path(record["transaction_path"])
            runner.plugin_overrides["zanaat-pack@divan"] = {
                "version": "9.9.9",
                "source": {"path": "foreign-root/plugins/zanaat-pack"},
            }
            runner.commands.clear()

            with self.assertRaises(HOST_INSTALL.InstallError):
                HOST_INSTALL.rollback_transaction(transaction, runner=runner)

        self.assertIn("zanaat-pack@divan", runner.plugins["codex"])
        self.assertFalse(
            any(command[1:3] == ("plugin", "remove") for command in runner.commands)
        )

    def test_fingerprintless_legacy_journal_fails_closed_before_remove(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            transaction = pathlib.Path(temporary) / "install-legacy.json"
            transaction.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "status": "in-progress",
                        "before": {
                            "codex": {"marketplaces": ["personal"], "plugins": []}
                        },
                        "created": {
                            "marketplaces": ["codex"],
                            "plugins": [{"host": "codex", "id": "sadrazam@divan"}],
                        },
                        "pending": None,
                    }
                ),
                encoding="utf-8",
            )
            runner = FakeRunner()
            runner.marketplaces["codex"].add("divan")
            runner.plugins["codex"].add("sadrazam@divan")

            with self.assertRaisesRegex(HOST_INSTALL.InstallError, "fingerprint|legacy"):
                HOST_INSTALL.rollback_transaction(transaction, runner=runner)

        self.assertIn("sadrazam@divan", runner.plugins["codex"])
        self.assertIn("divan", runner.marketplaces["codex"])
        self.assertFalse(
            any(
                command[1:3] in (("plugin", "remove"), ("plugin", "uninstall"))
                or command[1:4] == ("plugin", "marketplace", "remove")
                for command in runner.commands
            )
        )

    def test_journal_is_persisted_before_every_external_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            state_dir = pathlib.Path(temporary)
            runner = JournalObservingRunner(state_dir)
            HOST_INSTALL.install(
                self.options(state_dir, host="claude"),
                runner=runner,
            )

        self.assertTrue(runner.saw_pending_journal)

    def test_in_progress_journal_can_be_recovered_without_touching_unrelated_state(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            transaction = pathlib.Path(temporary) / "install-interrupted.json"
            transaction.write_text(
                json.dumps(
                    _fingerprinted({
                        "schema": 1,
                        "transaction_path": str(transaction),
                        "status": "in-progress",
                        "before": {
                            "codex": {
                                "marketplaces": ["personal"],
                                "plugins": ["vibe-coder-standard@personal"],
                            }
                        },
                        "created": {
                            "marketplaces": ["codex"],
                            "plugins": [{"host": "codex", "id": "sadrazam@divan"}],
                        },
                        "pending": {
                            "phase": "forward",
                            "action": "install-plugin",
                            "host": "codex",
                            "id": "core-pack@divan",
                        },
                    })
                ),
                encoding="utf-8",
            )
            runner = FakeRunner()
            runner.marketplaces["codex"].add("divan")
            runner.plugins["codex"].update(
                {"sadrazam@divan", "core-pack@divan"}
            )

            recovered = HOST_INSTALL.rollback_transaction(transaction, runner=runner)

        self.assertEqual(recovered["status"], "recovered")
        self.assertEqual(runner.marketplaces["codex"], {"personal"})
        self.assertEqual(runner.plugins["codex"], {"vibe-coder-standard@personal"})

    def test_host_recovery_resumes_the_linked_legacy_journal_first(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            root = pathlib.Path(temporary)
            legacy_journal = root / "legacy-interrupted.json"
            legacy_journal.write_text(
                json.dumps({
                    "schema": 1,
                    "kind": "migration",
                    "journal": str(legacy_journal.resolve()),
                }) + "\n",
                encoding="utf-8",
            )
            transaction = root / "install-interrupted.json"
            transaction.write_text(
                json.dumps(
                    _fingerprinted({
                        "schema": 1,
                        "transaction_path": str(transaction),
                        "status": "in-progress",
                        "before": {
                            "codex": {
                                "marketplaces": ["personal"],
                                "plugins": ["vibe-coder-standard@personal"],
                            }
                        },
                        "created": {
                            "marketplaces": ["codex"],
                            "plugins": [{"host": "codex", "id": "sadrazam@divan"}],
                        },
                        "pending": {
                            "phase": "forward",
                            "action": "legacy-migration",
                            "host": "codex",
                            "journal": str(legacy_journal),
                        },
                    })
                )
                + "\n",
                encoding="utf-8",
            )
            runner = FakeRunner()
            runner.marketplaces["codex"].add("divan")
            runner.plugins["codex"].add("sadrazam@divan")

            recovered = HOST_INSTALL.rollback_transaction(transaction, runner=runner)

        recover_commands = [
            command
            for command in runner.commands
            if "legacy_state.py" in " ".join(command) and "recover" in command
        ]
        self.assertEqual(len(recover_commands), 1)
        self.assertIn(str(legacy_journal), recover_commands[0])
        self.assertEqual(recovered["status"], "recovered")

    def test_rollback_reverses_a_completed_legacy_migration_before_native_entries(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            root = pathlib.Path(temporary)
            legacy_journal = root / "legacy-completed.json"
            legacy_journal.write_text(
                json.dumps({
                    "schema": 1,
                    "kind": "migration",
                    "journal": str(legacy_journal.resolve()),
                }) + "\n",
                encoding="utf-8",
            )
            transaction = root / "install-verified.json"
            transaction.write_text(
                json.dumps(
                    _fingerprinted({
                        "schema": 1,
                        "transaction_path": str(transaction),
                        "status": "verified",
                        "before": {
                            "codex": {
                                "marketplaces": ["personal"],
                                "plugins": ["vibe-coder-standard@personal"],
                            }
                        },
                        "created": {
                            "marketplaces": ["codex"],
                            "plugins": [{"host": "codex", "id": "sadrazam@divan"}],
                        },
                        "pending": None,
                        "legacy_migration": {
                            "result": {"journal": str(legacy_journal)}
                        },
                    })
                )
                + "\n",
                encoding="utf-8",
            )
            runner = FakeRunner()
            runner.marketplaces["codex"].add("divan")
            runner.plugins["codex"].add("sadrazam@divan")

            HOST_INSTALL.rollback_transaction(transaction, runner=runner)

        recovery_index = next(
            index
            for index, command in enumerate(runner.commands)
            if "legacy_state.py" in " ".join(command) and "recover" in command
        )
        plugin_index = next(
            index
            for index, command in enumerate(runner.commands)
            if command[1:3] == ("plugin", "remove")
        )
        self.assertLess(recovery_index, plugin_index)

    def test_rollback_fails_closed_when_recorded_legacy_journal_is_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            root = pathlib.Path(temporary)
            transaction = root / "install-verified.json"
            missing = root / "legacy-missing.json"
            transaction.write_text(
                json.dumps(
                    _fingerprinted({
                        "schema": 1,
                        "transaction_path": str(transaction),
                        "status": "verified",
                        "before": {
                            "codex": {
                                "marketplaces": ["personal"],
                                "plugins": ["vibe-coder-standard@personal"],
                            }
                        },
                        "created": {
                            "marketplaces": ["codex"],
                            "plugins": [{"host": "codex", "id": "sadrazam@divan"}],
                        },
                        "pending": None,
                        "legacy_migration": {"result": {"journal": str(missing)}},
                    })
                )
                + "\n",
                encoding="utf-8",
            )
            runner = FakeRunner()
            runner.marketplaces["codex"].add("divan")
            runner.plugins["codex"].add("sadrazam@divan")

            with self.assertRaisesRegex(HOST_INSTALL.InstallError, "legacy journal is missing"):
                HOST_INSTALL.rollback_transaction(transaction, runner=runner)

        self.assertIn("divan", runner.marketplaces["codex"])
        self.assertIn("sadrazam@divan", runner.plugins["codex"])
        self.assertFalse(
            any(command[1:3] == ("plugin", "remove") for command in runner.commands)
        )

    def test_automatic_failure_undoes_legacy_before_removing_native_entries(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            state_dir = pathlib.Path(temporary)
            runner = FakeRunner()

            def fail_after_legacy(
                _root: pathlib.Path,
                _runner: HOST_INSTALL.Runner,
                journal: pathlib.Path,
            ) -> None:
                journal.write_text(
                    json.dumps({
                        "schema": 1,
                        "kind": "migration",
                        "journal": str(journal.resolve()),
                    }) + "\n",
                    encoding="utf-8",
                )
                raise HOST_INSTALL.InstallError("legacy migration returned invalid JSON")

            with mock.patch.object(HOST_INSTALL, "_migrate_legacy", fail_after_legacy):
                with self.assertRaisesRegex(HOST_INSTALL.InstallError, "invalid JSON"):
                    HOST_INSTALL.install(
                        self.options(state_dir, host="codex", migrate_legacy=True),
                        runner=runner,
                    )
            transaction = next(state_dir.glob("install-*.json"))
            record = json.loads(transaction.read_text(encoding="utf-8"))

        recovery_index = next(
            index
            for index, command in enumerate(runner.commands)
            if "legacy_state.py" in " ".join(command) and "recover" in command
        )
        plugin_index = next(
            index
            for index, command in enumerate(runner.commands)
            if command[1:3] == ("plugin", "remove")
        )
        self.assertLess(recovery_index, plugin_index)
        self.assertEqual(record["status"], "rolled-back")

    def test_interrupt_after_external_success_rolls_back_pending_owned_entry(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            state_dir = pathlib.Path(temporary)
            runner = InterruptAfterMutationRunner()
            with self.assertRaises(HOST_INSTALL.InstallError):
                HOST_INSTALL.install(self.options(state_dir), runner=runner)
            journal = json.loads(
                next(state_dir.glob("install-*.json")).read_text(encoding="utf-8")
            )

        self.assertEqual(journal["status"], "rolled-back")
        self.assertEqual(runner.marketplaces["claude"], {"claude-plugins-official"})
        self.assertEqual(runner.marketplaces["codex"], {"personal"})
        self.assertEqual(runner.plugins["claude"], {"unrelated@claude-plugins-official"})
        self.assertEqual(runner.plugins["codex"], {"vibe-coder-standard@personal"})

    def test_recovery_can_resume_after_a_second_interruption(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            transaction = pathlib.Path(temporary) / "install-double-interrupt.json"
            transaction.write_text(
                json.dumps(
                    _fingerprinted({
                        "schema": 1,
                        "status": "in-progress",
                        "transaction_path": str(transaction),
                        "before": {
                            "codex": {
                                "marketplaces": ["personal"],
                                "plugins": ["vibe-coder-standard@personal"],
                            }
                        },
                        "created": {
                            "marketplaces": ["codex"],
                            "plugins": [{"host": "codex", "id": "sadrazam@divan"}],
                        },
                        "pending": None,
                    })
                ),
                encoding="utf-8",
            )
            runner = InterruptOnceDuringRecoveryRunner()
            runner.marketplaces["codex"].add("divan")
            runner.plugins["codex"].add("sadrazam@divan")

            with self.assertRaises(KeyboardInterrupt):
                HOST_INSTALL.rollback_transaction(transaction, runner=runner)
            interrupted = json.loads(transaction.read_text(encoding="utf-8"))
            self.assertEqual(interrupted["status"], "recovering")

            recovered = HOST_INSTALL.rollback_transaction(transaction, runner=runner)

        self.assertEqual(recovered["status"], "recovered")
        self.assertEqual(runner.marketplaces["codex"], {"personal"})
        self.assertEqual(runner.plugins["codex"], {"vibe-coder-standard@personal"})

    def test_failure_rolls_back_only_entries_created_by_transaction(self) -> None:
        failure = ("codex", "plugin", "add", "ui-pack@divan", "--json")
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            runner = FakeRunner(fail_on=failure)
            with self.assertRaises(HOST_INSTALL.InstallError):
                HOST_INSTALL.install(self.options(pathlib.Path(temporary)), runner=runner)

        self.assertEqual(runner.marketplaces["claude"], {"claude-plugins-official"})
        self.assertEqual(runner.marketplaces["codex"], {"personal"})
        self.assertEqual(runner.plugins["claude"], {"unrelated@claude-plugins-official"})
        self.assertEqual(runner.plugins["codex"], {"vibe-coder-standard@personal"})

    def test_wrong_or_disabled_native_package_fails_closed_without_removing_it(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            runner = FakeRunner()
            runner.plugin_overrides["ui-pack@divan"] = {
                "version": "0.0.0",
                "enabled": False,
            }
            with self.assertRaisesRegex(HOST_INSTALL.InstallError, "version|enabled"):
                HOST_INSTALL.install(
                    self.options(pathlib.Path(temporary), host="codex"), runner=runner
                )

        self.assertIn("divan", runner.marketplaces["codex"])
        self.assertIn("ui-pack@divan", runner.plugins["codex"])

    def test_preexisting_divan_entries_survive_rollback(self) -> None:
        failure = ("codex", "plugin", "add", "ui-pack@divan", "--json")
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            runner = FakeRunner(fail_on=failure)
            runner.marketplaces["claude"].add("divan")
            runner.plugins["claude"].add("sadrazam@divan")
            with self.assertRaises(HOST_INSTALL.InstallError):
                HOST_INSTALL.install(self.options(pathlib.Path(temporary)), runner=runner)

        self.assertIn("divan", runner.marketplaces["claude"])
        self.assertIn("sadrazam@divan", runner.plugins["claude"])

    def test_existing_divan_marketplace_is_not_trusted_without_provenance(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            runner = FakeRunner()
            runner.marketplaces["codex"].add("divan")
            runner.plugins["codex"].update(
                f"{package}@divan" for package in HOST_INSTALL.PACKAGES
            )
            before_plugins = set(runner.plugins["codex"])

            with self.assertRaisesRegex(HOST_INSTALL.InstallError, "source/ref"):
                HOST_INSTALL.install(
                    self.options(pathlib.Path(temporary), host="codex"), runner=runner
                )

        self.assertIn("divan", runner.marketplaces["codex"])
        self.assertEqual(runner.plugins["codex"], before_plugins)
        self.assertFalse(
            any(command[1:3] == ("plugin", "remove") for command in runner.commands)
        )

    def test_orphaned_divan_plugins_are_not_trusted_without_provenance(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            runner = FakeRunner()
            runner.marketplaces["codex"].add("personal")
            runner.plugins["codex"].update(
                f"{package}@divan" for package in HOST_INSTALL.PACKAGES
            )
            before_marketplaces = set(runner.marketplaces["codex"])
            before_plugins = set(runner.plugins["codex"])

            with self.assertRaisesRegex(HOST_INSTALL.InstallError, "plugin source/ref"):
                HOST_INSTALL.install(
                    self.options(pathlib.Path(temporary), host="codex"), runner=runner
                )

        self.assertEqual(runner.marketplaces["codex"], before_marketplaces)
        self.assertEqual(runner.plugins["codex"], before_plugins)
        self.assertFalse(
            any(command[1:3] == ("plugin", "add") for command in runner.commands)
        )

    def test_legacy_migration_requires_verified_codex_target(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            runner = FakeRunner()
            with self.assertRaises(HOST_INSTALL.InstallError):
                HOST_INSTALL.install(
                    self.options(
                        pathlib.Path(temporary),
                        host="claude",
                        migrate_legacy=True,
                    ),
                    runner=runner,
                )

        self.assertEqual(runner.commands, [])


if __name__ == "__main__":
    unittest.main()
