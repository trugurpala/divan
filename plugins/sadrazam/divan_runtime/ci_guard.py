"""Evidence-gated retry budget for repeated CI failure fingerprints."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import tempfile
from collections.abc import Sequence
from typing import Any

from . import receipts

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
SHA = re.compile(r"\b[0-9a-f]{40}\b", re.IGNORECASE)
TIMESTAMP = re.compile(
    r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\b"
)
SPACE = re.compile(r"\s+")
RECORDED_AT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
MAX_REMEDIATIONS = 2


def _normalized(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("CI fingerprint fields must be non-empty text")
    cleaned = ANSI.sub("", value)
    cleaned = receipts.redact_text(cleaned)
    cleaned = SHA.sub("[SHA]", cleaned)
    cleaned = TIMESTAMP.sub("[TIME]", cleaned)
    return SPACE.sub(" ", cleaned).strip().casefold()


def fingerprint(
    workflow: str,
    job: str,
    check: str,
    error_signature: str,
) -> str:
    """Return a stable digest without retaining raw CI output."""
    material = "\0".join(
        _normalized(item) for item in (workflow, job, check, error_signature)
    )
    return "sha256:" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def _empty() -> dict[str, Any]:
    return {"schema_version": 1, "records": {}}


def _validate_ledger(value: object) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "records"}
        or value.get("schema_version") != 1
        or not isinstance(value.get("records"), dict)
    ):
        raise ValueError("CI failure ledger schema is invalid")
    for key, row in value["records"].items():
        if (
            not isinstance(key, str)
            or not key.startswith("sha256:")
            or not isinstance(row, dict)
            or set(row)
            != {"workflow", "job", "check", "status", "attempts"}
            or row["status"] not in {"OPEN", "BLOCKED"}
            or not isinstance(row["attempts"], list)
            or len(row["attempts"]) > MAX_REMEDIATIONS
        ):
            raise ValueError("CI failure ledger record is invalid")
        for attempt in row["attempts"]:
            if (
                not isinstance(attempt, dict)
                or set(attempt)
                != {
                    "sequence",
                    "hypothesis_digest",
                    "evidence",
                    "recorded_at",
                }
                or type(attempt["sequence"]) is not int
                or attempt["sequence"] <= 0
                or not isinstance(attempt["hypothesis_digest"], str)
                or not isinstance(attempt["evidence"], list)
                or not isinstance(attempt["recorded_at"], str)
            ):
                raise ValueError("CI failure ledger attempt is invalid")
    return value


def _load(path: pathlib.Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError("CI failure ledger cannot be a symlink")
    if not path.exists():
        return _empty()
    if not path.is_file():
        raise ValueError("CI failure ledger must be a file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"CI failure ledger cannot be read: {error}") from error
    return _validate_ledger(value)


def _atomic_write(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("CI failure ledger cannot be a symlink")
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = pathlib.Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _evidence(values: Sequence[str]) -> list[str]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("focused evidence must be a path list")
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("focused evidence paths must be non-empty")
        path = pathlib.PurePosixPath(value.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("focused evidence paths must be project-relative")
        result.append(path.as_posix())
    if len(result) != len(set(result)) or len(result) > 50:
        raise ValueError("focused evidence paths must be unique and bounded")
    return sorted(result)


def _hypothesis_digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(
        _normalized(value).encode("utf-8")
    ).hexdigest()


def _result(
    status: str,
    key: str,
    attempts: int,
    *,
    mutation_allowed: bool,
) -> dict[str, Any]:
    resulting_attempts = attempts + 1 if mutation_allowed else attempts
    return {
        "schema_version": 1,
        "status": status,
        "fingerprint": key,
        "attempt_number": resulting_attempts,
        "mutation_allowed": mutation_allowed,
        "remaining_remediations": max(
            0, MAX_REMEDIATIONS - resulting_attempts
        ),
    }


def evaluate(
    ledger_path: pathlib.Path | str,
    *,
    workflow: str,
    job: str,
    check: str,
    error_signature: str,
    hypothesis: str,
    evidence: Sequence[str],
    execute: bool = False,
    recorded_at: str,
) -> dict[str, Any]:
    """Authorize at most two evidence-backed, hypothesis-changing remediations."""
    path = pathlib.Path(ledger_path)
    ledger = _load(path)
    key = fingerprint(workflow, job, check, error_signature)
    row = ledger["records"].get(key)
    attempts = [] if row is None else row["attempts"]
    attempt_count = len(attempts)
    if attempt_count >= MAX_REMEDIATIONS:
        if row is not None and execute and row["status"] != "BLOCKED":
            row["status"] = "BLOCKED"
            _atomic_write(path, ledger)
        return _result("BLOCKED", key, attempt_count, mutation_allowed=False)
    focused = _evidence(evidence)
    if not focused:
        return _result(
            "FOCUSED_EVIDENCE_REQUIRED",
            key,
            attempt_count,
            mutation_allowed=False,
        )
    digest = _hypothesis_digest(hypothesis)
    if any(attempt["hypothesis_digest"] == digest for attempt in attempts):
        return _result(
            "CHANGED_HYPOTHESIS_REQUIRED",
            key,
            attempt_count,
            mutation_allowed=False,
        )
    if RECORDED_AT.fullmatch(recorded_at) is None:
        raise ValueError("recorded_at must be a UTC second timestamp")
    if execute:
        if row is None:
            row = {
                "workflow": _normalized(workflow),
                "job": _normalized(job),
                "check": _normalized(check),
                "status": "OPEN",
                "attempts": [],
            }
            ledger["records"][key] = row
        row["attempts"].append(
            {
                "sequence": attempt_count + 1,
                "hypothesis_digest": digest,
                "evidence": focused,
                "recorded_at": recorded_at,
            }
        )
        _atomic_write(path, ledger)
    return _result(
        "REMEDIATION_ALLOWED",
        key,
        attempt_count,
        mutation_allowed=True,
    )
