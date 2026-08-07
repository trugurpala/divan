from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any, Mapping
from uuid import uuid4

from .desktop_api import DesktopApi
from .desktop_state import evidence_root, task_root
from .execution_router import ExecutionRouter
from .orchestrator import DivanOrchestrator
from .project_readiness import discover_tools
from .project_registry import ProjectRegistry
from .review_gate import CheckResult
from .task_model import DivanTask, TaskState
from .task_store import TaskStore

API_VERSION = 1


def _ok(result: Any) -> dict[str, Any]:
    return {"api_version": API_VERSION, "ok": True, "result": result}


def _error(code: str, message: str) -> dict[str, Any]:
    return {
        "api_version": API_VERSION,
        "ok": False,
        "error": {"code": code, "message": message},
    }


def _tasks() -> TaskStore:
    return TaskStore(task_root())


def _orchestrator(router: ExecutionRouter) -> DivanOrchestrator:
    return DivanOrchestrator(
        router,
        state_root=task_root(),
        evidence_root=evidence_root(),
    )


def _task_id(payload: Mapping[str, Any]) -> str:
    value = payload.get("task_id")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("task_id is required")
    return value.strip()


def _load_task(payload: Mapping[str, Any]) -> DivanTask:
    return _tasks().load(_task_id(payload))


