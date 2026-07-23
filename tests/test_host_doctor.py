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
    "divan_host_doctor", ROOT / "scripts" / "host_lifecycle.py"
)
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


class DoctorRunner:
    def __init__(self, unavailable: set[str] | None = None) -> None:
        self.commands: list[tuple[str, ...]] = []
        self.unavailable = unavailable or set()
        self.marketplaces = {"claude": {"divan"}, "codex": {"divan"}}
        self.plugins = {
            host: {f"{package}@divan" for package in PACKAGE_VERSIONS}
            for host in ("claude", "codex")
        }
        self.marketplace_overrides: dict[str, dict[str, object]] = {}
        self.plugin_overrides: dict[str, dict[str, object]] = {}
        self.payload_overrides: dict[tuple[str, str], object] = {}

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        self.commands.append(tuple(command))
        host = command[0]
        if host in self.unavailable:
            return subprocess.CompletedProcess(command, 127, "", f"executable not found: {host}")
        if host == "git":
            if "get-url" in command:
                return subprocess.CompletedProcess(
                    command, 0, "https://github.com/trugurpala/divan.git\n", ""
                )
            if "describe" in command:
                return subprocess.CompletedProcess(command, 0, "v0.12.0\n", "")
            return subprocess.CompletedProcess(command, 0, "a" * 40 + "\n", "")
        if command[1:4] == ["plugin", "marketplace", "list"]:
            return self._marketplace_result(command, host)
        if command[1:3] == ["plugin", "list"]:
            return self._plugin_result(command, host)
        raise AssertionError(f"doctor attempted a mutating command: {command}")

    def _marketplace_result(
        self, command: list[str], host: str
    ) -> subprocess.CompletedProcess[str]:
        rows: list[dict[str, object]] = []
        for name in sorted(self.marketplaces[host]):
            row: dict[str, object] = {"name": name}
            if name == "divan":
                if host == "claude":
                    row.update(
                        {
                            "installLocation": "fixture-divan-root",
                            "url": "https://github.com/trugurpala/divan.git",
                            "ref": "v0.12.0",
                        }
                    )
                else:
                    row.update(
                        {
                            "root": "fixture-divan-root",
                            "marketplaceSource": {
                                "sourceType": "git",
                                "source": "https://github.com/trugurpala/divan.git",
                            },
                        }
                    )
            row.update(self.marketplace_overrides.get(host, {}))
            rows.append(row)
        output = self.payload_overrides.get(
            (host, "marketplaces"), rows if host == "claude" else {"marketplaces": rows}
        )
        return subprocess.CompletedProcess(command, 0, json.dumps(output), "")

    def _plugin_result(
        self, command: list[str], host: str
    ) -> subprocess.CompletedProcess[str]:
        rows = [self._plugin_row(host, plugin) for plugin in sorted(self.plugins[host])]
        output = self.payload_overrides.get(
            (host, "plugins"), rows if host == "claude" else {"installed": rows}
        )
        return subprocess.CompletedProcess(command, 0, json.dumps(output), "")

    def _plugin_row(self, host: str, plugin: str) -> dict[str, object]:
        key = "id" if host == "claude" else "pluginId"
        row: dict[str, object] = {key: plugin, "enabled": True}
        if plugin.endswith("@divan"):
            package = plugin.removesuffix("@divan")
            version = PACKAGE_VERSIONS[package]
            install_path = f"fixture-divan-root/plugins/{package}"
            if host == "claude":
                install_path = (
                    f"fixture-home/.claude/plugins/cache/divan/{package}/{version}"
                )
            row.update(
                {
                    "version": version,
                    "installed": True,
                    "marketplaceName": "divan",
                    "installPath": install_path,
                    "source": {"path": install_path},
                }
            )
            if host == "claude":
                row["scope"] = "user"
        row.update(self.plugin_overrides.get(plugin, {}))
        return row


