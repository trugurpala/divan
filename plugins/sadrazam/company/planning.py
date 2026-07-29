#!/usr/bin/env python3
"""Deterministic context budgeting and task decomposition for Company OS."""
from __future__ import annotations

import json
import math
import os
import pathlib
import re
import unicodedata
from typing import Any

DIRECTORY = pathlib.Path(__file__).resolve().parent
PROFILE_FILE = "host-profiles.json"
PROFILE_ENV = "DIVAN_HOST_PROFILE"
CONTEXT_ENV = "DIVAN_CONTEXT_WINDOW"
CONTEXT_SOURCE_ENV = "DIVAN_CONTEXT_SOURCE"

COMPLEXITY_PHRASES = {
    "all": 5,
    "baştan sona": 12,
    "bastan sona": 12,
    "büyük düşün": 8,
    "buyuk dusun": 8,
    "end to end": 12,
    "from scratch": 10,
    "migration": 10,
    "production": 8,
    "refactor": 7,
    "release": 8,
    "security": 8,
    "ship": 7,
    "sıfırdan": 10,
    "sifirdan": 10,
    "yayınla": 8,
    "yayinla": 8,
}

ROLE_HINTS = (
    (("threat", "security", "secret", "auth"), "security-reviewer"),
    (("design", "interaction", "accessibility", "creative"), "ux-designer"),
    (("browser", "test", "evidence", "verification", "crawl"), "qa-engineer"),
    (("review", "readback"), "independent-reviewer"),
    (("release", "publication", "promotion"), "release-manager"),
    (("provider", "deploy", "preview", "ci"), "platform-engineer"),
    (("document", "source", "canonical", "locale", "link"), "technical-writer"),
    (("api", "backend", "database", "server"), "backend-engineer"),
    (("frontend", "component", "ui"), "frontend-engineer"),
    (("contract", "brief", "plan", "applicability"), "product-strategist"),
)


