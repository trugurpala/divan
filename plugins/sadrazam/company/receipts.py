#!/usr/bin/env python3
"""Append-only, redacted, deterministic Project OS receipts."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import tempfile
from typing import Any

STATES = (
    "DISCOVERED",
    "SPECIFIED",
    "PLANNED",
    "IMPLEMENTING",
    "VERIFIED",
    "PREVIEWED",
    "RELEASED",
    "OBSERVED",
    "BLOCKED",
    "FAILED",
)
TARGETS = frozenset({"VERIFIED", "PREVIEWED", "RELEASED", "OBSERVED"})
RECEIPT_KEYS = frozenset(
    {"schema_version", "goal_id", "intent", "target", "state", "artifacts", "events"}
)
EVENT_KEYS = frozenset(
    {
        "sequence",
        "from_state",
        "to_state",
        "reason",
        "evidence",
        "results",
        "resume_from",
        "previous_hash",
        "hash",
    }
)
RESULT_KEYS = frozenset({"status", "evidence"})
RESULT_STATES = frozenset({"PASS", "FAIL", "BLOCKED"})
RECEIPT_RESULT_IDS = frozenset(
    {"DPS-005", "DPS-006", "DPS-007", "DPS-008", "DPS-011"}
)
GOAL_ID_PATTERN = re.compile(r"^goal-[0-9a-f]{12}$")
DPS_ID_PATTERN = re.compile(r"^DPS-(?:00[1-9]|01[0-2])$")
TERMINAL_STATES = frozenset({"FAILED", "OBSERVED"})
TRANSITIONS = {
    "DISCOVERED": frozenset({"SPECIFIED", "BLOCKED", "FAILED"}),
    "SPECIFIED": frozenset({"PLANNED", "BLOCKED", "FAILED"}),
    "PLANNED": frozenset({"IMPLEMENTING", "BLOCKED", "FAILED"}),
    "IMPLEMENTING": frozenset({"VERIFIED", "BLOCKED", "FAILED"}),
    "VERIFIED": frozenset({"PREVIEWED", "RELEASED", "BLOCKED", "FAILED"}),
    "PREVIEWED": frozenset({"RELEASED", "BLOCKED", "FAILED"}),
    "RELEASED": frozenset({"OBSERVED", "BLOCKED", "FAILED"}),
}
SECRET_PATTERN = re.compile(
    r"(?i)\b(?P<label>api[_-]?key|password|secret|token|authorization)"
    r"(?P<separator>\s*[:=]\s*)(?!\[REDACTED_SECRET\])\S+"
)
WINDOWS_ABSOLUTE = re.compile(r"(?i)(?:^|[\s\"'])[a-z]:[\\/]")
POSIX_ABSOLUTE = re.compile(r"(?<![:/\w])/(?!/)[^\s\"']+")
TILDE_HOME = re.compile(r"(?<!\w)~[\\/][^\s\"']+")
STANDALONE_SECRET = re.compile(
    r"(?i)(?:"
    r"\bsk-(?:proj-)?[a-z0-9_-]{16,}"
    r"|\bghp_[a-z0-9]{20,}"
    r"|\bgithub_pat_[a-z0-9_]{20,}"
    r"|\bxox[a-z]-[a-z0-9-]{20,}"
    r"|\bbearer\s+[a-z0-9._~+/-]{20,}"
    r"|\b[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}\b"
    r")"
)


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _atomic_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_json_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _event_hash(value: dict[str, Any]) -> str:
    material = {key: item for key, item in value.items() if key != "hash"}
    return hashlib.sha256(
        json.dumps(
            material, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
    ).hexdigest()


def _event(
    sequence: int,
    from_state: str | None,
    to_state: str,
    reason: str = "",
    evidence: list[str] | None = None,
    results: dict[str, dict[str, Any]] | None = None,
    resume_from: str | None = None,
    previous_hash: str | None = None,
) -> dict[str, Any]:
    value = {
        "sequence": sequence,
        "from_state": from_state,
        "to_state": to_state,
        "reason": reason,
        "evidence": [] if evidence is None else list(evidence),
        "results": {} if results is None else results,
        "resume_from": resume_from,
        "previous_hash": previous_hash,
    }
    value["hash"] = _event_hash(value)
    return value


def new_receipt(
    goal_id: str,
    intent: str,
    target: str,
    artifacts: dict[str, str],
) -> dict[str, Any]:
    """Build the canonical initial receipt value."""
    if not GOAL_ID_PATTERN.fullmatch(goal_id):
        raise ValueError("receipt goal_id is invalid")
    if not isinstance(intent, str) or not intent.strip():
        raise ValueError("receipt intent must be nonempty text")
    if target.upper() not in TARGETS:
        raise ValueError("receipt target is invalid")
    if not artifacts:
        raise ValueError("receipt artifacts must be nonempty")
    return {
        "schema_version": 1,
        "goal_id": goal_id,
        "intent": intent,
        "target": target.upper(),
        "state": "DISCOVERED",
        "artifacts": dict(sorted(artifacts.items())),
        "events": [_event(1, None, "DISCOVERED")],
    }


def write_receipt(path: pathlib.Path | str, value: dict[str, Any]) -> None:
    _atomic_json(pathlib.Path(path), value)


def _load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("receipt root must be an object")
    return value


def append_transition(
    path: pathlib.Path | str,
    to_state: str,
    *,
    reason: str = "",
    evidence: list[str] | None = None,
    results: dict[str, dict[str, Any]] | None = None,
    resume_from: str | None = None,
) -> dict[str, Any]:
    """Append one legal phase event and atomically replace the receipt."""
    receipt_path = pathlib.Path(path)
    verification = verify_receipt(receipt_path)
    if not verification["ok"]:
        raise ValueError("; ".join(verification["errors"]))
    value = _load(receipt_path)
    current = value.get("state")
    destination = to_state.upper()
    if current in TERMINAL_STATES:
        raise ValueError(f"{current} is terminal")
    if current == "BLOCKED":
        expected = value.get("events", [])[-1].get("resume_from")
        if destination != expected:
            raise ValueError(f"BLOCKED may resume only to {expected}")
    elif destination not in TRANSITIONS.get(str(current), frozenset()):
        raise ValueError(f"illegal transition: {current} -> {destination}")
    if destination == "BLOCKED":
        if resume_from is not None and resume_from != current:
            raise ValueError("BLOCKED resume_from must be the preceding phase")
        resume_from = str(current)
    elif current == "BLOCKED":
        resume_from = None
    elif resume_from is not None:
        raise ValueError("resume_from is valid only for BLOCKED")
    events = value.get("events")
    if not isinstance(events, list):
        raise ValueError("receipt events must be an array")
    events.append(
        _event(
            len(events) + 1,
            str(current),
            destination,
            reason=redact_text(reason),
            evidence=evidence,
            results={} if results is None else results,
            resume_from=resume_from,
            previous_hash=events[-1].get("hash") if events else None,
        )
    )
    value["state"] = destination
    result = verify_receipt_value(value, receipt_path)
    if result["errors"]:
        raise ValueError("; ".join(result["errors"]))
    _atomic_json(receipt_path, value)
    return value


def resume_receipt(path: pathlib.Path | str) -> dict[str, Any]:
    receipt_path = pathlib.Path(path)
    verification = verify_receipt(receipt_path)
    if not verification["ok"]:
        raise ValueError("; ".join(verification["errors"]))
    value = _load(receipt_path)
    if value.get("state") != "BLOCKED":
        raise ValueError("goal is not BLOCKED")
    events = value.get("events")
    if not isinstance(events, list) or not events:
        raise ValueError("receipt has no BLOCKED event")
    resume_from = events[-1].get("resume_from")
    if not isinstance(resume_from, str):
        raise ValueError("BLOCKED receipt has no resume_from")
    return append_transition(path, resume_from)


def _canonical_receipt_context(
    path: pathlib.Path,
) -> tuple[pathlib.Path | None, str | None, list[str]]:
    if ".." in path.parts:
        return None, None, ["receipt path cannot contain parent traversal"]
    absolute = path.absolute()
    errors: list[str] = []
    try:
        goal_id = absolute.parent.name
        root = absolute.parents[3]
    except IndexError:
        return None, None, ["receipt path is not canonical"]
    expected = root / ".divan" / "evidence" / goal_id / "receipt.json"
    if absolute != expected or not GOAL_ID_PATTERN.fullmatch(goal_id):
        errors.append(
            "receipt path must be .divan/evidence/<goal-id>/receipt.json"
        )
    if root.is_symlink():
        errors.append("receipt path uses a symlink")
    cursor = root
    for part in (".divan", "evidence", goal_id, "receipt.json"):
        cursor = cursor / part
        if cursor.is_symlink():
            errors.append("receipt path uses a symlink")
            break
    if not absolute.is_file():
        errors.append("receipt path must name a real file")
    try:
        absolute.resolve(strict=False).relative_to(root.resolve())
    except ValueError:
        errors.append("receipt path escapes the project")
    return root.resolve(), goal_id, errors


def _relative_path_errors(value: Any, label: str) -> list[str]:
    if not isinstance(value, str) or not value:
        return [f"{label} must be a project-relative path"]
    pure = pathlib.PurePosixPath(value.replace("\\", "/"))
    if pure.is_absolute() or ".." in pure.parts or WINDOWS_ABSOLUTE.search(value):
        return [f"{label} must be a project-relative path"]
    return []


def _artifact_containment_errors(
    root: pathlib.Path, candidate: pathlib.Path, label: str
) -> list[str]:
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return [f"{label} escapes the project"]
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return [f"{label} uses a symlink"]
    try:
        candidate.resolve(strict=False).relative_to(root)
    except ValueError:
        return [f"{label} escapes the project"]
    return []


def _artifact_content_errors(candidate: pathlib.Path, label: str) -> list[str]:
    try:
        artifact_text = candidate.read_text(encoding="utf-8")
    except UnicodeError:
        return []
    return _redaction_errors(artifact_text, f"{label}.content")


def _redaction_errors(value: Any, label: str = "receipt") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            errors.extend(_redaction_errors(item, f"{label}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_redaction_errors(item, f"{label}[{index}]"))
    elif isinstance(value, str):
        if SECRET_PATTERN.search(value):
            errors.append(f"{label} contains an unredacted secret")
        if STANDALONE_SECRET.search(value):
            errors.append(f"{label} contains an unredacted standalone secret")
        home = str(pathlib.Path.home())
        if home and home.casefold() in value.casefold():
            errors.append(f"{label} contains a home or absolute path")
        elif WINDOWS_ABSOLUTE.search(value):
            errors.append(f"{label} contains an absolute path")
        elif POSIX_ABSOLUTE.search(value):
            errors.append(f"{label} contains an absolute path")
        elif TILDE_HOME.search(value):
            errors.append(f"{label} contains a home path")
    return errors


def redact_text(value: str) -> str:
    """Redact credential assignments and the current user's home path."""
    redacted = SECRET_PATTERN.sub(
        lambda match: (
            f"{match.group('label')}{match.group('separator')}"
            "[REDACTED_SECRET]"
        ),
        value,
    )
    redacted = STANDALONE_SECRET.sub("[REDACTED_SECRET]", redacted)
    redacted = TILDE_HOME.sub("[REDACTED_HOME]", redacted)
    home = str(pathlib.Path.home())
    if home:
        redacted = re.sub(
            re.escape(home), "[REDACTED_HOME]", redacted, flags=re.IGNORECASE
        )
    redacted = re.sub(
        r"(?i)\b[a-z]:[\\/][^\s\"']+",
        "[REDACTED_PATH]",
        redacted,
    )
    redacted = re.sub(
        r"(?i)/(?:home|users)/[^\s\"']+",
        "[REDACTED_PATH]",
        redacted,
    )
    redacted = POSIX_ABSOLUTE.sub("[REDACTED_PATH]", redacted)
    return redacted