class HostDoctorTests(unittest.TestCase):
    def options(self, state_dir: pathlib.Path, **changes: object) -> object:
        values = {
            "host": "both",
            "source": "https://github.com/trugurpala/divan.git",
            "ref": "v0.12.0",
            "execute": False,
            "migrate_legacy": False,
            "state_dir": state_dir,
        }
        values.update(changes)
        return HOST_INSTALL.Options(**values)

    def diagnose(self, runner: DoctorRunner, options: object) -> dict[str, object]:
        result = HOST_INSTALL.doctor(options, runner=runner, root=ROOT)
        self.assertEqual(set(result), {"status", "ref", "hosts", "issues", "next_command"})
        self.assertTrue(
            all(
                command[0] == "git"
                or command[1:4] == ("plugin", "marketplace", "list")
                or command[1:3] == ("plugin", "list")
                for command in runner.commands
            ),
            runner.commands,
        )
        return result

    def test_missing_cli_is_unavailable_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-doctor-") as temporary:
            runner = DoctorRunner({"claude"})
            result = self.diagnose(runner, self.options(pathlib.Path(temporary), host="claude"))

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["hosts"]["claude"]["status"], "unavailable")
        self.assertIn("CLI unavailable", result["issues"])

    def test_healthy_pinned_install_reports_no_issues(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-doctor-") as temporary:
            result = self.diagnose(DoctorRunner(), self.options(pathlib.Path(temporary)))

        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["issues"], [])
        self.assertEqual(set(result["hosts"]), {"claude", "codex"})
        self.assertTrue(all(host["status"] == "healthy" for host in result["hosts"].values()))

    def test_healthy_local_source_proves_both_checkout_heads_without_url_comparison(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-doctor-") as temporary:
            source = pathlib.Path(temporary) / "source-checkout"
            source.mkdir()
            options = self.options(
                pathlib.Path(temporary) / "state",
                source=str(source),
                ref="a" * 40,
            )
            result = self.diagnose(DoctorRunner(), options)

        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["issues"], [])

    def test_unexpected_codex_json_shapes_are_attention_not_a_crash(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-doctor-") as temporary:
            runner = DoctorRunner()
            runner.payload_overrides[("codex", "marketplaces")] = []
            runner.payload_overrides[("codex", "plugins")] = []
            result = self.diagnose(runner, self.options(pathlib.Path(temporary), host="codex"))

        self.assertEqual(result["status"], "attention")
        self.assertIn("divan marketplace missing", result["issues"])

    def test_version_drift_needs_attention_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-doctor-") as temporary:
            runner = DoctorRunner()
            runner.plugin_overrides["sadrazam@divan"] = {"version": "0.0.0"}
            result = self.diagnose(runner, self.options(pathlib.Path(temporary), host="claude"))

        self.assertEqual(result["status"], "attention")
        self.assertIn("sadrazam@divan version", result["issues"])

    def test_disabled_package_needs_attention_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-doctor-") as temporary:
            runner = DoctorRunner()
            runner.plugin_overrides["sadrazam@divan"] = {"enabled": False}
            result = self.diagnose(runner, self.options(pathlib.Path(temporary), host="codex"))

        self.assertEqual(result["status"], "attention")
        self.assertIn("sadrazam@divan disabled", result["issues"])

    def test_foreign_marketplace_needs_attention_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-doctor-") as temporary:
            runner = DoctorRunner()
            runner.marketplace_overrides["claude"] = {
                "url": "https://github.com/foreign/divan.git"
            }
            result = self.diagnose(runner, self.options(pathlib.Path(temporary), host="claude"))

        self.assertEqual(result["status"], "attention")
        self.assertIn("marketplace source", result["issues"])

    def test_orphaned_package_needs_attention_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-doctor-") as temporary:
            runner = DoctorRunner()
            runner.marketplaces["codex"].remove("divan")
            result = self.diagnose(runner, self.options(pathlib.Path(temporary), host="codex"))

        self.assertEqual(result["status"], "attention")
        self.assertIn("orphaned packages", result["issues"])

    def test_unfinished_transaction_has_exact_recovery_command_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-doctor-") as temporary:
            state_dir = pathlib.Path(temporary)
            transaction = state_dir / "install-stuck.json"
            transaction.write_text('{"schema": 1, "status": "in-progress"}', encoding="utf-8")
            result = self.diagnose(DoctorRunner(), self.options(state_dir, host="claude"))

        self.assertEqual(result["status"], "attention")
        self.assertIn("unfinished transaction", result["issues"])
        self.assertEqual(
            result["next_command"],
            f"python scripts/divan.py recover {transaction}",
        )

    def test_malformed_or_unreadable_transaction_is_recovery_attention(self) -> None:
        for name, directory in (
            ("install-malformed.json", False),
            ("upgrade-unreadable.json", True),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix="divan-host-doctor-"
            ) as temporary:
                state_dir = pathlib.Path(temporary)
                transaction = state_dir / name
                if directory:
                    transaction.mkdir()
                else:
                    transaction.write_text("{", encoding="utf-8")
                runner = DoctorRunner()

                result = self.diagnose(runner, self.options(state_dir))

                self.assertEqual(result["status"], "attention")
                self.assertTrue(
                    any("transaction journal" in issue for issue in result["issues"])
                )
                self.assertEqual(
                    result["next_command"],
                    subprocess.list2cmdline(
                        [
                            "python",
                            "scripts/divan.py",
                            "recover",
                            str(transaction),
                        ]
                    ),
                )

    def test_json_cli_writes_only_the_doctor_result(self) -> None:
        payload = {
            "status": "healthy",
            "ref": "v0.12.0",
            "hosts": {"claude": {"status": "healthy", "issues": []}},
            "issues": [],
            "next_command": "python scripts/divan.py doctor --host claude --ref v0.12.0",
        }
        output = io.StringIO()
        with mock.patch.object(HOST_INSTALL, "doctor", return_value=payload, create=True):
            with redirect_stdout(output):
                self.assertEqual(
                    HOST_INSTALL.main(["--doctor", "--json", "--host", "claude", "--ref", "v0.12.0"]),
                    0,
                )

        self.assertEqual(json.loads(output.getvalue()), payload)

    def test_human_cli_has_one_line_per_host_and_next_command(self) -> None:
        payload = {
            "status": "attention",
            "ref": "v0.12.0",
            "hosts": {
                "claude": {"status": "healthy", "issues": []},
                "codex": {"status": "attention", "issues": ["sadrazam@divan version"]},
            },
            "issues": ["sadrazam@divan version"],
            "next_command": "python scripts/divan.py install --host codex --ref v0.12.0",
        }
        output = io.StringIO()
        with mock.patch.object(HOST_INSTALL, "doctor", return_value=payload, create=True):
            with redirect_stdout(output):
                self.assertEqual(
                    HOST_INSTALL.main(["--doctor", "--host", "both", "--ref", "v0.12.0"]),
                    0,
                )

        self.assertEqual(
            output.getvalue().splitlines(),
            [
                "claude: healthy",
                "codex: attention - sadrazam@divan version",
                "NEXT: python scripts/divan.py install --host codex --ref v0.12.0",
            ],
        )

    def test_human_cli_prints_an_unfinished_transaction_status(self) -> None:
        payload = {
            "status": "attention",
            "ref": "v0.12.0",
            "hosts": {"claude": {"status": "healthy", "issues": []}},
            "issues": ["unfinished transaction"],
            "next_command": "python scripts/divan.py recover \"C:\\state folder\\run.json\"",
        }
        output = io.StringIO()
        with mock.patch.object(HOST_INSTALL, "doctor", return_value=payload, create=True):
            with redirect_stdout(output):
                self.assertEqual(
                    HOST_INSTALL.main(["--doctor", "--host", "claude", "--ref", "v0.12.0"]),
                    0,
                )

        self.assertEqual(
            output.getvalue().splitlines(),
            [
                "claude: healthy",
                "STATUS: attention - unfinished transaction",
                "NEXT: python scripts/divan.py recover \"C:\\state folder\\run.json\"",
            ],
        )

    def test_unfinished_transaction_quotes_a_path_with_spaces(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-doctor-") as temporary:
            state_dir = pathlib.Path(temporary) / "state folder"
            state_dir.mkdir()
            transaction = state_dir / "install stuck.json"
            transaction.write_text('{"schema": 1, "status": "in-progress"}', encoding="utf-8")
            result = self.diagnose(DoctorRunner(), self.options(state_dir, host="claude"))

        self.assertEqual(
            result["next_command"],
            subprocess.list2cmdline(
                ["python", "scripts/divan.py", "recover", str(transaction)]
            ),
        )

    def test_cli_module_description_is_preserved(self) -> None:
        self.assertIn("Divan", HOST_INSTALL.__doc__ or "")

    def test_json_requires_doctor_mode(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                HOST_INSTALL._parse_options(["--json", "--ref", "v0.12.0"])


if __name__ == "__main__":
    unittest.main()
