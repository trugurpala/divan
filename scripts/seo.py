#!/usr/bin/env python3
"""Bounded SEO inspection and externally observed evidence verification."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPANY = ROOT / "plugins" / "sadrazam" / "company"
POLICY_PATH = ROOT / "registry" / "seo-policy.json"
for module_path in (COMPANY, ROOT / "scripts"):
    if str(module_path) not in sys.path:
        sys.path.insert(0, str(module_path))

from engine import inspect_project, load_contracts  # noqa: E402
from project_os import render_plan_command, render_seo_workflow  # noqa: E402,F401
from seo_evidence import (  # noqa: E402
    command_plan_digest,
    command_plans,
    evidence_verdict,
    search_console_status,
)
from seo_evidence import native_bytes_verdict as native_bytes_verdict  # noqa: E402,F401
from seo_provider import verify_github_observation  # noqa: E402
from seo_static import absolute_http_url, static_checks  # noqa: E402

IGNORED = {
    ".divan",
    ".git",
    ".next",
    ".nuxt",
    ".svelte-kit",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
}
WEB_FRAMEWORKS = {"astro", "nextjs", "nuxt", "svelte", "sveltekit", "vite", "vue"}


def load_policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _contained_root(project: pathlib.Path) -> pathlib.Path:
    supplied = project.expanduser().absolute()
    if supplied.is_symlink():
        raise ValueError("project root cannot be a symlink")
    try:
        root = supplied.resolve(strict=True)
    except OSError as error:
        raise ValueError("project must be an existing directory") from error
    if not root.is_dir():
        raise ValueError("project must be an existing directory")
    return root


def _directory_entries(
    directory: pathlib.Path, limits: dict[str, int]
) -> list[pathlib.Path]:
    entries = sorted(directory.iterdir(), key=lambda row: row.name.casefold())
    if len(entries) > limits["max_entries_per_directory"]:
        raise ValueError("project directory entry limit exceeded")
    return entries


def _validated_child(
    root: pathlib.Path,
    child: pathlib.Path,
    limits: dict[str, int],
) -> pathlib.Path | None:
    if child.name in IGNORED:
        return None
    if child.is_symlink():
        raise ValueError("project scan encountered a symlink")
    relative = child.relative_to(root)
    if len(relative.parts) > limits["max_depth"]:
        raise ValueError("project traversal depth limit exceeded")
    resolved = child.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("project path escapes the root") from error
    return child


def _append_file(
    child: pathlib.Path,
    files: list[pathlib.Path],
    limits: dict[str, int],
) -> None:
    if not child.is_file():
        raise ValueError("project scan encountered a non-regular file")
    if child.stat().st_size > limits["max_file_bytes"]:
        raise ValueError("project file size limit exceeded")
    files.append(child)
    if len(files) > limits["max_files"]:
        raise ValueError("project file limit exceeded")


def _scan(root: pathlib.Path) -> list[pathlib.Path]:
    limits = load_policy()["limits"]
    files: list[pathlib.Path] = []
    pending = [root]
    directories = 0
    while pending:
        directory = pending.pop(0)
        directories += 1
        if directories > limits["max_directories"]:
            raise ValueError("project directory limit exceeded")
        for raw_child in _directory_entries(directory, limits):
            child = _validated_child(root, raw_child, limits)
            if child is None:
                continue
            if child.is_dir():
                pending.append(child)
            else:
                _append_file(child, files, limits)
    return files


def _project_digest(root: pathlib.Path, files: list[pathlib.Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda row: row.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return f"sha256:{digest.hexdigest()}"


def _package_json(files: list[pathlib.Path]) -> list[dict[str, Any]]:
    packages: list[dict[str, Any]] = []
    for path in files:
        if path.name != "package.json":
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            packages.append(value)
    return packages


def _source_entry(files: list[pathlib.Path], root: pathlib.Path) -> bool:
    paths = {path.relative_to(root).as_posix() for path in files}
    web_suffixes = {".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".astro"}
    return any(
        path.startswith(("app/", "pages/", "src/pages/"))
        and pathlib.PurePosixPath(path).suffix in web_suffixes
        for path in paths
    )


def _has_web_entry(
    root: pathlib.Path,
    files: list[pathlib.Path],
    inspection: dict[str, Any],
) -> bool:
    if any(path.suffix.casefold() in {".html", ".htm"} for path in files):
        return True
    web_framework = bool(set(inspection["frameworks"]) & WEB_FRAMEWORKS)
    if not web_framework:
        return False
    if _source_entry(files, root):
        return True
    return any(
        isinstance(package.get("scripts"), dict)
        and {"build", "dev", "serve"} & set(package["scripts"])
        for package in _package_json(files)
    )


def _static_status(applicable: bool, checks: list[dict[str, str]]) -> str:
    if not applicable:
        return "NOT_APPLICABLE"
    if any(row["status"] == "NOT_OBSERVED" for row in checks):
        return "NOT_OBSERVED"
    if all(row["status"] == "PASS" for row in checks):
        return "PASS"
    return "FAIL"


def _overall_status(
    applicable: bool,
    static_status: str,
    evidence_status: str,
    search_status: str,
) -> str:
    if not applicable:
        return "NOT_APPLICABLE"
    if static_status == "FAIL" or evidence_status == "FAIL":
        return "FAIL"
    if (
        static_status != "PASS"
        or evidence_status != "PASS"
        or search_status not in {"DISABLED", "READY_READ_ONLY"}
    ):
        return "BLOCKED"
    return "PASS"


def _managed_expected_url(root: pathlib.Path) -> str | None:
    path = root / ".divan" / "seo-tools.json"
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError("managed SEO config must be a regular file")
    if path.stat().st_size > load_policy()["limits"]["max_file_bytes"]:
        raise ValueError("managed SEO config exceeds the file size limit")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("managed SEO config must be valid UTF-8 JSON") from error
    expected = value.get("expected_url") if isinstance(value, dict) else None
    if not isinstance(expected, str) or not absolute_http_url(expected):
        raise ValueError("managed expected_url is invalid")
    return expected


def audit_project(
    project: pathlib.Path,
    profile: str = "standard",
    *,
    evidence: Any = None,
    search_console: Any = None,
    expected_url: str | None = None,
) -> dict[str, Any]:
    policy = load_policy()
    if profile not in policy["profiles"]:
        raise ValueError(f"unknown profile: {profile}")
    root = _contained_root(pathlib.Path(project))
    managed_url = _managed_expected_url(root)
    if managed_url is not None:
        if expected_url is not None and expected_url != managed_url:
            raise ValueError("CLI expected_url does not match managed expected_url")
        expected_url = managed_url
    files = _scan(root)
    inspection = inspect_project(root, load_contracts(COMPANY))
    applicable = _has_web_entry(root, files, inspection)
    project_types = [
        value
        for value in inspection["project_types"]
        if value != "public-web" or applicable
    ]
    if applicable and "public-web" not in project_types:
        project_types.append("public-web")
    project_types.sort()
    digest = _project_digest(root, files)
    if expected_url is not None and not absolute_http_url(expected_url):
        raise ValueError("expected_url must be an absolute HTTP(S) URL")
    checks = static_checks(root, files, expected_url) if applicable else []
    static_status = _static_status(applicable, checks)
    plans = command_plans(profile) if applicable else []
    plan_digest = command_plan_digest(plans) if applicable else None
    evidence_status, evidence_errors = (
        evidence_verdict(
            evidence,
            root,
            inspection["project"],
            digest,
            profile,
            expected_url,
            plans,
        )
        if applicable
        else ("NOT_APPLICABLE", [])
    )
    search_status = search_console_status(search_console)
    status = _overall_status(
        applicable, static_status, evidence_status, search_status["status"]
    )
    return {
        "schema_version": 2,
        "profile": profile,
        "project": inspection["project"],
        "project_types": project_types,
        "project_digest": digest,
        "applicable": applicable,
        "status": status,
        "static_status": static_status,
        "evidence_status": evidence_status,
        "evidence_errors": evidence_errors,
        "checks": checks,
        "thresholds": policy["profiles"][profile] if applicable else {},
        "command_plans": plans,
        "command_plan_digest": plan_digest,
        "expected_url": expected_url,
        "search_console": search_status,
    }


def _subprocess_runner(command: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, capture_output=True, check=False)


def _git_output(root: pathlib.Path, arguments: list[str]) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError("local Git source identity is unavailable")
    return completed.stdout.strip()


def _repository_from_origin(value: str) -> str:
    normalized = value.strip().removesuffix(".git")
    if normalized.startswith("git@github.com:"):
        candidate = normalized.removeprefix("git@github.com:")
    elif normalized.startswith("https://github.com/"):
        candidate = normalized.removeprefix("https://github.com/")
    else:
        raise ValueError("local Git origin must be github.com")
    if candidate.count("/") != 1:
        raise ValueError("local Git origin is not a canonical repository")
    return candidate


def _local_source_identity(root: pathlib.Path) -> tuple[str, dict[str, str]]:
    if _git_output(root, ["status", "--porcelain"]):
        raise ValueError("local Git worktree must be clean")
    commit = _git_output(root, ["rev-parse", "HEAD"])
    tree = _git_output(root, ["rev-parse", "HEAD^{tree}"])
    repository = _repository_from_origin(
        _git_output(root, ["remote", "get-url", "origin"])
    )
    return repository, {"commit": commit, "tree": tree}


def verify_github(
    project: pathlib.Path,
    *,
    repository: str | None = None,
    run_id: str,
    run_attempt: int,
    workflow_commit: str,
    expected_url: str | None = None,
    profile: str = "standard",
    runner: Any = _subprocess_runner,
) -> dict[str, Any]:
    """Explicitly verify provider artifacts; local audit remains network-free."""
    report = audit_project(project, profile, expected_url=expected_url)
    if not report["applicable"] or report["static_status"] != "PASS":
        return report
    resolved_url = report["expected_url"]
    if not isinstance(resolved_url, str):
        raise ValueError("managed expected_url is required for live verification")
    root = pathlib.Path(project).resolve()
    canonical_repository, source_identity = _local_source_identity(root)
    if repository is not None and repository != canonical_repository:
        raise ValueError("CLI repository does not match local Git origin")
    repository = canonical_repository
    workflow = root / ".github" / "workflows" / "divan-seo.yml"
    if workflow.is_symlink() or not workflow.is_file():
        raise ValueError("managed Divan SEO workflow is required")
    canonical_workflow = render_seo_workflow(profile, resolved_url).encode("utf-8")
    if workflow.read_bytes() != canonical_workflow:
        raise ValueError("local Divan SEO workflow is not canonical")
    observation = verify_github_observation(
        runner=runner,
        repository=repository,
        run_id=run_id,
        run_attempt=run_attempt,
        workflow_commit=workflow_commit,
        source_identity=source_identity,
        profile=profile,
        expected_url=resolved_url,
        command_plan_digest=report["command_plan_digest"],
        expected_workflow=canonical_workflow,
    )
    report["evidence_status"] = observation.verdict
    report["status"] = "PASS" if observation.verdict == "PASS" else "FAIL"
    report["provider"] = {
        "name": "github",
        "verified": True,
        "run_id": run_id,
        "run_attempt": run_attempt,
    }
    return report


if __name__ == "__main__":
    from seo_cli import main

    sys.exit(main())
