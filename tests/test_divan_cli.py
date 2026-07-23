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
        self.assertEqual(payload["workflow_count"], 8)


class RepositoryDivanCliTests(unittest.TestCase):
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
