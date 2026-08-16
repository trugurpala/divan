from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .desktop_protocol_support import ProtocolValidationError
from .desktop_protocol_support import ok_response as _ok
from .desktop_protocol_support import optional_string as _optional_string
from .execution_router import ExecutionRouter
from .knowledge_contract import ObservationOutcome
from .knowledge_desktop import (
    knowledge_analytics_payload,
    knowledge_book_payload,
    knowledge_observation_payload,
    knowledge_search_payload,
    memory_recall_payload,
    project_memory_payload,
)
from .project_registry import ProjectRegistry

KnowledgeHandler = Callable[[Mapping[str, Any], ExecutionRouter | None], dict[str, Any]]


def _project_root(payload: Mapping[str, Any]) -> str:
    project_id = _optional_string(payload, "project_id", "DESKTOP_PROJECT_ID_INVALID")
    if project_id:
        return ProjectRegistry().get(project_id).root
    root = _optional_string(
        payload,
        "project_root",
        "DESKTOP_PROJECT_ROOT_INVALID",
    )
    if root is None:
        raise ProtocolValidationError(
            "DESKTOP_PROJECT_ROOT_REQUIRED",
            "project_id or project_root is required",
        )
    return root


def _analytics(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del payload, router
    return _ok(knowledge_analytics_payload())


def _search(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    query = _optional_string(payload, "query", "DESKTOP_KNOWLEDGE_QUERY_INVALID") or ""
    return _ok(knowledge_search_payload(query))


def _project(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    intent = _optional_string(payload, "intent", "DESKTOP_KNOWLEDGE_INTENT_INVALID") or ""
    return _ok(project_memory_payload(_project_root(payload), intent=intent))


def _book(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    query = _optional_string(payload, "query", "DESKTOP_KNOWLEDGE_QUERY_INVALID") or ""
    return _ok(knowledge_book_payload(query))


def _recall(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    intent = _optional_string(payload, "intent", "DESKTOP_KNOWLEDGE_INTENT_INVALID") or ""
    return _ok(memory_recall_payload(_project_root(payload), intent=intent))


def _observe(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    item_id = _optional_string(payload, "item_id", "DESKTOP_KNOWLEDGE_ITEM_INVALID")
    project_id = _optional_string(payload, "project_id", "DESKTOP_PROJECT_ID_INVALID")
    observed_at = _optional_string(payload, "observed_at", "DESKTOP_KNOWLEDGE_TIME_INVALID")
    raw_outcome = _optional_string(payload, "outcome", "DESKTOP_KNOWLEDGE_OUTCOME_INVALID")
    if not item_id or not project_id or not observed_at or not raw_outcome:
        raise ProtocolValidationError(
            "DESKTOP_KNOWLEDGE_OBSERVATION_INCOMPLETE",
            "item_id, project_id, outcome and observed_at are required",
        )
    try:
        outcome = ObservationOutcome(raw_outcome)
    except ValueError as error:
        raise ProtocolValidationError(
            "DESKTOP_KNOWLEDGE_OUTCOME_INVALID",
            f"outcome must be one of {[value.value for value in ObservationOutcome]}",
        ) from error
    return _ok(
        knowledge_observation_payload(
            item_id=item_id,
            project_id=project_id,
            outcome=outcome,
            observed_at=observed_at,
            evidence_sha256=_optional_string(
                payload, "evidence_sha256", "DESKTOP_KNOWLEDGE_EVIDENCE_INVALID"
            ),
            note=_optional_string(payload, "note", "DESKTOP_KNOWLEDGE_NOTE_INVALID") or "",
        )
    )


KNOWLEDGE_HANDLERS: dict[str, KnowledgeHandler] = {
    "knowledge.analytics": _analytics,
    "knowledge.search": _search,
    "knowledge.project": _project,
    "knowledge.book": _book,
    "knowledge.recall": _recall,
    "knowledge.observe": _observe,
}
