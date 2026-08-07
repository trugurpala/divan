from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from .desktop_api import DesktopApi
from .execution_router import ExecutionRouter
from .project_readiness import discover_tools

API_VERSION = 1


def _ok(result: Any) -> dict[str, Any]:
    return {"api_version": API_VERSION, "ok": True, "result": result}


def _error(code: str, message: str) -> dict[str, Any]:
    return {
        "api_version": API_VERSION,
        "ok": False,
        "error": {"code": code, "message": message},
    }


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
