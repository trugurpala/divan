from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import goals, seyir_state, status  # noqa: E402


class SeyirStateTests(unittest.TestCase):
    def _goal(self, project: pathlib.Path) -> tuple[str, list[str]]:
        result = goals.start_goal(
            project,
            "Ship a trustworthy local progress view",
            "released",
            True,
            host_profile="codex",
            environment={},
        )
        identifier = str(result["goal_id"])
        route = json.loads(
            (
                project / ".divan" / "specs" / identifier / "route.json"
            ).read_text(encoding="utf-8")
        )
        task_ids = [
            str(item["id"])
            for item in route["execution_plan"]["tasks"]
        ]
        return identifier, task_ids

    def test_started_goal_becomes_the_explicit_active_goal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-seyir-state-") as temporary:
            project = pathlib.Path(temporary)
            identifier, task_ids = self._goal(project)

            value = seyir_state.load(project)

        self.assertEqual(value["active_goal_id"], identifier)
        self.assertEqual(value["completed_task_ids"], [])
        self.assertEqual(value["current_task_id"], task_ids[0])
        self.assertEqual(value["next_task_id"], task_ids[1])
        self.assertRegex(value["receipt_event_hash"], r"^[0-9a-f]{64}$")

    def test_progress_update_drives_the_reader_snapshot(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-seyir-state-") as temporary:
            project = pathlib.Path(temporary)
            identifier, task_ids = self._goal(project)

            planned = seyir_state.update(
                project,
                identifier,
                completed_task_ids=[task_ids[0]],
                current_task_id=task_ids[1],
                next_task_id=task_ids[2],
                execute=False,
            )
            self.assertEqual(planned["status"], "planned")
            unchanged = status.build_snapshot(project, "en")
            self.assertEqual(unchanged["tasks"][0]["status"], "CURRENT")

            applied = seyir_state.update(
                project,
                identifier,
                completed_task_ids=[task_ids[0]],
                current_task_id=task_ids[1],
                next_task_id=task_ids[2],
                execute=True,
            )
            snapshot = status.build_snapshot(project, "en")

        self.assertEqual(applied["status"], "updated")
        self.assertEqual(snapshot["goal"]["id"], identifier)
        self.assertEqual(snapshot["tasks"][0]["status"], "DONE")
        self.assertEqual(snapshot["tasks"][1]["status"], "CURRENT")
        self.assertEqual(snapshot["current"]["task"], snapshot["tasks"][1]["title"])
        self.assertEqual(snapshot["next_action"], snapshot["tasks"][2]["title"])

    def test_unknown_or_completed_current_task_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-seyir-state-") as temporary:
            project = pathlib.Path(temporary)
            identifier, task_ids = self._goal(project)

            with self.assertRaisesRegex(ValueError, "current task"):
                seyir_state.update(
                    project,
                    identifier,
                    completed_task_ids=[task_ids[0]],
                    current_task_id=task_ids[0],
                    next_task_id=task_ids[1],
                    execute=True,
                )
            with self.assertRaisesRegex(ValueError, "unknown task"):
                seyir_state.update(
                    project,
                    identifier,
                    completed_task_ids=[],
                    current_task_id="task-999",
                    next_task_id=None,
                    execute=True,
                )

    def test_goal_advance_is_dry_run_first_and_updates_receipt_phase(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-seyir-state-") as temporary:
            project = pathlib.Path(temporary)
            identifier, _ = self._goal(project)

            planned = goals.advance_goal(
                project, identifier, "specified", execute=False
            )
            before = status.build_snapshot(project, "en")
            advanced = goals.advance_goal(
                project,
                identifier,
                "specified",
                execute=True,
                reason="Design was approved.",
            )
            after = status.build_snapshot(project, "en")

        self.assertEqual(planned["status"], "planned")
        self.assertEqual(before["goal"]["status"], "DISCOVERED")
        self.assertEqual(advanced["status"], "advanced")
        self.assertEqual(after["goal"]["status"], "SPECIFIED")


if __name__ == "__main__":
    unittest.main()
