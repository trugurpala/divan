#!/usr/bin/env python3
"""Validate Pusula's locked plan and compact continuity checkpoint chain."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

from scripts import pusula_checkpoint_core as checkpoint_core

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = Path(".pusula/plan-lock.json")
CONTINUITY_DIR = Path(".pusula/continuity")
CHECKPOINT_NAME_RE = re.compile(r"^checkpoint-(00|25|50|75|100)\.json$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PLAN_KEYS = frozenset(
    {
        "schema",
        "plan_version",
        "constitution_version",
        "baseline",
        "target_product",
        "target_repository",
        "incubation_branch",
        "change_rule",
        "checkpoints",
        "layers",
        "tasks",
        "provider_posture",
        "upstream_pins",
    }
)
BASELINE_KEYS = frozenset(
    {
        "repository",
        "sha",
        "source_version",
        "canonical_test_count",
        "canonical_skips",
        "coverage_percent",
    }
)


class ContractError(ValueError):
    """Raised when the locked Pusula planning contract is inconsistent."""


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"JSON root must be an object: {path}")
    return value


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def _validate_baseline(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != BASELINE_KEYS:
        raise ContractError("baseline schema is invalid")
    sha = _nonempty_string(value["sha"], "baseline.sha").lower()
    if SHA_RE.fullmatch(sha) is None:
        raise ContractError("baseline.sha must be an exact lowercase Git SHA")
    for field in ("canonical_test_count", "canonical_skips", "coverage_percent"):
        item = value[field]
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise ContractError(f"baseline.{field} must be a non-negative integer")
    coverage = value["coverage_percent"]
    if coverage > 100:
        raise ContractError("baseline.coverage_percent must not exceed 100")
    return {
        "repository": _nonempty_string(value["repository"], "baseline.repository"),
        "sha": sha,
        "source_version": _nonempty_string(value["source_version"], "baseline.source_version"),
        "canonical_test_count": value["canonical_test_count"],
        "canonical_skips": value["canonical_skips"],
        "coverage_percent": coverage,
    }


def _validate_tasks(value: object) -> dict[int, str]:
    if not isinstance(value, list) or len(value) != 40:
        raise ContractError("tasks must contain exactly 40 locked tasks")
    result: dict[int, str] = {}
    for row in value:
        if not isinstance(row, list) or len(row) != 2:
            raise ContractError("each task must be [id, title]")
        task_id, title = row
        if isinstance(task_id, bool) or not isinstance(task_id, int):
            raise ContractError("task id must be an integer")
        if task_id in result:
            raise ContractError(f"duplicate task id: {task_id}")
        result[task_id] = _nonempty_string(title, f"task {task_id} title")
    if sorted(result) != list(range(1, 41)):
        raise ContractError("task ids must be exactly 1 through 40")
    return result


def _validate_layers(value: object, task_ids: set[int]) -> None:
    if not isinstance(value, list) or len(value) != 10:
        raise ContractError("layers must contain exactly 10 entries")
    seen: list[int] = []
    expected_layer_ids = list("ABCDEFGHIJ")
    for index, row in enumerate(value):
        if not isinstance(row, Mapping) or set(row) != {"id", "name", "tasks"}:
            raise ContractError("layer schema is invalid")
        if row["id"] != expected_layer_ids[index]:
            raise ContractError("layer ids must be A through J in order")
        _nonempty_string(row["name"], f"layer {row['id']} name")
        tasks = row["tasks"]
        if not isinstance(tasks, list) or len(tasks) != 4:
            raise ContractError(f"layer {row['id']} must own exactly four tasks")
        if any(isinstance(item, bool) or not isinstance(item, int) for item in tasks):
            raise ContractError(f"layer {row['id']} task ids must be integers")
        seen.extend(tasks)
    if set(seen) != task_ids or len(seen) != len(set(seen)):
        raise ContractError("layers must cover every task exactly once")


def validate_plan(value: Mapping[str, Any]) -> dict[str, Any]:
    if set(value) != PLAN_KEYS or value.get("schema") != 1:
        raise ContractError("plan-lock schema is invalid")
    plan_version = _nonempty_string(value["plan_version"], "plan_version")
    constitution_version = _nonempty_string(
        value["constitution_version"], "constitution_version"
    )
    baseline = _validate_baseline(value["baseline"])
    if value["checkpoints"] != [0, 25, 50, 75, 100]:
        raise ContractError("checkpoints must be exactly 0, 25, 50, 75, 100")
    tasks = _validate_tasks(value["tasks"])
    _validate_layers(value["layers"], set(tasks))
    for field in (
        "target_product",
        "target_repository",
        "incubation_branch",
        "change_rule",
    ):
        _nonempty_string(value[field], field)
    for field in ("provider_posture", "upstream_pins"):
        item = value[field]
        if not isinstance(item, dict) or not item:
            raise ContractError(f"{field} must be a non-empty object")
    return {
        "plan_version": plan_version,
        "constitution_version": constitution_version,
        "baseline": baseline,
        "task_ids": set(tasks),
    }


def _checkpoint_percent_from_name(path: Path) -> int:
    match = CHECKPOINT_NAME_RE.fullmatch(path.name)
    if match is None:
        raise ContractError(f"unexpected continuity JSON file: {path.name}")
    return int(match.group(1))


def _checkpoint_files(root: Path) -> list[Path]:
    continuity = root / CONTINUITY_DIR
    try:
        files = sorted(path for path in continuity.glob("checkpoint-*.json") if path.is_file())
    except OSError as exc:
        raise ContractError(f"cannot enumerate continuity checkpoints: {exc}") from exc
    if not files:
        raise ContractError("at least one continuity checkpoint is required")
    return files


def _validate_checkpoint(
    root: Path,
    path: Path,
    percent: int,
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        capsule = checkpoint_core.validate_capsule(_read_object(path))
    except checkpoint_core.CapsuleError as exc:
        raise ContractError(f"invalid checkpoint {path.name}: {exc}") from exc
    if capsule["checkpoint_percent"] != percent:
        raise ContractError(f"checkpoint filename and payload disagree: {path.name}")
    if capsule["baseline_sha"] != plan["baseline"]["sha"]:
        raise ContractError(f"checkpoint baseline drift: {path.name}")
    if capsule["plan_version"] != plan["plan_version"]:
        raise ContractError(f"checkpoint plan version drift: {path.name}")
    if capsule["constitution_version"] != plan["constitution_version"]:
        raise ContractError(f"checkpoint constitution drift: {path.name}")
    completed = set(capsule["completed_tasks"])
    if not completed <= plan["task_ids"]:
        raise ContractError(f"checkpoint contains unknown task ids: {path.name}")
    if not (root / capsule["active_spec"]).is_file():
        raise ContractError(f"checkpoint active spec does not exist: {path.name}")
    return capsule


def validate_checkpoints(root: Path, plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    previous_completed: set[int] = set()
    previous_percent = -1
    for path in _checkpoint_files(root):
        percent = _checkpoint_percent_from_name(path)
        if percent <= previous_percent:
            raise ContractError("checkpoint percentages must be strictly increasing")
        capsule = _validate_checkpoint(root, path, percent, plan)
        completed = set(capsule["completed_tasks"])
        if not previous_completed <= completed:
            raise ContractError("completed tasks must be monotonic across checkpoints")
        validated.append(capsule)
        previous_completed = completed
        previous_percent = percent
    return validated


def check(root: Path = ROOT) -> dict[str, Any]:
    resolved = root.resolve()
    plan = validate_plan(_read_object(resolved / PLAN_PATH))
    checkpoints = validate_checkpoints(resolved, plan)
    latest = checkpoints[-1]
    return {
        "status": "valid",
        "plan_version": plan["plan_version"],
        "constitution_version": plan["constitution_version"],
        "checkpoint_count": len(checkpoints),
        "latest_checkpoint_percent": latest["checkpoint_percent"],
        "latest_digest": latest["digest"],
        "completed_task_count": len(latest["completed_tasks"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate the Pusula planning contract")
    arguments = parser.parse_args(argv)
    if not arguments.check:
        parser.error("--check is required")
    try:
        print(json.dumps(check(), sort_keys=True))
    except ContractError as exc:
        print(f"PUSULA CONTRACT INVALID: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
