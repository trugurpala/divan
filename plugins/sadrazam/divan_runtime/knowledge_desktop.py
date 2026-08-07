from __future__ import annotations

from pathlib import Path
from typing import Any

from .desktop_state import knowledge_database
from .knowledge_contract import KnowledgeItem
from .knowledge_relevance import inspect_memory_context, relevant_knowledge
from .knowledge_store import KnowledgeStore


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
