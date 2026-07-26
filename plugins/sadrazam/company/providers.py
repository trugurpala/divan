#!/usr/bin/env python3
"""Read-only provider capabilities and live-verified release orchestration."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import ssl
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, TypeGuard
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    HTTPSHandler,
    Request,
    build_opener,
)

import goals
import project_os
import receipts


class ProviderCapabilityV1(dict[str, Any]):
    """Diagnostic schema-v1 capability object with five locked fields."""

    id: str
    available: bool
    operations: list[str]
    missing: list[str]
    evidence: list[str]

    def __init__(
        self,
        identifier: str,
        available: bool,
        operations: list[str],
        missing: list[str],
        evidence: list[str],
    ) -> None:
        super().__init__(
            id=identifier,
            available=available,
            operations=operations,
            missing=missing,
            evidence=evidence,
        )


PROVIDER_OPERATIONS = {
    "local": (
        "inspect",
        "plan",
        "impact",
        "init",
        "audit",
        "verify",
        "goal",
        "receipt",
        "release",
    ),
    "github": ("pr", "ci", "ruleset", "tag", "release", "live-readback"),
    "context7": ("official-docs",),
    "vercel": (
        "preview",
        "browser-verify",
        "staged-production",
        "promote",
        "live-readback",
    ),
}
RELEASE_OPERATIONS = {
    "github": PROVIDER_OPERATIONS["github"],
    "vercel": PROVIDER_OPERATIONS["vercel"],
}
SAFE_ENVIRONMENT_MARKERS = {
    "github": ("GITHUB_ACTIONS",),
    "context7": ("DIVAN_CONTEXT7_AVAILABLE",),
    "vercel": ("DIVAN_VERCEL_AVAILABLE",),
}
SAFE_EXECUTABLES = {"github": ("gh",), "vercel": ("vercel",)}
PROVIDER_PROOF_KEYS = {
    "schema_version",
    "goal_id",
    "project_identity",
    "provider",
    "operation",
    "source_commit",
    "resource_id",
    "resource_url",
    "sha256",
    "observed_status",
    "readback",
}
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}")
RESOURCE_PATTERN = re.compile(r"[A-Za-z0-9._:/-]{1,240}")
PROJECT_PATTERN = re.compile(
    r"[a-z0-9.-]+/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+"
)
VERCEL_PROJECT_ID_PATTERN = re.compile(r"prj_[A-Za-z0-9_]{1,128}")
VERCEL_ACCOUNT_ID_PATTERN = re.compile(r"[A-Za-z0-9_]{1,128}")
GIT_COMPONENT_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,99})")
SUCCESS_STATUSES = {
    "ACTIVE",
    "COMPLETED",
    "MERGED",
    "PASS",
    "PUBLISHED",
    "READY",
    "SUCCESS",
    "VERIFIED",
}
MUTABLE_RESOURCE_IDS = {"head", "latest", "main", "master", "preview", "production"}
PROJECT_STATE_FILES = {
    ".divan/PROJECT_RULES.md",
    ".divan/config.json",
    ".divan/waivers.json",
}
MAX_MANAGED_FILES = 128
MAX_MANAGED_FILE_BYTES = 1024 * 1024
MAX_MANAGED_TOTAL_BYTES = 8 * 1024 * 1024
Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class HTTPSObservation:
    """Transport-level observation made by a TLS-verifying HTTPS client."""

    status: int
    final_url: str
    request_id: str
    tls_verified: bool


HTTPSVerifier = Callable[[str], HTTPSObservation | None]


def _diagnostics(
    provider: str,
    environ: Mapping[str, str],
    which: Callable[[str], str | None],
) -> list[str]:
    evidence = [
        f"environment:{marker}"
        for marker in SAFE_ENVIRONMENT_MARKERS.get(provider, ())
        if environ.get(marker)
    ]
    for executable in SAFE_EXECUTABLES.get(provider, ()):
        try:
            present = which(executable) is not None
        except OSError:
            present = False
        if present:
            evidence.append(f"executable:{executable}")
    return evidence


def discover_capabilities(
    *,
    environ: Mapping[str, str] | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> list[ProviderCapabilityV1]:
    """Describe capabilities without granting authority from ambient signals."""
    environment = os.environ if environ is None else environ
    capabilities: list[ProviderCapabilityV1] = []
    for provider, required in PROVIDER_OPERATIONS.items():
        if provider == "local":
            operations, evidence = list(required), ["builtin:local"]
        else:
            operations = []
            evidence = _diagnostics(provider, environment, which)
        missing = [
            f"{provider}.{operation}"
            for operation in required
            if operation not in operations
        ]
        capabilities.append(
            ProviderCapabilityV1(
                provider,
                not missing,
                operations,
                missing,
                evidence,
            )
        )
    return capabilities


def _receipt_path(root: pathlib.Path, identifier: str) -> pathlib.Path:
    if goals.GOAL_ID_PATTERN.fullmatch(identifier) is None:
        raise ValueError("goal identifier must match goal-[0-9a-f]{12}")
    return root / ".divan" / "evidence" / identifier / "receipt.json"


def _valid_url(provider: str, value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        return False
    host = (parsed.hostname or "").casefold()
    if provider == "github":
        return host in {"github.com", "api.github.com"}
    return host == "vercel.com" or host.endswith(".vercel.app")


def _github_url_project(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlsplit(value)
    parts = [part for part in parsed.path.split("/") if part]
    host = (parsed.hostname or "").casefold()
    if host == "github.com" and len(parts) >= 2:
        owner, repository = parts[:2]
    elif host == "api.github.com" and len(parts) >= 3 and parts[0] == "repos":
        owner, repository = parts[1:3]
    else:
        return None
    return f"github.com/{owner}/{repository}".casefold()


def _immutable_resource_id(provider: str, operation: str, value: Any) -> bool:
    if not isinstance(value, str) or RESOURCE_PATTERN.fullmatch(value) is None:
        return False
    if value.casefold() in MUTABLE_RESOURCE_IDS:
        return False
    if provider == "github":
        if operation in {"pr", "ci", "ruleset"}:
            return value.isdecimal()
        if operation == "tag":
            return value.startswith("refs/tags/") and (
                value.removeprefix("refs/tags/").casefold()
                not in MUTABLE_RESOURCE_IDS
            )
        return "/" not in value
    if operation in {
        "preview",
        "staged-production",
        "promote",
        "live-readback",
    }:
        return value.startswith("dpl_")
    return operation == "browser-verify"


def _canonical_remote(value: str) -> str | None:
    candidate = value.strip()
    if candidate.startswith("git@") and ":" in candidate:
        host, path = candidate[4:].split(":", 1)
    else:
        parsed = urlsplit(candidate)
        if parsed.scheme not in {"https", "ssh"} or not parsed.hostname:
            return None
        host = parsed.hostname
        path = parsed.path.lstrip("/")
    path = path.removesuffix(".git").strip("/")
    identity = f"{host}/{path}".casefold()
    return identity if PROJECT_PATTERN.fullmatch(identity) else None


def _valid_project_state_file(path: pathlib.Path, relative: str) -> bool:
    try:
        size = path.stat().st_size
        if size > MAX_MANAGED_FILE_BYTES:
            return False
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    root = path.parents[1]
    if relative == ".divan/PROJECT_RULES.md":
        config, errors = project_os._load_config(root)
        if config is None or errors:
            return False
        expected = project_os._rules(str(config["locale"]))
        return content.replace("\r\n", "\n") == expected.replace("\r\n", "\n")
    if relative == ".divan/config.json":
        _, errors = project_os._load_config(root)
        return not errors
    _, errors = project_os._load_waivers(root)
    return not errors


def _managed_project_os_path(root: pathlib.Path, relative: str) -> bool:
    """Accept only bounded, regular Project OS state under the project root."""
    if (
        not relative
        or "\\" in relative
        or relative.startswith("/")
        or any(part in {"", ".", ".."} for part in relative.split("/"))
    ):
        return False
    parts = relative.split("/")
    allowed = relative in PROJECT_STATE_FILES
    if len(parts) == 4 and parts[:2] == [".divan", "specs"]:
        allowed = (
            goals.GOAL_ID_PATTERN.fullmatch(parts[2]) is not None
            and parts[3] in {"spec.md", "plan.md", "tasks.md"}
        )
    elif len(parts) == 4 and parts[:2] == [".divan", "evidence"]:
        goal_id, name = parts[2:]
        proof_names = {
            f"{operation}-{provider}.json"
            for provider, operations in RELEASE_OPERATIONS.items()
            for operation in operations
        }
        allowed = (
            goals.GOAL_ID_PATTERN.fullmatch(goal_id) is not None
            and (name == "receipt.json" or name in proof_names)
        )
    if not allowed:
        return False
    candidate = root.joinpath(*parts)
    current = root
    try:
        for part in parts:
            current /= part
            if current.is_symlink():
                return False
        resolved_root = root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
    except OSError:
        return False
    if not resolved.is_relative_to(resolved_root) or not candidate.is_file():
        return False
    if relative in PROJECT_STATE_FILES:
        return _valid_project_state_file(candidate, relative)
    try:
        return candidate.stat().st_size <= MAX_MANAGED_FILE_BYTES
    except OSError:
        return False


def _managed_status_is_safe(root: pathlib.Path, status: bytes) -> bool:
    entries = [entry for entry in status.split(b"\0") if entry]
    if len(entries) > MAX_MANAGED_FILES:
        return False
    total_size = 0
    for entry in entries:
        if len(entry) < 4 or entry[2:3] != b" ":
            return False
        state = entry[:2]
        if (
            b"R" in state
            or b"C" in state
            or b"U" in state
            or state in {b"DD", b"AA"}
        ):
            return False
        try:
            relative = entry[3:].decode("utf-8", errors="strict")
        except UnicodeError:
            return False
        if not _managed_project_os_path(root, relative):
            return False
        try:
            total_size += root.joinpath(*relative.split("/")).stat().st_size
        except OSError:
            return False
        if total_size > MAX_MANAGED_TOTAL_BYTES:
            return False
    return True


def _source_context(root: pathlib.Path) -> tuple[str, str] | None:
    try:
        status = subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
            ],
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
        source_commit = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            encoding="utf-8",
            errors="strict",
            stderr=subprocess.DEVNULL,
            timeout=15,
        ).strip()
        remote = subprocess.check_output(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            text=True,
            encoding="utf-8",
            errors="strict",
            stderr=subprocess.DEVNULL,
            timeout=15,
        ).strip()
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None
    project_identity = _canonical_remote(remote)
    if (
        not isinstance(status, bytes)
        or not _managed_status_is_safe(root, status)
        or SHA_PATTERN.fullmatch(source_commit) is None
    ):
        return None
    if project_identity is None:
        return None
    return project_identity, source_commit


def _load_proof(
    root: pathlib.Path,
    identifier: str,
    project_identity: str,
    source_commit: str,
    provider: str,
    operation: str,
    artifacts: Mapping[str, str],
) -> tuple[str, dict[str, Any]] | None:
    relative = f".divan/evidence/{identifier}/{operation}-{provider}.json"
    if relative not in artifacts:
        return None
    path = root.joinpath(*pathlib.PurePosixPath(relative).parts)
    try:
        proof = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(proof, dict) or set(proof) != PROVIDER_PROOF_KEYS:
        return None
    if (
        proof.get("schema_version") != 1
        or proof.get("goal_id") != identifier
        or proof.get("project_identity") != project_identity
        or proof.get("provider") != provider
        or proof.get("operation") != operation
        or proof.get("source_commit") != source_commit
        or not _immutable_resource_id(
            provider, operation, proof.get("resource_id")
        )
        or not _valid_url(provider, proof.get("resource_url"))
        or (
            provider == "github"
            and _github_url_project(proof.get("resource_url"))
            != project_identity.casefold()
        )
        or DIGEST_PATTERN.fullmatch(str(proof.get("sha256", ""))) is None
        or not isinstance(proof.get("observed_status"), str)
        or proof["observed_status"].upper() not in SUCCESS_STATUSES
        or not isinstance(proof.get("readback"), str)
        or not proof["readback"]
    ):
        return None
    return relative, proof


def _github_command(operation: str, proof: Mapping[str, Any]) -> list[str]:
    resource = str(proof["resource_id"])
    url = str(proof["resource_url"])
    if operation == "pr":
        return ["gh", "pr", "view", resource, "--json", "number,url,headRefOid,state"]
    if operation == "ci":
        return [
            "gh",
            "run",
            "view",
            resource,
            "--json",
            "databaseId,url,headSha,status,conclusion",
        ]
    if operation == "ruleset":
        parsed = urlsplit(url)
        parts = [part for part in parsed.path.split("/") if part]
        if (
            parsed.hostname != "github.com"
            or len(parts) != 4
            or parts[2] != "rules"
            or parts[3] != resource
        ):
            raise ValueError("GitHub ruleset URL does not match its immutable ID")
        return [
            "gh",
            "api",
            f"repos/{parts[0]}/{parts[1]}/rulesets/{resource}",
        ]
    if operation == "tag":
        return ["gh", "api", url]
    return [
        "gh",
        "release",
        "view",
        resource,
        "--json",
        "tagName,url,targetCommitish,isDraft",
    ]


def _verification_command(
    provider: str, operation: str, proof: Mapping[str, Any]
) -> list[str]:
    if provider == "github":
        return _github_command(operation, proof)
    if operation == "browser-verify":
        return ["vercel", "curl", str(proof["resource_url"])]
    resource = str(proof["resource_id"])
    if operation == "promote":
        return ["vercel", "api", f"/v2/deployments/{resource}/aliases"]
    return ["vercel", "api", f"/v13/deployments/{resource}"]


def _default_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=30,
        check=False,
    )


class _VercelRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self,
        request: Request,
        file_pointer: Any,
        code: int,
        message: str,
        headers: Any,
        new_url: str,
    ) -> Request | None:
        if not _valid_url("vercel", new_url):
            raise ValueError("HTTPS verification redirected outside Vercel")
        return super().redirect_request(
            request,
            file_pointer,
            code,
            message,
            headers,
            new_url,
        )


def _default_https_verifier(url: str) -> HTTPSObservation | None:
    if not _valid_url("vercel", url):
        return None
    opener = build_opener(
        HTTPSHandler(context=ssl.create_default_context()),
        _VercelRedirectHandler(),
    )
    request = Request(
        url,
        headers={
            "Range": "bytes=0-0",
            "User-Agent": "Divan-native-verifier/1",
        },
        method="GET",
    )
    try:
        with opener.open(request, timeout=15) as response:
            status = getattr(response, "status", None)
            final_url = response.geturl()
            request_id = response.headers.get("x-vercel-id")
            response.read(1)
    except (OSError, UnicodeError, ValueError, ssl.SSLError):
        return None
    if (
        type(status) is not int
        or not isinstance(final_url, str)
        or not _valid_url("vercel", final_url)
        or not isinstance(request_id, str)
        or RESOURCE_PATTERN.fullmatch(request_id) is None
    ):
        return None
    return HTTPSObservation(
        status=status,
        final_url=final_url,
        request_id=request_id,
        tls_verified=True,
    )


def _https_observation_json(observation: HTTPSObservation) -> str:
    return json.dumps(
        {
            "final_url": observation.final_url,
            "request_id": observation.request_id,
            "status": observation.status,
            "tls_verified": observation.tls_verified,
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def _github_live(
    operation: str,
    live: Mapping[str, Any],
) -> dict[str, Any] | None:
    if operation == "pr":
        state = live.get("state")
        status = state.upper() if isinstance(state, str) else state
        return {
            "source_commit": live.get("headRefOid"),
            "resource_id": str(live.get("number", "")),
            "resource_url": live.get("url"),
            "status": status,
            "readback": status,
        }
    if operation == "ci":
        conclusion = live.get("conclusion")
        if not isinstance(conclusion, str) or conclusion.upper() != "SUCCESS":
            return None
        status = conclusion.upper()
        return {
            "source_commit": live.get("headSha"),
            "resource_id": str(live.get("databaseId", "")),
            "resource_url": live.get("url"),
            "status": status,
            "readback": status,
        }
    if operation == "ruleset":
        links = live.get("_links")
        html = links.get("html") if isinstance(links, Mapping) else None
        status = str(live.get("enforcement", "")).upper()
        target = live.get("target")
        name = live.get("name")
        if (
            type(live.get("id")) is not int
            or not isinstance(html, Mapping)
            or not isinstance(target, str)
            or not isinstance(name, str)
        ):
            return None
        return {
            "resource_id": str(live["id"]),
            "resource_url": html.get("href"),
            "status": status,
            "readback": f"{target}:{name}",
        }
    if operation == "tag":
        target = live.get("object")
        if (
            not isinstance(live.get("ref"), str)
            or not isinstance(live.get("url"), str)
            or not isinstance(target, Mapping)
        ):
            return None
        return {
            "source_commit": target.get("sha"),
            "resource_id": live["ref"],
            "resource_url": live["url"],
            "status": "VERIFIED",
            "readback": target.get("type"),
        }
    if operation in {"release", "live-readback"}:
        status = "PUBLISHED" if live.get("isDraft") is False else "DRAFT"
        return {
            "source_commit": live.get("targetCommitish"),
            "resource_id": live.get("tagName"),
            "resource_url": live.get("url"),
            "status": status,
            "readback": status,
        }
    return None


def _vercel_git_provenance(
    live: Mapping[str, Any],
) -> tuple[str, int] | None:
    git_source = live.get("gitSource")
    if (
        not isinstance(git_source, Mapping)
        or git_source.get("type") != "github"
        or not _positive_integer(git_source.get("repoId"))
    ):
        return None
    sha = git_source.get("sha")
    commit_sha = git_source.get("commitSha")
    candidates = [item for item in (sha, commit_sha) if item is not None]
    if (
        not candidates
        or any(
            not isinstance(item, str)
            or SHA_PATTERN.fullmatch(item) is None
            for item in candidates
        )
        or any(item != candidates[0] for item in candidates[1:])
    ):
        return None
    return candidates[0], int(git_source["repoId"])


def _vercel_deployment_scope(
    live: Mapping[str, Any],
) -> tuple[str, str] | None:
    project_id = live.get("projectId")
    account_id = live.get("ownerId")
    if (
        not isinstance(project_id, str)
        or VERCEL_PROJECT_ID_PATTERN.fullmatch(project_id) is None
        or not isinstance(account_id, str)
        or VERCEL_ACCOUNT_ID_PATTERN.fullmatch(account_id) is None
    ):
        return None
    project = live.get("project")
    if (
        isinstance(project, Mapping)
        and "id" in project
        and project.get("id") != project_id
    ):
        return None
    team = live.get("team")
    if (
        isinstance(team, Mapping)
        and "id" in team
        and team.get("id") != account_id
    ):
        return None
    return project_id, account_id


def _positive_integer(value: Any) -> TypeGuard[int]:
    return type(value) is int and value > 0


def _vercel_project_identity(
    project: Any,
    expected_project_id: str,
    expected_account_id: str,
) -> tuple[str, int] | None:
    if (
        not isinstance(project, Mapping)
        or project.get("id") != expected_project_id
        or project.get("accountId") != expected_account_id
    ):
        return None
    link = project.get("link")
    if not isinstance(link, Mapping) or link.get("type") != "github":
        return None
    owner = link.get("org")
    repository = link.get("repo")
    if (
        not isinstance(owner, str)
        or GIT_COMPONENT_PATTERN.fullmatch(owner) is None
        or owner in {".", ".."}
        or not isinstance(repository, str)
        or GIT_COMPONENT_PATTERN.fullmatch(repository) is None
        or repository in {".", ".."}
        or not _positive_integer(link.get("repoId"))
        or not _positive_integer(link.get("repoOwnerId"))
    ):
        return None
    ambiguous_fields = {
        "owner",
        "slug",
        "projectNamespace",
        "projectUrl",
        "projectId",
    }
    if any(link.get(field) is not None for field in ambiguous_fields):
        return None
    identity = _canonical_remote(f"https://github.com/{owner}/{repository}")
    if identity is None:
        return None
    return identity, int(link["repoId"])


def _vercel_project_command(project_id: str, account_id: str) -> list[str]:
    path = f"/v9/projects/{project_id}"
    if account_id.startswith("team_"):
        path += f"?teamId={account_id}"
    return ["vercel", "api", path]


def _vercel_project_readback(
    runner: Runner,
    project_id: str,
    account_id: str,
) -> tuple[str, int] | None:
    try:
        completed = runner(_vercel_project_command(project_id, account_id))
    except (OSError, subprocess.SubprocessError, UnicodeError, ValueError):
        return None
    if completed.returncode != 0 or not isinstance(completed.stdout, str):
        return None
    try:
        project = json.loads(completed.stdout)
    except (json.JSONDecodeError, ValueError):
        return None
    return _vercel_project_identity(project, project_id, account_id)


def _vercel_deployment_url(live: Mapping[str, Any]) -> Any:
    url = live.get("url")
    if isinstance(url, str) and not url.startswith("https://"):
        url = f"https://{url}"
    return url


def _vercel_preview(live: Mapping[str, Any]) -> dict[str, Any] | None:
    if live.get("target") != "preview":
        return None
    scope = _vercel_deployment_scope(live)
    provenance = _vercel_git_provenance(live)
    if scope is None or provenance is None:
        return None
    return {
        "project_id": scope[0],
        "account_id": scope[1],
        "source_commit": provenance[0],
        "repository_id": provenance[1],
        "resource_id": str(live.get("uid") or live.get("id") or ""),
        "resource_url": _vercel_deployment_url(live),
        "status": live.get("readyState"),
        "readback": "target=preview",
    }


def _vercel_browser(live: HTTPSObservation) -> dict[str, Any] | None:
    if (
        type(live.status) is not int
        or not isinstance(live.request_id, str)
        or not isinstance(live.final_url, str)
        or live.tls_verified is not True
    ):
        return None
    return {
        "resource_id": live.request_id,
        "resource_url": live.final_url,
        "status": "PASS" if 200 <= live.status < 400 else "FAILED",
        "readback": (
            f"tls=verified;http={live.status};final={live.final_url}"
        ),
    }


def _vercel_staged(live: Mapping[str, Any]) -> dict[str, Any] | None:
    aliases = live.get("aliases")
    if live.get("target") != "production" or aliases != []:
        return None
    scope = _vercel_deployment_scope(live)
    provenance = _vercel_git_provenance(live)
    if scope is None or provenance is None:
        return None
    return {
        "project_id": scope[0],
        "account_id": scope[1],
        "source_commit": provenance[0],
        "repository_id": provenance[1],
        "resource_id": str(live.get("uid") or live.get("id") or ""),
        "resource_url": _vercel_deployment_url(live),
        "status": live.get("readyState"),
        "readback": "target=production;aliases=0",
    }


def _vercel_promotion(
    live: Any, proof: Mapping[str, Any]
) -> dict[str, Any] | None:
    if not isinstance(live, Mapping) or not isinstance(
        live.get("aliases"), list
    ):
        return None
    candidates = live["aliases"]
    expected_url = str(proof["resource_url"])
    expected_alias = urlsplit(expected_url).hostname
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        alias = candidate.get("alias")
        if alias != expected_alias:
            continue
        return {
            "resource_id": proof["resource_id"],
            "resource_url": expected_url,
            "status": "VERIFIED",
            "readback": f"alias={alias}",
        }
    return None


def _vercel_live_readback(
    live: Mapping[str, Any], proof: Mapping[str, Any]
) -> dict[str, Any] | None:
    aliases = live.get("aliases")
    expected_url = str(proof["resource_url"])
    expected_alias = urlsplit(expected_url).hostname
    if (
        live.get("target") != "production"
        or not isinstance(aliases, list)
        or expected_alias not in aliases
    ):
        return None
    scope = _vercel_deployment_scope(live)
    provenance = _vercel_git_provenance(live)
    if scope is None or provenance is None:
        return None
    return {
        "project_id": scope[0],
        "account_id": scope[1],
        "source_commit": provenance[0],
        "repository_id": provenance[1],
        "resource_id": str(live.get("uid") or live.get("id") or ""),
        "resource_url": expected_url,
        "status": live.get("readyState"),
        "readback": f"production-alias={expected_alias}",
    }


def _normalized_live(
    provider: str,
    operation: str,
    live: Any,
    proof: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    if provider == "github" and isinstance(live, Mapping):
        return _github_live(operation, live)
    if provider != "vercel":
        return None
    if operation == "browser-verify" and isinstance(live, HTTPSObservation):
        return _vercel_browser(live)
    if operation == "promote":
        return _vercel_promotion(live, proof)
    if not isinstance(live, Mapping):
        return None
    if operation == "preview":
        return _vercel_preview(live)
    if operation == "staged-production":
        return _vercel_staged(live)
    if operation == "live-readback":
        return _vercel_live_readback(live, proof)
    return None


def _live_result(
    provider: str,
    operation: str,
    proof: Mapping[str, Any],
    runner: Runner,
    https_verifier: HTTPSVerifier = _default_https_verifier,
) -> Mapping[str, Any] | None:
    if provider == "vercel" and operation == "browser-verify":
        try:
            live = https_verifier(str(proof["resource_url"]))
        except (OSError, UnicodeError, ValueError):
            return None
        if not isinstance(live, HTTPSObservation):
            return None
        raw = _https_observation_json(live)
    else:
        try:
            completed = runner(_verification_command(provider, operation, proof))
        except (OSError, subprocess.SubprocessError, UnicodeError, ValueError):
            return None
        if completed.returncode != 0 or not isinstance(completed.stdout, str):
            return None
        raw = completed.stdout
        try:
            live = json.loads(raw)
        except json.JSONDecodeError:
            return None
    if hashlib.sha256(raw.encode("utf-8")).hexdigest() != proof["sha256"]:
        return None
    normalized = _normalized_live(provider, operation, live, proof)
    if normalized is None:
        return None
    expected = {
        "resource_id": proof["resource_id"],
        "resource_url": proof["resource_url"],
        "status": proof["observed_status"],
        "readback": proof["readback"],
    }
    if "source_commit" in normalized:
        expected["source_commit"] = proof["source_commit"]
    extra = (
        {"project_id", "account_id", "repository_id"}
        if provider == "vercel"
        and operation in {"preview", "staged-production", "live-readback"}
        else set()
    )
    if set(normalized) != set(expected) | extra:
        return None
    if not all(normalized.get(key) == value for key, value in expected.items()):
        return None
    return normalized


def _live_matches(
    provider: str,
    operation: str,
    proof: Mapping[str, Any],
    runner: Runner,
    https_verifier: HTTPSVerifier = _default_https_verifier,
) -> bool:
    return (
        _live_result(provider, operation, proof, runner, https_verifier)
        is not None
    )


def _provider_preflight(provider: str, runner: Runner) -> bool:
    command = (
        ["gh", "auth", "status", "--active"]
        if provider == "github"
        else ["vercel", "whoami"]
    )
    try:
        completed = runner(command)
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return False
    return completed.returncode == 0


def _vercel_chain_valid(
    loaded: list[tuple[str, str, dict[str, Any]]],
) -> bool:
    proofs = {operation: proof for operation, _, proof in loaded}
    try:
        preview = proofs["preview"]
        browser = proofs["browser-verify"]
        staged = proofs["staged-production"]
        promotion = proofs["promote"]
        live = proofs["live-readback"]
    except KeyError:
        return False
    browser_pattern = re.compile(
        r"tls=verified;http=[23][0-9]{2};final="
        + re.escape(str(preview["resource_url"]))
    )
    return (
        browser["resource_url"] == preview["resource_url"]
        and browser_pattern.fullmatch(str(browser["readback"])) is not None
        and staged["resource_id"]
        == promotion["resource_id"]
        == live["resource_id"]
        and promotion["resource_url"] == live["resource_url"]
    )


def _block(
    result: dict[str, Any],
    receipt_path: pathlib.Path,
    verification: Mapping[str, Any],
    missing: list[str],
    execute: bool,
) -> dict[str, Any]:
    result["status"] = "BLOCKED"
    result["missing"] = missing
    if execute and verification["state"] != "BLOCKED":
        receipts.append_transition(
            receipt_path,
            "BLOCKED",
            reason=f"missing verified provider authority: {missing[0]}",
        )
    return result


def release_project(
    project: pathlib.Path | str,
    goal: str,
    provider: str,
    execute: bool = False,
    *,
    runner: Runner = _default_runner,
    https_verifier: HTTPSVerifier = _default_https_verifier,
) -> dict[str, Any]:
    """Plan or record RELEASED only after live provider verification."""
    root = pathlib.Path(project).resolve()
    if not root.is_dir():
        raise ValueError(f"project directory does not exist: {root}")
    if provider not in RELEASE_OPERATIONS:
        raise ValueError(f"provider does not support release: {provider}")
    receipt_path = _receipt_path(root, goal)
    verification = receipts.verify_receipt(receipt_path)
    if not verification["ok"]:
        raise ValueError("; ".join(verification["errors"]))
    required = RELEASE_OPERATIONS[provider]
    result: dict[str, Any] = {
        "schema_version": 1,
        "status": "planned",
        "project": root.name,
        "goal_id": goal,
        "provider": provider,
        "execute_required": True,
        "required_operations": list(required),
        "missing": [],
        "evidence": [],
    }
    context = _source_context(root)
    if context is None:
        return _block(
            result,
            receipt_path,
            verification,
            ["source.identity"],
            execute,
        )
    project_identity, source_commit = context

    loaded: list[tuple[str, str, dict[str, Any]]] = []
    for operation in required:
        item = _load_proof(
            root,
            goal,
            project_identity,
            source_commit,
            provider,
            operation,
            verification["artifacts"],
        )
        if item is None:
            return _block(
                result,
                receipt_path,
                verification,
                [f"{provider}.evidence.{operation}"],
                execute,
            )
        relative, proof = item
        loaded.append((operation, relative, proof))
    if provider == "vercel" and not _vercel_chain_valid(loaded):
        return _block(
            result,
            receipt_path,
            verification,
            ["vercel.evidence.chain"],
            execute,
        )
    if not _provider_preflight(provider, runner):
        return _block(
            result,
            receipt_path,
            verification,
            [f"{provider}.authority"],
            execute,
        )
    evidence: list[str] = []
    vercel_scope: tuple[str, str] | None = None
    vercel_provenance: tuple[str, int] | None = None
    for operation, relative, proof in loaded:
        live_result = _live_result(
            provider,
            operation,
            proof,
            runner,
            https_verifier,
        )
        if live_result is None:
            return _block(
                result,
                receipt_path,
                verification,
                [f"{provider}.verification.{operation}"],
                execute,
            )
        if provider == "vercel" and operation in {
            "preview",
            "staged-production",
            "live-readback",
        }:
            current_scope = (
                live_result.get("project_id"),
                live_result.get("account_id"),
            )
            current_commit = live_result.get("source_commit")
            current_repository = live_result.get("repository_id")
            if (
                not all(isinstance(item, str) for item in current_scope)
                or not isinstance(current_commit, str)
                or SHA_PATTERN.fullmatch(current_commit) is None
                or not _positive_integer(current_repository)
            ):
                return _block(
                    result,
                    receipt_path,
                    verification,
                    [f"vercel.verification.{operation}"],
                    execute,
                )
            typed_scope = (str(current_scope[0]), str(current_scope[1]))
            typed_provenance = (current_commit, int(current_repository))
            if operation == "preview":
                vercel_scope = typed_scope
                vercel_provenance = typed_provenance
                project_binding = _vercel_project_readback(
                    runner, *typed_scope
                )
                if (
                    project_binding is None
                    or project_binding[0].casefold()
                    != project_identity.casefold()
                    or project_binding[1] != typed_provenance[1]
                ):
                    return _block(
                        result,
                        receipt_path,
                        verification,
                        ["vercel.project.identity"],
                        execute,
                    )
            elif (
                vercel_scope is None
                or typed_scope != vercel_scope
                or vercel_provenance is None
                or typed_provenance != vercel_provenance
            ):
                return _block(
                    result,
                    receipt_path,
                    verification,
                    [f"vercel.verification.{operation}"],
                    execute,
                )
        evidence.append(relative)
    result["evidence"] = evidence
    if not execute:
        return result
    if verification["state"] not in {"VERIFIED", "PREVIEWED"}:
        raise ValueError("release requires a VERIFIED or PREVIEWED goal")
    receipts.append_transition(
        receipt_path,
        "RELEASED",
        reason=f"{provider} operations and live readback verified",
        evidence=evidence,
        results={"DPS-007": {"status": "PASS", "evidence": evidence}},
    )
    result["status"] = "RELEASED"
    result["execute_required"] = False
    return result