def _evidence_boundary(
    standard_id: str, goal_id: str, evidence: list[str]
) -> bool:
    spec_root = f".divan/specs/{goal_id}/"
    evidence_root = f".divan/evidence/{goal_id}/"
    if standard_id == "DPS-005":
        required = {
            f"{spec_root}spec.md",
            f"{spec_root}plan.md",
            f"{spec_root}tasks.md",
        }
        return set(evidence) == required
    return bool(evidence) and all(
        item.startswith(evidence_root)
        for item in evidence
    )


def _result_errors(
    results: Any, label: str, artifact_paths: set[str], goal_id: str
) -> list[str]:
    if not isinstance(results, dict):
        return [f"{label}.results must be an object"]
    errors: list[str] = []
    for standard_id, result in results.items():
        result_label = f"{label}.results.{standard_id}"
        if (
            not isinstance(standard_id, str)
            or not DPS_ID_PATTERN.fullmatch(standard_id)
            or standard_id not in RECEIPT_RESULT_IDS
        ):
            errors.append(f"{result_label} has an invalid DPS ID")
            continue
        if not isinstance(result, dict) or set(result) != RESULT_KEYS:
            errors.append(f"{result_label} keys are invalid")
            continue
        status = result.get("status")
        if not isinstance(status, str) or status not in RESULT_STATES:
            errors.append(f"{result_label}.status is invalid")
        evidence = result.get("evidence")
        if not isinstance(evidence, list) or not evidence or not all(
            isinstance(item, str) and item in artifact_paths for item in evidence
        ):
            errors.append(
                f"{result_label}.evidence must name nonempty receipt artifacts"
            )
        elif not _evidence_boundary(standard_id, goal_id, evidence):
            errors.append(
                f"{result_label}.evidence is outside the DPS registry boundary"
            )
    return errors


