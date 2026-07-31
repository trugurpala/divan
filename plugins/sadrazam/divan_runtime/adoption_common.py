"""Shared serialization, privacy, and environment helpers for adoption receipts."""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import platform
import re
from typing import Any

from . import receipts

SAFE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
EMAIL = re.compile(r"(?i)\b[^@\s]+@[^@\s]+\.[^@\s]+\b")
REMOTE = re.compile(r"(?i)\b(?:https?|ssh|git)://|\bgit@[\w.-]+:")
JSON_MARKER_START = "<!-- DIVAN_ADOPTION_JSON\n"
JSON_MARKER_END = "DIVAN_ADOPTION_JSON -->"


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def digest_schema_1(value: dict[str, Any]) -> str:
    material = {
        key: item for key, item in value.items() if key != "receipt_digest"
    }
    canonical = json.dumps(
        material, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def digest_schema_2(value: dict[str, Any]) -> str:
    material = copy.deepcopy(value)
    proof = material.get("proof")
    if isinstance(proof, dict):
        proof.pop("receipt_digest", None)
    canonical = json.dumps(
        material, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def coarse_environment() -> dict[str, str]:
    system = platform.system().casefold()
    operating_system = {
        "windows": "windows",
        "linux": "linux",
        "darwin": "macos",
    }.get(system, "other")
    machine = platform.machine().casefold()
    architecture = (
        "arm64"
        if machine in {"aarch64", "arm64"}
        else "x86_64"
        if machine in {"amd64", "x86_64"}
        else "other"
    )
    return {"os": operating_system, "architecture": architecture}


def privacy_errors(value: Any, label: str = "receipt") -> list[str]:
    errors = receipts._redaction_errors(value, label)
    if isinstance(value, dict):
        for key, item in value.items():
            errors.extend(privacy_errors(item, f"{label}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(privacy_errors(item, f"{label}[{index}]"))
    elif isinstance(value, str):
        if EMAIL.search(value):
            errors.append(f"{label} contains an email address")
        if REMOTE.search(value):
            errors.append(f"{label} contains a remote URL")
    return sorted(set(errors))


def read_receipt(path: pathlib.Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    document = text
    if path.suffix.casefold() == ".md":
        if JSON_MARKER_START not in text or JSON_MARKER_END not in text:
            raise ValueError("Markdown adoption receipt has no JSON envelope")
        text = text.split(JSON_MARKER_START, 1)[1].split(
            JSON_MARKER_END, 1
        )[0]
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("adoption receipt root must be an object")
    return value, document
