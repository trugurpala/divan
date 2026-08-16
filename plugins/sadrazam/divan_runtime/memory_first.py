"""Answer "what do we already know?" before any research or planning runs.

A recall pack is deliberately small. Handing a planner the whole knowledge
book is the same mistake as handing a worker the whole repository: it costs
tokens, buries the relevant claim and invites the model to invent structure.

This module only reads. It never writes knowledge, never grants execution
authority, and never presents a quarantined or superseded claim as usable.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .knowledge_contract import ACTIVE_STATUSES, KnowledgeItem, KnowledgeKind
from .knowledge_relevance import inspect_memory_context, relevant_knowledge
from .knowledge_store import KnowledgeStore

RECALL_SCHEMA_VERSION = 1

#: How many claims of each class a recall pack may carry.
_CLASS_LIMITS = {
    "decisions": 5,
    "incidents": 5,
    "recipes": 3,
    "project_profile": 2,
}
_CLASS_KINDS = {
    "decisions": (KnowledgeKind.DECISION,),
    "incidents": (KnowledgeKind.LESSON,),
    "recipes": (KnowledgeKind.RECIPE, KnowledgeKind.PATTERN),
    "project_profile": (KnowledgeKind.PROJECT_PROFILE,),
}


@dataclass(frozen=True)
class RecalledItem:
    item_id: str
    kind: str
    title: str
    summary: str
    status: str
    confidence: float
    last_verified_at: str | None
    source_project: str | None


@dataclass(frozen=True)
class RecallPack:
    """The bounded answer to "what do we already know about this Ferman?"."""

    intent: str
    project: str
    decisions: tuple[RecalledItem, ...]
    incidents: tuple[RecalledItem, ...]
    recipes: tuple[RecalledItem, ...]
    project_profile: tuple[RecalledItem, ...]
    considered: int
    withheld_inactive: int
    gaps: tuple[str, ...]

    @property
    def item_ids(self) -> tuple[str, ...]:
        return tuple(
            item.item_id
            for group in (
                self.decisions,
                self.incidents,
                self.recipes,
                self.project_profile,
            )
            for item in group
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": RECALL_SCHEMA_VERSION,
            "intent": self.intent,
            "project": self.project,
            "decisions": [asdict(item) for item in self.decisions],
            "incidents": [asdict(item) for item in self.incidents],
            "recipes": [asdict(item) for item in self.recipes],
            "project_profile": [asdict(item) for item in self.project_profile],
            "considered": self.considered,
            "withheld_inactive": self.withheld_inactive,
            # What memory could NOT answer. This is the only part that should
            # ever trigger fresh intelligence gathering.
            "gaps": list(self.gaps),
            "recalled_item_ids": list(self.item_ids),
        }


def _recalled(item: KnowledgeItem) -> RecalledItem:
    return RecalledItem(
        item_id=item.item_id,
        kind=item.kind.value,
        title=item.title,
        summary=item.summary,
        status=item.status.value,
        confidence=item.confidence,
        last_verified_at=item.last_verified_at,
        source_project=item.source_project,
    )


def recall(
    store: KnowledgeStore,
    project_root: Path | str,
    *,
    intent: str,
    candidate_limit: int = 50,
) -> RecallPack:
    """Build one bounded recall pack for a Ferman in a project."""
    context = inspect_memory_context(project_root)
    matches = relevant_knowledge(store, context, intent=intent, limit=candidate_limit)
    considered = len(matches)

    usable: list[KnowledgeItem] = []
    withheld = 0
    for match in matches:
        item = match.item
        # A quarantined or superseded claim is exactly what must not be handed
        # to a planner as if it were settled.
        if item.status not in ACTIVE_STATUSES:
            withheld += 1
            continue
        usable.append(item)

    grouped: dict[str, tuple[RecalledItem, ...]] = {}
    for name, kinds in _CLASS_KINDS.items():
        selected = [item for item in usable if item.kind in kinds][: _CLASS_LIMITS[name]]
        grouped[name] = tuple(_recalled(item) for item in selected)

    gaps = tuple(name for name, items in grouped.items() if not items)
    return RecallPack(
        intent=intent,
        project=str(context.inspection.get("project", "")),
        decisions=grouped["decisions"],
        incidents=grouped["incidents"],
        recipes=grouped["recipes"],
        project_profile=grouped["project_profile"],
        considered=considered,
        withheld_inactive=withheld,
        gaps=gaps,
    )
