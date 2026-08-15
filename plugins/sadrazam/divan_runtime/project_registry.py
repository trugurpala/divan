from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .desktop_state import projects_file


@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    name: str
    root: str
    created_at: str
    last_opened_at: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectRegistry:
    """Small project catalog owned by Divan Desktop.

    The registry stores only canonical local repository paths and timestamps.
    Credentials, tokens and remote URLs are intentionally not copied here.
    """

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else projects_file()

    def list(self) -> tuple[ProjectRecord, ...]:
        payload = self._read()
        rows = payload.get("projects", [])
        if not isinstance(rows, list):
            raise ValueError("projects registry is invalid")
        records: list[ProjectRecord] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            records.append(
                ProjectRecord(
                    project_id=str(row["project_id"]),
                    name=str(row["name"]),
                    root=str(row["root"]),
                    created_at=str(row["created_at"]),
                    last_opened_at=str(row["last_opened_at"]),
                )
            )
        return tuple(
            sorted(records, key=lambda item: item.last_opened_at, reverse=True)
        )

    def register(self, root: str) -> ProjectRecord:
        canonical = resolve_git_root(root)
        now = _now()
        project_id = hashlib.sha256(
            os.path.normcase(str(canonical)).encode("utf-8")
        ).hexdigest()[:12]
        existing = {item.project_id: item for item in self.list()}
        previous = existing.get(project_id)
        record = ProjectRecord(
            project_id=project_id,
            name=canonical.name or str(canonical),
            root=str(canonical),
            created_at=previous.created_at if previous else now,
            last_opened_at=now,
        )
        existing[project_id] = record
        self._write(
            {
                "schema_version": 1,
                "projects": [asdict(item) for item in existing.values()],
            }
        )
        return record

    def get(self, project_id: str) -> ProjectRecord:
        for record in self.list():
            if record.project_id == project_id:
                return record
        raise KeyError(f"project not found: {project_id}")

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": 1, "projects": []}
        payload: Any = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise ValueError("projects registry is invalid")
        return payload

    def _write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.path.parent,
            delete=False,
        ) as handle:
            handle.write(text)
            temporary = Path(handle.name)
        os.replace(temporary, self.path)


def resolve_git_root(value: str) -> Path:
    """Resolve one existing Git repository root, or fail closed."""
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("project root must be an existing directory")
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
        shell=False,
    )
    if completed.returncode != 0:
        raise ValueError("selected folder is not a Git repository")
    canonical = Path(completed.stdout.strip()).resolve()
    if not canonical.is_dir():
        raise ValueError("Git repository root could not be resolved")
    return canonical