def _event_schema_errors(
    event: dict[str, Any],
    index: int,
    artifact_paths: set[str],
    goal_id: str,
) -> list[str]:
    label = f"events[{index}]"
    errors = [] if set(event) == EVENT_KEYS else [
        f"{label} keys do not match schema 1"
    ]
    if type(event.get("sequence")) is not int:
        errors.append(f"{label}.sequence must be an integer")
    for field in ("from_state", "resume_from"):
        if event.get(field) is not None and event.get(field) not in STATES:
            errors.append(f"{label}.{field} is invalid")
    if event.get("to_state") not in STATES:
        errors.append(f"{label}.to_state is invalid")
    if not isinstance(event.get("reason"), str):
        errors.append(f"{label}.reason must be text")
    evidence = event.get("evidence")
    if not isinstance(evidence, list) or not all(
        isinstance(item, str) and item in artifact_paths for item in evidence
    ):
        errors.append(
            f"{label}.evidence must name existing hashed receipt artifacts"
        )
    previous_hash = event.get("previous_hash")
    if previous_hash is not None and (
        not isinstance(previous_hash, str)
        or not re.fullmatch(r"[0-9a-f]{64}", previous_hash)
    ):
        errors.append(f"{label}.previous_hash is invalid")
    if not isinstance(event.get("hash"), str) or not re.fullmatch(
        r"[0-9a-f]{64}", event.get("hash", "")
    ):
        errors.append(f"{label}.hash is invalid")
    results = event.get("results")
    errors.extend(_result_errors(results, label, artifact_paths, goal_id))
    if isinstance(evidence, list) and isinstance(results, dict) and results:
        result_evidence = {
            item
            for result in results.values()
            if isinstance(result, dict) and isinstance(result.get("evidence"), list)
            for item in result["evidence"]
            if isinstance(item, str)
        }
        if not set(evidence).issubset(result_evidence):
            errors.append(f"{label}.evidence does not match its DPS results")
    return errors


