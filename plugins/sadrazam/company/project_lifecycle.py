"""Read-only lifecycle status for installed Divan Project OS contracts."""
from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any

import project_os
import project_state


def _digest(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _managed_block(path: pathlib.Path) -> tuple[bytes | None, str | None]:
    if path.is_symlink() or not path.is_file():
        return None, "managed host file is unavailable or unsafe"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None, "managed host file is not strict UTF-8"
    normalized = text.replace("\r\n", "\n")
    begin = project_os.BEGIN_MARKER
    end = project_os.END_MARKER
    if normalized.count(begin) != 1 or normalized.count(end) != 1:
        return None, "managed block markers are invalid"
    start = normalized.find(begin)
    finish = normalized.find(end, start)
    if finish < start:
        return None, "managed block markers are invalid"
    block = normalized[start : finish + len(end)]
    return block.encode("utf-8"), None


def _observed_payload(
    root: pathlib.Path, row: dict[str, Any]
) -> tuple[str | None, str | None, bool]:
    path = root / row["path"]
    if row["mode"] == "marked-block":
        payload, error = _managed_block(path)
        return (None if payload is None else _digest(payload)), error, False
    if path.is_symlink() or (path.exists() and not path.is_file()):
        return None, "managed whole file is unsafe", False
    if not path.exists():
        return None, None, True
    try:
        return _digest(path.read_bytes()), None, False
    except OSError:
        return None, "managed whole file cannot be read", False


def _desired_plan(
    root: pathlib.Path, config: dict[str, Any]
) -> dict[str, Any]:
    managed = config.get("managed_files", [])
    hosts = [
        name
        for name, relative in project_os.HOST_PATHS.items()
        if relative in managed
    ]
    expected_url = None
    tools = root / project_os.SEO_TOOL_PATH
    if tools.is_file() and not tools.is_symlink():
        try:
            candidate = json.loads(tools.read_text(encoding="utf-8")).get(
                "expected_url"
            )
            expected_url = candidate if isinstance(candidate, str) else None
        except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
            expected_url = None
    return project_os.build_init_plan(
        root,
        config["profile"],
        config["locale"],
        hosts,
        project_os.CI_PATH in managed,
        expected_url=expected_url,
    )


def _classify_surfaces(
    root: pathlib.Path,
    recorded: dict[str, Any],
    desired: dict[str, Any],
) -> tuple[list[dict[str, str]], list[str]]:
    old = {row["path"]: row for row in recorded["managed_files"]}
    new = {row["path"]: row for row in desired["managed_files"]}
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for path in sorted(set(old) | set(new)):
        previous = old.get(path)
        target = new.get(path)
        if previous is None:
            classification = "unmanaged"
        elif target is None:
            classification = "stale-record"
        elif previous["mode"] != target["mode"]:
            classification = "unsafe"
            errors.append(f"{path}: ownership mode changed")
        else:
            observed, error, missing = _observed_payload(root, previous)
            if error is not None:
                classification = "unsafe"
                errors.append(f"{path}: {error}")
            elif missing:
                classification = "missing"
            elif observed != previous["payload_sha256"]:
                classification = "user-modified"
            elif previous["payload_sha256"] != target["payload_sha256"]:
                classification = "update-available"
            else:
                classification = "current"
        rows.append({"path": path, "classification": classification})
    return rows, errors


def _overall_status(
    surfaces: list[dict[str, str]],
    errors: list[str],
    source_changed: bool,
) -> str:
    classes = {row["classification"] for row in surfaces}
    if errors or "unsafe" in classes:
        return "BLOCKED"
    if classes.intersection({"user-modified", "missing", "stale-record"}):
        return "DRIFTED"
    if source_changed or classes.intersection(
        {"update-available", "unmanaged"}
    ):
        return "UPDATE_AVAILABLE"
    return "CURRENT"


def project_status(project: pathlib.Path | str) -> dict[str, Any]:
    """Return ownership and drift status without writing target or host state."""
    root = pathlib.Path(project).resolve()
    config, config_errors = project_os._load_config(root)
    recorded, state_errors = project_state.load_install_state(root)
    errors = [*config_errors, *state_errors]
    if config is None or recorded is None:
        return {
            "schema_version": 1,
            "status": "BLOCKED",
            "project": root.name,
            "surfaces": [],
            "errors": errors,
            "continuation_command": (
                "python scripts/divan.py project status --project . --json"
            ),
        }
    if recorded["project_identity"] != project_os._project_identity(root):
        errors.append("install state project identity does not match this project")
    try:
        plan = _desired_plan(root, config)
        desired = json.loads(
            next(
                row["content"]
                for row in plan["writes"]
                if row["path"] == project_os.INSTALL_STATE_PATH
            )
        )
    except (OSError, ValueError, StopIteration, json.JSONDecodeError) as error:
        errors.append(f"desired project state cannot be rendered: {error}")
        desired = recorded
    surfaces, surface_errors = _classify_surfaces(root, recorded, desired)
    errors.extend(surface_errors)
    source_changed = recorded["installed"] != desired["installed"]
    status = _overall_status(surfaces, errors, source_changed)
    result: dict[str, Any] = {
        "schema_version": 1,
        "status": status,
        "project": root.name,
        "installed": recorded["installed"],
        "desired": desired["installed"],
        "surfaces": surfaces,
        "errors": errors,
    }
    if status != "CURRENT":
        command = {
            "UPDATE_AVAILABLE": (
                "python scripts/divan.py project update --project ."
            ),
            "DRIFTED": "python scripts/divan.py project repair --project .",
            "BLOCKED": (
                "python scripts/divan.py project status --project . --json"
            ),
        }[status]
        result["continuation_command"] = command
    return result

