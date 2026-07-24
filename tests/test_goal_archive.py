from __future__ import annotations

import importlib
import json
import os
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
    goal_archive = importlib.import_module("goal_archive")
except ModuleNotFoundError:
    goal_archive = None

SOURCE = {
    "version": "0.16.0",
    "source_repository": "https://github.com/trugurpala/divan",
    "source_ref": "v0.16.0",
    "source_commit": "a" * 40,
}


class GoalArchiveTests(unittest.TestCase):
    def require_module(self):
        if goal_archive is None:
            self.fail("goal_archive module is not implemented")
        return goal_archive

    def create_goal(
        self, project: pathlib.Path, *, verified: bool
    ) -> tuple[str, pathlib.Path]:
        with mock.patch.object(
            project_os, "_runtime_source_identity", return_value=SOURCE
        ):
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
        result = goals.start_goal(
            project, "Publish the API guide", "verified", execute=True
        )
        receipt = project / result["receipt"]
        if verified:
            with mock.patch.object(
                receipts, "_utc_date", return_value="2026-07-24", create=True
            ):
                for state in ("SPECIFIED", "PLANNED", "IMPLEMENTING", "VERIFIED"):
                    receipts.append_transition(receipt, state)
        return result["goal_id"], receipt

    @staticmethod
    def snapshot(project: pathlib.Path) -> dict[str, bytes]:
        return {
            path.relative_to(project).as_posix(): path.read_bytes()
            for path in project.rglob("*")
            if path.is_file()
        }

    @staticmethod
    def downgrade_to_schema_1(receipt: pathlib.Path) -> None:
        value = json.loads(receipt.read_text(encoding="utf-8"))
        value["schema_version"] = 1
        previous_hash = None
        for event in value["events"]:
            event.pop("recorded_on")
            event["previous_hash"] = previous_hash
            event["hash"] = receipts._event_hash(event)
            previous_hash = event["hash"]
        receipts.write_receipt(receipt, value)

    def test_verified_goal_archives_dry_run_first_with_bound_hashes(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-archive-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, _receipt = self.create_goal(project, verified=True)
            before = self.snapshot(project)
            plan = module.build_archive_plan(project, goal_id)
            after_plan = self.snapshot(project)
            result = module.apply_archive_plan(plan)
            destination = (
                project / ".divan" / "archive" / f"2026-07-24-{goal_id}"
            )
            archive = json.loads(
                (destination / "archive.json").read_text(encoding="utf-8")
            )
            source_spec = project / ".divan" / "specs" / goal_id
            source_evidence = project / ".divan" / "evidence" / goal_id

            self.assertEqual(before, after_plan)
            self.assertEqual(plan["status"], "PLANNED")
            self.assertEqual(result["status"], "ARCHIVED")
            self.assertFalse(source_spec.exists())
            self.assertFalse(source_evidence.exists())
            self.assertEqual(archive["goal_id"], goal_id)
            self.assertEqual(archive["terminal_state"], "VERIFIED")
            self.assertTrue((destination / "specs" / "spec.md").is_file())
            self.assertTrue(
                (destination / "evidence" / "receipt.json").is_file()
            )

    def test_archive_destination_uses_terminal_event_not_receipt_mtime(
        self,
    ) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-archive-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt = self.create_goal(project, verified=True)
            first = module.build_archive_plan(project, goal_id)
            os.utime(receipt, (1893456000, 1893456000))  # 2030-01-01 UTC
            second = module.build_archive_plan(project, goal_id)

            self.assertEqual(first["destination"], second["destination"])
            self.assertIn(f"2026-07-24-{goal_id}", first["destination"])

    def test_legacy_receipt_requires_explicit_deterministic_date_authority(
        self,
    ) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-archive-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt = self.create_goal(project, verified=True)
            self.downgrade_to_schema_1(receipt)
            before = self.snapshot(project)

            blocked = module.build_archive_plan(project, goal_id)
            invalid = module.build_archive_plan(
                project, goal_id, "2026-02-30"
            )
            plan = module.build_archive_plan(project, goal_id, "2026-07-23")

            self.assertEqual(blocked["status"], "BLOCKED")
            self.assertIn("--recorded-on", blocked["continuation"])
            self.assertEqual(invalid["status"], "BLOCKED")
            self.assertEqual(plan["status"], "PLANNED")
            self.assertEqual(
                plan["archive"]["date_authority"],
                "declared-legacy-terminal-event",
            )
            self.assertIn(f"2026-07-23-{goal_id}", plan["destination"])
            self.assertEqual(before, self.snapshot(project))

    def test_unfinished_tampered_or_colliding_goal_is_blocked_without_mutation(
        self,
    ) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-archive-") as temporary:
            project = pathlib.Path(temporary)
            unfinished, _ = self.create_goal(project, verified=False)
            before = self.snapshot(project)
            blocked = module.build_archive_plan(project, unfinished)
            self.assertEqual(blocked["status"], "BLOCKED")
            self.assertEqual(before, self.snapshot(project))

        with tempfile.TemporaryDirectory(prefix="divan-archive-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt = self.create_goal(project, verified=True)
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            payload["intent"] = "tampered"
            receipt.write_text(json.dumps(payload), encoding="utf-8")
            before = self.snapshot(project)
            blocked = module.build_archive_plan(project, goal_id)
            self.assertEqual(blocked["status"], "BLOCKED")
            self.assertEqual(before, self.snapshot(project))

        with tempfile.TemporaryDirectory(prefix="divan-archive-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, _ = self.create_goal(project, verified=True)
            plan = module.build_archive_plan(project, goal_id)
            collision = project / plan["destination"]
            collision.mkdir(parents=True)
            before = self.snapshot(project)
            blocked = module.build_archive_plan(project, goal_id)
            self.assertEqual(blocked["status"], "BLOCKED")
            self.assertEqual(before, self.snapshot(project))

    def test_apply_rolls_back_if_source_removal_is_interrupted(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-archive-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, _ = self.create_goal(project, verified=True)
            plan = module.build_archive_plan(project, goal_id)
            before = self.snapshot(project)

            def interrupt(
                root: pathlib.Path,
                entries: list[dict[str, str]],
                _identifier: str,
            ) -> None:
                first = project_os._safe_destination(root, entries[0]["source"])
                first.unlink()
                raise OSError("injected archive interruption")

            with mock.patch.object(
                module, "_remove_known_sources", side_effect=interrupt
            ), self.assertRaisesRegex(OSError, "injected"):
                module.apply_archive_plan(plan)

            self.assertEqual(before, self.snapshot(project))
            self.assertFalse((project / plan["destination"]).exists())

    def test_pending_journal_resumes_after_process_interruption(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-archive-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, _ = self.create_goal(project, verified=True)
            plan = module.build_archive_plan(project, goal_id)
            destination = project / plan["destination"]
            destination.mkdir(parents=True)
            for row in plan["entries"]:
                source = project_os._safe_destination(project, row["source"])
                target = destination / pathlib.PurePosixPath(
                    row["destination"]
                )
                project_os._atomic_replace(target, source.read_bytes())
            project_os._atomic_replace(
                destination / "archive.json",
                module._canonical_bytes(plan["archive"]),
            )
            first_source = project_os._safe_destination(
                project, plan["entries"][0]["source"]
            )
            first_source.unlink()
            module._write_archive_journal(project, plan)

            resumed = module.build_archive_plan(project, goal_id)
            result = module.apply_archive_plan(resumed)

            self.assertEqual(resumed["plan_digest"], plan["plan_digest"])
            self.assertEqual(result["status"], "ARCHIVED")
            self.assertFalse(
                module._archive_journal_path(project, goal_id).exists()
            )
            self.assertFalse(
                (project / ".divan" / "specs" / goal_id).exists()
            )
            self.assertFalse(
                (project / ".divan" / "evidence" / goal_id).exists()
            )
