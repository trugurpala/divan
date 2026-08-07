from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .desktop_protocol_support import ProtocolValidationError
from .desktop_protocol_support import ok_response as _ok
from .desktop_protocol_support import optional_string as _optional_string
from .execution_router import ExecutionRouter
from .knowledge_desktop import (
    knowledge_analytics_payload,
    knowledge_search_payload,
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


KNOWLEDGE_HANDLERS: dict[str, KnowledgeHandler] = {
    "knowledge.analytics": _analytics,
    "knowledge.search": _search,
    "knowledge.project": _project,
}
