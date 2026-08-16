from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any
from uuid import uuid4

from . import local_ai, ordu, prompt_library
from .desktop_protocol_support import ProtocolValidationError
from .desktop_protocol_support import ok_response as _ok
from .desktop_protocol_support import optional_string as _optional_string
from .desktop_protocol_support import required_string as _required_string
from .desktop_state import task_root
from .execution_router import ExecutionRouter
from .project_registry import ProjectRegistry
from .task_model import DivanTask
from .task_store import TaskStore


def _tasks() -> TaskStore:
    return TaskStore(task_root())


def _resolve_project_root(payload: Mapping[str, Any]) -> str | None:
    project_id = _optional_string(payload, "project_id", "DESKTOP_PROJECT_ID_INVALID")
    if project_id:
        return ProjectRegistry().get(project_id).root
    return _optional_string(
        payload,
        "project_root",
        "DESKTOP_PROJECT_ROOT_INVALID",
    )


def handle_project_list(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del payload, router
    return _ok([asdict(item) for item in ProjectRegistry().list()])


def handle_project_register(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    root = _required_string(payload, "root", "DESKTOP_PROJECT_ROOT_REQUIRED")
    return _ok(asdict(ProjectRegistry().register(root)))


def handle_task_create(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    title = _required_string(payload, "title", "DESKTOP_TASK_TITLE_REQUIRED")
    raw_task_id = payload.get("task_id")
    if raw_task_id is None:
        task_id = f"DIV-{uuid4().hex[:8].upper()}"
    elif isinstance(raw_task_id, str) and raw_task_id.strip():
        task_id = raw_task_id.strip()
    else:
        raise ProtocolValidationError(
            "DESKTOP_TASK_ID_INVALID",
            "task_id must be a string",
        )
    task = DivanTask(
        task_id=task_id,
        title=title,
        project_root=_resolve_project_root(payload),
        engine_id=_optional_string(payload, "engine_id", "DESKTOP_ENGINE_ID_INVALID"),
    )
    _tasks().save(task)
    return _ok(task.to_dict())


def handle_prompt_search(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    query = _optional_string(payload, "query", "DESKTOP_PROMPT_QUERY_INVALID") or ""
    limit = payload.get("limit", 30)
    if not isinstance(limit, int):
        raise ProtocolValidationError(
            "DESKTOP_PROMPT_LIMIT_INVALID",
            "prompt limit must be a number",
        )
    return _ok(
        {
            "items": prompt_library.search(query, limit=limit),
            "total": prompt_library.catalogue_size(),
            "source": prompt_library.provenance(),
        }
    )


def handle_prompt_get(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    prompt_id = _required_string(payload, "prompt_id", "DESKTOP_PROMPT_ID_REQUIRED")
    return _ok(prompt_library.get(prompt_id).detail())


def handle_task_create_from_prompt(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    prompt_id = _required_string(payload, "prompt_id", "DESKTOP_PROMPT_ID_REQUIRED")
    values = payload.get("variables")
    if values is not None and not isinstance(values, Mapping):
        raise ProtocolValidationError(
            "DESKTOP_PROMPT_VARIABLES_INVALID",
            "variables must be an object",
        )
    rendered = prompt_library.render(prompt_id, values)
    task = DivanTask(
        task_id=f"OTT-{uuid4().hex[:8].upper()}",
        title=str(rendered["title"]),
        project_root=_resolve_project_root(payload),
        engine_id=_optional_string(payload, "engine_id", "DESKTOP_ENGINE_ID_INVALID"),
        metadata={"prompt_library": rendered},
    )
    _tasks().save(task)
    return _ok(task.to_dict())


def handle_local_ai_status(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del payload, router
    return _ok(local_ai.status())


def handle_local_ai_draft(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    prompt = _required_string(payload, "prompt", "DESKTOP_LOCAL_AI_PROMPT_REQUIRED")
    model = _optional_string(payload, "model", "DESKTOP_LOCAL_AI_MODEL_INVALID")
    return _ok(local_ai.draft(prompt, model=model or local_ai.DEFAULT_MODEL))


def handle_ordu_plan(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    return _ok(ordu.plan(_required_string(payload, "title", "DESKTOP_ORDU_TITLE_REQUIRED")))
