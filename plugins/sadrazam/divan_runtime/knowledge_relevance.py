from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .engine import Contracts, inspect_project, load_contracts
from .knowledge_contract import KnowledgeItem, KnowledgeStatus
from .knowledge_store import KnowledgeStore


@dataclass(frozen=True)
class ProjectMemoryContext:
    inspection: dict[str, Any]
    stack: tuple[str, ...]
    tags: tuple[str, ...]


@dataclass(frozen=True)
class KnowledgeMatch:
    item: KnowledgeItem
    score: float
    reasons: tuple[str, ...]
    observations: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        item = self.item
        return {
            "item": {
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
            },
            "score": round(self.score, 3),
            "reasons": list(self.reasons),
            "observations": self.observations,
        }


def inspect_memory_context(
    project: Path | str,
    *,
    contracts: Contracts | None = None,
) -> ProjectMemoryContext:
    active_contracts = contracts or load_contracts()
    inspection = inspect_project(Path(project), active_contracts)
    stack = tuple(
        sorted(
            {
                *[str(value).casefold() for value in inspection["frameworks"]],
                *[str(value).casefold() for value in inspection["package_managers"]],
            }
        )
    )
    tags = tuple(str(value).casefold() for value in inspection["project_types"])
    return ProjectMemoryContext(inspection=inspection, stack=stack, tags=tags)


def relevant_knowledge(
    store: KnowledgeStore,
    context: ProjectMemoryContext,
    *,
    intent: str = "",
    limit: int = 10,
) -> tuple[KnowledgeMatch, ...]:
    terms = tuple(part.casefold() for part in intent.split() if part.strip())
    matches: list[KnowledgeMatch] = []
    for item in store.search(limit=1000):
        ranked = _rank_item(store, item, context, terms)
        if ranked is not None:
            matches.append(ranked)
    matches.sort(key=lambda match: (-match.score, match.item.item_id))
    return tuple(matches[: max(0, limit)])


def _rank_item(
    store: KnowledgeStore,
    item: KnowledgeItem,
    context: ProjectMemoryContext,
    terms: tuple[str, ...],
) -> KnowledgeMatch | None:
    if item.status is KnowledgeStatus.DEPRECATED:
        return None
    stack_overlap = sorted(set(item.stack).intersection(context.stack))
    tag_overlap = sorted(set(item.tags).intersection(context.tags))
    searchable = " ".join((item.title, item.summary, *item.tags, *item.stack)).casefold()
    term_hits = [term for term in terms if term in searchable]
    if not stack_overlap and not tag_overlap and not term_hits:
        return None

    observations = store.observation_stats(item.item_id)
    reasons: list[str] = []
    score = item.confidence
    if stack_overlap:
        reasons.append(f"stack: {', '.join(stack_overlap)}")
        score += 4.0 * len(stack_overlap)
    if tag_overlap:
        reasons.append(f"project type: {', '.join(tag_overlap)}")
        score += 2.0 * len(tag_overlap)
    if term_hits:
        reasons.append(f"intent: {', '.join(term_hits[:5])}")
        score += 1.5 * len(term_hits)
    if item.status is KnowledgeStatus.VALIDATED:
        reasons.append("validated knowledge")
        score += 3.0
    reused_projects = int(observations["projects"])
    if reused_projects > 1:
        reasons.append(f"reused in {reused_projects} projects")
        score += min(reused_projects, 5) * 0.5
    success_rate = observations["success_rate"]
    if isinstance(success_rate, float) and observations["attempts"] >= 2:
        score += success_rate
    return KnowledgeMatch(item, score, tuple(reasons), observations)
