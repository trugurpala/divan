"""Deterministic Nizam-i Sefer planning without a model or agent runtime."""

from __future__ import annotations

import hashlib
import json
import math
import os
from collections.abc import Mapping
from typing import Any

from . import planning_policy

HOST_PROFILES = (
    "antigravity-cli",
    "claude-code",
    "codex",
    "cursor",
    "gemini-cli",
    "github-copilot",
    "kiro-cli",
    "kiro-ide",
    "opencode",
    "other-agents",
    "windsurf",
)
FALLBACK_CONTEXT_TOKENS = 32_768
MIN_CONTEXT_TOKENS = 8_192
MAX_CONTEXT_TOKENS = 10_000_000
MAX_PARALLEL_WORKSTREAMS = 3

HOST_ENV_HINTS = (
    ("codex", ("CODEX_HOME",)),
    ("claude-code", ("CLAUDE_CODE_PLUGIN_ROOT",)),
)

TARGET_WEIGHTS = planning_policy.TARGET_WEIGHTS
ROLE_HINTS = (
    (("threat", "security", "auth"), "security-reviewer"),
    (("design", "interaction", "accessibility"), "ux-designer"),
    (("integration", "contract", "provider"), "integration-engineer"),
    (("release", "publication", "promotion", "public surface"), "release-manager"),
    (("documentation", "source", "locale", "link"), "technical-writer"),
    (("review",), "independent-reviewer"),
    (("test", "verification", "evidence", "regression"), "qa-engineer"),
    (("implementation", "fix", "root cause"), "backend-engineer"),
)


def _validated_host(host_profile: str | None) -> str | None:
    if host_profile is None or host_profile == "auto":
        return None
    if host_profile not in HOST_PROFILES:
        raise ValueError(f"unknown host profile: {host_profile}")
    return host_profile


def _detect_host(
    host_profile: str | None, environment: Mapping[str, str]
) -> dict[str, Any]:
    explicit = _validated_host(host_profile)
    if explicit is not None:
        return {
            "id": explicit,
            "source": "explicit",
            "confidence": "declared",
            "hint_keys": [],
        }
    declared = environment.get("DIVAN_HOST")
    if declared:
        try:
            resolved = _validated_host(declared)
        except ValueError as error:
            raise ValueError(
                "DIVAN_HOST must name a supported host profile"
            ) from error
        if resolved is None:
            raise ValueError("DIVAN_HOST must name a supported host profile")
        return {
            "id": resolved,
            "source": "environment",
            "confidence": "declared",
            "hint_keys": ["DIVAN_HOST"],
        }
    matches = [
        (host_id, name)
        for host_id, names in HOST_ENV_HINTS
        for name in names
        if environment.get(name)
    ]
    hosts = sorted({host_id for host_id, _name in matches})
    if len(hosts) == 1:
        return {
            "id": hosts[0],
            "source": "environment",
            "confidence": "hint",
            "hint_keys": sorted(name for _host, name in matches),
        }
    if len(hosts) > 1:
        return {
            "id": "ambiguous",
            "source": "environment",
            "confidence": "conflicting-hints",
            "hint_keys": sorted(name for _host, name in matches),
        }
    return {
        "id": "unknown",
        "source": "fallback",
        "confidence": "unknown",
        "hint_keys": [],
    }


