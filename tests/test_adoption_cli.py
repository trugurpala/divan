from __future__ import annotations

import contextlib
import io
import pathlib
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import cli, cli_parser  # noqa: E402


def preview_plan() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ready",
        "proof_id": "proof-123456789abc",
        "divan": {
            "version": "0.18.3",
            "ref": "v0.18.3",
            "commit": "a" * 40,
            "distribution": "immutable-release",
            "runner_sha256": "sha256:" + "a" * 64,
        },
        "host_probe": {
            "argv": ("claude", "--version"),
            "status": "planned",
        },
        "operator": {"role": "maintainer"},
        "environment": {"os": "windows", "architecture": "x86_64"},
        "project": {
            "identity_sha256": "sha256:" + "b" * 64,
            "distinct_from_divan": True,
            "distinctness_policy_sha256": "sha256:" + "c" * 64,
            "types": ["application", "monorepo"],
            "workspace_count": 11,
        },
        "goal": {
            "id": "goal-5e033a4d324a",
            "state": "VERIFIED",
            "target": "VERIFIED",
            "receipt_sha256": "sha256:" + "d" * 64,
            "artifact_sha256": ["sha256:" + "e" * 64],
        },
        "checks": [
            {
                "id": "root:test",
                "class": "test",
                "workspace": ".",
                "workspace_sha256": "sha256:" + "b" * 64,
                "runner": "bun",
                "name": "test",
                "argv": ("bun", "run", "test"),
                "argv_sha256": "sha256:" + "c" * 64,
                "timeout_class": "test",
                "timeout_ms": 600000,
                "timeout_policy_sha256": "sha256:" + "d" * 64,
            }
        ],
        "writes": [".divan/adoption/proof-123456789abc/"],
        "plan_digest": "sha256:" + "f" * 64,
        "_private": {"root": pathlib.Path("C:/private/user/project")},
    }


class AdoptionProofCliTests(unittest.TestCase):
    def test_parser_defaults_to_write_free_preview(self) -> None:
        options = cli_parser.build_parser().parse_args(
            [
                "adoption",
                "prove",
                "--project",
                ".",
                "--goal",
                "goal-5e033a4d324a",
                "--host",
                "claude-code",
            ]
        )

        self.assertFalse(options.execute)
        self.assertEqual(options.operator_role, "maintainer")
        self.assertEqual(options.lang, "en")

    def test_preview_never_executes_and_removes_private_context(self) -> None:
        options = cli_parser.build_parser().parse_args(
            [
                "adoption",
                "prove",
                "--project",
                ".",
                "--goal",
                "goal-5e033a4d324a",
                "--host",
                "claude-code",
                "--json",
            ]
        )
        plan = preview_plan()
        with mock.patch.object(
            cli.adoption_proof,
            "build_proof_plan",
            return_value=plan,
        ), mock.patch.object(
            cli.adoption_proof,
            "execute_proof",
            side_effect=AssertionError("preview must not execute"),
        ):
            result = cli._execute(options)

        self.assertEqual(result["kind"], "adoption-proof-preview")
        self.assertEqual(result["status"], "ready")
        self.assertNotIn("_private", result)
        self.assertNotIn("C:/private", str(result))
        self.assertEqual(
            result["host_probe"],
            {"command": ["claude", "--version"], "status": "planned"},
        )
        self.assertTrue(result["next_command"].endswith("--execute"))

    def test_execute_routes_the_same_plan_to_the_executor(self) -> None:
        options = cli_parser.build_parser().parse_args(
            [
                "adoption",
                "prove",
                "--project",
                ".",
                "--goal",
                "goal-5e033a4d324a",
                "--host",
                "claude-code",
                "--execute",
            ]
        )
        executed = {
            "schema_version": 1,
            "status": "passed",
            "proof_id": "proof-123456789abc",
            "receipt_status": "valid-clean-room-adoption",
            "checks_passed": 1,
            "files": [
                ".divan/adoption/proof-123456789abc/adoption-receipt.json"
            ],
        }
        with mock.patch.object(
            cli.adoption_proof,
            "build_proof_plan",
            return_value=preview_plan(),
        ), mock.patch.object(
            cli.adoption_proof,
            "execute_proof",
            return_value=executed,
        ) as execute:
            result = cli._execute(options)

        execute.assert_called_once()
        self.assertEqual(result["kind"], "adoption-proof-result")
        self.assertEqual(result["receipt_status"], "valid-clean-room-adoption")

    def test_human_preview_and_success_are_vibe_coder_friendly(self) -> None:
        preview_options = cli_parser.build_parser().parse_args(
            [
                "adoption",
                "prove",
                "--project",
                ".",
                "--goal",
                "goal-5e033a4d324a",
                "--host",
                "claude-code",
                "--lang",
                "tr",
            ]
        )
        with mock.patch.object(
            cli.adoption_proof,
            "build_proof_plan",
            return_value=preview_plan(),
        ):
            preview = cli._execute(preview_options)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli._write_human(preview, "tr")
        rendered = output.getvalue()
        self.assertIn("Divan neyi kanıtlayacak?", rendered)
        self.assertIn("Çalışacak kontroller", rendered)
        self.assertIn("Henüz hiçbir dosya yazılmadı.", rendered)
        self.assertIn("Başlatmak için:", rendered)
        self.assertNotIn("identity_sha256", rendered)

        success = {
            "kind": "adoption-proof-result",
            "status": "passed",
            "proof_id": "proof-123456789abc",
            "receipt_status": "valid-clean-room-adoption",
            "checks_passed": 5,
            "files": [".divan/adoption/proof-123456789abc/"],
        }
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli._write_human(success, "tr")
        self.assertIn("Temiz-proje kanıtı geçti.", output.getvalue())

    def test_failed_proof_status_returns_nonzero(self) -> None:
        with mock.patch.object(
            cli,
            "_execute",
            return_value={
                "kind": "adoption-proof-result",
                "status": "failed-checks",
                "reason": "check root:test failed",
            },
        ):
            exit_code = cli.main(
                [
                    "adoption",
                    "prove",
                    "--project",
                    ".",
                    "--goal",
                    "goal-5e033a4d324a",
                    "--host",
                    "codex",
                    "--execute",
                    "--json",
                ]
            )
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
