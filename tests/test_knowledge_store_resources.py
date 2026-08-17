from __future__ import annotations

import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import knowledge_store as knowledge_store_module
from divan_runtime.knowledge_capture import lesson_from_failure
from divan_runtime.knowledge_contract import ObservationOutcome
from divan_runtime.knowledge_store import KnowledgeStore


class _ConnectionLedger:
    """Wrap sqlite3.connect so every opened connection can be accounted for."""

    def __init__(self) -> None:
        self.opened: list[sqlite3.Connection] = []
        # Bind the real factory now; the patch replaces the module attribute.
        self._connect = sqlite3.connect

    def connect(self, *args, **kwargs) -> sqlite3.Connection:
        connection = self._connect(*args, **kwargs)
        self.opened.append(connection)
        return connection

    def leaked(self) -> list[sqlite3.Connection]:
        leaked: list[sqlite3.Connection] = []
        for connection in self.opened:
            try:
                connection.execute("SELECT 1")
            except sqlite3.ProgrammingError:
                continue  # already closed, which is what we want
            leaked.append(connection)
        return leaked


class KnowledgeStoreResourceTests(unittest.TestCase):
    """The store must not keep SQLite handles open after a call returns.

    sqlite3.Connection.__exit__ only ends the transaction. On Windows an open
    handle keeps the database file locked, so a caller cannot remove its own
    state directory. This is invisible on POSIX, where an open file can still
    be unlinked, so the guard counts connections instead of deleting files.
    """

    def _exercise(self, store: KnowledgeStore) -> None:
        lesson = lesson_from_failure(
            problem="Vite build failed because an import used the wrong case.",
            solution="Match the import casing to the file name.",
            stack=("React", "Vite"),
            tags=("build", "windows"),
        )
        store.upsert(lesson)
        store.get(lesson.item_id)
        store.search("import")
        store.observe(
            lesson.item_id,
            project_id="demo",
            outcome=ObservationOutcome.SUCCESS,
            observed_at="2026-08-16T00:00:00+00:00",
        )
        store.observation_stats(lesson.item_id)
        store.analytics()

    def test_no_sqlite_connection_stays_open_after_a_call(self) -> None:
        ledger = _ConnectionLedger()
        with tempfile.TemporaryDirectory() as directory:
            database = pathlib.Path(directory) / "knowledge.sqlite3"
            with patch.object(
                knowledge_store_module.sqlite3, "connect", ledger.connect
            ):
                self._exercise(KnowledgeStore(database))

            self.assertGreater(len(ledger.opened), 1, "store opened no connections")
            self.assertEqual(
                ledger.leaked(),
                [],
                f"{len(ledger.leaked())} of {len(ledger.opened)} connections stayed open",
            )

    def test_state_directory_can_be_removed_after_use(self) -> None:
        directory = tempfile.TemporaryDirectory()
        database = pathlib.Path(directory.name) / "knowledge.sqlite3"
        self._exercise(KnowledgeStore(database))

        # Fails with WinError 32 on Windows while a handle is still open.
        directory.cleanup()
        self.assertFalse(pathlib.Path(directory.name).exists())


if __name__ == "__main__":
    unittest.main()
