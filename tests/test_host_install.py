from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("divan_host_install", ROOT / "scripts" / "kur-hostlar.py")
assert SPEC and SPEC.loader
HOST_INSTALL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOST_INSTALL)


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

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        argv = tuple(command)
        self.commands.append(argv)
        if self.fail_on and self.fail_on == argv:
            return subprocess.CompletedProcess(command, 7, "", "fixture failure")

        host = command[0]
        if command[1:4] == ["plugin", "marketplace", "list"]:
            if host == "claude":
                output = [{"name": name} for name in sorted(self.marketplaces[host])]
            else:
                output = {"marketplaces": [{"name": name} for name in sorted(self.marketplaces[host])]}
            return subprocess.CompletedProcess(command, 0, json.dumps(output), "")
        if command[1:3] == ["plugin", "list"]:
            if host == "claude":
                output = [{"id": plugin} for plugin in sorted(self.plugins[host])]
            else:
                output = {"installed": [{"pluginId": plugin} for plugin in sorted(self.plugins[host])]}
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


class HostInstallTests(unittest.TestCase):
    def options(self, state_dir: pathlib.Path, **changes: object):
        values = {
            "host": "both",
            "source": "trugurpala/divan",
            "ref": "v0.12.0",
            "execute": True,
            "migrate_legacy": False,
            "state_dir": state_dir,
        }
        values.update(changes)
        return HOST_INSTALL.Options(**values)

    def test_dry_run_never_invokes_host_cli(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            runner = FakeRunner()
            record = HOST_INSTALL.install(
                self.options(pathlib.Path(temporary), execute=False), runner=runner
            )

        self.assertEqual(runner.commands, [])
        self.assertEqual(record["status"], "dry-run")
        rendered = "\n".join(" ".join(command) for command in record["planned_commands"])
        self.assertIn("claude plugin marketplace add trugurpala/divan#v0.12.0", rendered)
        self.assertIn("codex plugin marketplace add trugurpala/divan --ref v0.12.0", rendered)

    def test_installs_both_hosts_and_preserves_unrelated_plugins(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-install-") as temporary:
            runner = FakeRunner()
            state_dir = pathlib.Path(temporary)
            record = HOST_INSTALL.install(self.options(state_dir), runner=runner)

            self.assertEqual(record["status"], "verified")
            self.assertTrue(record["transaction_path"].startswith(str(state_dir)))
            self.assertTrue(pathlib.Path(record["transaction_path"]).is_file())
            self.assertIn("unrelated@claude-plugins-official", runner.plugins["claude"])
            self.assertIn("vibe-coder-standard@personal", runner.plugins["codex"])
            for package in HOST_INSTALL.PACKAGES:
                self.assertIn(f"{package}@divan", runner.plugins["claude"])
                self.assertIn(f"{package}@divan", runner.plugins["codex"])

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
