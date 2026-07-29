#!/usr/bin/env python3
"""Deterministic Project OS goal artifacts."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import tempfile
import unicodedata
from typing import Any

import engine
import planning
import receipts

TARGETS = ("VERIFIED", "PREVIEWED", "RELEASED", "OBSERVED")
GOAL_ID_PATTERN = re.compile(r"^goal-[0-9a-f]{12}$")


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _route(
    project: pathlib.Path,
    intent: str,
    target: str,
    host_profile: str,
    context_window: int | None,
) -> dict[str, Any]:
    company = pathlib.Path(engine.__file__).resolve().parent
    contracts = engine.load_contracts(company)
    base = engine.plan_intent(intent, project, contracts, target.casefold())
    return planning.enrich_plan(
        base,
        host_profile=host_profile,
        context_window=context_window,
        target=target.casefold(),
        directory=company,
    )


def goal_id(intent: str, target: str, route: dict[str, Any]) -> str:
    """Derive the stable goal ID from normalized inputs and the enriched route."""
    seed = {
        "intent": _normalized(intent),
        "target": target.upper(),
        "route": route,
    }
    encoded = json.dumps(
        seed, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return f"goal-{hashlib.sha256(encoded).hexdigest()[:12]}"


def _command_lines(route: dict[str, Any]) -> list[str]:
    commands = route.get("commands", [])
    lines = [
        f"- `{item.get('command')}` ({item.get('workspace', '.')})"
        for item in commands
        if isinstance(item, dict) and isinstance(item.get("command"), str)
    ]
    return lines or ["- No project-native command was discovered."]


def _sefer_lines(route: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for sefer in route.get("sefers", []):
        if not isinstance(sefer, dict):
            continue
        stages = ", ".join(str(item) for item in sefer.get("stages", []))
        owners = ", ".join(str(item) for item in sefer.get("paşalar", []))
        lines.extend(
            [
                f"### {sefer.get('id')}",
                "",
                f"- Stages: {stages or 'unclassified'}",
                f"- Paşalar: {owners or 'sadrazam'}",
                f"- Exit gate: {sefer.get('exit_gate')}",
                f"- Handoff required: {str(bool(sefer.get('handoff_required'))).lower()}",
                "",
            ]
        )
    return lines


def _task_lines(route: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for task in route.get("tasks", []):
        if not isinstance(task, dict):
            continue
        dependencies = ", ".join(str(item) for item in task.get("dependencies", []))
        evidence = ", ".join(str(item) for item in task.get("required_evidence", []))
        lines.extend(
            [
                f"- [ ] **{task.get('id')} · {task.get('stage')}**",
                f"  - Owner: `{task.get('owner_role')}`",
                f"  - Depends on: {dependencies or 'none'}",
                f"  - Evidence: {evidence or 'completion receipt'}",
            ]
        )
    return lines or ["- [ ] Sadrazam must classify the first executable task."]


def _artifact_values(
    identifier: str,
    intent: str,
    target: str,
    route: dict[str, Any],
    route_digest: str,
) -> dict[str, bytes]:
    project_types = ", ".join(route.get("project_types", [])) or "unclassified"
    workflows = ", ".join(route.get("workflows", [])) or "feature-delivery"
    roles = ", ".join(route.get("roles", [])) or "sadrazam"
    evidence = "\n".join(
        f"- {item}" for item in route.get("required_evidence", [])
    ) or "- Verification result"
    complexity = route.get("complexity", {})
    context = route.get("context_budget", {})
    obligations = route.get("publication_obligations", {})
    surface_classes = ", ".join(obligations.get("surface_classes", []))
    route_path = f".divan/routes/{identifier}.json"

    spec = (
        f"# Goal {identifier}\n\n"
        f"## Intent\n\n{intent.strip()}\n\n"
        f"## Target\n\n{target.upper()}\n\n"
        "## Company route\n\n"
        f"- Project types: {project_types}\n"
        f"- Workflows: {workflows}\n"
        f"- Vezirler: {roles}\n"
        f"- Machine route: `{route_path}`\n"
        f"- Route SHA-256: `{route_digest}`\n"
        f"- Surface classes: {surface_classes or 'project-memory, verification-evidence'}\n\n"
        "## Acceptance evidence\n\n"
        f"{evidence}\n"
    )

    sefer_text = "\n".join(_sefer_lines(route))
    commands = "\n".join(_command_lines(route))
    warning = context.get("warning")
    warning_line = f"\n- Capacity warning: {warning}" if warning else ""
    plan = (
        f"# Plan for {identifier}\n\n"
        "## Nizâm-ı Sefer\n\n"
        f"- Complexity: {complexity.get('band')} ({complexity.get('score')})\n"
        f"- Estimated working set: {complexity.get('estimated_working_set_tokens')} tokens\n"
        f"- Host profile: {context.get('profile')}\n"
        f"- Context source: {context.get('capacity_source')}\n"
        f"- Usable tokens per session: {context.get('usable_tokens_per_session')}\n"
        f"- Recommended sessions: {route.get('recommended_sessions')}\n"
        f"- Orchestration lane: {route.get('orchestration_lane')}\n"
        f"- Safe parallel workstreams: {route.get('safe_parallel_workstreams')}\n"
        f"- Handoff threshold: {context.get('handoff_percent')}%"
        f"{warning_line}\n\n"
        "## Seferler\n\n"
        f"{sefer_text}\n"
        "## Discovered commands\n\n"
        f"{commands}\n\n"
        "## Standing completion law\n\n"
        "1. Calculate impact before editing and from the actual changed paths.\n"
        "2. Block completion when any path is unclassified.\n"
        "3. Update canonical documentation and derived public surfaces in the same change.\n"
        "4. Record checkpoint, decisions, progress, evidence and the next action after every sefer.\n"
        "5. Require remote readback whenever the publication contract says so.\n"
    )

    tasks = (
        f"# Tasks for {identifier}\n\n"
        + "\n".join(_task_lines(route))
        + "\n"
    )
    return {
        "spec.md": spec.encode("utf-8"),
        "plan.md": plan.encode("utf-8"),
        "tasks.md": tasks.encode("utf-8"),
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


def _goal_paths(
    root: pathlib.Path, identifier: str
) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path, pathlib.Path]:
    validated = _validate_goal_id(identifier)
    spec_root = root / ".divan" / "specs" / validated
    route_path = root / ".divan" / "routes" / f"{validated}.json"
    evidence_root = root / ".divan" / "evidence" / validated
    receipt_path = evidence_root / "receipt.json"
    for path in (spec_root, route_path, evidence_root, receipt_path):
        _safe_goal_path(root, path)
    return spec_root, route_path, evidence_root, receipt_path


def start_goal(
    project: pathlib.Path | str,
    intent: str,
    target: str,
    execute: bool,
    *,
    host_profile: str = "auto",
    context_window: int | None = None,
) -> dict[str, Any]:
    """Plan or create deterministic spec, route, tasks and initial receipt files."""
    root = pathlib.Path(project).resolve()
    if not root.is_dir():
        raise ValueError(f"project directory does not exist: {root}")
    if not isinstance(intent, str) or not intent.strip():
        raise ValueError("goal intent must be non-empty")
    normalized_target = target.upper()
    if normalized_target not in TARGETS:
        raise ValueError(
            "goal target must be verified, previewed, released, or observed"
        )
    safe_intent = receipts.redact_text(intent.strip())
    route = _route(
        root,
        safe_intent,
        normalized_target,
        host_profile,
        context_window,
    )
    identifier = goal_id(safe_intent, normalized_target, route)
    route_content = (
        json.dumps(route, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    route_digest = hashlib.sha256(route_content).hexdigest()
    artifacts = _artifact_values(
        identifier, safe_intent, normalized_target, route, route_digest
    )
    spec_root, route_path, _evidence_root, receipt_path = _goal_paths(
        root, identifier
    )
    relative_artifacts = {
        (pathlib.PurePosixPath(".divan") / "specs" / identifier / name).as_posix():
        hashlib.sha256(content).hexdigest()
        for name, content in artifacts.items()
    }
    paths = [
        *(spec_root / name for name in ("spec.md", "plan.md", "tasks.md")),
        route_path,
        receipt_path,
    ]
    result = {
        "schema_version": 2,
        "status": "planned",
        "project": root.name,
        "goal_id": identifier,
        "target": normalized_target,
        "writes": [path.relative_to(root).as_posix() for path in paths],
        "receipt": receipt_path.relative_to(root).as_posix(),
        "route": route_path.relative_to(root).as_posix(),
        "route_sha256": route_digest,
        "complexity": route["complexity"],
        "recommended_sessions": route["recommended_sessions"],
        "orchestration_lane": route["orchestration_lane"],
        "safe_parallel_workstreams": route["safe_parallel_workstreams"],
    }
    if not execute:
        return result

    desired = {spec_root / name: content for name, content in artifacts.items()}
    desired[route_path] = route_content
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
            raise ValueError(
                f"goal artifact already exists with different content: {path.name}"
            )
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
    _, _, _, path = _goal_paths(root, identifier)
    verification = receipts.verify_receipt(path)
    return {"goal_id": identifier, **verification}


def resume_goal(project: pathlib.Path | str, identifier: str, execute: bool) -> dict[str, Any]:
    root = pathlib.Path(project).resolve()
    _, _, _, path = _goal_paths(root, identifier)
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
