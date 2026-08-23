"""Validation and serialization contract for Pusula continuity capsules."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = 1
CHECKPOINTS = frozenset({0, 25, 50, 75, 100})
MAX_CAPSULE_CHARS = 12_000
MAX_TEXT_CHARS = 800

LIST_LIMITS = {
    "completed_tasks": 40,
    "decisions": 12,
    "verified_facts": 20,
    "open_risks": 8,
    "next_actions": 5,
    "evidence_refs": 16,
}

REQUIRED_KEYS = frozenset(
    {
        "schema",
        "project",
        "checkpoint_percent",
        "baseline_sha",
        "constitution_version",
        "plan_version",
        "active_spec",
        "completed_tasks",
        "decisions",
        "verified_facts",
        "open_risks",
        "next_actions",
        "evidence_refs",
        "budget",
    }
)

RAW_SECRET_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "password",
        "secret",
        "secret_value",
        "access_token",
        "refresh_token",
        "private_key",
        "client_secret",
    }
)

SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bgh[opusr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")


class CapsuleError(ValueError):
    """Raised when a continuity capsule violates the Pusula contract."""


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise CapsuleError(f"{field} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise CapsuleError(f"{field} must not be empty")
    if len(cleaned) > MAX_TEXT_CHARS:
        raise CapsuleError(f"{field} exceeds {MAX_TEXT_CHARS} characters")
    return cleaned


def _validate_relative_path(value: Any, field: str) -> str:
    text = _require_string(value, field)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        raise CapsuleError(f"{field} must be a repository-relative path")
    return text.replace("\\", "/")


def _validate_string_list(data: Mapping[str, Any], field: str) -> list[str]:
    value = data.get(field)
    if not isinstance(value, list):
        raise CapsuleError(f"{field} must be a list")
    limit = LIST_LIMITS[field]
    if len(value) > limit:
        raise CapsuleError(f"{field} exceeds item limit {limit}")
    cleaned: list[str] = []
    for index, item in enumerate(value):
        cleaned.append(_require_string(item, f"{field}[{index}]"))
    return cleaned


def _validate_completed_tasks(value: Any) -> list[int]:
    if not isinstance(value, list):
        raise CapsuleError("completed_tasks must be a list")
    if len(value) > LIST_LIMITS["completed_tasks"]:
        raise CapsuleError("completed_tasks exceeds the locked 40-task plan")
    tasks: list[int] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int) or not 1 <= item <= 40:
            raise CapsuleError("completed_tasks entries must be integers from 1 through 40")
        tasks.append(item)
    if len(tasks) != len(set(tasks)):
        raise CapsuleError("completed_tasks must not contain duplicates")
    return sorted(tasks)


def _validate_budget(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CapsuleError("budget must be an object")
    result: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip():
            raise CapsuleError("budget keys must be non-empty strings")
        if isinstance(item, bool) or item is None or isinstance(item, (int, float, str)):
            if isinstance(item, str) and len(item) > MAX_TEXT_CHARS:
                raise CapsuleError(f"budget.{key} exceeds {MAX_TEXT_CHARS} characters")
            result[key] = item
            continue
        raise CapsuleError(f"budget.{key} must be a JSON scalar")
    return result


def _walk_for_secrets(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in RAW_SECRET_KEYS:
                raise CapsuleError(f"raw secret field is forbidden: {path}.{key}")
            _walk_for_secrets(item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _walk_for_secrets(item, f"{path}[{index}]")
        return
    if isinstance(value, str):
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                raise CapsuleError(f"secret-like value detected at {path}")


def _normalized_body(data: Mapping[str, Any]) -> dict[str, Any]:
    unknown = set(data) - REQUIRED_KEYS - {"digest"}
    missing = REQUIRED_KEYS - set(data)
    if missing:
        raise CapsuleError(f"missing required fields: {', '.join(sorted(missing))}")
    if unknown:
        raise CapsuleError(f"unknown fields: {', '.join(sorted(unknown))}")
    if data.get("schema") != SCHEMA_VERSION:
        raise CapsuleError(f"schema must equal {SCHEMA_VERSION}")

    checkpoint = data.get("checkpoint_percent")
    if isinstance(checkpoint, bool) or not isinstance(checkpoint, int):
        raise CapsuleError("checkpoint_percent must be an integer")
    if checkpoint not in CHECKPOINTS:
        raise CapsuleError("checkpoint_percent must be one of 0, 25, 50, 75, 100")

    baseline_sha = _require_string(data.get("baseline_sha"), "baseline_sha").lower()
    if not SHA1_RE.fullmatch(baseline_sha):
        raise CapsuleError("baseline_sha must be a lowercase 40-character Git SHA")

    constitution_version = _require_string(
        data.get("constitution_version"), "constitution_version"
    )
    if not VERSION_RE.fullmatch(constitution_version):
        raise CapsuleError("constitution_version must be semantic-version shaped")

    body = {
        "schema": SCHEMA_VERSION,
        "project": _require_string(data.get("project"), "project"),
        "checkpoint_percent": checkpoint,
        "baseline_sha": baseline_sha,
        "constitution_version": constitution_version,
        "plan_version": _require_string(data.get("plan_version"), "plan_version"),
        "active_spec": _validate_relative_path(data.get("active_spec"), "active_spec"),
        "completed_tasks": _validate_completed_tasks(data.get("completed_tasks")),
        "decisions": _validate_string_list(data, "decisions"),
        "verified_facts": _validate_string_list(data, "verified_facts"),
        "open_risks": _validate_string_list(data, "open_risks"),
        "next_actions": _validate_string_list(data, "next_actions"),
        "evidence_refs": _validate_string_list(data, "evidence_refs"),
        "budget": _validate_budget(data.get("budget")),
    }
    if checkpoint < 100 and not body["next_actions"]:
        raise CapsuleError("next_actions must contain at least one item before 100%")
    _walk_for_secrets(body)
    return body


def canonical_json(data: Mapping[str, Any]) -> str:
    """Return canonical JSON for the digest, excluding any existing digest field."""

    body = _normalized_body(data)
    rendered = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(rendered) > MAX_CAPSULE_CHARS:
        raise CapsuleError(
            f"capsule exceeds token-friendly character budget: {len(rendered)} > "
            f"{MAX_CAPSULE_CHARS}"
        )
    return rendered


def compute_digest(data: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def seal_capsule(data: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize and seal a draft capsule with a SHA-256 digest."""

    body = _normalized_body(data)
    rendered = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(rendered) > MAX_CAPSULE_CHARS:
        raise CapsuleError(
            f"capsule exceeds token-friendly character budget: {len(rendered)} > "
            f"{MAX_CAPSULE_CHARS}"
        )
    result = deepcopy(body)
    result["digest"] = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    return result


