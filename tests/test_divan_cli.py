import contextlib
import importlib.util
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPANY_CLI = ROOT / "plugins" / "sadrazam" / "company" / "cli.py"
DIVAN_CLI = ROOT / "scripts" / "divan.py"
LEGACY_CLI = ROOT / "scripts" / "kur-hostlar.py"


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortableCompanyCliTests(unittest.TestCase):
    def test_json_output_recursively_redacts_secrets_and_sensitive_keys(self) -> None:
        cli = load_module("divan_company_cli_redaction", COMPANY_CLI)
        output = io.StringIO()
        secret = "xox" + "b-123456789012-123456789012-abcdefghijklmnopqrstuvwx"
        with contextlib.redirect_stdout(output):
            cli._write_json(
                {
                    "status": "blocked",
                    "reason": f"provider returned {secret}",
                    "nested": [{"access_token": "plain-value"}],
                }
            )

        rendered = output.getvalue()
        self.assertNotIn(secret, rendered)
        self.assertNotIn("plain-value", rendered)
        self.assertEqual(
            json.loads(rendered)["nested"][0]["access_token"],
            "[REDACTED_SECRET]",
        )

    def test_release_requires_an_explicit_provider(self) -> None:
        cli = load_module("divan_company_cli_provider", COMPANY_CLI)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            cli._parser().parse_args(
                [
                    "release",
                    "--project",
                    str(ROOT),
                    "--goal",
                    "goal-0123456789ab",
                ]
            )

    def test_inspect_writes_stable_utf8_json(self) -> None:
        cli = load_module("divan_company_cli", COMPANY_CLI)
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "package.json").write_text(
                json.dumps({"dependencies": {"react": "19.1.0"}}),
                encoding="utf-8",
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = cli.main(
                    ["inspect", "--project", str(project), "--json"]
                )

        self.assertEqual(result, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["frameworks"], ["react"])
        self.assertTrue(output.getvalue().endswith("\n"))

    def test_plan_human_output_supports_english_and_turkish(self) -> None:
        cli = load_module("divan_company_cli_locale", COMPANY_CLI)
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            for language, expected in (("en", "Workflow:"), ("tr", "İş akışı:")):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    result = cli.main(
                        [
                            "plan",
                            "--project",
                            str(project),
                            "--intent",
                            "Fix the broken API",
                            "--lang",
                            language,
                        ]
                    )
                self.assertEqual(result, 0)
                self.assertIn(expected, output.getvalue())

    def test_validate_reports_contract_counts(self) -> None:
        cli = load_module("divan_company_cli_validate", COMPANY_CLI)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = cli.main(["validate", "--json"])
        payload = json.loads(output.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "valid")
        self.assertEqual(payload["role_count"], 12)
        self.assertEqual(payload["workflow_count"], 11)


class RepositoryDivanCliTests(unittest.TestCase):
    def test_project_status_is_forwarded_and_read_only(self) -> None:
        cli = load_module("repository_divan_lifecycle_cli", DIVAN_CLI)
        with tempfile.TemporaryDirectory(prefix="divan-cli-status-") as temporary:
            project = pathlib.Path(temporary)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    cli.main(
                        [
                            "init",
                            "--project",
                            str(project),
                            "--host",
                            "agents",
                            "--execute",
                            "--json",
                        ]
                    ),
                    0,
                )
            before = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = cli.main(
                    ["project", "status", "--project", str(project), "--json"]
                )
            after = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }

        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "CURRENT")
        self.assertEqual(before, after)

    def test_project_init_defaults_to_both_hosts_and_dry_run(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-cli-") as temporary:
            project = pathlib.Path(temporary)
            result = subprocess.run(
                [
                    sys.executable,
                    str(DIVAN_CLI),
                    "init",
                    "--project",
                    str(project),
                    "--json",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hosts"], ["agents", "claude"])
            self.assertEqual(payload["status"], "planned")
            self.assertFalse((project / ".divan").exists())
            self.assertTrue(result.stdout.endswith("\n"))

    def test_project_routes_execute_init_and_goal_but_audit_is_read_only(self) -> None:
        cli = load_module("repository_divan_project_cli", DIVAN_CLI)
        with tempfile.TemporaryDirectory(prefix="divan-cli-") as temporary:
            project = pathlib.Path(temporary)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    cli.main(
                        [
                            "init",
                            "--project",
                            str(project),
                            "--host",
                            "agents",
                            "--execute",
                            "--json",
                        ]
                    ),
                    0,
                )
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertFalse((project / "CLAUDE.md").exists())

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    cli.main(
                        [
                            "goal",
                            "start",
                            "--project",
                            str(project),
                            "--intent",
                            "Document API",
                            "--target",
                            "verified",
                            "--json",
                        ]
                    ),
                    0,
                )
            self.assertEqual(json.loads(output.getvalue())["status"], "planned")

            before = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    cli.main(["audit", "--project", str(project), "--json"]), 0
                )
            after = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before, after)

    def test_receipt_verify_route_returns_nonzero_for_invalid_receipt(self) -> None:
        cli = load_module("repository_divan_receipt_cli", DIVAN_CLI)
        with tempfile.TemporaryDirectory(prefix="divan-cli-") as temporary:
            receipt = pathlib.Path(temporary) / "receipt.json"
            receipt.write_text("{}\n", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = cli.main(
                    ["receipt", "verify", str(receipt), "--json"]
                )
            self.assertEqual(result, 1)
            self.assertFalse(json.loads(output.getvalue())["ok"])

    def test_documented_company_options_are_forwarded(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(DIVAN_CLI),
                "plan",
                "--project",
                str(ROOT),
                "--intent",
                "build an API",
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["workflow"], "feature-delivery")

    def test_update_translates_to_existing_host_lifecycle_contract(self) -> None:
        cli = load_module("repository_divan_cli", DIVAN_CLI)
        with mock.patch.object(cli.host_lifecycle, "main", return_value=0) as lifecycle:
            result = cli.main(
                [
                    "update",
                    "--host",
                    "both",
                    "--ref",
                    "v0.14.0",
                    "--execute",
                ]
            )

        self.assertEqual(result, 0)
        lifecycle.assert_called_once_with(
            [
                "--host",
                "both",
                "--source",
                "https://github.com/trugurpala/divan.git",
                "--ref",
                "v0.14.0",
                "--upgrade",
                "--execute",
            ]
        )

    def test_doctor_and_recover_use_english_subcommands(self) -> None:
        cli = load_module("repository_divan_cli_host", DIVAN_CLI)
        with mock.patch.object(cli.host_lifecycle, "main", return_value=0) as lifecycle:
            self.assertEqual(
                cli.main(["doctor", "--ref", "v0.14.0", "--json"]), 0
            )
            self.assertEqual(cli.main(["recover", "transaction.json"]), 0)

        self.assertEqual(
            lifecycle.call_args_list,
            [
                mock.call(
                    [
                        "--host",
                        "both",
                        "--source",
                        "https://github.com/trugurpala/divan.git",
                        "--ref",
                        "v0.14.0",
                        "--doctor",
                        "--json",
                    ]
                ),
                mock.call(["--rollback-transaction", "transaction.json"]),
            ],
        )

    def test_legacy_entrypoint_is_only_a_compatibility_wrapper(self) -> None:
        text = LEGACY_CLI.read_text(encoding="utf-8")
        self.assertIn("from host_lifecycle import", text)
        self.assertIn("deprecated", text.lower())
        self.assertLessEqual(len(text.splitlines()), 20)
