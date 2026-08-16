from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest
from dataclasses import replace

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.knowledge_capture import pattern_from_project
from divan_runtime.knowledge_contract import KnowledgeStatus, ObservationOutcome
from divan_runtime.knowledge_relevance import inspect_memory_context, relevant_knowledge
from divan_runtime.knowledge_store import KnowledgeStore


class KnowledgeRelevanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.project = self.root / "wellness-dashboard"
        self.project.mkdir()
        (self.project / "package.json").write_text(
            """{
  "name": "wellness-dashboard",
  "packageManager": "pnpm@11.0.0",
  "scripts": {"build": "vite build", "test": "vitest run"},
  "dependencies": {"react": "19.2.0"},
  "devDependencies": {"vite": "8.0.0"}
}
""",
            encoding="utf-8",
        )
        self.store = KnowledgeStore(self.root / "knowledge.sqlite3")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_existing_engine_inspection_becomes_memory_context(self) -> None:
        context = inspect_memory_context(self.project)

        self.assertEqual(context.inspection["project"], "wellness-dashboard")
        self.assertIn("react", context.inspection["frameworks"])
        self.assertIn("vite", context.inspection["frameworks"])
        self.assertIn("pnpm", context.stack)
        self.assertIn("application", context.tags)
        self.assertTrue(
            any(
                row["command"] == "pnpm run build"
                for row in context.inspection["commands"]
            )
        )

    def test_relevance_prefers_validated_reused_stack_match(self) -> None:
        react_pattern = replace(
            pattern_from_project(
                name="Accessible wellness form",
                summary="Use native labeled inputs and keep form state explicit.",
                stack=("react", "vite", "pnpm"),
                tags=("application", "wellness"),
                observed_at="2026-08-07T20:00:00+00:00",
            ),
            status=KnowledgeStatus.VALIDATED,
        )
        rust_pattern = pattern_from_project(
            name="Rust worker queue",
            summary="Use bounded worker concurrency for background jobs.",
            stack=("rust",),
            tags=("service",),
            observed_at="2026-08-07T20:00:00+00:00",
        )
        self.store.upsert(react_pattern)
        self.store.upsert(rust_pattern)
        for project_id in ("hydration-one", "hydration-two"):
            self.store.observe(
                react_pattern.item_id,
                project_id=project_id,
                outcome=ObservationOutcome.SUCCESS,
                observed_at="2026-08-07T21:00:00+00:00",
            )

        matches = relevant_knowledge(
            self.store,
            inspect_memory_context(self.project),
            intent="build wellness form",
        )

        self.assertEqual(matches[0].item.item_id, react_pattern.item_id)
        self.assertNotIn(
            rust_pattern.item_id,
            [match.item.item_id for match in matches],
        )
        self.assertIn("validated knowledge", matches[0].reasons)
        self.assertIn("reused in 2 projects", matches[0].reasons)
        self.assertEqual(matches[0].observations["success_rate"], 1.0)

    def test_deprecated_memory_is_never_recommended(self) -> None:
        pattern = replace(
            pattern_from_project(
                name="Old React workaround",
                summary="A workaround that no longer applies to the current stack.",
                stack=("react",),
                tags=("application",),
                observed_at="2026-08-07T20:00:00+00:00",
            ),
            status=KnowledgeStatus.DEPRECATED,
        )
        self.store.upsert(pattern)

        matches = relevant_knowledge(
            self.store,
            inspect_memory_context(self.project),
            intent="react application",
        )

        self.assertEqual(matches, ())


if __name__ == "__main__":
    unittest.main()