def validate_capsule(data: Mapping[str, Any], *, require_digest: bool = True) -> dict[str, Any]:
    """Validate a capsule and return its normalized representation."""

    body = _normalized_body(data)
    rendered = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(rendered) > MAX_CAPSULE_CHARS:
        raise CapsuleError(
            f"capsule exceeds token-friendly character budget: {len(rendered)} > "
            f"{MAX_CAPSULE_CHARS}"
        )
    expected = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    actual = data.get("digest")
    if require_digest:
        if not isinstance(actual, str) or not actual:
            raise CapsuleError("digest is required")
        if actual != expected:
            raise CapsuleError("digest mismatch")
    result = deepcopy(body)
    if isinstance(actual, str):
        result["digest"] = actual
    return result


def render_markdown(data: Mapping[str, Any]) -> str:
    capsule = validate_capsule(data)

    def bullets(items: list[Any], empty: str = "- none") -> str:
        return "\n".join(f"- {item}" for item in items) if items else empty

    budget = capsule["budget"]
    budget_lines = [f"- {key}: {budget[key]}" for key in sorted(budget)] or ["- none"]
    completed = ", ".join(str(item) for item in capsule["completed_tasks"]) or "none"
    return "\n".join(
        [
            f"# Pusula checkpoint {capsule['checkpoint_percent']}%",
            "",
            f"- project: {capsule['project']}",
            f"- baseline: {capsule['baseline_sha']}",
            f"- constitution: {capsule['constitution_version']}",
            f"- plan: {capsule['plan_version']}",
            f"- spec: {capsule['active_spec']}",
            f"- completed tasks: {completed}",
            f"- digest: {capsule['digest']}",
            "",
            "## Accepted decisions",
            bullets(capsule["decisions"]),
            "",
            "## Verified facts",
            bullets(capsule["verified_facts"]),
            "",
            "## Open risks",
            bullets(capsule["open_risks"]),
            "",
            "## Next actions",
            bullets(capsule["next_actions"]),
            "",
            "## Evidence refs",
            bullets(capsule["evidence_refs"]),
            "",
            "## Budget",
            "\n".join(budget_lines),
            "",
        ]
    )


def load_capsule(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CapsuleError(f"cannot read JSON capsule {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CapsuleError("capsule root must be an object")
    return value


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)
