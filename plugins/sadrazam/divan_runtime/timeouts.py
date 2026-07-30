"""Evidence-backed, finite timeout decisions for Divan-owned commands."""

from __future__ import annotations

import json
import math
import pathlib
from dataclasses import asdict, dataclass
from typing import Any, Mapping

SAFE_FALLBACK_SECONDS = 300
DATA_DIRECTORY = pathlib.Path(__file__).resolve().parent / "data"
CLASS_KEYS = {
    "default_seconds",
    "maximum_seconds",
    "minimum_seconds",
    "workflows",
}


@dataclass(frozen=True)
class TimeoutDecision:
    command_class: str
    configured_seconds: int
    source: str
    sample_count: int
    percentile_seconds: int | None
    minimum_seconds: int
    maximum_seconds: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_json(path: pathlib.Path | str) -> dict[str, Any]:
    try:
        value = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"timeout contract cannot be read: {error}") from error
    if not isinstance(value, dict):
        raise ValueError("timeout contract root must be an object")
    return value


def _positive_integer(value: object, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def validate_policy(value: Mapping[str, Any]) -> None:
    expected = {
        "schema_version",
        "minimum_trusted_samples",
        "percentile",
        "safety_margin",
        "trusted",
        "classes",
    }
    if set(value) != expected or value.get("schema_version") != 1:
        raise ValueError("timeout policy schema is invalid")
    _positive_integer(value["minimum_trusted_samples"], "minimum samples")
    percentile = _positive_integer(value["percentile"], "percentile")
    if percentile > 100:
        raise ValueError("percentile must not exceed 100")
    margin = value["safety_margin"]
    if not isinstance(margin, Mapping) or set(margin) != {
        "numerator",
        "denominator",
    }:
        raise ValueError("timeout safety margin is invalid")
    _positive_integer(margin["numerator"], "margin numerator")
    _positive_integer(margin["denominator"], "margin denominator")
    trusted = value["trusted"]
    if (
        not isinstance(trusted, Mapping)
        or set(trusted) != {"repository", "branch", "events"}
        or not isinstance(trusted["repository"], str)
        or not isinstance(trusted["branch"], str)
        or not isinstance(trusted["events"], list)
        or not trusted["events"]
        or any(not isinstance(item, str) or not item for item in trusted["events"])
    ):
        raise ValueError("trusted benchmark source is invalid")
    classes = value["classes"]
    if not isinstance(classes, Mapping) or not classes:
        raise ValueError("timeout classes must be a non-empty object")
    for name, row in classes.items():
        if not isinstance(name, str) or not isinstance(row, Mapping):
            raise ValueError("timeout class is invalid")
        if set(row) != CLASS_KEYS:
            raise ValueError(f"timeout class schema is invalid: {name}")
        minimum = _positive_integer(row["minimum_seconds"], "minimum timeout")
        default = _positive_integer(row["default_seconds"], "default timeout")
        maximum = _positive_integer(row["maximum_seconds"], "maximum timeout")
        if not minimum <= default <= maximum:
            raise ValueError(f"timeout class bounds are invalid: {name}")
        workflows = row["workflows"]
        if (
            not isinstance(workflows, list)
            or len(workflows) != len(set(workflows))
            or any(not isinstance(item, str) or not item for item in workflows)
        ):
            raise ValueError(f"timeout workflows are invalid: {name}")


def _validate_benchmarks(value: Mapping[str, Any]) -> None:
    if (
        value.get("schema_version") != 1
        or not isinstance(value.get("source_repository"), str)
        or not isinstance(value.get("collected_at"), str)
        or not isinstance(value.get("runs"), list)
    ):
        raise ValueError("timeout benchmark schema is invalid")
    seen: set[int] = set()
    for row in value["runs"]:
        if not isinstance(row, Mapping):
            raise ValueError("timeout benchmark row is invalid")
        required = {
            "workflow",
            "run_id",
            "event",
            "conclusion",
            "branch",
            "duration_seconds",
        }
        if not required.issubset(row):
            raise ValueError("timeout benchmark row is incomplete")
        run_id = row["run_id"]
        if type(run_id) is not int or run_id <= 0 or run_id in seen:
            raise ValueError("timeout benchmark run id is invalid")
        seen.add(run_id)
        for key in ("workflow", "event", "conclusion", "branch"):
            if not isinstance(row[key], str) or not row[key]:
                raise ValueError(f"timeout benchmark {key} is invalid")
        _positive_integer(row["duration_seconds"], "benchmark duration")


def _fallback(command_class: str, source: str) -> TimeoutDecision:
    return TimeoutDecision(
        command_class=command_class,
        configured_seconds=SAFE_FALLBACK_SECONDS,
        source=source,
        sample_count=0,
        percentile_seconds=None,
        minimum_seconds=1,
        maximum_seconds=SAFE_FALLBACK_SECONDS,
    )


def _trusted_samples(
    command_class: str,
    policy: Mapping[str, Any],
    benchmarks: Mapping[str, Any],
) -> list[int]:
    row = policy["classes"][command_class]
    trusted = policy["trusted"]
    workflows = set(row["workflows"])
    if benchmarks["source_repository"] != trusted["repository"]:
        return []
    events = set(trusted["events"])
    return sorted(
        run["duration_seconds"]
        for run in benchmarks["runs"]
        if run["workflow"] in workflows
        and run["event"] in events
        and run["conclusion"] == "success"
        and run["branch"] == trusted["branch"]
    )


def resolve(
    command_class: str,
    policy: Mapping[str, Any],
    benchmarks: Mapping[str, Any],
    *,
    override_seconds: int | None = None,
) -> TimeoutDecision:
    """Resolve one deterministic timeout without ever returning infinity."""
    try:
        validate_policy(policy)
        row = policy["classes"][command_class]
    except (KeyError, TypeError, ValueError):
        return _fallback(command_class, "safe-fallback")
    minimum = int(row["minimum_seconds"])
    maximum = int(row["maximum_seconds"])
    if override_seconds is not None:
        seconds = _positive_integer(override_seconds, "timeout override")
        if not minimum <= seconds <= maximum:
            raise ValueError("timeout override is outside class safety bounds")
        return TimeoutDecision(
            command_class,
            seconds,
            "override",
            0,
            None,
            minimum,
            maximum,
        )
    try:
        _validate_benchmarks(benchmarks)
        samples = _trusted_samples(command_class, policy, benchmarks)
    except (KeyError, TypeError, ValueError):
        return TimeoutDecision(
            command_class,
            int(row["default_seconds"]),
            "default-invalid-benchmark",
            0,
            None,
            minimum,
            maximum,
        )
    minimum_samples = int(policy["minimum_trusted_samples"])
    if len(samples) < minimum_samples:
        return TimeoutDecision(
            command_class,
            int(row["default_seconds"]),
            "default-insufficient-samples",
            len(samples),
            None,
            minimum,
            maximum,
        )
    rank = max(1, math.ceil(int(policy["percentile"]) * len(samples) / 100))
    percentile_seconds = samples[rank - 1]
    margin = policy["safety_margin"]
    configured = math.ceil(
        percentile_seconds * int(margin["numerator"]) / int(margin["denominator"])
    )
    configured = min(max(configured, minimum), maximum)
    return TimeoutDecision(
        command_class,
        configured,
        "benchmark",
        len(samples),
        percentile_seconds,
        minimum,
        maximum,
    )


def resolve_default(
    command_class: str,
    *,
    override_seconds: int | None = None,
    data_directory: pathlib.Path | str = DATA_DIRECTORY,
) -> TimeoutDecision:
    """Resolve from the offline policy and benchmark snapshot packaged with Divan."""
    directory = pathlib.Path(data_directory)
    try:
        policy = load_json(directory / "timeout-policy.json")
        benchmarks = load_json(directory / "timeout-benchmarks.json")
    except ValueError:
        return _fallback(command_class, "safe-fallback")
    return resolve(
        command_class,
        policy,
        benchmarks,
        override_seconds=override_seconds,
    )
