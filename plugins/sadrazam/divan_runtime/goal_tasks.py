from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import goals
from .task_model import DivanTask, TaskState
from .task_store import TaskStore

_COMPLETE_DEPENDENCY_STATES = {TaskState.MERGED, TaskState.RELEASED}


def _verified_execution_plan(root: Path, goal_id: str) -> dict[str, Any]:
    verification = goals.goal_status(root, goal_id)
    if verification.get("ok") is not True:
        errors = verification.get("errors")
        detail = "; ".join(str(item) for item in errors or [])
        raise ValueError(f"goal receipt is not valid: {detail or goal_id}")
    route_relative = f".divan/specs/{goal_id}/route.json"
    artifacts = verification.get("artifacts")
    expected_digest = artifacts.get(route_relative) if isinstance(artifacts, dict) else None
    route_path = root / ".divan" / "specs" / goal_id / "route.json"
    if not isinstance(expected_digest, str):
        raise ValueError("verified goal receipt does not bind route.json")
    try:
        route_bytes = route_path.read_bytes()
    except OSError as error:
        raise ValueError("verified goal route is unreadable") from error
    if hashlib.sha256(route_bytes).hexdigest() != expected_digest:
        raise ValueError("verified goal route hash does not match receipt")
    try:
        route = json.loads(route_bytes.decode("utf-8"))
        execution = route["execution_plan"]
    except (UnicodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError("verified goal route is invalid") from error
    if not isinstance(execution, dict):
        raise ValueError("verified goal execution plan is invalid")
    return execution


def _route_tasks(execution: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = execution.get("tasks")
    if not isinstance(rows, list) or not rows:
        raise ValueError("goal execution plan has no tasks")
    tasks: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("goal execution task must be an object")
        identifier = row.get("id")
        dependencies = row.get("depends_on")
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError("goal execution task id is invalid")
        if identifier in identifiers:
            raise ValueError("goal execution task ids must be unique")
        if not isinstance(dependencies, list) or any(
            not isinstance(item, str) for item in dependencies
        ):
            raise ValueError(f"goal task dependencies are invalid: {identifier}")
        identifiers.add(identifier)
        tasks.append(row)
    for row in tasks:
        unknown = sorted(set(row["depends_on"]) - identifiers)
        if unknown:
            raise ValueError(
                f"goal task has unknown dependencies: {row['id']}: {', '.join(unknown)}"
            )
    return tasks


def _membership(rows: object, label: str) -> dict[str, str]:
    if not isinstance(rows, list):
        raise ValueError(f"goal {label} inventory is invalid")
    result: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"goal {label} entry is invalid")
        identifier = row.get("id")
        task_ids = row.get("task_ids")
        if not isinstance(identifier, str) or not isinstance(task_ids, list):
            raise ValueError(f"goal {label} entry is invalid")
        for task_id in task_ids:
            if not isinstance(task_id, str):
                raise ValueError(f"goal {label} task id is invalid")
            if task_id in result:
                raise ValueError(f"goal task belongs to multiple {label}s: {task_id}")
            result[task_id] = identifier
    return result


def _task_ids(root: Path, goal_id: str, rows: list[dict[str, Any]]) -> dict[str, str]:
    project_token = hashlib.sha256(
        os.path.normcase(str(root)).encode("utf-8")
    ).hexdigest()[:6].upper()
    goal_token = goal_id.removeprefix("goal-")[-6:].upper()
    return {
        str(row["id"]): f"DIV-{project_token}-{goal_token}-{index:03d}"
        for index, row in enumerate(rows, start=1)
    }


def _metadata(
    row: Mapping[str, Any],
    execution: Mapping[str, Any],
    task_ids: Mapping[str, str],
    workstreams: Mapping[str, str],
    sefers: Mapping[str, str],
    goal_id: str,
) -> dict[str, Any]:
    route_task_id = str(row["id"])
    return {
        "source": "nizam-i-sefer",
        "goal_id": goal_id,
        "route_id": execution.get("route_id"),
        "route_task_id": route_task_id,
        "depends_on": [task_ids[item] for item in row["depends_on"]],
        "route_depends_on": list(row["depends_on"]),
        "owner_role": row.get("owner_role"),
        "stage": row.get("stage"),
        "workflow": row.get("workflow"),
        "workstream_id": workstreams.get(route_task_id),
        "sefer_id": sefers.get(route_task_id),
        "required_evidence": list(row.get("required_evidence", [])),
        "commands": list(row.get("commands", [])),
    }


def _title(row: Mapping[str, Any]) -> str:
    stage = str(row.get("stage") or "work package").strip()
    role = str(row.get("owner_role") or "agent").strip()
    return f"{stage} · {role}"


def _same_materialization(existing: DivanTask, expected: DivanTask) -> bool:
    return (
        existing.title == expected.title
        and existing.project_root == expected.project_root
        and dict(existing.metadata) == dict(expected.metadata)
    )


def _ready(task: DivanTask, by_id: Mapping[str, DivanTask]) -> bool:
    if task.state not in {TaskState.PLANNED, TaskState.RETRY}:
        return False
    dependencies = task.metadata.get("depends_on", [])
    if not isinstance(dependencies, list):
        return False
    return all(
        dependency in by_id
        and by_id[dependency].state in _COMPLETE_DEPENDENCY_STATES
        for dependency in dependencies
    )


def materialize_goal(
    project: Path | str,
    goal_id: str,
    store: TaskStore,
) -> dict[str, Any]:
    """Create idempotent Desktop tasks from one receipt-verified goal route."""
    root = Path(project).resolve()
    execution = _verified_execution_plan(root, goal_id)
    rows = _route_tasks(execution)
    task_ids = _task_ids(root, goal_id, rows)
    workstreams = _membership(execution.get("workstreams"), "workstream")
    sefers = _membership(execution.get("sefers"), "sefer")
    created: list[str] = []
    retained: list[str] = []
    tasks: list[DivanTask] = []
    for row in rows:
        route_task_id = str(row["id"])
        expected = DivanTask(
            task_id=task_ids[route_task_id],
            title=_title(row),
            project_root=str(root),
            metadata=_metadata(
                row,
                execution,
                task_ids,
                workstreams,
                sefers,
                goal_id,
            ),
        ).transition(
            TaskState.PLANNED,
            "Materialized from receipt-verified Nizam-i Sefer goal route",
        )
        try:
            existing = store.load(expected.task_id)
        except FileNotFoundError:
            store.save(expected)
            tasks.append(expected)
            created.append(expected.task_id)
            continue
        if not _same_materialization(existing, expected):
            raise ValueError(f"materialized task conflicts with existing task: {expected.task_id}")
        tasks.append(existing)
        retained.append(existing.task_id)
    by_id = {task.task_id: task for task in tasks}
    orchestration = execution.get("orchestration", {})
    return {
        "schema_version": 1,
        "goal_id": goal_id,
        "route_id": execution.get("route_id"),
        "created_task_ids": created,
        "retained_task_ids": retained,
        "ready_task_ids": [task.task_id for task in tasks if _ready(task, by_id)],
        "task_count": len(tasks),
        "max_parallel_workstreams": (
            orchestration.get("max_parallel_workstreams")
            if isinstance(orchestration, dict)
            else None
        ),
        "tasks": [task.to_dict() for task in tasks],
        "execution_authority": "not-granted",
    }


def goal_tasks(project: Path | str, goal_id: str, store: TaskStore) -> dict[str, Any]:
    """Return materialized tasks and dependency-ready state for one project goal."""
    root = str(Path(project).resolve())
    tasks = [
        task
        for task in store.list()
        if task.project_root == root
        and task.metadata.get("goal_id") == goal_id
        and task.metadata.get("source") == "nizam-i-sefer"
    ]
    by_id = {task.task_id: task for task in tasks}
    return {
        "schema_version": 1,
        "goal_id": goal_id,
        "task_count": len(tasks),
        "ready_task_ids": [task.task_id for task in tasks if _ready(task, by_id)],
        "tasks": [task.to_dict() for task in tasks],
    }