def _context_budget(context_window: int | None) -> dict[str, Any]:
    if context_window is not None and (
        isinstance(context_window, bool)
        or not isinstance(context_window, int)
        or not MIN_CONTEXT_TOKENS <= context_window <= MAX_CONTEXT_TOKENS
    ):
        raise ValueError(
            f"context window must be {MIN_CONTEXT_TOKENS}..{MAX_CONTEXT_TOKENS}"
        )
    total = context_window or FALLBACK_CONTEXT_TOKENS
    reserve = max(2_048, total // 4)
    source = "override" if context_window is not None else "fallback"
    authority = "user-declared" if context_window is not None else "planning-assumption"
    return {
        "total_tokens": total,
        "usable_tokens": total - reserve,
        "reserve_tokens": reserve,
        "handoff_at_tokens": (total - reserve) * 3 // 4,
        "source": source,
        "authority": authority,
        "verified_product_limit": False,
    }


def _stage_role(stage: str, roles: list[str]) -> str:
    normalized = stage.casefold()
    for markers, role in ROLE_HINTS:
        if role in roles and any(marker in normalized for marker in markers):
            return role
    return roles[0] if roles else "orchestrator"


def _native_argv(command: dict[str, str]) -> list[str]:
    manager = command["manager"]
    name = command["name"]
    if manager in {"npm", "pnpm", "yarn", "bun"}:
        return [manager, "run", name]
    if manager == "python":
        return ["python", "-m", "unittest", "discover"]
    if manager == "go":
        return ["go", "test", "./..."]
    return ["cargo", "test"]


def _command_rows(route: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [{
            "kind": "project-check", "display": source["command"],
            "workspace": source["workspace"], "auto_execute": False,
            "argv": _native_argv(source), "shell": False,
        }
        for source in route["commands"]
    ]
    native_displays = {source["command"] for source in route["commands"]}
    rows.extend(
        {"kind": "project-check", "display": check, "auto_execute": False}
        for check in route["checks"]
        if check not in native_displays
    )
    return rows


def _tasks(route: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = route["required_evidence"]
    tasks: list[dict[str, Any]] = []
    workflow_ends: list[str] = []
    for contract in route["workflow_contracts"]:
        previous = None
        for stage in contract["stages"]:
            task_id = f"task-{len(tasks) + 1:03d}"
            commands = (
                _command_rows(route)
                if any(
                    marker in stage.casefold()
                    for marker in ("test", "verification", "review", "evidence", "ci")
                )
                else []
            )
            tasks.append(
                {
                    "id": task_id,
                    "workflow": contract["id"],
                    "stage": stage,
                    "owner_role": _stage_role(stage, contract["roles"]),
                    "depends_on": [previous] if previous is not None else [],
                    "required_evidence": [
                        evidence[(len(tasks) - 1) % len(evidence)]
                    ]
                    if evidence
                    else [],
                    "commands": commands,
                }
            )
            previous = task_id
        if previous is not None:
            workflow_ends.append(previous)
    final_id = f"task-{len(tasks) + 1:03d}"
    tasks.append(
        {
            "id": final_id,
            "workflow": "integrated-delivery",
            "stage": "integrated verification",
            "owner_role": _stage_role("verification", route["roles"]),
            "depends_on": workflow_ends,
            "required_evidence": evidence,
            "commands": _command_rows(route),
        }
    )
    return tasks


def _continuation_task(task: dict[str, Any]) -> dict[str, Any]:
    commands: list[dict[str, Any]] = []
    manual_checks: list[str] = []
    for command in task["commands"]:
        argv = command.get("argv")
        if isinstance(argv, list):
            commands.append(
                {
                    "kind": command["kind"],
                    "workspace": command["workspace"],
                    "argv": list(argv),
                    "shell": False,
                    "auto_execute": False,
                }
            )
        else:
            manual_checks.append(command["display"])
    return {
        "id": task["id"],
        "workflow": task["workflow"],
        "stage": task["stage"],
        "owner_role": task["owner_role"],
        "depends_on": list(task["depends_on"]),
        "required_evidence": list(task["required_evidence"]),
        "commands": commands,
        "manual_checks": manual_checks,
    }


def _initial_continuation(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    ready = sorted((task for task in tasks if not task["depends_on"]), key=lambda task: task["id"])
    if not ready:
        raise ValueError("execution plan requires an initial ready task")
    return {
        "schema_version": 1,
        "kind": "initial-task",
        "selection_policy": "first-ready-by-task-id",
        "ready_task_ids": [task["id"] for task in ready],
        "task": _continuation_task(ready[0]),
        "auto_execute": False,
        "execution_authority": "not-granted",
    }


def _route_id(execution: dict[str, Any]) -> str:
    encoded = json.dumps(
        execution, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return f"route-{hashlib.sha256(encoded).hexdigest()[:16]}"


def _pre_continuation_route_matches(existing: Any, current: dict[str, Any]) -> bool:
    if type(existing) is not dict or type(current) is not dict:
        return False
    existing_value, current_value = existing.get("execution_plan"), current.get("execution_plan")
    if type(existing_value) is not dict or type(current_value) is not dict:
        return False
    existing_execution, current_execution = dict(existing_value), dict(current_value)
    try:
        existing_route_id = existing_execution.pop("route_id")
        current_execution.pop("route_id")
        current_execution.pop("continuation")
    except KeyError:
        return False
    existing_route = {**existing, "execution_plan": existing_execution}
    current_route = {**current, "execution_plan": current_execution}
    return existing_route_id == _route_id(existing_execution) and existing_route == current_route


def _sefer_count(
    complexity: dict[str, Any], budget: dict[str, Any], task_count: int
) -> int:
    capacity = max(MIN_CONTEXT_TOKENS, budget["usable_tokens"] // 2)
    count = math.ceil(complexity["estimated_working_set_tokens"] / capacity)
    minimum = {"low": 1, "moderate": 1, "high": 2, "critical": 3}[
        complexity["level"]
    ]
    return min(max(count, minimum), max(1, task_count))


def _sefers(tasks: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(count):
        start = len(tasks) * index // count
        end = len(tasks) * (index + 1) // count
        sefer_id = f"sefer-{index + 1:03d}"
        rows.append(
            {
                "id": sefer_id,
                "order": index + 1,
                "depends_on": [] if index == 0 else [f"sefer-{index:03d}"],
                "task_ids": [task["id"] for task in tasks[start:end]],
            }
        )
    return rows


def _obligations(route: dict[str, Any], target: str) -> dict[str, Any]:
    workflows = set(route["workflows"])
    canonical = ["implementation", "tests", "goal route"]
    public: list[str] = []
    if workflows & {"documentation-delivery", "release-delivery"}:
        canonical.extend(["versioned documentation", "release notes"])
        public.extend(["README", "documentation", "Wiki"])
    if workflows & {"deployment-delivery", "release-delivery", "seo-delivery"}:
        public.extend(["site", "live readback"])
    if workflows & {"ui-delivery", "seo-delivery"}:
        public.extend(["accessibility evidence", "browser evidence"])
    if target in {"released", "observed"}:
        public.extend(["release artifacts", "remote readback"])
    return {
        "canonical_sources": list(dict.fromkeys(canonical)),
        "public_surfaces": list(dict.fromkeys(public)),
        "required_checks": route["checks"],
        "required_providers": route["providers"],
    }


def build_execution_plan(
    route: dict[str, Any],
    *,
    target: str = "verified",
    host_profile: str | None = None,
    context_window: int | None = None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Add capacity-aware, bounded execution guidance to a route."""
    normalized_target = target.casefold()
    if normalized_target not in TARGET_WEIGHTS:
        raise ValueError(
            f"target must be one of: {', '.join(sorted(TARGET_WEIGHTS))}"
        )
    current_environment = environment if environment is not None else os.environ
    host = _detect_host(host_profile, current_environment)
    budget = _context_budget(context_window)
    complexity = planning_policy.complexity(route, normalized_target)
    tasks = _tasks(route)
    workstreams = planning_policy.workstreams(tasks)
    count = _sefer_count(complexity, budget, len(tasks))
    parallel = 1
    if host["id"] not in {"unknown", "ambiguous"}:
        if complexity["level"] == "high":
            parallel = min(2, len(route["workflows"]))
        elif complexity["level"] == "critical":
            parallel = min(MAX_PARALLEL_WORKSTREAMS, len(route["workflows"]))
    result = {
        "schema_version": 1,
        "policy_id": "nizam-i-sefer-v1",
        "status": "estimated",
        "host": host,
        "context_budget": budget,
        "complexity": complexity,
        "orchestration": {
            "lane": "bounded-parallel" if parallel > 1 else "sequential",
            "max_parallel_workstreams": max(1, parallel),
            "recommended_sefers": count,
            "sefer_semantics": "sequential-context-windows",
            "workstream_semantics": "dependency-graph-lanes",
            "external_agent_harness_required": False,
        },
        "model_policy": planning_policy.model_policy(
            complexity["level"], host["id"]
        ),
        "sefers": _sefers(tasks, count),
        "workstreams": workstreams,
        "tasks": tasks,
        "continuation": _initial_continuation(tasks),
        "handoff": {
            "at_each_sefer_boundary": True,
            "at_context_tokens": budget["handoff_at_tokens"],
            "record": ["completed task ids", "evidence", "blockers", "next task id"],
            "durable_artifact": "route.json",
        },
        "obligations": _obligations(route, normalized_target),
    }
    return {**result, "route_id": _route_id(result)}
