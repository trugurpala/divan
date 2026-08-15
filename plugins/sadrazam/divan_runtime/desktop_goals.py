from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import engine, goals
from .desktop_protocol_support import ProtocolValidationError
from .desktop_protocol_support import optional_string as _optional_string
from .desktop_protocol_support import required_string as _required_string
from .project_registry import ProjectRegistry


def _project_root(payload: Mapping[str, Any]) -> Path:
    project_id = _optional_string(
        payload,
        "project_id",
        "DESKTOP_PROJECT_ID_INVALID",
    )
    if project_id:
        return Path(ProjectRegistry().get(project_id).root)
    project_root = _optional_string(
        payload,
        "project_root",
        "DESKTOP_PROJECT_ROOT_INVALID",
    )
    if not project_root:
        raise ProtocolValidationError(
            "DESKTOP_PROJECT_REQUIRED",
            "goal planning requires project_id or project_root",
        )
    return Path(project_root).expanduser().resolve()


def _intent(payload: Mapping[str, Any]) -> str:
    return _required_string(
        payload,
        "intent",
        "DESKTOP_GOAL_INTENT_REQUIRED",
    )


def _target(payload: Mapping[str, Any]) -> str:
    return (
        _optional_string(
            payload,
            "target",
            "DESKTOP_GOAL_TARGET_INVALID",
        )
        or "verified"
    ).casefold()


def _route(root: Path, intent: str, target: str) -> dict[str, Any]:
    contracts = engine.load_contracts(Path(engine.__file__).resolve().parent)
    return engine.plan_intent(
        intent,
        root,
        contracts,
        target,
        environment={},
    )


def _summary(route: Mapping[str, Any]) -> dict[str, Any]:
    execution = route.get("execution_plan")
    if not isinstance(execution, Mapping):
        raise ValueError("goal route has no execution plan")
    orchestration = execution.get("orchestration")
    if not isinstance(orchestration, Mapping):
        raise ValueError("goal route has no orchestration plan")
    tasks = execution.get("tasks")
    workstreams = execution.get("workstreams")
    sefers = execution.get("sefers")
    if not isinstance(tasks, list) or not isinstance(workstreams, list) or not isinstance(sefers, list):
        raise ValueError("goal route planning collections are invalid")
    return {
        "route_id": execution.get("route_id"),
        "workflow": route.get("workflow"),
        "workflows": list(route.get("workflows", [])),
        "roles": list(route.get("roles", [])),
        "frameworks": list(route.get("frameworks", [])),
        "project_types": list(route.get("project_types", [])),
        "task_count": len(tasks),
        "workstream_count": len(workstreams),
        "sefer_count": len(sefers),
        "lane": orchestration.get("lane"),
        "max_parallel_workstreams": orchestration.get("max_parallel_workstreams"),
        "required_evidence": list(route.get("required_evidence", [])),
    }


def preview_goal(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Inspect a registered project and build a deterministic read-only goal route."""
    root = _project_root(payload)
    intent = _intent(payload)
    target = _target(payload)
    route = _route(root, intent, target)
    return {
        "project_root": str(root),
        "intent": intent,
        "target": target,
        "summary": _summary(route),
        "route": route,
        "writes": [],
        "execution_authority": "not-granted",
    }


def create_goal(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Persist only Divan goal artifacts after an explicit plan-write approval."""
    if payload.get("approve_plan_write") is not True:
        raise ProtocolValidationError(
            "DESKTOP_GOAL_WRITE_APPROVAL_REQUIRED",
            "persisting a goal plan requires explicit approve_plan_write=true",
        )
    root = _project_root(payload)
    intent = _intent(payload)
    target = _target(payload)
    result = goals.start_goal(
        root,
        intent,
        target,
        True,
        environment={},
    )
    route = _route(root, intent, target)
    return {
        "goal": result,
        "summary": _summary(route),
        "execution_authority": "not-granted",
    }
