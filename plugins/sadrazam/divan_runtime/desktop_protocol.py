from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, replace
from typing import Any
from uuid import uuid4

from .desktop_api import DesktopApi
from .desktop_protocol_support import ProtocolValidationError
from .desktop_protocol_support import (
    error_response as _error,
    ok_response as _ok,
    optional_string as _optional_string,
    required_string as _required_string,
)
from .desktop_state import evidence_root, task_root
from .execution_router import ExecutionRouter
from .orchestrator import DivanOrchestrator
from .project_readiness import discover_tools
from .project_registry import ProjectRegistry
from .review_gate import CheckResult, ReviewDecision
from .task_model import DivanTask, TaskState
from .task_store import TaskStore

API_VERSION = 1
_AGENT_IDS = {"codex", "claude", "opencode", "cursor-agent"}
Handler = Callable[[Mapping[str, Any], ExecutionRouter | None], dict[str, Any]]


def _tasks() -> TaskStore:
    return TaskStore(task_root())


def _orchestrator(router: ExecutionRouter) -> DivanOrchestrator:
    return DivanOrchestrator(
        router,
        state_root=task_root(),
        evidence_root=evidence_root(),
    )


def _task_id(payload: Mapping[str, Any]) -> str:
    return _required_string(payload, "task_id", "DESKTOP_TASK_ID_REQUIRED")


def _load_task(payload: Mapping[str, Any]) -> DivanTask:
    return _tasks().load(_task_id(payload))


def _require_router(router: ExecutionRouter | None) -> ExecutionRouter:
    if router is None:
        raise ProtocolValidationError(
            "DESKTOP_ROUTER_UNAVAILABLE",
            "execution router is not configured",
        )
    return router


def _recommended_engine(engines: list[str]) -> str | None:
    for engine_id in ("orca", "native"):
        if engine_id in engines:
            return engine_id
    return engines[0] if engines else None


