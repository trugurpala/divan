#!/usr/bin/env python3
"""Durable, host-neutral project memory storage for Divan."""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
from contextlib import AbstractContextManager
from datetime import datetime, timezone
from typing import Any

MEMORY_DIR = ".divan"
SCHEMA_VERSION = 1
TASK_ID_RE = re.compile(r"^TASK-(\d{3,})$")
LIFECYCLE_STATES = (
    "CREATED", "BASELINED", "PLANNED", "IMPLEMENTING", "VERIFYING",
    "REVIEWING", "READY_TO_SHIP", "SHIPPED", "MAINTENANCE",
)
TASK_STATUSES = {"pending", "in_progress", "blocked", "completed"}
REQUIRED_DIRECTORIES = (
    "decisions", "evidence", "handoffs", "history", "lessons", "spec",
)
REQUIRED_FILES = ("project.json", "tasks.json", "current-state.json", "progress.md")

class ProjectMemoryError(RuntimeError):
    """A durable-memory contract or operation failed."""

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "project"

def memory_root(project_root: pathlib.Path) -> pathlib.Path:
    return project_root.resolve() / MEMORY_DIR

def read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectMemoryError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectMemoryError(f"JSON root must be an object: {path}")
    return value

def atomic_write_text(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_symlink():
        raise ProjectMemoryError(f"refusing to replace symlink: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)

def atomic_write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

class MemoryLock(AbstractContextManager["MemoryLock"]):
    """Fail-closed single-writer lock for one project's durable memory."""

    def __init__(self, project_root: pathlib.Path, initialization: bool = False) -> None:
        root = project_root.resolve()
        self.path = root / ".divan-init.lock" if initialization else memory_root(root) / ".memory.lock"
        self.descriptor: int | None = None

    def __enter__(self) -> "MemoryLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise ProjectMemoryError(
                f"memory is locked by another writer: {self.path}"
            ) from exc
        payload = f"pid={os.getpid()}\ncreated_at={utc_now()}\n".encode()
        os.write(self.descriptor, payload)
        os.fsync(self.descriptor)
        return self

    def __exit__(self, *_: object) -> None:
        if self.descriptor is not None:
            os.close(self.descriptor)
        self.path.unlink(missing_ok=True)

def git_snapshot(project_root: pathlib.Path) -> tuple[str | None, str | None]:
    def value(arguments: list[str]) -> str | None:
        try:
            completed = subprocess.run(
                ["git", "-C", str(project_root), *arguments],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None
        output = completed.stdout.strip()
        return output or None

    return value(["branch", "--show-current"]), value(["rev-parse", "HEAD"])

def initial_payloads(
    name: str,
    goal: str,
    profile: str | None,
    source_repository: str | None,
    source_commit: str | None,
    deployment: str | None,
) -> dict[str, dict[str, Any]]:
    now = utc_now()
    source = None
    if source_repository or source_commit:
        source = {"repository": source_repository, "commit": source_commit}
    project = {
        "schema_version": SCHEMA_VERSION,
        "project_id": slugify(name),
        "name": name.strip(),
        "goal": goal.strip(),
        "profile": profile,
        "source": source,
        "deployment": deployment,
        "lifecycle_state": "CREATED",
        "created_at": now,
        "updated_at": now,
    }
    tasks = {"schema_version": SCHEMA_VERSION, "next_sequence": 1, "tasks": []}
    current = {
        "schema_version": SCHEMA_VERSION,
        "active_task": None,
        "active_branch": None,
        "last_commit": None,
        "last_successful_gate": None,
        "last_transition_evidence": [],
        "next_action": "Define the first vertical-slice task.",
        "blocked": False,
        "blocker": None,
        "last_checkpoint_at": now,
        "last_handoff": None,
    }
    return {"project.json": project, "tasks.json": tasks, "current-state.json": current}

def initialization_plan(project_root: pathlib.Path) -> list[str]:
    base = memory_root(project_root)
    return [
        *(str(base / directory) for directory in REQUIRED_DIRECTORIES),
        *(str(base / filename) for filename in REQUIRED_FILES),
    ]

def initialize(
    project_root: pathlib.Path,
    name: str,
    goal: str,
    profile: str | None = None,
    source_repository: str | None = None,
    source_commit: str | None = None,
    deployment: str | None = None,
    execute: bool = False,
) -> dict[str, Any]:
    root = project_root.resolve()
    base = memory_root(root)
    plan = initialization_plan(root)
    if not root.is_dir():
        raise ProjectMemoryError(f"project root does not exist: {root}")
    if not name.strip() or not goal.strip():
        raise ProjectMemoryError("name and goal are required")
    if source_commit and not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ProjectMemoryError("source commit must be a full lowercase commit SHA")
    if base.exists():
        raise ProjectMemoryError(f"existing project memory will not be overwritten: {base}")
    if not execute:
        return {"status": "planned", "writes": plan}
    payloads = initial_payloads(
        name, goal, profile, source_repository, source_commit, deployment
    )
    with MemoryLock(root, initialization=True):
        temporary = pathlib.Path(tempfile.mkdtemp(dir=root, prefix=".divan.init."))
        try:
            for directory in REQUIRED_DIRECTORIES:
                (temporary / directory).mkdir(parents=True)
            for filename, payload in payloads.items():
                atomic_write_json(temporary / filename, payload)
            atomic_write_text(
                temporary / "progress.md",
                render_progress(
                    payloads["project.json"], payloads["tasks.json"], payloads["current-state.json"]
                ),
            )
            event = {
                "at": utc_now(),
                "event": "memory_initialized",
                "details": {"project_id": payloads["project.json"]["project_id"]},
            }
            atomic_write_text(
                temporary / "history" / "events.jsonl",
                json.dumps(event, ensure_ascii=False) + "\n",
            )
            os.replace(temporary, base)
        finally:
            shutil.rmtree(temporary, ignore_errors=True)
    return {"status": "initialized", "writes": plan}

def load_memory(project_root: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    base = memory_root(project_root)
    return (
        read_json(base / "project.json"),
        read_json(base / "tasks.json"),
        read_json(base / "current-state.json"),
    )

def append_event(project_root: pathlib.Path, event: str, details: dict[str, Any]) -> None:
    path = memory_root(project_root) / "history" / "events.jsonl"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    row = {"at": utc_now(), "event": event, "details": details}
    atomic_write_text(path, existing + json.dumps(row, ensure_ascii=False) + "\n")

def _task_groups(tasks: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = tasks.get("tasks")
    if not isinstance(rows, list):
        return [], []
    completed: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("status") == "completed":
            completed.append(row)
        elif row.get("status") in {"pending", "blocked"}:
            remaining.append(row)
    return completed, remaining


def _active_task_text(tasks: dict[str, Any], active_task: object) -> str:
    rows = tasks.get("tasks")
    if not isinstance(rows, list):
        return "None"
    for row in rows:
        if isinstance(row, dict) and row.get("id") == active_task:
            return f"{row['id']}: {row['title']}"
    return "None"


def _task_lines(rows: list[dict[str, Any]], include_status: bool = False) -> str:
    if not rows:
        return "- None."
    lines: list[str] = []
    for row in rows:
        suffix = f" ({row['status']})" if include_status else ""
        lines.append(f"- {row['id']}: {row['title']}{suffix}")
    return "\n".join(lines)


def render_progress(project: dict[str, Any], tasks: dict[str, Any],
                    current: dict[str, Any]) -> str:
    completed, remaining = _task_groups(tasks)
    active_text = _active_task_text(tasks, current.get("active_task"))
    return (
        "# Divan Project Progress\n\n"
        f"Updated: {utc_now()}\n\n"
        "## Project\n\n"
        f"- Name: {project.get('name')}\n"
        f"- Goal: {project.get('goal')}\n"
        f"- Lifecycle: {project.get('lifecycle_state')}\n\n"
        "## Active task\n\n"
        f"{active_text}\n\n"
        "## Completed\n\n"
        f"{_task_lines(completed[-10:])}\n\n"
        "## Remaining\n\n"
        f"{_task_lines(remaining[:10], include_status=True)}\n\n"
        "## Blocker\n\n"
        f"{current.get('blocker') or 'None'}\n\n"
        "## Next exact action\n\n"
        f"{current.get('next_action') or 'Not recorded.'}\n"
    )
