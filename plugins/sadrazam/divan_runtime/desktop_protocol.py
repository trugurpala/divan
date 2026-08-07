from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping
from uuid import uuid4

from .desktop_api import DesktopApi
from .desktop_state import task_root
from .execution_router import ExecutionRouter
from .project_readiness import discover_tools
from .task_model import DivanTask
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


def handle_request(payload: Mapping[str, Any], router: ExecutionRouter | None = None) -> dict[str, Any]:
    command = payload.get("command")
    if not isinstance(command, str) or not command.strip():
        return _error("DESKTOP_COMMAND_REQUIRED", "command is required")

    if command == "capabilities":
        api = DesktopApi(router or ExecutionRouter([]))
        return _ok(api.capabilities())

    if command == "readiness":
        readiness = discover_tools()
        return _ok(
            {
                "ready": readiness.ready,
                "tools": [asdict(tool) for tool in readiness.tools],
            }
        )

    if command == "task.list":
        try:
            return _ok(DesktopApi.serialize_tasks(_tasks().list()))
        except Exception as error:
            return _error("DESKTOP_TASK_LIST_FAILED", str(error))

    if command == "task.create":
        title = payload.get("title")
        if not isinstance(title, str) or not title.strip():
            return _error("DESKTOP_TASK_TITLE_REQUIRED", "title is required")
        task_id = payload.get("task_id")
        if task_id is None:
            task_id = f"DIV-{uuid4().hex[:8].upper()}"
        if not isinstance(task_id, str) or not task_id.strip():
            return _error("DESKTOP_TASK_ID_INVALID", "task_id must be a string")
        project_root = payload.get("project_root")
        if project_root is not None and not isinstance(project_root, str):
            return _error("DESKTOP_PROJECT_ROOT_INVALID", "project_root must be a string")
        try:
            store = _tasks()
            task = DivanTask(task_id=task_id, title=title.strip(), project_root=project_root)
            store.save(task)
            return _ok(task.to_dict())
        except Exception as error:
            return _error("DESKTOP_TASK_CREATE_FAILED", str(error))

    if command == "engine.status":
        if router is None:
            return _error("DESKTOP_ENGINE_ROUTER_REQUIRED", "engine router is not configured")
        engine_id = payload.get("engine_id")
        if engine_id is not None and not isinstance(engine_id, str):
            return _error("DESKTOP_ENGINE_ID_INVALID", "engine_id must be a string")
        try:
            return _ok(DesktopApi(router).engine_status(engine_id))
        except Exception as error:
            return _error("DESKTOP_ENGINE_STATUS_FAILED", str(error))

    return _error("DESKTOP_COMMAND_UNKNOWN", f"unknown command: {command}")