def _transition_errors(
    events: Any, declared_state: Any, artifact_paths: set[str], goal_id: str
) -> list[str]:
    if not isinstance(events, list) or not events:
        return ["receipt.events must be a non-empty array"]
    errors: list[str] = []
    current: str | None = None
    blocked_resume: str | None = None
    previous_hash: str | None = None
    for index, event in enumerate(events, 1):
        label = f"events[{index - 1}]"
        if not isinstance(event, dict):
            errors.append(f"{label} must be an object")
            continue
        errors.extend(
            _event_schema_errors(event, index - 1, artifact_paths, goal_id)
        )
        if event.get("sequence") != index:
            errors.append(f"{label}.sequence must be {index}")
        if event.get("previous_hash") != previous_hash:
            errors.append(f"{label} event hash chain is broken")
        if event.get("hash") != _event_hash(event):
            errors.append(f"{label} event hash does not match")
        source = event.get("from_state")
        destination = event.get("to_state")
        if index == 1:
            if source is not None or destination != "DISCOVERED":
                errors.append("first receipt event must discover the goal")
            if event.get("resume_from") is not None:
                errors.append("first receipt event resume_from must be null")
            if event.get("previous_hash") is not None:
                errors.append("first receipt event previous_hash must be null")
            current = "DISCOVERED"
            previous_hash = event.get("hash")
            continue
        if source != current:
            errors.append(f"{label}.from_state does not match preceding state")
        if current in TERMINAL_STATES:
            errors.append(f"{label} follows terminal state {current}")
        elif current == "BLOCKED":
            if destination != blocked_resume:
                errors.append(
                    f"{label} must resume BLOCKED goal to {blocked_resume}"
                )
        elif destination not in TRANSITIONS.get(str(current), frozenset()):
            errors.append(f"{label} has illegal transition {current} -> {destination}")
        resume_from = event.get("resume_from")
        if destination == "BLOCKED":
            if resume_from != current:
                errors.append(f"{label}.resume_from must be {current}")
            blocked_resume = str(current)
        else:
            if resume_from is not None:
                errors.append(f"{label}.resume_from is valid only for BLOCKED")
            blocked_resume = None
        if isinstance(destination, str):
            current = destination
        previous_hash = event.get("hash")
    if declared_state != current:
        errors.append("receipt.state does not match the final event")
    return errors


