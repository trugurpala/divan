"""Authenticated GitHub readback for authoritative SEO observations."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import subprocess
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from seo_evidence import native_bytes_verdict

Runner = Callable[[list[str]], subprocess.CompletedProcess[Any]]
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
COMMIT = re.compile(r"[0-9a-f]{40}")
WORKFLOW_PATH = ".github/workflows/divan-seo.yml"
ARTIFACT_NAME = "divan-seo-evidence"


@dataclass(frozen=True)
class _VerifiedObservation:
    """Process-local authority created only after authenticated provider readback."""

    head_sha: str
    artifact_id: int
    verdict: str


def _run(runner: Runner, endpoint: str) -> Any:
    command = ["gh", "api", endpoint]
    completed = runner(command)
    if completed.returncode != 0:
        raise ValueError(f"GitHub readback failed: {endpoint}")
    return completed.stdout


def _json(runner: Runner, endpoint: str) -> dict[str, Any]:
    output = _run(runner, endpoint)
    if isinstance(output, bytes):
        try:
            output = output.decode("utf-8")
        except UnicodeError as error:
            raise ValueError("GitHub JSON readback was not UTF-8") from error
    if not isinstance(output, str):
        raise ValueError("GitHub JSON readback was not text")
    try:
        value = json.loads(output)
    except json.JSONDecodeError as error:
        raise ValueError("GitHub JSON readback is invalid") from error
    if not isinstance(value, dict):
        raise ValueError("GitHub JSON readback must be an object")
    return value


def _archive_files(content: bytes) -> dict[str, bytes]:
    if len(content) > 4 * 1024 * 1024:
        raise ValueError("GitHub artifact archive is too large")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as bundle:
            if len(bundle.infolist()) != 3:
                raise ValueError("GitHub artifact file set is invalid")
            if any(
                item.is_dir()
                or item.file_size > 1024 * 1024
                or "/" in item.filename
                or "\\" in item.filename
                for item in bundle.infolist()
            ):
                raise ValueError("GitHub artifact member is unsafe")
            files = {
                item.filename: bundle.read(item)
                for item in bundle.infolist()
            }
    except zipfile.BadZipFile as error:
        raise ValueError("GitHub artifact is not a ZIP archive") from error
    if set(files) != {"lighthouse.json", "lychee.json", "manifest.json"}:
        raise ValueError("GitHub artifact file set is invalid")
    return files


def _manifest(content: bytes, expected: dict[str, Any]) -> None:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("GitHub artifact manifest is invalid") from error
    if not isinstance(value, dict) or value != expected:
        raise ValueError("GitHub artifact manifest binding does not match")


def _validate_run(
    run: dict[str, Any],
    run_id: str,
    run_attempt: int,
    workflow_commit: str,
) -> None:
    expected = {
        "id": int(run_id),
        "run_attempt": run_attempt,
        "head_sha": workflow_commit,
        "path": WORKFLOW_PATH,
        "status": "completed",
        "conclusion": "success",
    }
    if any(run.get(key) != value for key, value in expected.items()):
        raise ValueError("GitHub workflow run readback does not match")


def _select_artifact(
    listing: dict[str, Any],
    run_id: str,
    workflow_commit: str,
) -> tuple[int, str]:
    rows = listing.get("artifacts")
    if not isinstance(rows, list):
        raise ValueError("GitHub SEO artifact readback is invalid")
    matches = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("name") == ARTIFACT_NAME
        and row.get("expired") is False
    ]
    if len(matches) != 1:
        raise ValueError("GitHub SEO artifact readback is ambiguous")
    artifact = matches[0]
    workflow_run = artifact.get("workflow_run")
    artifact_id = artifact.get("id")
    digest = artifact.get("digest")
    valid = (
        isinstance(artifact_id, int)
        and isinstance(workflow_run, dict)
        and workflow_run.get("id") == int(run_id)
        and workflow_run.get("head_sha") == workflow_commit
        and isinstance(digest, str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
    )
    if not valid:
        raise ValueError("GitHub SEO artifact metadata does not match")
    assert isinstance(artifact_id, int) and isinstance(digest, str)
    return artifact_id, digest


def verify_github_observation(
    *,
    runner: Runner,
    repository: str,
    run_id: str,
    run_attempt: int,
    workflow_commit: str,
    source_identity: dict[str, str],
    profile: str,
    expected_url: str,
    command_plan_digest: str,
    expected_workflow: bytes,
) -> _VerifiedObservation:
    """Return non-serializable authority from five fixed GitHub API readbacks."""
    if not REPOSITORY.fullmatch(repository):
        raise ValueError("canonical repository is invalid")
    if not run_id.isdigit() or run_attempt < 1 or not COMMIT.fullmatch(workflow_commit):
        raise ValueError("GitHub run identity is invalid")
    repo = _json(runner, f"repos/{repository}")
    if repo.get("full_name") != repository:
        raise ValueError("canonical repository readback does not match")
    run = _json(
        runner,
        f"repos/{repository}/actions/runs/{run_id}/attempts/{run_attempt}",
    )
    _validate_run(run, run_id, run_attempt, workflow_commit)
    workflow = _json(
        runner,
        f"repos/{repository}/contents/{WORKFLOW_PATH}?ref={workflow_commit}",
    )
    try:
        provider_workflow = base64.b64decode(
            workflow.get("content", ""), validate=True
        )
    except (TypeError, ValueError) as error:
        raise ValueError("immutable workflow content readback is invalid") from error
    if (
        not COMMIT.fullmatch(str(workflow.get("sha", "")))
        or workflow.get("encoding") != "base64"
        or provider_workflow != expected_workflow
    ):
        raise ValueError("immutable workflow content readback is invalid")
    commit = _json(
        runner, f"repos/{repository}/git/commits/{workflow_commit}"
    )
    tree = commit.get("tree")
    if (
        commit.get("sha") != workflow_commit
        or not isinstance(tree, dict)
        or tree.get("sha") != source_identity["tree"]
        or source_identity.get("commit") != workflow_commit
    ):
        raise ValueError("GitHub source identity readback does not match")
    listing = _json(
        runner, f"repos/{repository}/actions/runs/{run_id}/artifacts"
    )
    artifact_id, digest = _select_artifact(
        listing, run_id, workflow_commit
    )
    archive = _run(
        runner, f"repos/{repository}/actions/artifacts/{artifact_id}/zip"
    )
    if not isinstance(archive, bytes):
        raise ValueError("GitHub artifact download was not binary")
    if f"sha256:{hashlib.sha256(archive).hexdigest()}" != digest:
        raise ValueError("GitHub artifact digest does not match")
    files = _archive_files(archive)
    _manifest(
        files["manifest.json"],
        {
            "schema_version": 1,
            "repository": repository,
            "run_id": run_id,
            "run_attempt": run_attempt,
            "head_sha": workflow_commit,
            "workflow_digest": (
                "sha256:" + hashlib.sha256(expected_workflow).hexdigest()
            ),
            "source_identity": source_identity,
            "profile": profile,
            "expected_url": expected_url,
            "command_plan_digest": command_plan_digest,
        },
    )
    verdict, errors = native_bytes_verdict(
        files["lighthouse.json"], files["lychee.json"], expected_url, profile
    )
    if errors:
        raise ValueError("; ".join(errors))
    return _VerifiedObservation(workflow_commit, artifact_id, verdict)
