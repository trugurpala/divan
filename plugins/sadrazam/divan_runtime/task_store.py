from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .task_model import DivanTask, TaskEvent, TaskState


class TaskStore:
    """Small atomic JSON store for desktop/operator task state."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def path_for(self, task_id: str) -> Path:
        safe = task_id.strip()
        if not safe or any(char in safe for char in "/\\") or safe in {".", ".."}:
            raise ValueError("task_id must be a non-empty file-safe identifier")
        return self.root / f"{safe}.json"

    def save(self, task: DivanTask) -> Path:
        path = self.path_for(task.task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(task.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(payload)
            temporary = Path(handle.name)
        os.replace(temporary, path)
        return path

    def load(self, task_id: str) -> DivanTask:
        path = self.path_for(task_id)
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("task file root must be an object")
        events = tuple(
            TaskEvent(
                from_state=TaskState(event["from"]),
                to_state=TaskState(event["to"]),
                at=str(event["at"]),
                reason=event.get("reason"),
            )
            for event in payload.get("events", [])
        )
        return DivanTask(
            task_id=str(payload["task_id"]),
            title=str(payload["title"]),
            state=TaskState(payload["state"]),
            project_root=payload.get("project_root"),
            engine_id=payload.get("engine_id"),
            mandate_id=payload.get("mandate_id"),
            metadata=payload.get("metadata", {}),
            events=events,
        )

    def list(self) -> tuple[DivanTask, ...]:
        if not self.root.exists():
            return ()
        return tuple(self.load(path.stem) for path in sorted(self.root.glob("*.json")))
