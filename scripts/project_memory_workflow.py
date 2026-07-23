#!/usr/bin/env python3
"""Task, lifecycle, checkpoint, decision and lesson operations for Divan memory."""
from __future__ import annotations

import pathlib
import re
import uuid
from typing import Any

from project_memory_store import (
    LIFECYCLE_STATES,
    MemoryLock,
    ProjectMemoryError,
    append_event,
    atomic_write_json,
    atomic_write_text,
    git_snapshot,
    load_memory,
    memory_root,
    render_progress,
    slugify,
    utc_now,
)
from project_memory_validation import validate_memory

ALLOWED_TRANSITIONS = {
    "CREATED": {"BASELINED"},
    "BASELINED": {"PLANNED"},
    "PLANNED": {"IMPLEMENTING"},
    "IMPLEMENTING": {"VERIFYING"},
    "VERIFYING": {"REVIEWING", "IMPLEMENTING"},
    "REVIEWING": {"READY_TO_SHIP", "IMPLEMENTING"},
    "READY_TO_SHIP": {"SHIPPED", "IMPLEMENTING"},
    "SHIPPED": {"MAINTENANCE"},
    "MAINTENANCE": {"IMPLEMENTING"},
}

def _ready_memory(project_root: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    errors = validate_memory(project_root)
    if errors:
        raise ProjectMemoryError("; ".join(errors))
    return load_memory(project_root)

def _task(tasks: dict[str, Any], task_id: str) -> dict[str, Any]:
    for row in tasks["tasks"]:
        if row["id"] == task_id:
            return row
    raise ProjectMemoryError(f"unknown task: {task_id}")

def _write_core(project_root: pathlib.Path, project: dict[str, Any],
                tasks: dict[str, Any], current: dict[str, Any]) -> None:
    base = memory_root(project_root)
    atomic_write_json(base / "project.json", project)
    atomic_write_json(base / "tasks.json", tasks)
    atomic_write_json(base / "current-state.json", current)
    atomic_write_text(base / "progress.md", render_progress(project, tasks, current))

def _mutation_result(action: str, execute: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"status": "ok" if execute else "planned", "action": action, **details}

def add_task(
    project_root: pathlib.Path,
    title: str,
    description: str = "",
    depends_on: list[str] | None = None,
    acceptance: list[str] | None = None,
    execute: bool = False,
) -> dict[str, Any]:
    project, tasks, current = _ready_memory(project_root)
    dependencies = list(dict.fromkeys(depends_on or []))
    for dependency in dependencies:
        _task(tasks, dependency)
    if not title.strip():
        raise ProjectMemoryError("task title is required")
    task_id = f"TASK-{tasks['next_sequence']:03d}"
    row = {
        "id": task_id,
        "title": title.strip(),
        "description": description.strip(),
        "status": "pending",
        "depends_on": dependencies,
        "acceptance_criteria": [item.strip() for item in acceptance or [] if item.strip()],
        "evidence": [],
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "completed_at": None,
        "blocker": None,
    }
    result = _mutation_result("task_add", execute, {"task": row})
    if not execute:
        return result
    with MemoryLock(project_root):
        tasks["tasks"].append(row)
        tasks["next_sequence"] += 1
        project["updated_at"] = utc_now()
        _write_core(project_root, project, tasks, current)
        append_event(project_root, "task_added", {"task_id": task_id, "title": row["title"]})
    return result

def start_task(project_root: pathlib.Path, task_id: str,
               execute: bool = False) -> dict[str, Any]:
    project, tasks, current = _ready_memory(project_root)
    row = _task(tasks, task_id)
    if current["active_task"] and current["active_task"] != task_id:
        raise ProjectMemoryError(f"another task is active: {current['active_task']}")
    if row["status"] not in {"pending", "blocked"}:
        raise ProjectMemoryError(f"task cannot start from status {row['status']}")
    completed = {item["id"] for item in tasks["tasks"] if item["status"] == "completed"}
    missing = [item for item in row["depends_on"] if item not in completed]
    if missing:
        raise ProjectMemoryError(f"task dependencies are incomplete: {', '.join(missing)}")
    result = _mutation_result("task_start", execute, {"task_id": task_id})
    if not execute:
        return result
    with MemoryLock(project_root):
        row.update({"status": "in_progress", "updated_at": utc_now(), "blocker": None})
        current.update(
            {
                "active_task": task_id,
                "next_action": row["title"],
                "blocked": False,
                "blocker": None,
            }
        )
        project["updated_at"] = utc_now()
        _write_core(project_root, project, tasks, current)
        append_event(project_root, "task_started", {"task_id": task_id})
    return result

def block_task(project_root: pathlib.Path, task_id: str, reason: str,
               next_action: str, execute: bool = False) -> dict[str, Any]:
    project, tasks, current = _ready_memory(project_root)
    row = _task(tasks, task_id)
    if row["status"] != "in_progress" or current["active_task"] != task_id:
        raise ProjectMemoryError("only the active in-progress task can be blocked")
    if not reason.strip() or not next_action.strip():
        raise ProjectMemoryError("blocker reason and next action are required")
    result = _mutation_result(
        "task_block", execute, {"task_id": task_id, "reason": reason.strip()}
    )
    if not execute:
        return result
    with MemoryLock(project_root):
        row.update({"status": "blocked", "updated_at": utc_now(), "blocker": reason.strip()})
        current.update(
            {
                "active_task": None,
                "blocked": True,
                "blocker": reason.strip(),
                "next_action": next_action.strip(),
            }
        )
        project["updated_at"] = utc_now()
        _write_core(project_root, project, tasks, current)
        append_event(project_root, "task_blocked", {"task_id": task_id, "reason": reason.strip()})
    return result

def _evidence_paths(project_root: pathlib.Path, raw_paths: list[str]) -> list[str]:
    if not raw_paths:
        raise ProjectMemoryError("at least one evidence file is required")
    root = project_root.resolve()
    normalized: list[str] = []
    for raw in raw_paths:
        candidate = pathlib.Path(raw)
        path = candidate if candidate.is_absolute() else root / candidate
        resolved = path.resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            raise ProjectMemoryError(f"evidence is missing or outside project: {raw}")
        normalized.append(resolved.relative_to(root).as_posix())
    return list(dict.fromkeys(normalized))

def complete_task(project_root: pathlib.Path, task_id: str, evidence: list[str],
                  next_action: str, execute: bool = False) -> dict[str, Any]:
    project, tasks, current = _ready_memory(project_root)
    row = _task(tasks, task_id)
    if row["status"] != "in_progress" or current["active_task"] != task_id:
        raise ProjectMemoryError("only the active in-progress task can be completed")
    proof = _evidence_paths(project_root, evidence)
    result = _mutation_result(
        "task_complete", execute, {"task_id": task_id, "evidence": proof}
    )
    if not execute:
        return result
    now = utc_now()
    with MemoryLock(project_root):
        row.update(
            {
                "status": "completed",
                "evidence": proof,
                "updated_at": now,
                "completed_at": now,
                "blocker": None,
            }
        )
        current.update(
            {
                "active_task": None,
                "blocked": False,
                "blocker": None,
                "next_action": next_action.strip() or "Select the next ready task.",
            }
        )
        project["updated_at"] = now
        _write_core(project_root, project, tasks, current)
        append_event(project_root, "task_completed", {"task_id": task_id, "evidence": proof})
    return result

def transition(project_root: pathlib.Path, target: str, evidence: list[str],
               confirm_ship: bool = False, execute: bool = False) -> dict[str, Any]:
    project, tasks, current = _ready_memory(project_root)
    target = target.upper()
    current_state = project["lifecycle_state"]
    if target not in LIFECYCLE_STATES:
        raise ProjectMemoryError(f"unknown lifecycle state: {target}")
    if target not in ALLOWED_TRANSITIONS[current_state]:
        raise ProjectMemoryError(f"invalid transition: {current_state} -> {target}")
    if target == "SHIPPED" and not confirm_ship:
        raise ProjectMemoryError("SHIPPED requires --confirm-ship")
    proof = _evidence_paths(project_root, evidence)
    if target == "PLANNED" and not tasks["tasks"]:
        raise ProjectMemoryError("PLANNED requires at least one task")
    if target == "IMPLEMENTING" and not current["active_task"]:
        raise ProjectMemoryError("IMPLEMENTING requires an active task")
    result = _mutation_result(
        "lifecycle_transition",
        execute,
        {"from": current_state, "to": target, "evidence": proof},
    )
    if not execute:
        return result
    with MemoryLock(project_root):
        project.update({"lifecycle_state": target, "updated_at": utc_now()})
        current["last_transition_evidence"] = proof
        _write_core(project_root, project, tasks, current)
        append_event(
            project_root,
            "lifecycle_transition",
            {"from": current_state, "to": target, "evidence": proof},
        )
    return result

def _handoff_body(project: dict[str, Any], current: dict[str, Any],
                  done: list[str], remaining: list[str], warnings: list[str]) -> str:
    def section(values: list[str]) -> str:
        return "\n".join(f"- {value}" for value in values) or "- None."

    return (
        f"# Project handoff\n\n"
        f"Created: {utc_now()}\n\n"
        f"## Project\n\n- {project['name']}\n- Lifecycle: {project['lifecycle_state']}\n\n"
        f"## Active task\n\n- {current.get('active_task') or 'None'}\n\n"
        f"## Done this session\n\n{section(done)}\n\n"
        f"## Remaining\n\n{section(remaining)}\n\n"
        f"## Warnings\n\n{section(warnings)}\n\n"
        f"## Next exact action\n\n{current.get('next_action')}\n"
    )

def checkpoint(
    project_root: pathlib.Path,
    next_action: str,
    done: list[str] | None = None,
    remaining: list[str] | None = None,
    warnings: list[str] | None = None,
    gate: str | None = None,
    evidence: list[str] | None = None,
    execute: bool = False,
) -> dict[str, Any]:
    project, tasks, current = _ready_memory(project_root)
    if not next_action.strip():
        raise ProjectMemoryError("next action is required")
    proof = _evidence_paths(project_root, evidence) if evidence else []
    branch, commit = git_snapshot(project_root)
    stamp = utc_now().replace("-", "").replace(":", "")
    token = uuid.uuid4().hex[:6]
    relative_handoff = f".divan/handoffs/{stamp}-{token}.md"
    result = _mutation_result(
        "checkpoint",
        execute,
        {"handoff": relative_handoff, "branch": branch, "commit": commit},
    )
    if not execute:
        return result
    now = utc_now()
    with MemoryLock(project_root):
        current.update(
            {
                "active_branch": branch,
                "last_commit": commit,
                "last_successful_gate": gate or current.get("last_successful_gate"),
                "next_action": next_action.strip(),
                "last_checkpoint_at": now,
                "last_handoff": relative_handoff,
            }
        )
        handoff = _handoff_body(
            project, current, done or [], remaining or [], warnings or []
        )
        atomic_write_text(project_root / relative_handoff, handoff)
        snapshot = {
            "schema_version": 1,
            "recorded_at": now,
            "project": project,
            "current_state": current,
            "task_counts": _task_counts(tasks),
            "evidence": proof,
        }
        history_path = memory_root(project_root) / "history" / f"checkpoint-{stamp}-{token}.json"
        atomic_write_json(history_path, snapshot)
        project["updated_at"] = now
        _write_core(project_root, project, tasks, current)
        append_event(
            project_root,
            "checkpoint",
            {"handoff": relative_handoff, "evidence": proof, "gate": gate},
        )
    return result

def _task_counts(tasks: dict[str, Any]) -> dict[str, int]:
    counts = {"pending": 0, "in_progress": 0, "blocked": 0, "completed": 0}
    for row in tasks["tasks"]:
        counts[row["status"]] += 1
    return counts

def resume_summary(project_root: pathlib.Path) -> dict[str, Any]:
    project, tasks, current = _ready_memory(project_root)
    active = None
    if current["active_task"]:
        active = _task(tasks, current["active_task"])
    completed = {row["id"] for row in tasks["tasks"] if row["status"] == "completed"}
    ready = [
        row
        for row in tasks["tasks"]
        if row["status"] == "pending" and set(row["depends_on"]).issubset(completed)
    ]
    return {
        "project": project["name"],
        "goal": project["goal"],
        "lifecycle_state": project["lifecycle_state"],
        "active_task": active,
        "next_ready_task": ready[0] if ready else None,
        "branch": current["active_branch"],
        "last_commit": current["last_commit"],
        "last_successful_gate": current["last_successful_gate"],
        "next_action": current["next_action"],
        "blocked": current["blocked"],
        "blocker": current["blocker"],
        "last_handoff": current["last_handoff"],
        "task_counts": _task_counts(tasks),
    }

def add_decision(project_root: pathlib.Path, title: str, context: str, choice: str,
                 consequences: list[str], execute: bool = False) -> dict[str, Any]:
    _ready_memory(project_root)
    directory = memory_root(project_root) / "decisions"
    numbers = [
        int(match.group(1))
        for path in directory.glob("[0-9][0-9][0-9][0-9]-*.md")
        if (match := re.match(r"^(\d{4})-", path.name))
    ]
    number = max(numbers, default=0) + 1
    relative = f".divan/decisions/{number:04d}-{slugify(title)}.md"
    result = _mutation_result("decision_add", execute, {"path": relative})
    if not execute:
        return result
    body = (
        f"# ADR {number:04d}: {title.strip()}\n\n"
        f"Date: {utc_now()}\n\n## Context\n\n{context.strip()}\n\n"
        f"## Decision\n\n{choice.strip()}\n\n## Consequences\n\n"
        + ("\n".join(f"- {item.strip()}" for item in consequences if item.strip()) or "- None recorded.")
        + "\n"
    )
    with MemoryLock(project_root):
        atomic_write_text(project_root / relative, body)
        append_event(project_root, "decision_added", {"path": relative, "title": title.strip()})
    return result

def add_lesson(project_root: pathlib.Path, topic: str, text: str,
               execute: bool = False) -> dict[str, Any]:
    _ready_memory(project_root)
    relative = f".divan/lessons/{slugify(topic)}.md"
    result = _mutation_result("lesson_add", execute, {"path": relative})
    if not execute:
        return result
    path = project_root / relative
    existing = path.read_text(encoding="utf-8") if path.exists() else f"# {topic.strip()}\n"
    body = existing.rstrip() + f"\n\n## {utc_now()}\n\n{text.strip()}\n"
    with MemoryLock(project_root):
        atomic_write_text(path, body)
        append_event(project_root, "lesson_added", {"path": relative, "topic": topic.strip()})
    return result
