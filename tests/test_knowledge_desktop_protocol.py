from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.desktop_protocol import handle_request
from divan_runtime.desktop_state import knowledge_database
from divan_runtime.knowledge_capture import pattern_from_project
from divan_runtime.knowledge_contract import KnowledgeStatus, ObservationOutcome
from divan_runtime.knowledge_store import KnowledgeStore


class KnowledgeDesktopProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.project = self.root / "hydration-app"
        self.project.mkdir()
        self.package = self.project / "package.json"
        self.package.write_text(
            """{
  "name": "hydration-app",
  "packageManager": "pnpm@11.0.0",
  "scripts": {"build": "vite build"},
  "dependencies": {"react": "19.2.0"},
  "devDependencies": {"vite": "8.0.0"}
}
""",
            encoding="utf-8",
        )
        self.environment = patch.dict(
            os.environ,
            {"DIVAN_DATA_DIR": str(self.root / "divan-state")},
            clear=False,
        )
        self.environment.start()
        pattern = replace(
            pattern_from_project(
                name="Hydration form baseline",
                summary="Use labeled native inputs and explicit daily persistence boundaries.",
                stack=("react", "vite", "pnpm"),
                tags=("application", "wellness"),
                observed_at="2026-08-07T20:00:00+00:00",
            ),
            status=KnowledgeStatus.VALIDATED,
        )
        store = KnowledgeStore(knowledge_database())
        store.upsert(pattern)
        store.observe(
            pattern.item_id,
            project_id="wellness-one",
            outcome=ObservationOutcome.SUCCESS,
            observed_at="2026-08-07T21:00:00+00:00",
        )
        self.pattern = pattern

    def tearDown(self) -> None:
        self.environment.stop()
        self.temp.cleanup()

    def test_project_memory_inspects_locally_and_returns_relevant_history(self) -> None:
        before = self.package.read_bytes()

        response = handle_request(
            {
                "command": "knowledge.project",
                "project_root": str(self.project),
                "intent": "build hydration form",
            }
        )

        self.assertTrue(response["ok"], response)
        result = response["result"]
        self.assertEqual(result["inspection"]["project"], "hydration-app")
        self.assertIn("react", result["inspection"]["frameworks"])
        self.assertEqual(result["matches"][0]["item"]["item_id"], self.pattern.item_id)
        self.assertEqual(result["matches"][0]["observations"]["success_rate"], 1.0)
        self.assertEqual(before, self.package.read_bytes())

    def test_search_and_analytics_are_read_only(self) -> None:
        search = handle_request({"command": "knowledge.search", "query": "hydration"})
        analytics = handle_request({"command": "knowledge.analytics"})

        self.assertTrue(search["ok"], search)
        self.assertEqual(search["result"]["items"][0]["item_id"], self.pattern.item_id)
        self.assertTrue(analytics["ok"], analytics)
        self.assertEqual(analytics["result"]["analytics"]["items"], 1)
        self.assertEqual(analytics["result"]["analytics"]["observations"], 1)

    def test_project_memory_requires_explicit_project(self) -> None:
        response = handle_request({"command": "knowledge.project"})

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "DESKTOP_PROJECT_ROOT_REQUIRED")


if __name__ == "__main__":
    unittest.main()
