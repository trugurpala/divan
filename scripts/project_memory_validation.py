#!/usr/bin/env python3
"""Fail-closed validation for Divan durable project memory."""
from __future__ import annotations

import pathlib
from typing import Any

from project_memory_store import (
    LIFECYCLE_STATES,
    MEMORY_DIR,
    REQUIRED_DIRECTORIES,
    REQUIRED_FILES,
    SCHEMA_VERSION,
    TASK_ID_RE,
    TASK_STATUSES,
    ProjectMemoryError,
    load_memory,
    memory_root,
)


def _layout_errors(project_root: pathlib.Path) -> list[str]:
    base = memory_root(project_root)
    errors: list[str] = []
    for directory in REQUIRED_DIRECTORIES:
        if not (base / directory).is_dir():
            errors.append(f"missing memory directory: {MEMORY_DIR}/{directory}")
    for filename in REQUIRED_FILES:
        path = base / filename
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            content = ""
        if not content.strip():
            errors.append(f"missing or empty memory file: {MEMORY_DIR}/{filename}")
    return errors


def _schema_errors(project: dict[str, Any], tasks: dict[str, Any],
                   current: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for label, payload in (("project", project), ("tasks", tasks), ("current-state", current)):
        if payload.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{label}.schema_version must be {SCHEMA_VERSION}")
    return errors


def _project_shape_errors(project: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if project.get("lifecycle_state") not in LIFECYCLE_STATES:
        errors.append("project.lifecycle_state is invalid")
    if not isinstance(project.get("name"), str) or not project["name"].strip():
        errors.append("project.name must be a non-empty string")
    if not isinstance(project.get("goal"), str) or not project["goal"].strip():
        errors.append("project.goal must be a non-empty string")
    return errors


def _tasks_shape_errors(tasks: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sequence = tasks.get("next_sequence")
    if not isinstance(sequence, int) or sequence < 1:
        errors.append("tasks.next_sequence must be a positive integer")
    if not isinstance(tasks.get("tasks"), list):
        errors.append("tasks.tasks must be a list")
    return errors


def _current_shape_errors(current: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(current.get("last_transition_evidence"), list):
        errors.append("current-state.last_transition_evidence must be a list")
    if not isinstance(current.get("blocked"), bool):
        errors.append("current-state.blocked must be boolean")
    if not isinstance(current.get("next_action"), str) or not current["next_action"].strip():
        errors.append("current-state.next_action must be a non-empty string")
    return errors


def _required_shape_errors(
    project: dict[str, Any], tasks: dict[str, Any], current: dict[str, Any]
) -> list[str]:
    return [
        *_schema_errors(project, tasks, current),
        *_project_shape_errors(project),
        *_tasks_shape_errors(tasks),
        *_current_shape_errors(current),
    ]


def _task_identity_errors(task: dict[str, Any], prefix: str) -> tuple[list[str], str | None]:
    errors: list[str] = []
    task_id = task.get("id")
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        errors.append(f"{prefix}.id is invalid")
        task_id = None
    if not isinstance(task.get("title"), str) or not task["title"].strip():
        errors.append(f"{prefix}.title must be a non-empty string")
    return errors, task_id


def _task_list_errors(task: dict[str, Any], prefix: str) -> list[str]:
    errors: list[str] = []
    for field in ("depends_on", "acceptance_criteria", "evidence"):
        values = task.get(field)
        if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
            errors.append(f"{prefix}.{field} must be a string list")
    return errors


def _task_status_errors(task: dict[str, Any], prefix: str) -> list[str]:
    errors: list[str] = []
    status = task.get("status")
    if status not in TASK_STATUSES:
        errors.append(f"{prefix}.status is invalid")
    if status == "blocked" and not task.get("blocker"):
        errors.append(f"{prefix}.blocked task requires blocker")
    if status == "completed" and not task.get("completed_at"):
        errors.append(f"{prefix}.completed task requires completed_at")
    return errors


def _task_row_errors(task: object, index: int) -> tuple[list[str], str | None]:
    prefix = f"tasks[{index}]"
    if not isinstance(task, dict):
        return [f"{prefix} must be an object"], None
    identity_errors, task_id = _task_identity_errors(task, prefix)
    return [
        *identity_errors,
        *_task_list_errors(task, prefix),
        *_task_status_errors(task, prefix),
    ], task_id

def _task_index(rows: list[Any]) -> tuple[list[str], set[str], list[str]]:
    errors: list[str] = []
    ids: set[str] = set()
    in_progress: list[str] = []
    for index, task in enumerate(rows):
        row_errors, task_id = _task_row_errors(task, index)
        errors.extend(row_errors)
        if task_id is None:
            continue
        if task_id in ids:
            errors.append(f"duplicate task id: {task_id}")
        ids.add(task_id)
        if isinstance(task, dict) and task.get("status") == "in_progress":
            in_progress.append(task_id)
    return errors, ids, in_progress


def _dependency_errors(rows: list[Any], ids: set[str]) -> list[str]:
    errors: list[str] = []
    for index, task in enumerate(rows):
        if not isinstance(task, dict) or not isinstance(task.get("depends_on"), list):
            continue
        task_id = task.get("id")
        for dependency in task["depends_on"]:
            if dependency == task_id:
                errors.append(f"tasks[{index}] cannot depend on itself")
            elif dependency not in ids:
                errors.append(f"tasks[{index}] has unknown dependency: {dependency}")
    return errors


def _active_task_errors(current: dict[str, Any], ids: set[str],
                        in_progress: list[str]) -> list[str]:
    errors: list[str] = []
    active = current.get("active_task")
    if len(in_progress) > 1:
        errors.append("only one task may be in_progress")
    if active is not None and active not in ids:
        errors.append("current-state.active_task does not exist")
    if active is not None and active not in in_progress:
        errors.append("current-state.active_task must be in_progress")
    if in_progress and active != in_progress[0]:
        errors.append("in_progress task must match current-state.active_task")
    return errors


def _sequence_errors(tasks_payload: dict[str, Any], ids: set[str]) -> list[str]:
    sequence = tasks_payload.get("next_sequence")
    if not isinstance(sequence, int):
        return []
    numbers = [int(match.group(1)) for task_id in ids if (match := TASK_ID_RE.fullmatch(task_id))]
    if numbers and sequence <= max(numbers):
        return ["tasks.next_sequence must be greater than every allocated task id"]
    return []


def _task_errors(tasks_payload: dict[str, Any],
                 current: dict[str, Any]) -> list[str]:
    rows = tasks_payload.get("tasks")
    if not isinstance(rows, list):
        return []
    errors, ids, in_progress = _task_index(rows)
    errors.extend(_dependency_errors(rows, ids))
    errors.extend(_active_task_errors(current, ids, in_progress))
    errors.extend(_sequence_errors(tasks_payload, ids))
    return errors


def _evidence_row_errors(project_root: pathlib.Path, task: dict[str, Any]) -> list[str]:
    if task.get("status") != "completed":
        return []
    evidence = task.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return [f"{task.get('id')}: completed task requires evidence"]
    errors: list[str] = []
    root = project_root.resolve()
    for relative in evidence:
        path = root / relative
        try:
            resolved = path.resolve()
        except OSError:
            errors.append(f"{task.get('id')}: evidence cannot be resolved: {relative}")
            continue
        if not resolved.is_relative_to(root) or not path.is_file():
            errors.append(f"{task.get('id')}: evidence is missing or unsafe: {relative}")
    return errors


def _completed_evidence_errors(
    project_root: pathlib.Path, tasks_payload: dict[str, Any]
) -> list[str]:
    rows = tasks_payload.get("tasks")
    if not isinstance(rows, list):
        return []
    errors: list[str] = []
    for task in rows:
        if isinstance(task, dict):
            errors.extend(_evidence_row_errors(project_root, task))
    return errors


def _current_state_errors(project_root: pathlib.Path,
                          current: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    last_handoff = current.get("last_handoff")
    if last_handoff and not (project_root / str(last_handoff)).is_file():
        errors.append("current-state.last_handoff does not exist")
    if current.get("blocked") and not current.get("blocker"):
        errors.append("blocked state requires a blocker")
    if not current.get("blocked") and current.get("blocker"):
        errors.append("unblocked state cannot retain a blocker")
    return errors


def validate_memory(project_root: pathlib.Path) -> list[str]:
    root = project_root.resolve()
    errors = _layout_errors(root)
    if errors:
        return errors
    try:
        project, tasks, current = load_memory(root)
    except ProjectMemoryError as exc:
        return [str(exc)]
    errors.extend(_required_shape_errors(project, tasks, current))
    errors.extend(_task_errors(tasks, current))
    errors.extend(_completed_evidence_errors(root, tasks))
    errors.extend(_current_state_errors(root, current))
    return errors