def _latest_result_data(
    events: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    latest_results: dict[str, dict[str, Any]] = {}
    result_phases: dict[str, str] = {}
    for event in events:
        latest_results.update(event["results"])
        event_phase = (
            event.get("resume_from")
            if event.get("to_state") == "BLOCKED"
            else event.get("to_state")
        )
        if isinstance(event_phase, str):
            for standard_id in event["results"]:
                result_phases[standard_id] = event_phase
    return latest_results, result_phases


def verify_receipt_value(
    value: dict[str, Any], receipt_path: pathlib.Path | None = None
) -> dict[str, Any]:
    errors = [] if set(value) == RECEIPT_KEYS else [
        "receipt keys do not match schema 1"
    ]
    if type(value.get("schema_version")) is not int or value.get("schema_version") != 1:
        errors.append("receipt.schema_version must be 1")
    goal_id = value.get("goal_id")
    if not isinstance(goal_id, str) or not GOAL_ID_PATTERN.fullmatch(goal_id):
        errors.append("receipt.goal_id is invalid")
    intent = value.get("intent")
    if not isinstance(intent, str) or not intent.strip():
        errors.append("receipt.intent must be nonempty redacted text")
    target = value.get("target")
    if not isinstance(target, str) or target not in TARGETS:
        errors.append("receipt.target is invalid")
    if value.get("state") not in STATES:
        errors.append("receipt.state is invalid")
    root: pathlib.Path | None = None
    path_goal: str | None = None
    if receipt_path is None:
        errors.append("receipt verification requires a canonical receipt path")
    else:
        root, path_goal, path_errors = _canonical_receipt_context(receipt_path)
        errors.extend(path_errors)
        if isinstance(goal_id, str) and path_goal != goal_id:
            errors.append("receipt.goal_id does not match its canonical path")
    artifacts = value.get("artifacts")
    artifact_paths: set[str] = set()
    if not isinstance(artifacts, dict) or not artifacts:
        errors.append("receipt.artifacts must be a nonempty object")
    else:
        artifact_paths = set(artifacts) if all(
            isinstance(item, str) for item in artifacts
        ) else set()
        if isinstance(goal_id, str) and GOAL_ID_PATTERN.fullmatch(goal_id):
            required = {
                f".divan/specs/{goal_id}/spec.md",
                f".divan/specs/{goal_id}/plan.md",
                f".divan/specs/{goal_id}/tasks.md",
            }
            missing = sorted(required - artifact_paths)
            if missing:
                errors.append(
                    "receipt.artifacts missing canonical goal artifacts: "
                    + ", ".join(missing)
                )
        for relative, digest in artifacts.items():
            path_errors = _relative_path_errors(relative, f"artifacts.{relative}")
            errors.extend(path_errors)
            if not isinstance(digest, str) or not re.fullmatch(
                r"[0-9a-f]{64}", digest
            ):
                errors.append(f"artifacts.{relative} hash is invalid")
            elif root is not None and not path_errors:
                candidate = root.joinpath(
                    *pathlib.PurePosixPath(relative).parts
                )
                containment_errors = _artifact_containment_errors(
                    root, candidate, f"artifacts.{relative}"
                )
                errors.extend(containment_errors)
                if containment_errors:
                    continue
                if not candidate.is_file():
                    errors.append(f"artifacts.{relative} path does not exist")
                elif hashlib.sha256(candidate.read_bytes()).hexdigest() != digest:
                    errors.append(f"artifacts.{relative} hash does not match")
                else:
                    errors.extend(
                        _artifact_content_errors(
                            candidate, f"artifacts.{relative}"
                        )
                    )
    errors.extend(
        _transition_errors(
            value.get("events"),
            value.get("state"),
            artifact_paths,
            goal_id if isinstance(goal_id, str) else "",
        )
    )
    events = value.get("events")
    if isinstance(events, list):
        for event_index, event in enumerate(events):
            if not isinstance(event, dict):
                continue
            evidence = event.get("evidence")
            if not isinstance(evidence, list):
                errors.append(f"events[{event_index}].evidence must be an array")
            else:
                for evidence_index, item in enumerate(evidence):
                    errors.extend(
                        _relative_path_errors(
                            item,
                            f"events[{event_index}].evidence[{evidence_index}]",
                        )
                    )
    errors.extend(_redaction_errors(value))
    latest_results: dict[str, dict[str, Any]] = {}
    result_phases: dict[str, str] = {}
    if not errors and isinstance(events, list):
        latest_results, result_phases = _latest_result_data(events)
    return {
        "schema_version": 1,
        "ok": not errors,
        "state": value.get("state"),
        "resume_from": (
            events[-1].get("resume_from")
            if isinstance(events, list)
            and events
            and isinstance(events[-1], dict)
            else None
        ),
        "goal_id": goal_id if isinstance(goal_id, str) else None,
        "artifacts": (
            dict(artifacts)
            if isinstance(artifacts, dict)
            else {}
        ),
        "results": latest_results,
        "result_phases": result_phases,
        "errors": errors,
    }


def verify_receipt(path: pathlib.Path | str) -> dict[str, Any]:
    """Validate schema, hashes, transitions, redaction, and relative paths."""
    receipt_path = pathlib.Path(path)
    _, _, path_errors = _canonical_receipt_context(receipt_path)
    if path_errors:
        return {
            "schema_version": 1,
            "ok": False,
            "state": None,
            "resume_from": None,
            "goal_id": None,
            "artifacts": {},
            "results": {},
            "result_phases": {},
            "errors": path_errors,
        }
    try:
        value = _load(receipt_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return {
            "schema_version": 1,
            "ok": False,
            "state": None,
            "resume_from": None,
            "goal_id": None,
            "artifacts": {},
            "results": {},
            "result_phases": {},
            "errors": [f"receipt cannot be read: {error}"],
        }
    return verify_receipt_value(value, receipt_path)
