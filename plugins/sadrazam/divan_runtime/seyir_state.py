"""Canonical active-goal and task progress state for Divan Seyir."""

from __future__ import annotations

import json
import os
import pathlib
import tempfile
from typing import Any

from . import receipts

SCHEMA_VERSION = 1
STATE_PATH = pathlib.PurePosixPath(".divan/state/seyir.json")
STATE_KEYS = {
    "schema_version",
    "active_goal_id",
    "receipt_event_hash",
    "completed_task_ids",
    "current_task_id",
    "next_task_id",
}


def _root(project: pathlib.Path | str) -> pathlib.Path:
    root = pathlib.Path(project).resolve()
    if not root.is_dir():
        raise ValueError(f"project directory does not exist: {root}")
    return root


def _state_path(root: pathlib.Path) -> pathlib.Path:
    path = root.joinpath(*STATE_PATH.parts)
    cursor = root
    for part in STATE_PATH.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("Seyir state path cannot use a symlink")
    try:
        path.resolve(strict=False).relative_to(root)
    except ValueError as error:
        raise ValueError("Seyir state path escapes project") from error
    return path


def _receipt(root: pathlib.Path, goal_id: str) -> tuple[pathlib.Path, dict[str, Any]]:
    if receipts.GOAL_ID_PATTERN.fullmatch(goal_id) is None:
        raise ValueError("Seyir active goal identifier is invalid")
    path = root / ".divan" / "evidence" / goal_id / "receipt.json"
    verification = receipts.verify_receipt(path)
    if not verification.get("ok"):
        raise ValueError("Seyir active goal receipt is not valid")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("Seyir active goal receipt is unreadable") from error
    return path, value


def _task_ids(root: pathlib.Path, goal_id: str) -> list[str]:
    path = root / ".divan" / "specs" / goal_id / "route.json"
    try:
        route = json.loads(path.read_text(encoding="utf-8"))
        tasks = route["execution_plan"]["tasks"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError("Seyir goal route is unreadable") from error
    values = [
        str(task["id"])
        for task in tasks
        if isinstance(task, dict) and isinstance(task.get("id"), str)
    ]
    if not values or len(values) != len(tasks) or len(values) != len(set(values)):
        raise ValueError("Seyir goal route has an invalid task inventory")
    return values


def _event_hashes(receipt: dict[str, Any]) -> list[str]:
    events = receipt.get("events")
    if not isinstance(events, list) or not events:
        raise ValueError("Seyir active goal receipt has no events")
    values = [
        str(event.get("hash", ""))
        for event in events
        if isinstance(event, dict)
    ]
    if len(values) != len(events) or any(len(value) != 64 for value in values):
        raise ValueError("Seyir active goal receipt has invalid event hashes")
    return values


def _validate_task_state(
    known: list[str],
    completed: list[str],
    current: str | None,
    next_task: str | None,
) -> None:
    if len(completed) != len(set(completed)):
        raise ValueError("completed tasks must be unique")
    unknown = sorted(
        ({*completed, *([current] if current else []), *([next_task] if next_task else [])})
        - set(known)
    )
    if unknown:
        raise ValueError(f"Seyir state contains unknown task: {', '.join(unknown)}")
    if current in completed:
        raise ValueError("current task cannot already be completed")
    if next_task in completed:
        raise ValueError("next task cannot already be completed")
    if current is not None and current == next_task:
        raise ValueError("current task and next task must differ")
    observed_order = [item for item in known if item in set(completed)]
    if completed != observed_order:
        raise ValueError("completed tasks must follow the route order")


def _value(
    goal_id: str,
    receipt_hash: str,
    completed: list[str],
    current: str | None,
    next_task: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "active_goal_id": goal_id,
        "receipt_event_hash": receipt_hash,
        "completed_task_ids": completed,
        "current_task_id": current,
        "next_task_id": next_task,
    }


def _atomic_write(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def initialize(
    project: pathlib.Path | str,
    goal_id: str,
    *,
    execute: bool,
) -> dict[str, Any]:
    """Select one verified goal and initialize its task cursor."""
    root = _root(project)
    _, receipt = _receipt(root, goal_id)
    tasks = _task_ids(root, goal_id)
    hashes = _event_hashes(receipt)
    desired = _value(
        goal_id,
        hashes[-1],
        [],
        tasks[0],
        tasks[1] if len(tasks) > 1 else None,
    )
    result = {"status": "planned", **desired}
    if execute:
        _atomic_write(_state_path(root), desired)
        result["status"] = "active"
    return result


def load(project: pathlib.Path | str) -> dict[str, Any]:
    """Load and fail-closed validate the active Seyir state."""
    root = _root(project)
    path = _state_path(root)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("Seyir state is unavailable") from error
    if not isinstance(value, dict) or set(value) != STATE_KEYS:
        raise ValueError("Seyir state schema is invalid")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Seyir state schema version is invalid")
    goal_id = value.get("active_goal_id")
    if not isinstance(goal_id, str):
        raise ValueError("Seyir active goal identifier is invalid")
    _, receipt = _receipt(root, goal_id)
    receipt_hash = value.get("receipt_event_hash")
    if receipt_hash not in _event_hashes(receipt):
        raise ValueError("Seyir state is not bound to the active receipt")
    known = _task_ids(root, goal_id)
    completed = value.get("completed_task_ids")
    current = value.get("current_task_id")
    next_task = value.get("next_task_id")
    if (
        not isinstance(completed, list)
        or any(not isinstance(item, str) for item in completed)
        or (current is not None and not isinstance(current, str))
        or (next_task is not None and not isinstance(next_task, str))
    ):
        raise ValueError("Seyir task state schema is invalid")
    _validate_task_state(known, completed, current, next_task)
    return value


def update(
    project: pathlib.Path | str,
    goal_id: str,
    *,
    completed_task_ids: list[str],
    current_task_id: str | None,
    next_task_id: str | None,
    execute: bool,
) -> dict[str, Any]:
    """Plan or atomically record task progress for the active goal."""
    root = _root(project)
    active = load(root)
    if active["active_goal_id"] != goal_id:
        raise ValueError("Seyir progress may update only the active goal")
    _, receipt = _receipt(root, goal_id)
    known = _task_ids(root, goal_id)
    completed = list(completed_task_ids)
    _validate_task_state(known, completed, current_task_id, next_task_id)
    desired = _value(
        goal_id,
        _event_hashes(receipt)[-1],
        completed,
        current_task_id,
        next_task_id,
    )
    result = {"status": "planned", **desired}
    if execute:
        _atomic_write(_state_path(root), desired)
        result["status"] = "updated"
    return result
