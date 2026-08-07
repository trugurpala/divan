from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Mapping


class TaskState(StrEnum):
    DRAFT = "draft"
    PLANNED = "planned"
    RUNNING = "running"
    REVIEW = "review"
    PASSED = "passed"
    RETRY = "retry"
    BLOCKED = "blocked"
    APPROVAL = "approval"
    MERGED = "merged"
    RELEASED = "released"
    CANCELLED = "cancelled"


_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.DRAFT: {TaskState.PLANNED, TaskState.CANCELLED},
    TaskState.PLANNED: {TaskState.RUNNING, TaskState.BLOCKED, TaskState.CANCELLED},
    TaskState.RUNNING: {TaskState.REVIEW, TaskState.RETRY, TaskState.BLOCKED, TaskState.CANCELLED},
    TaskState.REVIEW: {TaskState.PASSED, TaskState.RETRY, TaskState.BLOCKED},
    TaskState.RETRY: {TaskState.RUNNING, TaskState.BLOCKED, TaskState.CANCELLED},
    TaskState.PASSED: {TaskState.APPROVAL, TaskState.BLOCKED},
    TaskState.APPROVAL: {TaskState.MERGED, TaskState.BLOCKED, TaskState.CANCELLED},
    TaskState.MERGED: {TaskState.RELEASED},
    TaskState.BLOCKED: {TaskState.PLANNED, TaskState.RETRY, TaskState.CANCELLED},
    TaskState.RELEASED: set(),
    TaskState.CANCELLED: set(),
}


class InvalidTaskTransition(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class TaskEvent:
    from_state: TaskState
    to_state: TaskState
    at: str
    reason: str | None = None


@dataclass(frozen=True)
class DivanTask:
    task_id: str
    title: str
    state: TaskState = TaskState.DRAFT
    project_root: str | None = None
    engine_id: str | None = None
    mandate_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    events: tuple[TaskEvent, ...] = ()

    def transition(self, target: TaskState, reason: str | None = None) -> "DivanTask":
        allowed = _TRANSITIONS[self.state]
        if target not in allowed:
            raise InvalidTaskTransition(f"invalid task transition: {self.state.value} -> {target.value}")
        event = TaskEvent(self.state, target, _now(), reason)
        return replace(self, state=target, events=(*self.events, event))

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "state": self.state.value,
            "project_root": self.project_root,
            "engine_id": self.engine_id,
            "mandate_id": self.mandate_id,
            "metadata": dict(self.metadata),
            "events": [
                {
                    "from": event.from_state.value,
                    "to": event.to_state.value,
                    "at": event.at,
                    "reason": event.reason,
                }
                for event in self.events
            ],
        }
