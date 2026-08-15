"""Project-level Agency OS status derived from verified Divan state.

This module is intentionally read-only. It projects the existing goal receipt,
Seyir cursor and materialized work packages into one project-level status for
human-facing clients without becoming a second source of truth.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from . import goals, seyir_state
from .task_model import TaskState
from .task_store import TaskStore

_COMPLETED = {TaskState.MERGED.value, TaskState.RELEASED.value}
_ACTIVE = {TaskState.RUNNING.value, TaskState.REVIEW.value, TaskState.RETRY.value}
_VERIFYING = {TaskState.REVIEW.value, TaskState.PASSED.value}


def _phase(goal_state: str | None, states: Counter[str], task_count: int) -> str:
    if goal_state in {"BLOCKED", "FAILED"} or states[TaskState.BLOCKED.value]:
        return "BLOCKED"
    if goal_state == "OBSERVED":
        return "LEARNING"
    if goal_state == "RELEASED":
        return "RELEASED"
    if goal_state == "PREVIEWED":
        return "STAGING_ACCEPTANCE"
    if states[TaskState.APPROVAL.value]:
        return "OWNER_DECISION"
    if states[TaskState.REVIEW.value] or states[TaskState.PASSED.value]:
        return "VERIFICATION"
    if states[TaskState.RUNNING.value] or states[TaskState.RETRY.value]:
        return "IMPLEMENTATION"
    if task_count and sum(states[name] for name in _COMPLETED) == task_count:
        return "DELIVERY_READY"
    if goal_state == "VERIFIED":
        return "DELIVERY_READY"
    if task_count:
        return "READY_FOR_EXECUTION"
    if goal_state is not None:
        return "PLAN_REVIEW"
    return "INTAKE"


def _authority(tasks: list[Mapping[str, Any]]) -> str:
    if not tasks:
        return "not-granted"
    granted = sum(
        1
        for task in tasks
        if isinstance(task.get("mandate_id"), str) and str(task["mandate_id"]).strip()
    )
    if granted == 0:
        return "not-granted"
    if granted == len(tasks):
        return "granted"
    return "partial"


def _base_result(root: Path, goal_count: int) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "project": root.name,
        "project_root": str(root),
        "active_goal_id": None,
        "goal_state": None,
        "goal_count": goal_count,
        "phase": "INTAKE",
        "attention": "none",
        "execution_authority": "not-granted",
        "work_packages": {
            "total": 0,
            "completed": 0,
            "active": 0,
            "verifying": 0,
            "blocked": 0,
            "awaiting_owner": 0,
            "ready_task_ids": [],
            "state_counts": {},
        },
        "state_health": "healthy",
    }


def build_project_agency_status(
    project: Path | str,
    task_store: TaskStore,
) -> dict[str, Any]:
    """Return one fail-closed, read-only Agency OS project status projection."""
    root = Path(project).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("agency status requires an existing project directory")

    inventory = goals.goal_status(root)
    goal_rows = inventory.get("goals", [])
    if not isinstance(goal_rows, list):
        raise ValueError("goal inventory is invalid")
    valid_goal_count = sum(
        1 for row in goal_rows if isinstance(row, Mapping) and row.get("ok") is True
    )
    result = _base_result(root, valid_goal_count)

    state_path = root / ".divan" / "state" / "seyir.json"
    if not state_path.exists():
        return result

    try:
        active = seyir_state.load(root)
    except ValueError:
        result.update(
            {
                "phase": "BLOCKED",
                "attention": "blocked",
                "state_health": "invalid",
                "state_problem": "Active project state could not be verified.",
            }
        )
        return result

    goal_id = active["active_goal_id"]
    verification = goals.goal_status(root, goal_id)
    if verification.get("ok") is not True:
        result.update(
            {
                "active_goal_id": goal_id,
                "phase": "BLOCKED",
                "attention": "blocked",
                "state_health": "invalid",
                "state_problem": "Active goal receipt could not be verified.",
            }
        )
        return result

    task_snapshot = task_store.goal_tasks(root, goal_id)
    raw_tasks = task_snapshot.get("tasks", [])
    if not isinstance(raw_tasks, list):
        raise ValueError("goal task inventory is invalid")
    tasks = [task for task in raw_tasks if isinstance(task, Mapping)]
    states: Counter[str] = Counter(str(task.get("state", "")) for task in tasks)
    goal_state = str(verification.get("state")) if verification.get("state") else None
    phase = _phase(goal_state, states, len(tasks))
    attention = (
        "blocked"
        if phase == "BLOCKED"
        else "owner-decision"
        if phase == "OWNER_DECISION"
        else "none"
    )

    result.update(
        {
            "active_goal_id": goal_id,
            "goal_state": goal_state,
            "phase": phase,
            "attention": attention,
            "execution_authority": _authority(tasks),
            "work_packages": {
                "total": len(tasks),
                "completed": sum(states[name] for name in _COMPLETED),
                "active": sum(states[name] for name in _ACTIVE),
                "verifying": sum(states[name] for name in _VERIFYING),
                "blocked": states[TaskState.BLOCKED.value],
                "awaiting_owner": states[TaskState.APPROVAL.value],
                "ready_task_ids": list(task_snapshot.get("ready_task_ids", [])),
                "state_counts": dict(sorted(states.items())),
            },
        }
    )
    return result
