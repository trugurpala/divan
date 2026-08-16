"""Desktop protocol surface for the Plugin Trust Center.

Kept beside the knowledge protocol rather than inside desktop_protocol so each
capability owns its own handler table and the shared dispatcher stays readable.
Inspection is read-only: nothing here activates or executes a plugin.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .desktop_protocol_support import ok_response as _ok
from .desktop_protocol_support import required_string as _required_string
from .execution_router import ExecutionRouter
from .plugin_desktop import inspect_plugin_manifest

PluginHandler = Callable[[Mapping[str, Any], ExecutionRouter | None], dict[str, Any]]


def _inspect(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    manifest_path = _required_string(
        payload,
        "manifest_path",
        "DESKTOP_PLUGIN_MANIFEST_PATH_REQUIRED",
    )
    return _ok(inspect_plugin_manifest(manifest_path))


PLUGIN_HANDLERS: dict[str, PluginHandler] = {
    "plugin.inspect": _inspect,
}
