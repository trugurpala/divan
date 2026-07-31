from __future__ import annotations

import hashlib
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
            turkish = status.build_snapshot(project, "tr")

        self.assertEqual(applied["status"], "updated")
        self.assertEqual(snapshot["goal"]["id"], identifier)
        self.assertEqual(snapshot["tasks"][0]["status"], "DONE")
        self.assertEqual(snapshot["tasks"][1]["status"], "CURRENT")
        self.assertEqual(snapshot["current"]["task"], snapshot["tasks"][1]["title"])
        self.assertEqual(snapshot["next_action"], snapshot["tasks"][2]["title"])
        self.assertEqual(turkish["tasks"][0]["title"], "ön kontrol")
        self.assertEqual(turkish["current"]["task"], "genel yüzey eşitleme")
        self.assertEqual(turkish["next_action"], "sürekli entegrasyon")
        self.assertEqual(
            [task["id"] for task in turkish["tasks"]],
            [task["id"] for task in snapshot["tasks"]],
        )

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

            planned = seyir_state.advance_goal(
                project, identifier, "specified", execute=False
            )
            before = status.build_snapshot(project, "en")
            advanced = seyir_state.advance_goal(
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

    def test_goal_advance_atomically_binds_new_project_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-seyir-state-") as temporary:
            project = pathlib.Path(temporary)
            identifier, _ = self._goal(project)
            evidence = project / "implementation.py"
            evidence.write_text("RESULT = 'verified'\n", encoding="utf-8")
            relative = "implementation.py"
            expected = hashlib.sha256(evidence.read_bytes()).hexdigest()

            planned = seyir_state.advance_goal(
                project,
                identifier,
                "specified",
                execute=False,
                evidence=[relative],
            )
            before = goals.goal_status(project, identifier)
            advanced = seyir_state.advance_goal(
                project,
                identifier,
                "specified",
                execute=True,
                evidence=[relative],
                reason="Implementation evidence reviewed.",
            )
            after = goals.goal_status(project, identifier)

        self.assertEqual(
            planned["new_artifacts"],
            [{"path": relative, "sha256": expected}],
        )
        self.assertNotIn(relative, before["artifacts"])
        self.assertEqual(advanced["new_artifacts"], planned["new_artifacts"])
        self.assertEqual(after["artifacts"][relative], expected)
        self.assertEqual(after["state"], "SPECIFIED")
        self.assertTrue(after["ok"])

    def test_goal_advance_rejects_unsafe_or_oversized_new_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-seyir-state-") as temporary:
            project = pathlib.Path(temporary)
            identifier, _ = self._goal(project)
            outside = project.parent / f"{project.name}-outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            oversized = project / "oversized.bin"
            oversized.write_bytes(
                b"x" * (seyir_state.MAX_TRANSITION_EVIDENCE_BYTES + 1)
            )
            try:
                cases = [
                    ([str(outside)], "project-relative"),
                    (["../outside.txt"], "project-relative"),
                    (["missing.txt"], "real file"),
                    (["oversized.bin"], "too large"),
                ]
                for evidence, message in cases:
                    with self.subTest(evidence=evidence):
                        with self.assertRaisesRegex(ValueError, message):
                            seyir_state.advance_goal(
                                project,
                                identifier,
                                "specified",
                                execute=True,
                                evidence=evidence,
                            )
            finally:
                outside.unlink(missing_ok=True)

    def test_verified_transition_requires_non_spec_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-seyir-state-") as temporary:
            project = pathlib.Path(temporary)
            identifier, _ = self._goal(project)
            for state in ("specified", "planned", "implementing"):
                seyir_state.advance_goal(
                    project, identifier, state, execute=True
                )
            spec = f".divan/specs/{identifier}/spec.md"

            with self.assertRaisesRegex(ValueError, "verification evidence"):
                seyir_state.advance_goal(
                    project, identifier, "verified", execute=True
                )
            with self.assertRaisesRegex(ValueError, "verification evidence"):
                seyir_state.advance_goal(
                    project,
                    identifier,
                    "verified",
                    execute=True,
                    evidence=[spec],
                )


if __name__ == "__main__":
    unittest.main()
