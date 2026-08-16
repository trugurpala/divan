from __future__ import annotations

import dataclasses
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.knowledge_capture import lesson_from_failure, pattern_from_project
from divan_runtime.knowledge_contract import KnowledgeStatus
from divan_runtime.knowledge_store import KnowledgeStore

_SECRET = "sk-abcdef1234567890"
_FAILURE = dict(
    problem=(
        "Build failed at C:/Users/User/Desktop/Projeler/Divan/app.py "
        f"with OPENAI_API_KEY={_SECRET}"
    ),
    solution="Rotate the key and read it from the environment.",
    stack=("Python",),
    tags=("build",),
)


class KnowledgeCaptureRedactionTests(unittest.TestCase):
    """Captured failure text is operator output; it carries paths and secrets.

    Every other persistence path in the runtime redacts before writing, so
    knowledge capture must too, or the memory store becomes the one place a
    credential survives.
    """

    def test_failure_lessons_do_not_persist_secrets_or_home_paths(self) -> None:
        lesson = lesson_from_failure(
            **_FAILURE,
            source_project="C:/Users/User/Desktop/Projeler/Divan",
        )
        blob = f"{lesson.title}\n{lesson.summary}\n{lesson.source_project}"

        self.assertNotIn(_SECRET, blob)
        self.assertNotIn("C:/Users/User", blob)
        self.assertNotIn("C:\\Users\\User", blob)
        self.assertIn("[REDACTED_SECRET]", lesson.summary)

    def test_project_patterns_do_not_persist_home_paths(self) -> None:
        pattern = pattern_from_project(
            name="Vite build layout",
            summary="Kept the app under C:/Users/User/Desktop/Projeler/Divan/apps.",
            stack=("Vite",),
            source_project="C:/Users/User/Desktop/Projeler/Divan",
        )
        blob = f"{pattern.title}\n{pattern.summary}\n{pattern.source_project}"

        self.assertNotIn("C:/Users/User", blob)
        self.assertNotIn("C:\\Users\\User", blob)

    def test_lesson_identity_survives_a_different_home_path(self) -> None:
        # Redacting before the digest keeps one lesson addressable across
        # machines instead of forking per operator home directory.
        first = lesson_from_failure(
            problem="Build failed at C:/Users/alice/proj/app.py",
            solution="Match the import casing.",
        )
        second = lesson_from_failure(
            problem="Build failed at C:/Users/bob/proj/app.py",
            solution="Match the import casing.",
        )
        self.assertEqual(first.item_id, second.item_id)


class KnowledgeCurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = KnowledgeStore(pathlib.Path(self.temp.name) / "knowledge.sqlite3")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_recapturing_a_known_failure_does_not_undo_curation(self) -> None:
        lesson = lesson_from_failure(**_FAILURE)
        self.store.upsert(lesson)
        first_seen = self.store.get(lesson.item_id).created_at
        self.store.curate(
            lesson.item_id,
            status=KnowledgeStatus.VALIDATED,
            confidence=0.95,
            last_verified_at="2026-01-01T00:00:00+00:00",
        )

        # Capture always emits candidate / 0.5 / a fresh created_at.
        recaptured = lesson_from_failure(**_FAILURE)
        self.assertEqual(recaptured.item_id, lesson.item_id)
        self.assertEqual(recaptured.status, KnowledgeStatus.CANDIDATE)
        self.store.upsert(recaptured)

        stored = self.store.get(lesson.item_id)
        self.assertEqual(stored.status, KnowledgeStatus.VALIDATED)
        self.assertEqual(stored.confidence, 0.95)
        self.assertEqual(stored.created_at, first_seen)
        self.assertEqual(stored.last_verified_at, "2026-01-01T00:00:00+00:00")

    def test_recapture_still_refreshes_the_content(self) -> None:
        lesson = lesson_from_failure(**_FAILURE)
        self.store.upsert(lesson)
        refreshed = dataclasses.replace(
            self.store.get(lesson.item_id), title="Lesson: rotated credential"
        )
        self.store.upsert(refreshed)

        self.assertEqual(self.store.get(lesson.item_id).title, "Lesson: rotated credential")


if __name__ == "__main__":
    unittest.main()
