from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .knowledge_contract import (
    KnowledgeItem,
    KnowledgeKind,
    KnowledgeOrigin,
    KnowledgeStatus,
    ObservationOutcome,
    validate_optional_sha256,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge_items (
    item_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    stack_json TEXT NOT NULL,
    origin TEXT NOT NULL,
    status TEXT NOT NULL,
    source_project TEXT,
    source_url TEXT,
    source_license TEXT,
    source_sha256 TEXT,
    problem_signature TEXT,
    solution_signature TEXT,
    evidence_sha256 TEXT,
    confidence REAL NOT NULL,
    created_at TEXT NOT NULL,
    last_verified_at TEXT
);
CREATE TABLE IF NOT EXISTS knowledge_observations (
    observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL REFERENCES knowledge_items(item_id) ON DELETE CASCADE,
    project_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    evidence_sha256 TEXT,
    note TEXT NOT NULL DEFAULT '',
    observed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_knowledge_kind ON knowledge_items(kind);
CREATE INDEX IF NOT EXISTS idx_knowledge_observation_item
    ON knowledge_observations(item_id);
"""


class KnowledgeStore:
    def __init__(self, database: Path | str) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def upsert(self, item: KnowledgeItem) -> None:
        values = _item_values(item)
        placeholders = ", ".join("?" for _ in values)
        columns = ", ".join(values)
        updates = ", ".join(
            f"{column}=excluded.{column}" for column in values if column != "item_id"
        )
        with self._connect() as connection:
            connection.execute(
                f"INSERT INTO knowledge_items ({columns}) VALUES ({placeholders}) "
                f"ON CONFLICT(item_id) DO UPDATE SET {updates}",
                tuple(values.values()),
            )

    def get(self, item_id: str) -> KnowledgeItem:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM knowledge_items WHERE item_id = ?",
                (item_id,),
            ).fetchone()
        if row is None:
            raise KeyError(item_id)
        return _row_to_item(row)

    def search(
        self,
        query: str = "",
        *,
        kind: KnowledgeKind | None = None,
        tags: Iterable[str] = (),
        stack: Iterable[str] = (),
        limit: int = 20,
    ) -> tuple[KnowledgeItem, ...]:
        requested_tags = {value.strip().casefold() for value in tags if value.strip()}
        requested_stack = {value.strip().casefold() for value in stack if value.strip()}
        terms = tuple(part.casefold() for part in query.split() if part.strip())
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM knowledge_items").fetchall()
        scored: list[tuple[float, KnowledgeItem]] = []
        for row in rows:
            item = _row_to_item(row)
            score = _match_score(item, terms, kind, requested_tags, requested_stack)
            if score is not None:
                scored.append((score, item))
        scored.sort(key=lambda pair: (-pair[0], pair[1].item_id))
        return tuple(item for _, item in scored[: max(0, limit)])

    def observe(
        self,
        item_id: str,
        *,
        project_id: str,
        outcome: ObservationOutcome,
        observed_at: str,
        evidence_sha256: str | None = None,
        note: str = "",
    ) -> None:
        project = project_id.strip()
        if not project:
            raise ValueError("knowledge observation project_id is required")
        validate_optional_sha256(evidence_sha256, field="observation evidence_sha256")
        self.get(item_id)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO knowledge_observations
                    (item_id, project_id, outcome, evidence_sha256, note, observed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    project,
                    outcome.value,
                    evidence_sha256,
                    note.strip()[:1000],
                    observed_at,
                ),
            )

    def analytics(self) -> dict[str, Any]:
        with self._connect() as connection:
            item_rows = connection.execute("SELECT * FROM knowledge_items").fetchall()
            observations = connection.execute(
                "SELECT item_id, project_id, outcome FROM knowledge_observations"
            ).fetchall()
        items = [_row_to_item(row) for row in item_rows]
        outcomes = Counter(str(row["outcome"]) for row in observations)
        attempts = outcomes["success"] + outcomes["failure"]
        return {
            "items": len(items),
            "validated": sum(item.status is KnowledgeStatus.VALIDATED for item in items),
            "lessons": sum(item.kind is KnowledgeKind.LESSON for item in items),
            "observations": len(observations),
            "success_rate": None if attempts == 0 else outcomes["success"] / attempts,
            "reused_items": _reused_items(observations),
            "top_tags": _top_values(item.tags for item in items),
            "top_stack": _top_values(item.stack for item in items),
        }

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


def _item_values(item: KnowledgeItem) -> dict[str, Any]:
    return {
        "item_id": item.item_id,
        "kind": item.kind.value,
        "title": item.title,
        "summary": item.summary,
        "tags_json": _json(item.tags),
        "stack_json": _json(item.stack),
        "origin": item.origin.value,
        "status": item.status.value,
        "source_project": item.source_project,
        "source_url": item.source_url,
        "source_license": item.source_license,
        "source_sha256": item.source_sha256,
        "problem_signature": item.problem_signature,
        "solution_signature": item.solution_signature,
        "evidence_sha256": item.evidence_sha256,
        "confidence": item.confidence,
        "created_at": item.created_at,
        "last_verified_at": item.last_verified_at,
    }


def _row_to_item(row: sqlite3.Row) -> KnowledgeItem:
    return KnowledgeItem(
        item_id=str(row["item_id"]),
        kind=KnowledgeKind(str(row["kind"])),
        title=str(row["title"]),
        summary=str(row["summary"]),
        tags=tuple(json.loads(str(row["tags_json"]))),
        stack=tuple(json.loads(str(row["stack_json"]))),
        origin=KnowledgeOrigin(str(row["origin"])),
        status=KnowledgeStatus(str(row["status"])),
        source_project=_optional(row["source_project"]),
        source_url=_optional(row["source_url"]),
        source_license=_optional(row["source_license"]),
        source_sha256=_optional(row["source_sha256"]),
        problem_signature=_optional(row["problem_signature"]),
        solution_signature=_optional(row["solution_signature"]),
        evidence_sha256=_optional(row["evidence_sha256"]),
        confidence=float(row["confidence"]),
        created_at=str(row["created_at"]),
        last_verified_at=_optional(row["last_verified_at"]),
    )


def _match_score(
    item: KnowledgeItem,
    terms: tuple[str, ...],
    kind: KnowledgeKind | None,
    tags: set[str],
    stack: set[str],
) -> float | None:
    if kind is not None and item.kind is not kind:
        return None
    item_tags = set(item.tags)
    item_stack = set(item.stack)
    if not tags.issubset(item_tags) or not stack.issubset(item_stack):
        return None
    title = item.title.casefold()
    summary = item.summary.casefold()
    searchable = " ".join((title, summary, *item.tags, *item.stack))
    if any(term not in searchable for term in terms):
        return None
    score = item.confidence
    score += sum(3.0 for term in terms if term in title)
    score += sum(1.0 for term in terms if term in summary)
    score += 2.0 * len(tags.intersection(item_tags))
    score += 1.5 * len(stack.intersection(item_stack))
    if item.status is KnowledgeStatus.VALIDATED:
        score += 2.0
    return score


def _top_values(groups: Iterable[Iterable[str]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for values in groups:
        counter.update(values)
    ranked = sorted(counter.items(), key=lambda pair: (-pair[1], pair[0]))[:10]
    return [{"value": value, "count": count} for value, count in ranked]


def _reused_items(rows: list[sqlite3.Row]) -> int:
    projects: dict[str, set[str]] = {}
    for row in rows:
        projects.setdefault(str(row["item_id"]), set()).add(str(row["project_id"]))
    return sum(len(values) > 1 for values in projects.values())


def _json(values: tuple[str, ...]) -> str:
    return json.dumps(list(values), ensure_ascii=False, separators=(",", ":"))


def _optional(value: object) -> str | None:
    return None if value is None else str(value)
