"""Shared immutable identifiers for clean-room proof planning and execution."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from . import timeouts

QUALIFYING_HOSTS = {
    "claude-code": ("claude", "--version"),
    "codex": ("codex", "--version"),
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def hash_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def domain_hash(domain: str, value: object) -> str:
    return hash_bytes(domain.encode("utf-8") + b"\0" + canonical_bytes(value))


def timeout_class(check_class: str) -> str:
    if check_class in {"test", "regression"}:
        return "test"
    if check_class == "build":
        return "verify"
    return "fast-check"


def timeout_policy_digest() -> str:
    policy = timeouts.DATA_DIRECTORY / "timeout-policy.json"
    return hash_bytes(policy.read_bytes())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("proof clock must return a timezone-aware datetime")
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def required_commands(goal_route: dict[str, Any]) -> set[str]:
    required = goal_route.get("checks")
    if (
        not isinstance(required, list)
        or not all(isinstance(item, str) for item in required)
    ):
        raise ValueError("goal route check authority is invalid")
    return set(required)


def enforce_check_capacity(
    candidates: list[dict[str, Any]], maximum: int
) -> None:
    if sum(row["goal_required"] for row in candidates) > maximum:
        raise ValueError(
            "goal route requires more than eight project checks; narrow the goal"
        )
