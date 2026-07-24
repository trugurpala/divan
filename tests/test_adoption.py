from __future__ import annotations

import importlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPANY = ROOT / "plugins" / "sadrazam" / "company"
if str(COMPANY) not in sys.path:
    sys.path.insert(0, str(COMPANY))

import goals  # noqa: E402
import project_os  # noqa: E402
import receipts  # noqa: E402

try:
    adoption = importlib.import_module("adoption")
except ModuleNotFoundError:
    adoption = None

SOURCE = {
    "version": "0.16.0",
    "source_repository": "https://github.com/trugurpala/divan",
    "source_ref": "v0.16.0",
    "source_commit": "a" * 40,
}


class AdoptionReceiptTests(unittest.TestCase):
    def require_module(self):
        if adoption is None:
            self.fail("adoption module is not implemented")
        return adoption

    def create_verified_goal(self, project: pathlib.Path) -> str:
        (project / "pyproject.toml").write_text(
            "[project]\nname = \"sample\"\nversion = \"1.0.0\"\n",
            encoding="utf-8",
        )
        with mock.patch.object(
            project_os, "_runtime_source_identity", return_value=SOURCE
        ):
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
        result = goals.start_goal(
            project, "Verify the release", "verified", execute=True
        )
        receipt = project / result["receipt"]
        for state in ("SPECIFIED", "PLANNED", "IMPLEMENTING", "VERIFIED"):
            receipts.append_transition(receipt, state)
        return result["goal_id"]

    def test_export_is_redacted_and_json_markdown_verify(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="Divan User Name adoption "
        ) as temporary:
            project = pathlib.Path(temporary)
            goal_id = self.create_verified_goal(project)
            before = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }
            exported = module.export_adoption(
                project, goal_id, "codex", "5.6.0", "maintainer"
            )
            after = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }
            serialized = exported["json"]
            json_path = project.parent / "redirected-adoption.json"
            markdown_path = project.parent / "redirected-adoption.md"
            json_path.write_text(serialized, encoding="utf-8")
            markdown_path.write_text(exported["markdown"], encoding="utf-8")

            self.assertEqual(before, after)
            self.assertTrue(serialized.endswith("\n"))
            self.assertTrue(exported["markdown"].endswith("\n"))
            self.assertNotIn(str(project), serialized)
            self.assertNotIn("Divan User Name", serialized)
            self.assertNotIn("github.com", serialized)
            self.assertNotIn("plugin", serialized.casefold())
            self.assertEqual(
                module.verify_adoption(json_path)["status"],
                "valid-owner-canary",
            )
            self.assertEqual(
                module.verify_adoption(markdown_path)["status"],
                "valid-owner-canary",
            )

    def test_independent_is_a_declaration_and_tamper_is_invalid(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-adoption-") as temporary:
            project = pathlib.Path(temporary)
            goal_id = self.create_verified_goal(project)
            exported = module.export_adoption(
                project, goal_id, "codex", "5.6.0", "independent"
            )
            path = project.parent / "redirected-independent.json"
            path.write_text(exported["json"], encoding="utf-8")
            self.assertEqual(
                module.verify_adoption(path)["status"],
                "valid-independent-declaration",
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["host"]["version"] = "token=super-secret-value"
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(module.verify_adoption(path)["status"], "invalid")

    def test_recomputed_digest_cannot_hide_schema_or_markdown_privacy_tamper(
        self,
    ) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-adoption-") as temporary:
            project = pathlib.Path(temporary)
            goal_id = self.create_verified_goal(project)
            exported = module.export_adoption(
                project, goal_id, "codex", "5.6.0", "maintainer"
            )
            json_path = project.parent / "redirected-tampered.json"
            markdown_path = project.parent / "redirected-tampered.md"
            json_path.write_text(exported["json"], encoding="utf-8")
            markdown_path.write_text(exported["markdown"], encoding="utf-8")
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            payload["project"]["workspace_count"] = -1
            payload["receipt_digest"] = module._digest(payload)
            json_path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(
                module.verify_adoption(json_path)["status"], "invalid"
            )

            markdown_path.write_text(
                markdown_path.read_text(encoding="utf-8")
                + "\npassword=not-public\n",
                encoding="utf-8",
            )
            self.assertEqual(
                module.verify_adoption(markdown_path)["status"], "invalid"
            )

    def test_export_rejects_unverified_goal_and_unsafe_host_version(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-adoption-") as temporary:
            project = pathlib.Path(temporary)
            goal_id = self.create_verified_goal(project)
            receipt = project / ".divan" / "evidence" / goal_id / "receipt.json"
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            payload["state"] = "IMPLEMENTING"
            receipt.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "verified"):
                module.export_adoption(
                    project, goal_id, "codex", "5.6.0", "maintainer"
                )

        with tempfile.TemporaryDirectory(prefix="divan-adoption-") as temporary:
            project = pathlib.Path(temporary)
            goal_id = self.create_verified_goal(project)
            with self.assertRaisesRegex(ValueError, "host version"):
                module.export_adoption(
                    project,
                    goal_id,
                    "codex",
                    "token=super-secret-value",
                    "maintainer",
                )
