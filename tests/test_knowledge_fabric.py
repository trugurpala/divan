from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.knowledge_capture import lesson_from_failure, pattern_from_project
from divan_runtime.knowledge_contract import (
    KnowledgeItem,
    KnowledgeKind,
    KnowledgeOrigin,
    KnowledgeStatus,
    ObservationOutcome,
)
from divan_runtime.knowledge_projection import render_book
from divan_runtime.knowledge_store import KnowledgeStore


class KnowledgeFabricTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.database = pathlib.Path(self.temp.name) / "knowledge.sqlite3"
        self.store = KnowledgeStore(self.database)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_failure_lesson_is_deterministic_and_searchable(self) -> None:
        lesson = lesson_from_failure(
            problem="Vite build failed because an import used the wrong case.",
            solution="Match the import casing to the file name and keep CI case-sensitive.",
            stack=("React", "Vite"),
            tags=("build", "windows"),
            source_project="project-1",
            observed_at="2026-08-07T20:00:00+00:00",
        )
        same = lesson_from_failure(
            problem="Vite build failed because an import used the wrong case.",
            solution="Match the import casing to the file name and keep CI case-sensitive.",
            stack=("vite", "react"),
            tags=("windows", "build"),
            source_project="project-1",
            observed_at="2026-08-07T20:00:00+00:00",
        )
        self.assertEqual(lesson.item_id, same.item_id)
        self.store.upsert(lesson)

        result = self.store.search("import case", stack=("vite",), tags=("build",))

        self.assertEqual([item.item_id for item in result], [lesson.item_id])
        self.assertEqual(result[0].stack, ("react", "vite"))
        self.assertIn("failure-learning", result[0].tags)

    def test_observations_measure_reuse_without_auto_promoting_memory(self) -> None:
        pattern = pattern_from_project(
            name="Local-first task state",
            summary="Keep task state outside the installer root and persist atomically.",
            stack=("Python", "Tauri"),
            tags=("desktop", "state"),
            source_project="divan",
            observed_at="2026-08-07T20:00:00+00:00",
        )
        self.store.upsert(pattern)
        for project_id, outcome, minute in (
            ("project-a", ObservationOutcome.SUCCESS, "10"),
            ("project-b", ObservationOutcome.SUCCESS, "20"),
            ("project-c", ObservationOutcome.FAILURE, "30"),
        ):
            self.store.observe(
                pattern.item_id,
                project_id=project_id,
                outcome=outcome,
                observed_at=f"2026-08-07T20:{minute}:00+00:00",
            )

        analytics = self.store.analytics()

        self.assertEqual(analytics["observations"], 3)
        self.assertEqual(analytics["reused_items"], 1)
        self.assertAlmostEqual(analytics["success_rate"], 2 / 3)
        self.assertEqual(self.store.get(pattern.item_id).status, KnowledgeStatus.CANDIDATE)

    def test_external_knowledge_requires_provenance(self) -> None:
        with self.assertRaises(ValueError):
            KnowledgeItem(
                item_id="source-example",
                kind=KnowledgeKind.SOURCE,
                title="Example source",
                summary="External source without license.",
                origin=KnowledgeOrigin.EXTERNAL,
                source_url="https://example.test/source",
            )

    def test_book_is_generated_projection_not_authoritative_storage(self) -> None:
        lesson = lesson_from_failure(
            problem="Updater re-queried the feed after the user-visible check.",
            solution="Bind install to the exact pending update candidate.",
            stack=("Tauri", "Rust"),
            tags=("security", "updater"),
            observed_at="2026-08-07T20:00:00+00:00",
        )
        self.store.upsert(lesson)

        book = render_book(self.store)

        self.assertIn("Generated projection from the local Knowledge Fabric", book)
        self.assertIn(lesson.title, book)
        self.assertIn("stack=rust, tauri", book)


if __name__ == "__main__":
    unittest.main()
