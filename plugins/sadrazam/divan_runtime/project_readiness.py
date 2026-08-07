from __future__ import annotations

from dataclasses import dataclass
import shutil
from typing import Callable


@dataclass(frozen=True)
class ToolStatus:
    id: str
    available: bool
    path: str | None
    required: bool


@dataclass(frozen=True)
class ProjectReadiness:
    ready: bool
    tools: tuple[ToolStatus, ...]


DEFAULT_TOOLS = (
    ("git", True),
    ("orca", False),
    ("codex", False),
    ("claude", False),
    ("opencode", False),
)


def discover_tools(which: Callable[[str], str | None] = shutil.which) -> ProjectReadiness:
    tools = tuple(
        ToolStatus(tool_id, bool(path := which(tool_id)), path, required)
        for tool_id, required in DEFAULT_TOOLS
    )
    return ProjectReadiness(
        ready=all(tool.available for tool in tools if tool.required),
        tools=tools,
    )