def _normalized(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = text.replace("\N{COMBINING DOT ABOVE}", "").replace(
        "\N{LATIN SMALL LETTER DOTLESS I}", "i"
    )
    return " ".join(
        "".join(character if character.isalnum() else " " for character in text)
        .split()
    )


def _positive_int(value: Any, context: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{context} must be a positive integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{context} must be a positive integer") from error
    if number <= 0:
        raise ValueError(f"{context} must be a positive integer")
    return number


def _load_profiles(directory: pathlib.Path = DIRECTORY) -> dict[str, Any]:
    path = directory / PROFILE_FILE
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid host planning profiles: {error}") from error
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("invalid host planning profile schema")
    rows = value.get("profiles")
    default = value.get("default_profile")
    if not isinstance(rows, list) or not rows or not isinstance(default, str):
        raise ValueError("host planning profiles require rows and a default")
    profiles: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("host planning profile row is invalid")
        identifier = row.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(
            r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier
        ):
            raise ValueError("host planning profile id is invalid")
        if identifier in profiles:
            raise ValueError("duplicate host planning profile id")
        reserve = _positive_int(row.get("reserve_percent"), "reserve percent")
        handoff = _positive_int(row.get("handoff_percent"), "handoff percent")
        if reserve >= 100 or handoff >= 100:
            raise ValueError("host planning percentages must be below 100")
        profiles[identifier] = {
            **row,
            "default_context_window_tokens": _positive_int(
                row.get("default_context_window_tokens"), "context window"
            ),
            "reserve_percent": reserve,
            "handoff_percent": handoff,
            "max_parallel_workstreams": _positive_int(
                row.get("max_parallel_workstreams"), "parallel workstreams"
            ),
        }
    if default not in profiles:
        raise ValueError("default host planning profile is unknown")
    return {"default_profile": default, "profiles": profiles}


def profile_ids(directory: pathlib.Path = DIRECTORY) -> tuple[str, ...]:
    """Return stable profile identifiers accepted by the CLI."""
    profiles = _load_profiles(directory)["profiles"]
    return tuple(sorted(profiles))


def _detected_profile(profiles: dict[str, Any], default: str) -> tuple[str, str]:
    configured = os.environ.get(PROFILE_ENV, "").strip().casefold()
    if configured:
        if configured not in profiles:
            raise ValueError(f"unknown {PROFILE_ENV} profile: {configured}")
        return configured, "environment-profile"
    if os.environ.get("CLAUDE_PLUGIN_ROOT") or os.environ.get("CLAUDE_CODE"):
        return ("claude" if "claude" in profiles else default), "host-hint"
    if os.environ.get("CODEX_HOME") or os.environ.get("CODEX_THREAD_ID"):
        return ("codex" if "codex" in profiles else default), "host-hint"
    return default, "portable-fallback"


def resolve_capacity(
    host_profile: str = "auto",
    context_window: int | None = None,
    directory: pathlib.Path = DIRECTORY,
) -> dict[str, Any]:
    """Resolve declared or conservative capacity without claiming model limits."""
    contract = _load_profiles(directory)
    profiles = contract["profiles"]
    if host_profile == "auto":
        identifier, profile_source = _detected_profile(
            profiles, contract["default_profile"]
        )
    else:
        identifier = host_profile.strip().casefold()
        if identifier not in profiles:
            raise ValueError(f"unknown host planning profile: {host_profile}")
        profile_source = "explicit-profile"
    profile = profiles[identifier]

    env_context = os.environ.get(CONTEXT_ENV, "").strip()
    if context_window is not None:
        window = _positive_int(context_window, "context window")
        capacity_source = "explicit-context-window"
    elif env_context:
        window = _positive_int(env_context, CONTEXT_ENV)
        capacity_source = os.environ.get(
            CONTEXT_SOURCE_ENV, "environment-context-window"
        ).strip() or "environment-context-window"
    else:
        window = profile["default_context_window_tokens"]
        capacity_source = "profile-fallback"

    reserve_tokens = math.ceil(window * profile["reserve_percent"] / 100)
    handoff_tokens = math.floor(window * profile["handoff_percent"] / 100)
    usable_tokens = max(1, min(window - reserve_tokens, handoff_tokens))
    warning = None
    if capacity_source == "profile-fallback":
        warning = (
            "Context capacity is a conservative planning fallback, not a verified "
            "model or subscription limit. Pass --context-window or set "
            f"{CONTEXT_ENV} when the host reports an exact value."
        )
    return {
        "profile": identifier,
        "profile_source": profile_source,
        "context_window_tokens": window,
        "capacity_source": capacity_source,
        "capacity_kind": profile.get("capacity_kind", "unspecified"),
        "reserve_percent": profile["reserve_percent"],
        "reserve_tokens": reserve_tokens,
        "handoff_percent": profile["handoff_percent"],
        "handoff_tokens": handoff_tokens,
        "usable_tokens_per_session": usable_tokens,
        "max_parallel_workstreams": profile["max_parallel_workstreams"],
        "warning": warning,
    }


def _complexity_score(route: dict[str, Any]) -> int:
    score = 8
    score += len(route.get("workflows", [])) * 6
    score += len(route.get("roles", [])) * 2
    score += len(route.get("frameworks", [])) * 2
    score += max(0, len(route.get("workspaces", [])) - 1) * 4
    score += len(route.get("stages", [])) * 2
    score += len(route.get("required_evidence", []))
    score += min(12, len(route.get("checks", [])))
    if "monorepo" in route.get("project_types", []):
        score += 10
    if route.get("package_manager_conflicts"):
        score += 12
    intent = _normalized(str(route.get("intent", "")))
    for phrase, weight in COMPLEXITY_PHRASES.items():
        if _normalized(phrase) in intent:
            score += weight
    return min(100, score)


def _complexity_band(score: int) -> str:
    if score < 30:
        return "small"
    if score < 50:
        return "standard"
    if score < 75:
        return "large"
    return "campaign"


def _owner_for_stage(stage: str, roles: list[str], index: int) -> str:
    normalized = _normalized(stage)
    for hints, role in ROLE_HINTS:
        if role in roles and any(hint in normalized for hint in hints):
            return role
    preferred = [
        role
        for role in roles
        if role not in {"independent-reviewer", "product-strategist"}
    ]
    pool = preferred or roles or ["sadrazam"]
    return pool[index % len(pool)]


def _stage_evidence(stage: str, required: list[str]) -> list[str]:
    words = set(_normalized(stage).split())
    matched = [
        item
        for item in required
        if words & set(_normalized(str(item)).split())
    ]
    return matched or [f"{stage} completion receipt"]


def _partition_stages(stages: list[str], sefer_count: int) -> list[list[str]]:
    if not stages:
        return [["brief", "implementation", "verification"]]
    count = max(1, min(sefer_count, len(stages)))
    return [
        stages[start:end]
        for index in range(count)
        if (
            start := math.floor(index * len(stages) / count)
        ) < (end := math.floor((index + 1) * len(stages) / count))
    ]


def _publication_obligations(route: dict[str, Any], target: str) -> dict[str, Any]:
    workflows = set(route.get("workflows", []))
    public = target in {"released", "observed"} or bool(
        workflows
        & {
            "deployment-delivery",
            "documentation-delivery",
            "release-delivery",
            "seo-delivery",
        }
    )
    surface_classes = ["project-memory", "verification-evidence"]
    if public:
        surface_classes.extend(
            ["canonical-documentation", "wiki", "public-site", "release-validation"]
        )
    return {
        "impact_before_edit": True,
        "impact_after_edit": True,
        "unclassified_paths_block_completion": True,
        "canonical_source_required": True,
        "derived_surfaces_same_change": True,
        "remote_readback_required": public,
        "surface_classes": surface_classes,
    }


def enrich_plan(
    route: dict[str, Any],
    *,
    host_profile: str = "auto",
    context_window: int | None = None,
    target: str = "verified",
    directory: pathlib.Path = DIRECTORY,
) -> dict[str, Any]:
    """Add Nizâm-ı Sefer budgeting, decomposition and command structure."""
    if not isinstance(route, dict) or not route.get("intent"):
        raise ValueError("Company OS route with an intent is required")
    normalized_target = target.strip().casefold()
    if normalized_target not in {"verified", "previewed", "released", "observed"}:
        raise ValueError("target must be verified, previewed, released, or observed")

    capacity = resolve_capacity(host_profile, context_window, directory)
    score = _complexity_score(route)
    estimated_tokens = 6000 + score * 1500
    session_capacity = capacity["usable_tokens_per_session"]
    sessions = max(1, min(12, math.ceil(estimated_tokens / session_capacity)))
    workflows = list(route.get("workflows", []))
    safe_parallel = 1
    if sessions > 1 and len(workflows) > 1:
        safe_parallel = min(
            capacity["max_parallel_workstreams"], len(workflows), 3
        )
    lane = (
        "tek-sefer"
        if sessions == 1
        else "sinirli-ordu"
        if safe_parallel > 1
        else "ardisik-sefer"
    )

    stages = [str(stage) for stage in route.get("stages", [])]
    stage_groups = _partition_stages(stages, sessions)
    roles = [str(role) for role in route.get("roles", [])]
    required = [str(item) for item in route.get("required_evidence", [])]
    tasks: list[dict[str, Any]] = []
    sefers: list[dict[str, Any]] = []
    task_index = 0
    previous_task: str | None = None
    for sefer_index, group in enumerate(stage_groups, start=1):
        sefer_tasks: list[str] = []
        owners: list[str] = []
        for stage in group:
            task_index += 1
            task_id = f"task-{task_index:02d}"
            owner = _owner_for_stage(stage, roles, task_index - 1)
            task = {
                "id": task_id,
                "stage": stage,
                "owner_role": owner,
                "dependencies": [previous_task] if previous_task else [],
                "required_evidence": _stage_evidence(stage, required),
                "completion_rule": "evidence-recorded",
            }
            tasks.append(task)
            sefer_tasks.append(task_id)
            if owner not in owners:
                owners.append(owner)
            previous_task = task_id
        sefers.append(
            {
                "id": f"sefer-{sefer_index:02d}",
                "ordinal": sefer_index,
                "stages": group,
                "task_ids": sefer_tasks,
                "paşalar": owners,
                "handoff_required": sefer_index < len(stage_groups),
                "exit_gate": "all tasks have recorded evidence",
            }
        )

    enriched = dict(route)
    enriched["route_schema_version"] = route.get("schema_version")
    enriched["schema_version"] = 3
    enriched["target"] = normalized_target
    enriched["complexity"] = {
        "score": score,
        "band": _complexity_band(score),
        "estimated_working_set_tokens": estimated_tokens,
    }
    enriched["context_budget"] = capacity
    enriched["recommended_sessions"] = sessions
    enriched["orchestration_lane"] = lane
    enriched["safe_parallel_workstreams"] = safe_parallel
    enriched["command_structure"] = {
        "padişah": "user",
        "sadrazam": "sadrazam",
        "vezirler": roles,
        "paşalar": sorted(
            {owner for sefer in sefers for owner in sefer["paşalar"]}
        ),
    }
    enriched["sefers"] = sefers
    enriched["tasks"] = tasks
    enriched["memory_contract"] = {
        "state_lives_on_disk": True,
        "checkpoint_after_each_sefer": True,
        "handoff_at_percent": capacity["handoff_percent"],
        "resume_requires_last_receipt": True,
        "required_records": [
            "specification",
            "plan",
            "task state",
            "decisions",
            "progress",
            "evidence",
            "next action",
        ],
    }
    enriched["publication_obligations"] = _publication_obligations(
        route, normalized_target
    )
    return enriched
