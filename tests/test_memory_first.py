from __future__ import annotations

import dataclasses
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.desktop_protocol import handle_request
from divan_runtime.knowledge_capture import lesson_from_failure, pattern_from_project
from divan_runtime.knowledge_contract import KnowledgeStatus
from divan_runtime.knowledge_store import KnowledgeStore
from divan_runtime.memory_first import recall
from divan_runtime.project_registry import ProjectRegistry

_SECRET = "sk-abcdef1234567890"


def _git_project(root: pathlib.Path) -> None:
    completed = subprocess.run(
        ["git", "init", str(root)], capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0, completed.stderr
    (root / "README.md").write_text("# Demo\n", encoding="utf-8")


class MemoryRecallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name) / "demo"
        _git_project(self.root)
        self.store = KnowledgeStore(pathlib.Path(self.temp.name) / "knowledge.sqlite3")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _lesson(self, problem: str, solution: str = "Match the import casing."):
        item = lesson_from_failure(
            problem=problem, solution=solution, stack=("Vite",), tags=("build",)
        )
        self.store.upsert(item)
        return item

    def test_recall_is_bounded_and_never_returns_the_whole_book(self) -> None:
        for index in range(40):
            self._lesson(f"Vite build failed in a different way number {index}")

        pack = recall(self.store, self.root, intent="Vite build hatasini duzelt")

        self.assertGreater(pack.considered, len(pack.item_ids))
        self.assertLessEqual(len(pack.incidents), 5)
        self.assertLessEqual(len(pack.item_ids), 15)

    def test_quarantined_and_superseded_claims_are_never_handed_to_a_planner(self) -> None:
        usable = self._lesson("Vite build failed because an import used the wrong case")
        conflicting = self._lesson(
            "Vite build failed because an import used the wrong case",
            solution="Disable case sensitivity instead.",
        )
        self.store.resolve_contradiction(
            existing_id=conflicting.item_id,
            replacement_id=usable.item_id,
            settled=True,
            observed_at="2026-08-16T00:00:00+00:00",
        )

        pack = recall(self.store, self.root, intent="Vite build import casing")

        self.assertIn(usable.item_id, pack.item_ids)
        self.assertNotIn(conflicting.item_id, pack.item_ids)
        self.assertGreaterEqual(pack.withheld_inactive, 1)

    def test_recall_reports_what_memory_could_not_answer(self) -> None:
        self._lesson("Vite build failed because an import used the wrong case")

        pack = recall(self.store, self.root, intent="Vite build import casing")

        # Only lessons exist, so every other class is an honest gap and is the
        # only thing that should trigger fresh research.
        self.assertIn("decisions", pack.gaps)
        self.assertIn("recipes", pack.gaps)
        self.assertNotIn("incidents", pack.gaps)

    def test_recall_read_path_never_exposes_a_secret_or_home_path(self) -> None:
        self._lesson(
            "Build failed at C:/Users/User/Desktop/Projeler/Divan/app.py "
            f"with OPENAI_API_KEY={_SECRET}"
        )
        self.store.upsert(
            pattern_from_project(
                name="Yerel yerlesim",
                summary="Uygulama C:/Users/User/Desktop/Projeler/Divan/apps altinda.",
                stack=("Vite",),
                source_project="C:/Users/User/Desktop/Projeler/Divan",
            )
        )

        pack = recall(self.store, self.root, intent="build")
        blob = repr(pack.to_dict())

        self.assertNotIn(_SECRET, blob)
        self.assertNotIn("C:/Users/User", blob)
        self.assertNotIn("C:\\Users\\User", blob)


class ContradictionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = KnowledgeStore(pathlib.Path(self.temp.name) / "knowledge.sqlite3")
        self.first = lesson_from_failure(
            problem="Use SQLite for local state", solution="Ship a single file store."
        )
        self.second = lesson_from_failure(
            problem="Use Postgres for local state", solution="Run a server."
        )
        self.store.upsert(self.first)
        self.store.upsert(self.second)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_a_settled_contradiction_supersedes_without_deleting(self) -> None:
        old, new = self.store.resolve_contradiction(
            existing_id=self.first.item_id,
            replacement_id=self.second.item_id,
            settled=True,
            observed_at="2026-08-16T00:00:00+00:00",
        )
        self.assertEqual(old.status, KnowledgeStatus.SUPERSEDED)
        self.assertEqual(new.status, KnowledgeStatus.CANDIDATE)
        # The superseded claim is still readable; nothing was silently lost.
        self.assertEqual(self.store.get(self.first.item_id).summary, self.first.summary)

    def test_an_unsettled_contradiction_quarantines_both_sides(self) -> None:
        old, new = self.store.resolve_contradiction(
            existing_id=self.first.item_id,
            replacement_id=self.second.item_id,
            settled=False,
            observed_at="2026-08-16T00:00:00+00:00",
        )
        self.assertEqual(old.status, KnowledgeStatus.QUARANTINED)
        self.assertEqual(new.status, KnowledgeStatus.QUARANTINED)

    def test_an_item_cannot_contradict_itself(self) -> None:
        with self.assertRaises(ValueError):
            self.store.resolve_contradiction(
                existing_id=self.first.item_id,
                replacement_id=self.first.item_id,
                settled=True,
                observed_at="2026-08-16T00:00:00+00:00",
            )


class KnowledgeProtocolSurfaceTests(unittest.TestCase):
    """The projection, recall and observation surfaces must be reachable."""

    def test_book_recall_and_observe_are_registered_and_work(self) -> None:
        with (
            tempfile.TemporaryDirectory() as data_dir,
            tempfile.TemporaryDirectory() as project,
        ):
            root = pathlib.Path(project) / "demo"
            _git_project(root)
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                project_id = ProjectRegistry().register(str(root)).project_id

                book = handle_request({"command": "knowledge.book"})
                recalled = handle_request(
                    {"command": "knowledge.recall", "project_id": project_id, "intent": "build"}
                )

            self.assertTrue(book["ok"], book)
            self.assertEqual(book["result"]["authority"], "projection-only")
            self.assertIn("Divan Knowledge Book", book["result"]["book"])
            self.assertTrue(recalled["ok"], recalled)
            self.assertEqual(recalled["result"]["recalled_item_ids"], [])

    def test_observation_requires_a_complete_evidence_bound_record(self) -> None:
        with tempfile.TemporaryDirectory() as data_dir:
            with patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False):
                response = handle_request(
                    {"command": "knowledge.observe", "item_id": "lesson-1"}
                )
                bad_outcome = handle_request(
                    {
                        "command": "knowledge.observe",
                        "item_id": "lesson-1",
                        "project_id": "p1",
                        "outcome": "maybe",
                        "observed_at": "2026-08-16T00:00:00+00:00",
                    }
                )

            self.assertFalse(response["ok"])
            self.assertEqual(
                response["error"]["code"], "DESKTOP_KNOWLEDGE_OBSERVATION_INCOMPLETE"
            )
            self.assertFalse(bad_outcome["ok"])
            self.assertEqual(
                bad_outcome["error"]["code"], "DESKTOP_KNOWLEDGE_OUTCOME_INVALID"
            )

    def test_a_failed_reuse_is_recorded_and_reuse_is_not_promotion(self) -> None:
        with (
            tempfile.TemporaryDirectory() as data_dir,
            tempfile.TemporaryDirectory() as store_dir,
        ):
            database = pathlib.Path(store_dir) / "knowledge.sqlite3"
            store = KnowledgeStore(database)
            lesson = lesson_from_failure(
                problem="Vite build failed on casing", solution="Match the casing."
            )
            store.upsert(lesson)
            before = store.get(lesson.item_id)

            with (
                patch.dict(os.environ, {"DIVAN_DATA_DIR": data_dir}, clear=False),
                patch(
                    "divan_runtime.knowledge_desktop.knowledge_database",
                    return_value=database,
                ),
            ):
                for outcome in ("success", "failure"):
                    response = handle_request(
                        {
                            "command": "knowledge.observe",
                            "item_id": lesson.item_id,
                            "project_id": "demo",
                            "outcome": outcome,
                            "observed_at": "2026-08-16T00:00:00+00:00",
                        }
                    )
                    self.assertTrue(response["ok"], response)
                    self.assertEqual(
                        response["result"]["promotion_authority"], "not-granted"
                    )

            after = store.get(lesson.item_id)
            # Reuse count is evidence, never automatic promotion.
            self.assertEqual(after.status, before.status)
            self.assertEqual(after.confidence, before.confidence)
            self.assertEqual(
                dataclasses.replace(after, last_verified_at=None),
                dataclasses.replace(before, last_verified_at=None),
            )


if __name__ == "__main__":
    unittest.main()