def _handle_capabilities(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del payload
    value = DesktopApi(router or ExecutionRouter([])).capabilities()
    value["commands"] = tuple(_HANDLERS)
    return _ok(value)


def _handle_readiness(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del payload
    readiness = discover_tools()
    tools = [asdict(tool) for tool in readiness.tools]
    agents = [
        tool["id"]
        for tool in tools
        if tool["id"] in _AGENT_IDS and tool["available"]
    ]
    engines = list(router.available_engines()) if router is not None else []
    return _ok(
        {
            "ready": readiness.ready,
            "tools": tools,
            "engines": engines,
            "recommended_engine": _recommended_engine(engines),
            "recommended_agent": agents[0] if agents else None,
            "api_keys_required": False,
        }
    )


def _handle_project_list(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del payload, router
    return _ok([asdict(item) for item in ProjectRegistry().list()])


def _handle_project_register(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    root = _required_string(payload, "root", "DESKTOP_PROJECT_ROOT_REQUIRED")
    return _ok(asdict(ProjectRegistry().register(root)))


def _handle_task_list(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del payload, router
    return _ok(DesktopApi.serialize_tasks(_tasks().list()))


def _handle_task_get(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    return _ok(_load_task(payload).to_dict())


def _resolve_project_root(payload: Mapping[str, Any]) -> str | None:
    project_id = _optional_string(payload, "project_id", "DESKTOP_PROJECT_ID_INVALID")
    if project_id:
        return ProjectRegistry().get(project_id).root
    return _optional_string(
        payload,
        "project_root",
        "DESKTOP_PROJECT_ROOT_INVALID",
    )


def _handle_task_create(
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


def _handle_task_plan(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    active_router = _require_router(router)
    task = _load_task(payload)
    reason = _optional_string(payload, "reason", "DESKTOP_TASK_REASON_INVALID")
    return _ok(_orchestrator(active_router).plan(task, reason).to_dict())


def _execution_task(payload: Mapping[str, Any], task: DivanTask) -> DivanTask:
    if payload.get("approve_execution") is not True:
        raise ProtocolValidationError(
            "DESKTOP_EXECUTION_APPROVAL_REQUIRED",
            "starting a mutating task requires explicit approve_execution=true",
        )
    if task.state not in {TaskState.PLANNED, TaskState.RETRY}:
        raise ProtocolValidationError(
            "DESKTOP_TASK_STATE_INVALID",
            "task must be planned or retry before execution",
        )
    engine_id = _optional_string(payload, "engine_id", "DESKTOP_ENGINE_ID_INVALID")
    mandate_id = task.mandate_id or f"mandate-{uuid4().hex}"
    return replace(task, engine_id=engine_id or task.engine_id, mandate_id=mandate_id)


def _handle_task_start(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    active_router = _require_router(router)
    task = _execution_task(payload, _load_task(payload))
    agent = _optional_string(payload, "agent", "DESKTOP_AGENT_INVALID")
    prompt = _optional_string(payload, "prompt", "DESKTOP_TASK_PROMPT_INVALID")
    worktree_name = (
        _optional_string(payload, "worktree_name", "DESKTOP_WORKTREE_NAME_INVALID")
        or task.task_id
    )
    _tasks().save(task)
    started = _orchestrator(active_router).start(
        task,
        worktree_name=worktree_name,
        agent=agent,
        prompt=prompt or task.title,
    )
    return _ok(started.to_dict())


def _handle_task_recover_interrupted(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    active_router = _require_router(router)
    recovered = _orchestrator(active_router).recover_interrupted(_load_task(payload))
    return _ok(recovered.to_dict())


def _handle_task_diff(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    active_router = _require_router(router)
    task = _load_task(payload)
    worktree = _optional_string(payload, "worktree", "DESKTOP_WORKTREE_INVALID")
    if worktree is None and DesktopApi.execution_worktree(task) is None:
        raise ProtocolValidationError(
            "DESKTOP_TASK_WORKTREE_UNAVAILABLE",
            "task has no execution worktree yet",
        )
    path = _optional_string(payload, "path", "DESKTOP_DIFF_PATH_INVALID") or "*"
    return _ok(DesktopApi(active_router).task_diff(task, worktree=worktree, path=path))


def _parse_review_checks(payload: Mapping[str, Any]) -> list[CheckResult]:
    checks_raw = payload.get("checks")
    if not isinstance(checks_raw, list) or not checks_raw:
        raise ProtocolValidationError(
            "DESKTOP_REVIEW_CHECKS_REQUIRED",
            "checks must be a non-empty list",
        )
    checks: list[CheckResult] = []
    for row in checks_raw:
        if not isinstance(row, Mapping):
            raise ProtocolValidationError(
                "DESKTOP_REVIEW_CHECK_INVALID",
                "review check must be an object",
            )
        name = row.get("name")
        passed = row.get("passed")
        if not isinstance(name, str) or type(passed) is not bool:
            raise ProtocolValidationError(
                "DESKTOP_REVIEW_CHECK_INVALID",
                "review check requires name and boolean passed",
            )
        checks.append(
            CheckResult(
                name=name,
                passed=passed,
                required=bool(row.get("required", True)),
                summary=str(row.get("summary", "")),
            )
        )
    return checks


def _review_result(task: DivanTask, decision: ReviewDecision) -> dict[str, Any]:
    return {
        "task": task.to_dict(),
        "review": {
            "verdict": decision.verdict.value,
            "checks": [asdict(item) for item in decision.checks],
            "reasons": list(decision.reasons),
        },
    }


def _handle_task_review(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    active_router = _require_router(router)
    updated, decision = _orchestrator(active_router).review(
        _load_task(payload),
        _parse_review_checks(payload),
    )
    return _ok(_review_result(updated, decision))


def _handle_task_review_auto(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    active_router = _require_router(router)
    updated, decision = _orchestrator(active_router).review_automated(_load_task(payload))
    return _ok(_review_result(updated, decision))


def _handle_approval_request(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    active_router = _require_router(router)
    task = _orchestrator(active_router).request_approval(_load_task(payload))
    return _ok(task.to_dict())


def _handle_task_approve(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    active_router = _require_router(router)
    if payload.get("approved") is not True:
        raise ProtocolValidationError(
            "DESKTOP_MERGE_APPROVAL_REQUIRED",
            "merge requires explicit approved=true",
        )
    task = _orchestrator(active_router).approve_merge(_load_task(payload), approved=True)
    return _ok(task.to_dict())


def _handle_task_release(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    task = _orchestrator(_require_router(router)).release(_load_task(payload))
    return _ok(task.to_dict())


def _handle_evidence_list(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    task_id = _task_id(payload)
    active_router = router or ExecutionRouter([])
    return _ok(list(_orchestrator(active_router).evidence.list(task_id)))


def _handle_engine_status(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    engine_id = _optional_string(payload, "engine_id", "DESKTOP_ENGINE_ID_INVALID")
    return _ok(DesktopApi(_require_router(router)).engine_status(engine_id))


_HANDLERS: dict[str, Handler] = {
    "capabilities": _handle_capabilities,
    "readiness": _handle_readiness,
    "project.list": _handle_project_list,
    "project.register": _handle_project_register,
    "task.list": _handle_task_list,
    "task.get": _handle_task_get,
    "task.create": _handle_task_create,
    "task.plan": _handle_task_plan,
    "task.start": _handle_task_start,
    "task.recover.interrupted": _handle_task_recover_interrupted,
    "task.diff": _handle_task_diff,
    "task.review": _handle_task_review,
    "task.review.auto": _handle_task_review_auto,
    "task.approval.request": _handle_approval_request,
    "task.approve": _handle_task_approve,
    "task.release": _handle_task_release,
    "evidence.list": _handle_evidence_list,
    "engine.status": _handle_engine_status,
}


def handle_request(
    payload: Mapping[str, Any],
    router: ExecutionRouter | None = None,
) -> dict[str, Any]:
    command = payload.get("command")
    if not isinstance(command, str) or not command.strip():
        return _error("DESKTOP_COMMAND_REQUIRED", "command is required")
    handler = _HANDLERS.get(command)
    if handler is None:
        return _error("DESKTOP_COMMAND_UNKNOWN", f"unknown command: {command}")
    try:
        return handler(payload, router)
    except ProtocolValidationError as error:
        return _error(error.code, error.message)
    except (KeyError, FileNotFoundError) as error:
        return _error("DESKTOP_NOT_FOUND", str(error))
    except ValueError as error:
        return _error("DESKTOP_VALIDATION_FAILED", str(error))
    except Exception as error:
        return _error("DESKTOP_OPERATION_FAILED", str(error))