def handle_request(
    payload: Mapping[str, Any],
    router: ExecutionRouter | None = None,
) -> dict[str, Any]:
    command = payload.get("command")
    if not isinstance(command, str) or not command.strip():
        return _error("DESKTOP_COMMAND_REQUIRED", "command is required")

    try:
        if command == "capabilities":
            api = DesktopApi(router or ExecutionRouter([]))
            value = api.capabilities()
            value["commands"] = (
                "readiness",
                "project.list",
                "project.register",
                "task.list",
                "task.get",
                "task.create",
                "task.plan",
                "task.start",
                "task.review",
                "task.approval.request",
                "task.approve",
                "task.release",
                "evidence.list",
                "engine.status",
            )
            return _ok(value)

        if command == "readiness":
            readiness = discover_tools()
            tools = [asdict(tool) for tool in readiness.tools]
            agents = [
                tool["id"]
                for tool in tools
                if tool["id"] in {"codex", "claude", "opencode", "cursor-agent"}
                and tool["available"]
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

        if command == "project.list":
            return _ok([asdict(item) for item in ProjectRegistry().list()])

        if command == "project.register":
            root = payload.get("root")
            if not isinstance(root, str) or not root.strip():
                return _error("DESKTOP_PROJECT_ROOT_REQUIRED", "root is required")
            return _ok(asdict(ProjectRegistry().register(root.strip())))

        if command == "task.list":
            return _ok(DesktopApi.serialize_tasks(_tasks().list()))

        if command == "task.get":
            return _ok(_load_task(payload).to_dict())

        if command == "task.create":
            title = payload.get("title")
            if not isinstance(title, str) or not title.strip():
                return _error("DESKTOP_TASK_TITLE_REQUIRED", "title is required")
            task_id = payload.get("task_id") or f"DIV-{uuid4().hex[:8].upper()}"
            if not isinstance(task_id, str) or not task_id.strip():
                return _error("DESKTOP_TASK_ID_INVALID", "task_id must be a string")

            project_root = payload.get("project_root")
            project_id = payload.get("project_id")
            if project_id is not None:
                if not isinstance(project_id, str) or not project_id.strip():
                    return _error("DESKTOP_PROJECT_ID_INVALID", "project_id must be a string")
                project_root = ProjectRegistry().get(project_id.strip()).root
            if project_root is not None and not isinstance(project_root, str):
                return _error("DESKTOP_PROJECT_ROOT_INVALID", "project_root must be a string")

            engine_id = payload.get("engine_id")
            if engine_id is not None and not isinstance(engine_id, str):
                return _error("DESKTOP_ENGINE_ID_INVALID", "engine_id must be a string")

            task = DivanTask(
                task_id=task_id.strip(),
                title=title.strip(),
                project_root=project_root,
                engine_id=engine_id,
            )
            _tasks().save(task)
            return _ok(task.to_dict())

        if command == "task.plan":
            _require_router(router)
            task = _load_task(payload)
            reason = payload.get("reason")
            if reason is not None and not isinstance(reason, str):
                return _error("DESKTOP_TASK_REASON_INVALID", "reason must be a string")
            return _ok(_orchestrator(router).plan(task, reason).to_dict())

        if command == "task.start":
            _require_router(router)
            task = _load_task(payload)
            if payload.get("approve_execution") is not True:
                return _error(
                    "DESKTOP_EXECUTION_APPROVAL_REQUIRED",
                    "starting a mutating task requires explicit approve_execution=true",
                )
            if task.state is not TaskState.PLANNED and task.state is not TaskState.RETRY:
                return _error(
                    "DESKTOP_TASK_STATE_INVALID",
                    "task must be planned or retry before execution",
                )
            agent = payload.get("agent")
            if agent is not None and not isinstance(agent, str):
                return _error("DESKTOP_AGENT_INVALID", "agent must be a string")
            prompt = payload.get("prompt")
            if prompt is not None and not isinstance(prompt, str):
                return _error("DESKTOP_TASK_PROMPT_INVALID", "prompt must be a string")
            worktree_name = payload.get("worktree_name")
            if worktree_name is None:
                worktree_name = task.task_id
            if not isinstance(worktree_name, str) or not worktree_name.strip():
                return _error("DESKTOP_WORKTREE_NAME_INVALID", "worktree_name must be a string")

            mandate_id = task.mandate_id or f"mandate-{uuid4().hex}"
            requested_engine = payload.get("engine_id")
            if requested_engine is not None and not isinstance(requested_engine, str):
                return _error("DESKTOP_ENGINE_ID_INVALID", "engine_id must be a string")
            if requested_engine:
                task = replace(task, engine_id=requested_engine)
            task = replace(task, mandate_id=mandate_id)
            _tasks().save(task)
            started = _orchestrator(router).start(
                task,
                worktree_name=worktree_name.strip(),
                agent=agent.strip() if isinstance(agent, str) and agent.strip() else None,
                prompt=prompt if isinstance(prompt, str) and prompt.strip() else task.title,
            )
            return _ok(started.to_dict())

        if command == "task.review":
            _require_router(router)
            task = _load_task(payload)
            checks_raw = payload.get("checks")
            if not isinstance(checks_raw, list) or not checks_raw:
                return _error("DESKTOP_REVIEW_CHECKS_REQUIRED", "checks must be a non-empty list")
            checks: list[CheckResult] = []
            for row in checks_raw:
                if not isinstance(row, Mapping):
                    return _error("DESKTOP_REVIEW_CHECK_INVALID", "review check must be an object")
                name = row.get("name")
                passed = row.get("passed")
                if not isinstance(name, str) or type(passed) is not bool:
                    return _error(
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
            updated, decision = _orchestrator(router).review(task, checks)
            return _ok(
                {
                    "task": updated.to_dict(),
                    "review": {
                        "verdict": decision.verdict.value,
                        "checks": [asdict(item) for item in decision.checks],
                        "reasons": list(decision.reasons),
                    },
                }
            )

        if command == "task.approval.request":
            _require_router(router)
            task = _load_task(payload)
            return _ok(_orchestrator(router).request_approval(task).to_dict())

        if command == "task.approve":
            _require_router(router)
            task = _load_task(payload)
            if payload.get("approved") is not True:
                return _error(
                    "DESKTOP_MERGE_APPROVAL_REQUIRED",
                    "merge requires explicit approved=true",
                )
            return _ok(_orchestrator(router).approve_merge(task, approved=True).to_dict())

        if command == "task.release":
            _require_router(router)
            task = _load_task(payload)
            return _ok(_orchestrator(router).release(task).to_dict())

        if command == "evidence.list":
            task_id = _task_id(payload)
            return _ok(list(_orchestrator(router or ExecutionRouter([])).evidence.list(task_id)))

        if command == "engine.status":
            _require_router(router)
            engine_id = payload.get("engine_id")
            if engine_id is not None and not isinstance(engine_id, str):
                return _error("DESKTOP_ENGINE_ID_INVALID", "engine_id must be a string")
            return _ok(DesktopApi(router).engine_status(engine_id))

        return _error("DESKTOP_COMMAND_UNKNOWN", f"unknown command: {command}")
    except KeyError as error:
        return _error("DESKTOP_NOT_FOUND", str(error))
    except FileNotFoundError as error:
        return _error("DESKTOP_NOT_FOUND", str(error))
    except ValueError as error:
        return _error("DESKTOP_VALIDATION_FAILED", str(error))
    except Exception as error:
        return _error("DESKTOP_OPERATION_FAILED", str(error))


def _require_router(router: ExecutionRouter | None) -> None:
    if router is None:
        raise ValueError("execution router is not configured")


def _recommended_engine(engines: list[str]) -> str | None:
    if "orca" in engines:
        return "orca"
    if "native" in engines:
        return "native"
    return engines[0] if engines else None
