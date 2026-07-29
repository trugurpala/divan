#!/usr/bin/env python3
"""Deterministic Divan Project Contract goal artifacts."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import tempfile
import unicodedata
from collections.abc import Mapping
from typing import Any

from . import engine, receipts

TARGETS = ("VERIFIED", "PREVIEWED", "RELEASED", "OBSERVED")
GOAL_ID_PATTERN = re.compile(r"^goal-[0-9a-f]{12}$")


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _inspection(project: pathlib.Path) -> dict[str, Any]:
    contracts = engine.load_contracts(pathlib.Path(engine.__file__).resolve().parent)
    return engine.inspect_project(project, contracts)


def goal_id(
    intent: str,
    target: str,
    inspection: dict[str, Any],
    planning_identity: dict[str, Any] | None = None,
) -> str:
    """Derive the stable goal ID from normalized inputs and inspection."""
    seed = {
        "intent": _normalized(intent),
        "target": target.upper(),
        "inspection": inspection,
    }
    if planning_identity is not None:
        seed["planning"] = planning_identity
    encoded = json.dumps(
        seed, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return f"goal-{hashlib.sha256(encoded).hexdigest()[:12]}"


def _plan_markdown(
    identifier: str, target: str, inspection: dict[str, Any], route: dict[str, Any]
) -> str:
    project_types = ", ".join(inspection.get("project_types", [])) or "unclassified"
    commands = inspection.get("commands", [])
    command_lines = [
        f"- `{item.get('command')}` ({item.get('workspace', '.')})"
        for item in commands
        if isinstance(item, dict) and isinstance(item.get("command"), str)
    ]
    if not command_lines:
        command_lines = ["- No project-native command was discovered."]
    execution = route["execution_plan"]
    orchestration = execution["orchestration"]
    model = execution["model_policy"]
    return (
        f"# Plan for {identifier}\n\n"
        f"Target: `{target.upper()}`. Project types: {project_types}.\n\n"
        f"Complexity: `{execution['complexity']['level']}`. "
        f"Recommended sefers: `{orchestration['recommended_sefers']}`. "
        f"Lane: `{orchestration['lane']}`. "
        f"Model class: `{model['capability_class']}`.\n\n"
        "## Discovered commands\n\n"
        + "\n".join(command_lines)
        + "\n"
    )


def _tasks_markdown(identifier: str, route: dict[str, Any]) -> str:
    lines = [f"# Tasks for {identifier}", ""]
    for task in route["execution_plan"]["tasks"]:
        dependencies = ", ".join(task["depends_on"]) or "none"
        lines.append(
            f"- [ ] `{task['id']}` {task['stage']} "
            f"(owner: `{task['owner_role']}`; depends on: {dependencies})"
        )
    return "\n".join(lines) + "\n"


def _artifact_values(
    identifier: str,
    intent: str,
    target: str,
    inspection: dict[str, Any],
    route: dict[str, Any],
) -> dict[str, bytes]:
    project_types = ", ".join(inspection.get("project_types", [])) or "unclassified"
    spec = (
        f"# Goal {identifier}\n\n"
        f"## Intent\n\n{intent.strip()}\n\n"
        f"## Target\n\n{target.upper()}\n\n"
        f"## Inspection\n\nProject types: {project_types}.\n"
    )
    return {
        "spec.md": spec.encode("utf-8"),
        "plan.md": _plan_markdown(
            identifier, target, inspection, route
        ).encode("utf-8"),
        "tasks.md": _tasks_markdown(identifier, route).encode("utf-8"),
        "route.json": (
            json.dumps(route, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
    }


def _atomic_write(path: pathlib.Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _safe_goal_path(root: pathlib.Path, path: pathlib.Path) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise ValueError("goal path escapes project") from error
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(
                f"goal path uses a symlink: {relative.as_posix()}"
            )
    try:
        path.resolve(strict=False).relative_to(root)
    except ValueError as error:
        raise ValueError(
            f"goal path escapes project: {relative.as_posix()}"
        ) from error


def _validate_goal_id(identifier: Any) -> str:
    if not isinstance(identifier, str) or not GOAL_ID_PATTERN.fullmatch(identifier):
        raise ValueError("goal identifier must match goal-[0-9a-f]{12}")
    return identifier


def _normalize_target(target: str) -> str:
    normalized = target.upper()
    if normalized not in TARGETS:
        raise ValueError(
            "goal target must be verified, previewed, released, or observed"
        )
    return normalized


def _goal_paths(
    root: pathlib.Path, identifier: str
) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    validated = _validate_goal_id(identifier)
    spec_root = root / ".divan" / "specs" / validated
    evidence_root = root / ".divan" / "evidence" / validated
    receipt_path = evidence_root / "receipt.json"
    for path in (spec_root, evidence_root, receipt_path):
        _safe_goal_path(root, path)
    return spec_root, evidence_root, receipt_path


def _goal_route(
    root: pathlib.Path,
    intent: str,
    target: str,
    host_profile: str | None,
    context_window: int | None,
    environment: Mapping[str, str] | None,
) -> dict[str, Any]:
    route_environment = environment
    if host_profile is None and context_window is None and environment is None:
        route_environment = {}
    contracts = engine.load_contracts(pathlib.Path(engine.__file__).resolve().parent)
    return engine.plan_intent(
        intent,
        root,
        contracts,
        target.casefold(),
        host_profile=host_profile,
        context_window=context_window,
        environment=route_environment,
    )


def _planning_identity(
    route: dict[str, Any],
    host_profile: str | None,
    context_window: int | None,
    environment: Mapping[str, str] | None,
) -> dict[str, Any] | None:
    if host_profile is None and context_window is None and environment is None:
        return None
    execution = route["execution_plan"]
    return {
        "schema_version": execution["schema_version"],
        "host": execution["host"],
        "context_budget": execution["context_budget"],
    }


def _legacy_goal_is_unchanged(
    spec_root: pathlib.Path,
    receipt_path: pathlib.Path,
    identifier: str,
    intent: str,
    target: str,
) -> bool:
    if (spec_root / "route.json").exists() or not receipt_path.is_file():
        return False
    verification = receipts.verify_receipt(receipt_path)
    if not verification["ok"]:
        return False
    value = json.loads(receipt_path.read_text(encoding="utf-8"))
    required = {
        f".divan/specs/{identifier}/{name}"
        for name in ("spec.md", "plan.md", "tasks.md")
    }
    return (
        value.get("intent") == intent
        and value.get("target") == target
        and set(value.get("artifacts", {})) == required
    )


def start_goal(
    project: pathlib.Path | str,
    intent: str,
    target: str,
    execute: bool,
    *,
    host_profile: str | None = None,
    context_window: int | None = None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Plan or create deterministic spec/plan/task and initial receipt files."""
    root = pathlib.Path(project).resolve()
    if not root.is_dir():
        raise ValueError(f"project directory does not exist: {root}")
    if not isinstance(intent, str) or not intent.strip():
        raise ValueError("goal intent must be non-empty")
    normalized_target = _normalize_target(target)
    snapshot = _inspection(root)
    safe_intent = receipts.redact_text(intent.strip())
    route = _goal_route(
        root,
        safe_intent,
        normalized_target,
        host_profile,
        context_window,
        environment,
    )
    identity = _planning_identity(
        route, host_profile, context_window, environment
    )
    identifier = goal_id(safe_intent, normalized_target, snapshot, identity)
    artifacts = _artifact_values(
        identifier, safe_intent, normalized_target, snapshot, route
    )
    spec_root, evidence_root, receipt_path = _goal_paths(root, identifier)
    relative_artifacts = {
        (pathlib.PurePosixPath(".divan") / "specs" / identifier / name).as_posix():
        hashlib.sha256(content).hexdigest()
        for name, content in artifacts.items()
    }
    paths = [
        *(
            spec_root / name
            for name in ("spec.md", "plan.md", "tasks.md", "route.json")
        ),
        receipt_path,
    ]
    result = {
        "schema_version": 1,
        "status": "planned",
        "project": root.name,
        "goal_id": identifier,
        "target": normalized_target,
        "writes": [path.relative_to(root).as_posix() for path in paths],
        "receipt": receipt_path.relative_to(root).as_posix(),
    }
    if identity is None and _legacy_goal_is_unchanged(
        spec_root, receipt_path, identifier, safe_intent, normalized_target
    ):
        result.update(
            {
                "status": "legacy-unchanged",
                "migration_required": True,
                "writes": [
                    path.relative_to(root).as_posix()
                    for path in (
                        spec_root / "spec.md",
                        spec_root / "plan.md",
                        spec_root / "tasks.md",
                        receipt_path,
                    )
                ],
            }
        )
        return result
    if not execute:
        return result

    desired = {spec_root / name: content for name, content in artifacts.items()}
    receipt_value = receipts.new_receipt(
        identifier, safe_intent, normalized_target, relative_artifacts
    )
    desired[receipt_path] = (
        json.dumps(
            receipt_value, ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n"
    ).encode("utf-8")
    for path in desired:
        _safe_goal_path(root, path)
    changed = False
    for path, content in desired.items():
        if path.exists() and path.read_bytes() != content:
            raise ValueError(f"goal artifact already exists with different content: {path.name}")
    for path, content in desired.items():
        if not path.exists():
            _atomic_write(path, content)
            changed = True
    result["status"] = "created" if changed else "unchanged"
    return result


def goal_status(
    project: pathlib.Path | str, identifier: str | None = None
) -> dict[str, Any]:
    root = pathlib.Path(project).resolve()
    evidence = root / ".divan" / "evidence"
    if identifier is None:
        goals = []
        if evidence.is_dir():
            for path in sorted(evidence.glob("goal-*/receipt.json")):
                verification = receipts.verify_receipt(path)
                goals.append(
                    {
                        "goal_id": path.parent.name,
                        "state": verification["state"],
                        "ok": verification["ok"],
                    }
                )
        return {"schema_version": 1, "status": "listed", "goals": goals}
    _, _, path = _goal_paths(root, identifier)
    verification = receipts.verify_receipt(path)
    return {"goal_id": identifier, **verification}


def resume_goal(project: pathlib.Path | str, identifier: str, execute: bool) -> dict[str, Any]:
    root = pathlib.Path(project).resolve()
    _, _, path = _goal_paths(root, identifier)
    verification = receipts.verify_receipt(path)
    if not verification["ok"]:
        raise ValueError("; ".join(verification["errors"]))
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("state") != "BLOCKED":
        raise ValueError("goal is not BLOCKED")
    resume_from = value["events"][-1].get("resume_from")
    result = {
        "schema_version": 1,
        "status": "planned",
        "goal_id": identifier,
        "from": "BLOCKED",
        "to": resume_from,
    }
    if execute:
        receipts.resume_receipt(path)
        result["status"] = "resumed"
    return result
