"""Read-only lifecycle status for installed Divan Project OS contracts."""
from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any

import project_os
import project_state
import project_transactions


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
    try:
        path = project_os._safe_destination(root, row["path"])
    except ValueError as path_error:
        return None, str(path_error), False
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
            candidate = root / path
            if candidate.exists() or candidate.is_symlink():
                errors.append(f"{path}: desired target exists without ownership")
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
    try:
        project_os._safe_destination(root, ".divan/config.json")
        project_os._safe_destination(root, ".divan/install-state.json")
    except ValueError as error:
        return {
            "schema_version": 1,
            "status": "BLOCKED",
            "project": root.name,
            "surfaces": [],
            "errors": [str(error)],
            "continuation_command": (
                "python scripts/divan.py project status --project . --json"
            ),
        }
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


def _canonical_digest(value: dict[str, Any]) -> str:
    material = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return _digest(material)


def _legacy_config(root: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    path = root / ".divan" / "config.json"
    if path.is_symlink() or not path.is_file():
        return None, [".divan/config.json is unavailable or unsafe"]
    try:
        content = path.read_bytes()
        value = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, [f".divan/config.json is invalid: {error}"]
    if not isinstance(value, dict) or set(value) != set(project_os.CONFIG_KEYS):
        return None, [".divan/config.json schema 1 keys are invalid"]
    errors: list[str] = []
    if value.get("schema_version") != 1:
        errors.append(".divan/config.json is not schema 1")
    if content != project_os._json_bytes(value):
        errors.append(".divan/config.json schema 1 bytes are not canonical")
    if value.get("profile") not in {"standard", "strict"}:
        errors.append(".divan/config.json profile is invalid")
    if value.get("locale") not in {"en", "tr"}:
        errors.append(".divan/config.json locale is invalid")
    if value.get("autonomy") != "supervised":
        errors.append(".divan/config.json autonomy is invalid")
    for field in (
        "project_types",
        "workspaces",
        "providers",
        "capabilities",
        "commands",
        "standards",
        "managed_files",
    ):
        if not isinstance(value.get(field), list):
            errors.append(f".divan/config.json {field} must be an array")
    if not errors:
        errors.extend(project_os._waiver_errors(root))
        errors.extend(project_os._managed_file_errors(root, value))
        errors.extend(project_os._inspection_drift_errors(root, value))
    return value, errors


def _blocked_plan(
    operation: str, root: pathlib.Path, errors: list[str], surfaces: list[Any]
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "operation": operation,
        "status": "BLOCKED",
        "project": str(root),
        "errors": errors,
        "surfaces": surfaces,
        "execute_required": True,
        "continuation_command": (
            "python scripts/divan.py project status --project . --json"
        ),
    }


def _bind_plan(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result["plan_digest"] = _canonical_digest(value)
    return result


def build_update_plan(project: pathlib.Path | str) -> dict[str, Any]:
    """Plan an ownership-safe update or the sole schema-1 migration."""
    root = pathlib.Path(project).resolve()
    config, config_errors = project_os._load_config(root)
    migration: str | None = None
    if config is None or config_errors:
        legacy, legacy_errors = _legacy_config(root)
        if legacy is None or legacy_errors:
            return _blocked_plan(
                "update", root, [*config_errors, *legacy_errors], []
            )
        config = legacy
        migration = "config-schema-1-to-2"
    init_plan = _desired_plan(root, config)
    if migration is None:
        status = project_status(root)
        if status["status"] in {"BLOCKED", "DRIFTED"}:
            return _blocked_plan(
                "update",
                root,
                list(status.get("errors", [])),
                list(status.get("surfaces", [])),
            )
        surfaces = status["surfaces"]
    else:
        surfaces = [
            {
                "path": ".divan/config.json",
                "classification": "update-available",
            },
            {
                "path": project_os.INSTALL_STATE_PATH,
                "classification": "unmanaged",
            },
        ]
    value: dict[str, Any] = {
        "schema_version": 1,
        "operation": "update",
        "status": "PLANNED",
        "project": str(root),
        "migration": migration,
        "surfaces": surfaces,
        "init_plan": init_plan,
        "execute_required": True,
    }
    return _bind_plan(value)


def _validate_bound_plan(
    plan: dict[str, Any], operation: str
) -> pathlib.Path:
    if (
        not isinstance(plan, dict)
        or plan.get("schema_version") != 1
        or plan.get("operation") != operation
        or plan.get("status") != "PLANNED"
    ):
        raise ValueError(f"{operation} plan is invalid or blocked")
    project = plan.get("project")
    if not isinstance(project, str):
        raise ValueError(f"{operation} plan project is invalid")
    unsigned = {key: value for key, value in plan.items() if key != "plan_digest"}
    if plan.get("plan_digest") != _canonical_digest(unsigned):
        raise ValueError(f"{operation} plan digest changed")
    return pathlib.Path(project).resolve()


def apply_update_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Revalidate and apply an update through the proven init transaction."""
    root = _validate_bound_plan(plan, "update")
    fresh = build_update_plan(root)
    if fresh.get("plan_digest") != plan.get("plan_digest"):
        raise ValueError("project changed after update plan")
    result = project_transactions.apply_managed_plan(plan["init_plan"])
    return {
        "schema_version": 1,
        "operation": "update",
        "status": "APPLIED",
        "project": root.name,
        "changed": result["changed"],
        "migration": plan.get("migration"),
    }


def build_repair_plan(project: pathlib.Path | str) -> dict[str, Any]:
    """Plan repair of only missing, recorded whole-file payloads."""
    root = pathlib.Path(project).resolve()
    status = project_status(root)
    surfaces = list(status.get("surfaces", []))
    missing = [
        row["path"]
        for row in surfaces
        if row.get("classification") == "missing"
    ]
    unsafe = [
        row
        for row in surfaces
        if row.get("classification") not in {"current", "missing"}
    ]
    state, state_errors = project_state.load_install_state(root)
    if (
        state is None
        or state_errors
        or status.get("installed") != status.get("desired")
        or unsafe
        or not missing
    ):
        errors = [*list(status.get("errors", [])), *state_errors]
        if unsafe:
            errors.append("repair permits only missing owned whole files")
        if status.get("installed") != status.get("desired"):
            errors.append("repair requires the currently installed Divan source")
        if not missing:
            errors.append("no repairable missing owned whole file was found")
        return _blocked_plan("repair", root, errors, surfaces)
    modes = {row["path"]: row["mode"] for row in state["managed_files"]}
    if any(modes.get(path) != "whole-file" for path in missing):
        return _blocked_plan(
            "repair",
            root,
            ["missing marked blocks cannot be repaired automatically"],
            surfaces,
        )
    config, config_errors = project_os._load_config(root)
    if config is None or config_errors:
        return _blocked_plan("repair", root, config_errors, surfaces)
    value = {
        "schema_version": 1,
        "operation": "repair",
        "status": "PLANNED",
        "project": str(root),
        "surfaces": surfaces,
        "repair_paths": missing,
        "init_plan": _desired_plan(root, config),
        "execute_required": True,
    }
    return _bind_plan(value)


def apply_repair_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Revalidate and repair missing generated files transactionally."""
    root = _validate_bound_plan(plan, "repair")
    fresh = build_repair_plan(root)
    if fresh.get("plan_digest") != plan.get("plan_digest"):
        raise ValueError("project changed after repair plan")
    result = project_transactions.apply_managed_plan(plan["init_plan"])
    return {
        "schema_version": 1,
        "operation": "repair",
        "status": "REPAIRED",
        "project": root.name,
        "changed": result["changed"],
    }
