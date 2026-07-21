from __future__ import annotations

import importlib.util
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "divan_host_upgrade", ROOT / "scripts" / "kur-hostlar.py"
)
assert SPEC and SPEC.loader
HOSTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOSTS)

TARGET_VERSIONS = {
    "sadrazam": "0.9.1",
    "core-pack": "0.5.1",
    "ui-pack": "0.1.0",
    "react-pack": "0.2.1",
    "zanaat-pack": "0.1.1",
}
SOURCE = "https://github.com/trugurpala/divan.git"
OLD_REF = "v0.12.0"
TARGET_REF = "v0.13.0"


def _write_catalog(root: pathlib.Path, versions: dict[str, str]) -> None:
    path = root / ".agents" / "plugins" / "marketplace.json"
    path.parent.mkdir(parents=True)
    plugins = [
        {
            "name": package,
            "version": version,
            "source": {"source": "local", "path": f"./plugins/{package}"},
        }
        for package, version in versions.items()
    ]
    path.write_text(json.dumps({"name": "divan", "plugins": plugins}), encoding="utf-8")


class UpgradeRunner:
    def __init__(
        self,
        fixture_root: pathlib.Path,
        *,
        old_versions: dict[str, dict[str, str]] | None = None,
        current_ref: str = OLD_REF,
    ) -> None:
        self.commands: list[tuple[str, ...]] = []
        self.mutations: list[tuple[str, ...]] = []
        self.journaled_mutations: list[tuple[str, ...]] = []
        self.state_dir = fixture_root / "state"
        defaults = {host: dict(TARGET_VERSIONS) for host in ("claude", "codex")}
        self.old_versions = old_versions or defaults
        self.old_roots = {
            "claude": fixture_root / "old-home" / ".claude" / "plugins" / "marketplaces" / "divan",
            "codex": fixture_root / "old-codex",
        }
        self.target_roots = {
            "claude": fixture_root / "target-home" / ".claude" / "plugins" / "marketplaces" / "divan",
            "codex": ROOT,
        }
        for host, root in self.old_roots.items():
            _write_catalog(root, self.old_versions[host])
        target_catalog = (ROOT / ".agents" / "plugins" / "marketplace.json").read_bytes()
        for root in self.target_roots.values():
            if root == ROOT:
                continue
            path = root / ".agents" / "plugins" / "marketplace.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(target_catalog)
        if current_ref == TARGET_REF:
            for root in self.old_roots.values():
                path = root / ".agents" / "plugins" / "marketplace.json"
                path.write_bytes(target_catalog)
        self.refs = {host: current_ref for host in ("claude", "codex")}
        self.sources = {host: SOURCE for host in ("claude", "codex")}
        self.roots = dict(self.old_roots)
        self.plugins = {
            host: {
                **{
                    f"{package}@divan": version
                    for package, version in self.old_versions[host].items()
                },
                f"unrelated@{host}": "9.9.9",
            }
            for host in ("claude", "codex")
        }
        self.plugin_overrides: dict[tuple[str, str], dict[str, object]] = {}
        self.fail_on: tuple[str, ...] | None = None
        self.interrupt_after: tuple[str, ...] | None = None
        self.interrupt_once = False

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        argv = tuple(command)
        self.commands.append(argv)
        if command[0] == "git":
            return self._git(command)
        if command[1:4] == ["plugin", "marketplace", "list"]:
            return self._marketplace_list(command)
        if command[1:3] == ["plugin", "list"]:
            return self._plugin_list(command)
        self._observe_journal(argv)
        self.mutations.append(argv)
        if self.fail_on == argv:
            self.fail_on = None
            return subprocess.CompletedProcess(command, 7, "", "fixture failure")
        self._mutate(command)
        if self.interrupt_after == argv and not self.interrupt_once:
            self.interrupt_once = True
            raise KeyboardInterrupt
        return subprocess.CompletedProcess(command, 0, "{}", "")

    def _git(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        root = pathlib.Path(command[2])
        host = next((name for name, value in self.roots.items() if value == root), None)
        source = SOURCE if root == ROOT else self.sources[host or "claude"]
        ref = TARGET_REF if root == ROOT else self.refs[host or "claude"]
        if "status" in command:
            output = ""
        elif "get-url" in command:
            output = source
        elif "describe" in command or "tag" in command:
            output = ref
        else:
            output = "a" * 40
        return subprocess.CompletedProcess(command, 0, output + "\n", "")

    def _marketplace_list(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        host = command[0]
        row = self._marketplace_row(host)
        unrelated = {"name": f"community-{host}", "url": "https://example.invalid/community"}
        rows = [unrelated, row] if row else [unrelated]
        output: object = rows if host == "claude" else {"marketplaces": rows}
        return subprocess.CompletedProcess(command, 0, json.dumps(output), "")

    def _marketplace_row(self, host: str) -> dict[str, object] | None:
        if host not in self.refs:
            return None
        row: dict[str, object] = {"name": "divan"}
        if host == "claude":
            row.update({
                "installLocation": str(self.roots[host]),
                "url": self.sources[host],
                "ref": self.refs[host],
            })
        else:
            row.update(
                {
                    "root": str(self.roots[host]),
                    "marketplaceSource": {
                        "sourceType": "git",
                        "source": self.sources[host],
                    },
                }
            )
        return row

    def _plugin_list(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        host = command[0]
        rows = [self._plugin_row(host, selector) for selector in sorted(self.plugins[host])]
        output: object = rows if host == "claude" else {"installed": rows}
        return subprocess.CompletedProcess(command, 0, json.dumps(output), "")

    def _plugin_row(self, host: str, selector: str) -> dict[str, object]:
        key = "id" if host == "claude" else "pluginId"
        row: dict[str, object] = {
            key: selector,
            "version": self.plugins[host][selector],
            "enabled": True,
        }
        if selector.endswith("@divan"):
            package = selector.removesuffix("@divan")
            install_path = self.roots[host] / "plugins" / package
            if host == "claude":
                install_path = (
                    self.roots[host].parent.parent
                    / "cache"
                    / "divan"
                    / package
                    / self.plugins[host][selector]
                )
                row["scope"] = "user"
            row.update(
                {
                    "installed": True,
                    "marketplaceName": "divan",
                    "installPath": str(install_path),
                    "source": {"path": str(install_path)},
                    "skills": sorted(
                        path.parent.name
                        for path in (ROOT / "plugins" / package / "skills").glob("*/SKILL.md")
                    ),
                }
            )
        row.update(self.plugin_overrides.get((host, selector), {}))
        return row

    def _observe_journal(self, argv: tuple[str, ...]) -> None:
        journals = list(self.state_dir.glob("upgrade-*.json"))
        if not journals:
            return
        record = json.loads(journals[0].read_text(encoding="utf-8"))
        if isinstance(record.get("pending"), dict) or isinstance(
            record.get("recovery_pending"), dict
        ):
            self.journaled_mutations.append(argv)

    def _mutate(self, command: list[str]) -> None:
        host = command[0]
        if command[1:4] == ["plugin", "marketplace", "remove"]:
            self.refs.pop(host, None)
            self.sources.pop(host, None)
            self.roots.pop(host, None)
        elif command[1:4] == ["plugin", "marketplace", "add"]:
            self._add_marketplace(command)
        elif command[1:3] in (["plugin", "uninstall"], ["plugin", "remove"]):
            self.plugins[host].pop(command[3], None)
        elif command[1:3] in (["plugin", "install"], ["plugin", "add"]):
            package = command[3].removesuffix("@divan")
            versions = TARGET_VERSIONS if self.refs[host] == TARGET_REF else self.old_versions[host]
            self.plugins[host][command[3]] = versions[package]

    def _add_marketplace(self, command: list[str]) -> None:
        host = command[0]
        if host == "claude":
            source, ref = command[4].rsplit("#", 1)
        else:
            source = command[4]
            ref = command[command.index("--ref") + 1]
        self.sources[host], self.refs[host] = source, ref
        self.roots[host] = self.target_roots[host] if ref == TARGET_REF else self.old_roots[host]


class HostUpgradeTests(unittest.TestCase):
    def test_real_codex_marketplace_without_ref_captures_checkout_identity(self) -> None:
        fixture = json.loads(
            (ROOT / "tests" / "fixtures" / "host-cli" / "codex-marketplace-list.json")
            .read_text(encoding="utf-8")
        )
        self.assertNotIn(
            "ref", HOSTS._host_adapters.marketplace_rows("codex", fixture)["divan"]
        )
        with tempfile.TemporaryDirectory(prefix="divan-upgrade-real-codex-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary))
            marketplace = fixture["marketplaces"][0]
            marketplace["root"] = str(runner.roots["codex"])
            plugins = json.loads(
                (ROOT / "tests" / "fixtures" / "host-cli" / "codex-plugin-list.json")
                .read_text(encoding="utf-8")
            )
            for row in plugins["installed"]:
                package = row["pluginId"].removesuffix("@divan")
                row["source"]["path"] = str(runner.roots["codex"] / "plugins" / package)
            io = HOSTS._host_upgrade.UpgradeIO(
                marketplace_rows=lambda _host: HOSTS._host_adapters.marketplace_rows(
                    "codex", fixture
                ),
                plugin_rows=lambda _host: HOSTS._host_adapters.plugin_rows(
                    "codex", plugins
                ),
                run=lambda command: HOSTS._run(runner, command),
                rollback=lambda _path: {},
                normalize_source=HOSTS._normalize_source,
            )

            captured = HOSTS._host_upgrade._capture_before("codex", SOURCE, io)

        self.assertEqual(captured["ref"], OLD_REF)
        self.assertEqual(captured["commit"], "a" * 40)
        self.assertEqual(runner.mutations, [])

    def options(self, state_dir: pathlib.Path, **changes: object) -> object:
        values = {
            "host": "both",
            "source": SOURCE,
            "ref": TARGET_REF,
            "execute": True,
            "migrate_legacy": False,
            "state_dir": state_dir,
            "upgrade": True,
        }
        values.update(changes)
        return HOSTS.Options(**values)

    def test_upgrade_is_dry_run_by_default_and_prints_exact_replace_plan(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-upgrade-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary))
            record = HOSTS.upgrade(
                self.options(runner.state_dir, execute=False), runner=runner, root=ROOT
            )

        self.assertEqual(record["schema"], 2)
        self.assertEqual(record["operation"], "upgrade")
        self.assertEqual(record["status"], "dry-run")
        self.assertEqual(runner.commands, [])
        self.assertIn(
            ["claude", "plugin", "uninstall", "sadrazam@divan", "--scope", "user", "--yes"],
            record["planned_commands"],
        )

    def test_same_source_ref_and_versions_are_a_no_op(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-upgrade-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary), current_ref=TARGET_REF)
            runner.roots = dict(runner.target_roots)
            record = HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

        self.assertEqual(record["status"], "no-op")
        self.assertEqual(runner.mutations, [])
        self.assertFalse(runner.state_dir.exists())

    def test_dual_host_success_is_schema_2_and_journals_every_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-upgrade-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary))
            record = HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

        self.assertEqual(record["status"], "verified")
        self.assertEqual(record["operation"], "upgrade")
        self.assertEqual(set(record["before_rows"]), {"claude", "codex"})
        self.assertEqual(set(record["verified"]), {"claude", "codex"})
        self.assertEqual(runner.journaled_mutations, runner.mutations)
        self.assertTrue(all(runner.refs[host] == TARGET_REF for host in runner.refs))
        self.assertIn("unrelated@claude", runner.plugins["claude"])
        self.assertIn("unrelated@codex", runner.plugins["codex"])

    def test_foreign_source_is_refused_before_journal_or_external_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-upgrade-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary))
            runner.sources["codex"] = "https://github.com/foreign/divan.git"
            with self.assertRaisesRegex(HOSTS.InstallError, "source"):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)

        self.assertEqual(runner.mutations, [])
        self.assertFalse(runner.state_dir.exists())

    def test_one_host_failure_restores_both_prior_versions_and_unrelated_rows(self) -> None:
        shared_versions = {
            package: f"1.0.{index}" for index, package in enumerate(TARGET_VERSIONS)
        }
        old_versions = {host: dict(shared_versions) for host in ("claude", "codex")}
        failure = ("codex", "plugin", "add", "ui-pack@divan", "--json")
        with tempfile.TemporaryDirectory(prefix="divan-host-upgrade-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary), old_versions=old_versions)
            runner.fail_on = failure
            with self.assertRaises(HOSTS.InstallError):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
            journal = json.loads(next(runner.state_dir.glob("upgrade-*.json")).read_text("utf-8"))

        self.assertEqual(journal["status"], "rolled-back")
        self.assertEqual(journal["rollback_errors"], [])
        self.assertEqual(runner.refs, {"claude": OLD_REF, "codex": OLD_REF})
        for host, versions in old_versions.items():
            self.assertEqual(
                {selector.removesuffix("@divan"): version for selector, version in runner.plugins[host].items() if selector.endswith("@divan")},
                versions,
            )
            self.assertIn(f"unrelated@{host}", runner.plugins[host])

    def test_interrupt_after_external_success_is_rolled_back_from_pending_marker(self) -> None:
        interrupted = ("codex", "plugin", "add", "sadrazam@divan", "--json")
        with tempfile.TemporaryDirectory(prefix="divan-host-upgrade-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary))
            runner.interrupt_after = interrupted
            with self.assertRaises(HOSTS.InstallError):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
            journal = json.loads(next(runner.state_dir.glob("upgrade-*.json")).read_text("utf-8"))

        self.assertEqual(journal["status"], "rolled-back")
        self.assertEqual(runner.refs, {"claude": OLD_REF, "codex": OLD_REF})
        self.assertTrue(all(len(rows) == 6 for rows in runner.plugins.values()))

    def test_recovery_resumes_after_a_second_interruption(self) -> None:
        failure = ("codex", "plugin", "add", "ui-pack@divan", "--json")
        recovery_interrupt = (
            "codex",
            "plugin",
            "marketplace",
            "add",
            SOURCE,
            "--ref",
            OLD_REF,
            "--json",
        )
        with tempfile.TemporaryDirectory(prefix="divan-host-upgrade-") as temporary:
            runner = UpgradeRunner(pathlib.Path(temporary))
            runner.fail_on = failure
            runner.interrupt_after = recovery_interrupt
            with self.assertRaises(HOSTS.InstallError):
                HOSTS.upgrade(self.options(runner.state_dir), runner=runner, root=ROOT)
            journal_path = next(runner.state_dir.glob("upgrade-*.json"))
            first = json.loads(journal_path.read_text("utf-8"))
            self.assertEqual(first["status"], "rollback-incomplete")
            self.assertIn("--rollback-transaction", first["recovery_command"])

            runner.fail_on = None
            runner.interrupt_once = False
            runner.interrupt_after = ("codex", "plugin", "add", "sadrazam@divan", "--json")
            with self.assertRaises(KeyboardInterrupt):
                HOSTS.rollback_transaction(journal_path, runner=runner)
            second = json.loads(journal_path.read_text("utf-8"))
            self.assertEqual(second["status"], "rollback-incomplete")

            runner.interrupt_after = None
            recovered = HOSTS.rollback_transaction(journal_path, runner=runner)

        self.assertEqual(recovered["status"], "recovered")
        self.assertEqual(runner.refs, {"claude": OLD_REF, "codex": OLD_REF})
        self.assertTrue(all(len(rows) == 6 for rows in runner.plugins.values()))

    def test_upgrade_cli_is_dry_run_by_default_and_can_combine_with_execute(self) -> None:
        preview = HOSTS._parse_options(["--upgrade", "--ref", TARGET_REF])
        execute = HOSTS._parse_options(
            ["--upgrade", "--execute", "--host", "codex", "--ref", TARGET_REF]
        )

        self.assertTrue(preview.upgrade)
        self.assertFalse(preview.execute)
        self.assertTrue(execute.upgrade)
        self.assertTrue(execute.execute)

    def test_upgrade_and_doctor_are_mutually_exclusive(self) -> None:
        errors = io.StringIO()
        with redirect_stderr(errors):
            with self.assertRaises(SystemExit):
                HOSTS._parse_options(["--upgrade", "--doctor", "--ref", TARGET_REF])
        self.assertIn("not allowed with argument", errors.getvalue())

    def test_main_dispatches_upgrade_and_prints_dry_run_plan(self) -> None:
        payload = {
            "schema": 2,
            "operation": "upgrade",
            "status": "dry-run",
            "planned_commands": [["codex", "plugin", "marketplace", "remove", "divan", "--json"]],
        }
        output = io.StringIO()
        with mock.patch.object(HOSTS, "upgrade", return_value=payload) as called:
            with redirect_stdout(output):
                result = HOSTS.main(["--upgrade", "--host", "codex", "--ref", TARGET_REF])

        self.assertEqual(result, 0)
        self.assertTrue(called.call_args.args[0].upgrade)
        self.assertIn("DRY-RUN", output.getvalue())

    def test_main_prints_no_op_without_requiring_a_transaction_path(self) -> None:
        payload = {
            "schema": 2,
            "operation": "upgrade",
            "status": "no-op",
            "planned_commands": [],
        }
        output = io.StringIO()
        with mock.patch.object(HOSTS, "upgrade", return_value=payload):
            with redirect_stdout(output):
                result = HOSTS.main(["--upgrade", "--ref", TARGET_REF])

        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue().strip(), "NO-OP - installed Divan already matches target.")


if __name__ == "__main__":
    unittest.main()
