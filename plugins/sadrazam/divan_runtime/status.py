"""Read-only, evidence-bound status snapshots for Divan Seyir."""

from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import subprocess
from collections.abc import Mapping
from typing import Any

from . import locales, receipts

SCHEMA_VERSION = 1
GIT_TIMEOUT_SECONDS = 5
STATE_PHASES = {
    "DISCOVERED": "FERMAN",
    "SPECIFIED": "FERMAN",
    "PLANNED": "PLAN",
    "IMPLEMENTING": "ICRA",
    "VERIFIED": "TEFTIS",
    "PREVIEWED": "TEFTIS",
    "RELEASED": "YAYIN",
    "OBSERVED": "YAYIN",
    "FAILED": "TEFTIS",
}


def _runtime_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]


def _version() -> str:
    try:
        value = (_runtime_root() / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"
    return value or "unknown"


def _safe_text(value: Any) -> str:
    return receipts.redact_text(str(value))


def _git_value(root: pathlib.Path, arguments: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _git_snapshot(root: pathlib.Path) -> dict[str, Any]:
    branch = _git_value(root, ["branch", "--show-current"])
    head = _git_value(root, ["rev-parse", "--short=7", "HEAD"])
    porcelain = _git_value(root, ["status", "--porcelain", "--untracked-files=normal"])
    return {
        "branch": branch or "unavailable",
        "head": head or "unavailable",
        "dirty": bool(porcelain) if porcelain is not None else None,
    }


def _verified_receipts(root: pathlib.Path) -> list[tuple[str, pathlib.Path, dict[str, Any]]]:
    evidence_root = root / ".divan" / "evidence"
    found: list[tuple[str, pathlib.Path, dict[str, Any]]] = []
    if not evidence_root.is_dir():
        return found
    for path in sorted(evidence_root.glob("goal-*/receipt.json")):
        verification = receipts.verify_receipt(path)
        if not verification.get("ok"):
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        events = value.get("events", [])
        recorded = max(
            (
                str(event.get("recorded_on", ""))
                for event in events
                if isinstance(event, dict)
            ),
            default="",
        )
        found.append((recorded, path, value))
    return found


def _latest_goal(root: pathlib.Path) -> tuple[pathlib.Path, dict[str, Any]] | None:
    found = _verified_receipts(root)
    if not found:
        return None
    _, path, value = max(
        found,
        key=lambda item: (item[0], str(item[2].get("goal_id", ""))),
    )
    return path, value


def _route_tasks(root: pathlib.Path, identifier: str) -> list[dict[str, str]]:
    route_path = root / ".divan" / "specs" / identifier / "route.json"
    try:
        route = json.loads(route_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    execution = route.get("execution_plan")
    source = execution.get("tasks", []) if isinstance(execution, dict) else []
    tasks: list[dict[str, str]] = []
    for index, task in enumerate(source, 1):
        if not isinstance(task, dict):
            continue
        identifier_value = _safe_text(task.get("id", f"task-{index:03d}"))
        title = _safe_text(task.get("stage", task.get("title", identifier_value)))
        tasks.append(
            {
                "id": identifier_value,
                "title": title,
                "status": "PENDING",
            }
        )
    return tasks


def _event_results(value: Mapping[str, Any]) -> list[dict[str, str]]:
    events = value.get("events")
    if not isinstance(events, list):
        return []
    latest: dict[str, dict[str, Any]] = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        results = event.get("results")
        if not isinstance(results, dict):
            continue
        for check_id, result in results.items():
            if isinstance(result, dict):
                latest[str(check_id)] = result
    return [
        {
            "id": _safe_text(check_id),
            "status": _safe_text(result.get("status", "UNKNOWN")),
        }
        for check_id, result in sorted(latest.items())
    ]


def _event_evidence(value: Mapping[str, Any]) -> list[dict[str, str]]:
    events = value.get("events")
    if not isinstance(events, list):
        return []
    observed: list[str] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        evidence = event.get("evidence")
        if not isinstance(evidence, list):
            continue
        for item in evidence:
            safe = _safe_text(item)
            if safe not in observed:
                observed.append(safe)
    return [{"label": item} for item in observed]


def _blocker(value: Mapping[str, Any]) -> dict[str, str] | None:
    state = str(value.get("state", ""))
    if state not in {"BLOCKED", "FAILED"}:
        return None
    events = value.get("events")
    if not isinstance(events, list) or not events:
        return {"state": state, "reason": ""}
    latest = events[-1] if isinstance(events[-1], dict) else {}
    return {
        "state": state,
        "reason": _safe_text(latest.get("reason", "")),
    }


def _phase(value: Mapping[str, Any]) -> str:
    state = str(value.get("state", "DISCOVERED"))
    if state != "BLOCKED":
        return STATE_PHASES.get(state, "FERMAN")
    events = value.get("events")
    if isinstance(events, list) and events and isinstance(events[-1], dict):
        resumed = str(events[-1].get("resume_from", "DISCOVERED"))
        return STATE_PHASES.get(resumed, "FERMAN")
    return "FERMAN"


def _utc_timestamp(now: datetime.datetime | None) -> str:
    observed = datetime.datetime.now(datetime.UTC) if now is None else now
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=datetime.UTC)
    return observed.astimezone(datetime.UTC).isoformat().replace("+00:00", "Z")


def build_snapshot(
    project: pathlib.Path | str,
    language: str = "auto",
    now: datetime.datetime | None = None,
) -> dict[str, Any]:
    """Build one bounded status view without mutating the project."""
    root = pathlib.Path(project).resolve()
    if not root.is_dir():
        raise ValueError(f"project directory does not exist: {root}")
    locale = locales.resolve_language(language)
    selected = _latest_goal(root)
    project_value = {"name": _safe_text(root.name), **_git_snapshot(root)}
    common = {
        "schema_version": SCHEMA_VERSION,
        "product": {"name": "Divan", "version": _version()},
        "locale": locale,
        "project": project_value,
        "generated_at": _utc_timestamp(now),
    }
    if selected is None:
        return {
            **common,
            "goal": {
                "id": None,
                "title": None,
                "status": "NO_ACTIVE_GOAL",
            },
            "current": {"phase": None, "task": None},
            "tasks": [],
            "checks": [],
            "evidence": [],
            "blocker": None,
            "next_action": None,
        }

    _, receipt = selected
    identifier = _safe_text(receipt.get("goal_id", ""))
    tasks = _route_tasks(root, identifier)
    current_task = next(
        (task["title"] for task in tasks if task["status"] != "DONE"),
        None,
    )
    return {
        **common,
        "goal": {
            "id": identifier,
            "title": _safe_text(receipt.get("intent", "")),
            "status": _safe_text(receipt.get("state", "UNKNOWN")),
        },
        "current": {"phase": _phase(receipt), "task": current_task},
        "tasks": tasks,
        "checks": _event_results(receipt),
        "evidence": _event_evidence(receipt),
        "blocker": _blocker(receipt),
        "next_action": current_task,
    }


def snapshot_etag(snapshot: Mapping[str, Any]) -> str:
    """Hash semantic snapshot content while ignoring observation time."""
    stable = dict(snapshot)
    stable.pop("generated_at", None)
    encoded = json.dumps(
        stable,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
