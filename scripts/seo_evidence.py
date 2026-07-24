"""Verify native SEO artifacts and immutable execution attestations."""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "registry" / "seo-policy.json"


def _policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _digest(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def command_plans(profile: str) -> list[dict[str, Any]]:
    policy = _policy()
    thresholds = policy["profiles"][profile]
    return [
        {
            "tool": tool,
            "identity": dict(policy["tools"][tool]["identity"]),
            "source_commit": policy["tools"][tool]["source_commit"],
            "acquisition": dict(policy["tools"][tool]["acquisition"]),
            "verification": {
                "verify_before_observation": True,
                "artifact_hash": "sha256",
                "network_during_audit": False,
            },
            "execute": False,
            "runtime": policy["tools"][tool]["runtime"],
            "outputs": list(policy["tools"][tool]["outputs"]),
            **({"thresholds": thresholds} if tool == "lighthouse-ci" else {}),
        }
        for tool in ("lighthouse-ci", "lychee")
    ]


def command_plan_digest(plans: list[dict[str, Any]]) -> str:
    return _digest(plans)


def _safe_artifact(root: pathlib.Path, relative: Any) -> pathlib.Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError("artifact path must be project-relative")
    pure = pathlib.PurePosixPath(relative.replace("\\", "/"))
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError("artifact path escapes project")
    path = root.joinpath(*pure.parts)
    if path.is_symlink() or not path.is_file():
        raise ValueError("artifact must be a regular non-symlink file")
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("artifact path escapes project") from error
    if path.stat().st_size > _policy()["limits"]["max_file_bytes"]:
        raise ValueError("artifact exceeds file size limit")
    return path


def _sha256(path: pathlib.Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _artifact(
    root: pathlib.Path,
    row: Any,
    plan: dict[str, Any],
) -> tuple[pathlib.Path | None, list[str]]:
    errors: list[str] = []
    if not isinstance(row, dict):
        return None, ["native artifact record must be an object"]
    if row.get("tool_identity") != plan["identity"]:
        errors.append("native artifact tool identity does not match")
    if row.get("exit_code") != 0:
        errors.append("native tool exit code must be zero")
    try:
        artifact = _safe_artifact(root, row.get("path"))
        executable = _safe_artifact(root, row.get("executable_path"))
    except ValueError as error:
        return None, [*errors, str(error)]
    if row.get("sha256") != _sha256(artifact):
        errors.append("native artifact SHA256 does not match")
    if row.get("executable_sha256") != _sha256(executable):
        errors.append("installed executable SHA256 does not match")
    return artifact, errors


def parse_lighthouse(
    content: bytes, expected_url: str
) -> tuple[dict[str, float], list[str]]:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return {}, ["Lighthouse native JSON is invalid"]
    categories = value.get("categories") if isinstance(value, dict) else None
    required = {"accessibility", "best-practices", "performance", "seo"}
    if not isinstance(value, dict) or value.get("finalUrl") != expected_url:
        return {}, ["Lighthouse final URL does not match expected URL"]
    if not isinstance(categories, dict) or not required <= set(categories):
        return {}, ["Lighthouse native categories are incomplete"]
    metrics = {
        name: categories[name].get("score")
        for name in required
        if isinstance(categories[name], dict)
    }
    if set(metrics) != required or any(
        not isinstance(score, (int, float))
        or isinstance(score, bool)
        or not 0 <= score <= 1
        for score in metrics.values()
    ):
        return {}, ["Lighthouse native scores are invalid"]
    return metrics, []


def parse_lychee(
    content: bytes, expected_url: str
) -> tuple[list[str], int, list[str]]:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return [], 0, ["Lychee native JSON is invalid"]
    if not isinstance(value, list) or not value:
        return [], 0, ["Lychee native result must contain links"]
    broken: list[str] = []
    expected = urlsplit(expected_url)
    for row in value:
        if not isinstance(row, dict) or not isinstance(row.get("url"), str):
            return [], 0, ["Lychee native result row is invalid"]
        observed = urlsplit(row["url"])
        base_path = expected.path.rstrip("/") + "/"
        if (
            observed.scheme != expected.scheme
            or observed.hostname != expected.hostname
            or observed.port != expected.port
            or not (
                observed.path == expected.path.rstrip("/")
                or observed.path.startswith(base_path)
            )
        ):
            return [], 0, ["Lychee URL does not match expected URL"]
        if row.get("status") != "OK":
            broken.append(row["url"])
    return broken, len(value), []


def _failed_threshold(metrics: dict[str, float], profile: str) -> bool:
    return any(
        rule["required"] and metrics[metric] < rule["minimum"]
        for metric, rule in _policy()["profiles"][profile].items()
    )


def native_bytes_verdict(
    lighthouse: bytes,
    lychee: bytes,
    expected_url: str,
    profile: str,
) -> tuple[str, list[str]]:
    metrics, lighthouse_errors = parse_lighthouse(lighthouse, expected_url)
    broken, _checked, lychee_errors = parse_lychee(lychee, expected_url)
    errors = [*lighthouse_errors, *lychee_errors]
    if errors:
        return "INVALID", errors
    return (
        "FAIL" if broken or _failed_threshold(metrics, profile) else "PASS",
        [],
    )


def _binding_errors(
    evidence: dict[str, Any],
    project: str,
    digest: str,
    profile: str,
    expected_url: str | None,
    plan_digest: str,
) -> list[str]:
    expected = (
        ("project", project, "evidence project does not match"),
        ("source_digest", digest, "evidence source_digest does not match"),
        ("profile", profile, "evidence profile does not match"),
        ("expected_url", expected_url, "evidence expected URL does not match"),
        (
            "command_plan_digest",
            plan_digest,
            "command plan digest does not match",
        ),
    )
    return [
        message for key, value, message in expected if evidence.get(key) != value
    ]


def _native_artifacts(
    root: pathlib.Path,
    artifacts: Any,
    plans: list[dict[str, Any]],
) -> tuple[pathlib.Path | None, pathlib.Path | None, list[str]]:
    if not isinstance(artifacts, dict):
        return None, None, ["native artifacts must be an object"]
    plan_by_tool = {row["tool"]: row for row in plans}
    lighthouse_path, lighthouse_errors = _artifact(
        root, artifacts.get("lighthouse-ci"), plan_by_tool["lighthouse-ci"]
    )
    lychee_path, lychee_errors = _artifact(
        root, artifacts.get("lychee"), plan_by_tool["lychee"]
    )
    return lighthouse_path, lychee_path, [
        *lighthouse_errors,
        *lychee_errors,
    ]


def evidence_verdict(
    evidence: Any,
    root: pathlib.Path,
    project: str,
    digest: str,
    profile: str,
    expected_url: str | None,
    plans: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    if evidence is None:
        return "NOT_OBSERVED", ["required native SEO artifacts are missing"]
    if not isinstance(evidence, dict) or evidence.get("schema_version") != 2:
        return "INVALID", ["native evidence schema_version must be 2"]
    plan_digest = command_plan_digest(plans)
    errors = _binding_errors(
        evidence, project, digest, profile, expected_url, plan_digest
    )
    lighthouse_path, lychee_path, artifact_errors = _native_artifacts(
        root, evidence.get("artifacts"), plans
    )
    errors.extend(artifact_errors)
    if errors or lighthouse_path is None or lychee_path is None:
        return "INVALID", errors
    assert expected_url is not None
    verdict, native_errors = native_bytes_verdict(
        lighthouse_path.read_bytes(),
        lychee_path.read_bytes(),
        expected_url,
        profile,
    )
    if verdict == "PASS":
        return "OBSERVED_UNVERIFIED", []
    return verdict, native_errors


def search_console_status(config: Any) -> dict[str, Any]:
    requirements = _policy()["search_console"]["requires"]
    if config is None or config == {"enabled": False}:
        return {"enabled": False, "status": "DISABLED", "requires": requirements}
    valid = (
        isinstance(config, dict)
        and config.get("enabled") is True
        and isinstance(config.get("account"), str)
        and bool(config["account"].strip())
        and isinstance(config.get("property"), str)
        and bool(config["property"].strip())
        and config.get("auth") == "provider-managed"
        and isinstance(config.get("capability"), dict)
    )
    return {
        "enabled": isinstance(config, dict) and config.get("enabled") is True,
        "status": "CONFIGURED_UNVERIFIED" if valid else "BLOCKED",
        "requires": requirements,
    }
