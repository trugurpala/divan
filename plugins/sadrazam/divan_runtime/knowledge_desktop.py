from __future__ import annotations

from pathlib import Path
from typing import Any

from .desktop_state import knowledge_database
from .knowledge_contract import KnowledgeItem, ObservationOutcome
from .knowledge_projection import render_book
from .knowledge_relevance import inspect_memory_context, relevant_knowledge
from .knowledge_store import KnowledgeStore
from .memory_first import recall


def knowledge_analytics_payload() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "analytics": KnowledgeStore(knowledge_database()).analytics(),
    }


def knowledge_search_payload(query: str = "", *, limit: int = 20) -> dict[str, Any]:
    store = KnowledgeStore(knowledge_database())
    return {
        "schema_version": 1,
        "query": query.strip(),
        "items": [_item_payload(item) for item in store.search(query, limit=_limit(limit))],
    }


def project_memory_payload(
    project_root: Path | str,
    *,
    intent: str = "",
    limit: int = 10,
) -> dict[str, Any]:
    store = KnowledgeStore(knowledge_database())
    context = inspect_memory_context(project_root)
    matches = relevant_knowledge(store, context, intent=intent, limit=_limit(limit))
    return {
        "schema_version": 1,
        "inspection": context.inspection,
        "memory_context": {
            "stack": list(context.stack),
            "tags": list(context.tags),
        },
        "matches": [match.to_dict() for match in matches],
    }


def _item_payload(item: KnowledgeItem) -> dict[str, Any]:
    return {
        "item_id": item.item_id,
        "kind": item.kind.value,
        "title": item.title,
        "summary": item.summary,
        "tags": list(item.tags),
        "stack": list(item.stack),
        "origin": item.origin.value,
        "status": item.status.value,
        "source_project": item.source_project,
        "source_url": item.source_url,
        "source_license": item.source_license,
        "confidence": item.confidence,
        "last_verified_at": item.last_verified_at,
    }


def _limit(value: int) -> int:
    return min(max(value, 0), 100)


def knowledge_book_payload(query: str = "", *, limit: int = 100) -> dict[str, Any]:
    """Return the human-readable projection of the store.

    Markdown is a projection only. The SQLite store stays authoritative, so
    this payload is safe to regenerate and must never be edited back in.
    """
    store = KnowledgeStore(knowledge_database())
    return {
        "schema_version": 1,
        "query": query.strip(),
        "format": "markdown",
        "authority": "projection-only",
        "book": render_book(store, query=query.strip(), limit=_limit(limit)),
    }


def memory_recall_payload(
    project_root: Path | str, *, intent: str = ""
) -> dict[str, Any]:
    """Answer what is already known before any fresh research is started."""
    store = KnowledgeStore(knowledge_database())
    return recall(store, project_root, intent=intent).to_dict()


def knowledge_observation_payload(
    *,
    item_id: str,
    project_id: str,
    outcome: ObservationOutcome,
    observed_at: str,
    evidence_sha256: str | None = None,
    note: str = "",
) -> dict[str, Any]:
    """Record one evidence-backed reuse outcome for a remembered claim.

    Reuse count is never promotion. This writes what happened; whether the
    claim becomes more trusted stays an explicit curation decision.
    """
    store = KnowledgeStore(knowledge_database())
    store.observe(
        item_id,
        project_id=project_id,
        outcome=outcome,
        observed_at=observed_at,
        evidence_sha256=evidence_sha256,
        note=note,
    )
    return {
        "schema_version": 1,
        "item_id": item_id,
        "outcome": outcome.value,
        "stats": store.observation_stats(item_id),
        "promotion_authority": "not-granted",
    }
