#!/usr/bin/env python3
"""Deterministic, dry-run-first project bootstrap and inspection."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import secrets
import shlex
import socket
import stat
import subprocess
import tempfile
import time
import unicodedata
from datetime import date
from typing import Any, TypeGuard
from urllib.parse import urlsplit

import engine
import project_state
import receipts

BEGIN_MARKER = "<!-- divan:begin v1 -->"
END_MARKER = "<!-- divan:end v1 -->"
CONFIG_KEYS = (
    "schema_version",
    "profile",
    "locale",
    "autonomy",
    "project_types",
    "workspaces",
    "providers",
    "capabilities",
    "commands",
    "standards",
    "managed_files",
)
PROJECT_TYPES = (
    "library",
    "service",
    "application",
    "public-web",
    "documentation",
    "monorepo",
)
INIT_LOCK_STALE_SECONDS = 30
PROJECT_REQUIRED_IDS = tuple(f"DPS-{number:03d}" for number in range(1, 13))
PROJECT_STANDARD_FIELDS = (
    "id",
    "title_en",
    "title_tr",
    "level",
    "purpose",
    "applies_to",
    "checks",
    "evidence",
)
WAIVER_FIELDS = (
    "standard_id",
    "target",
    "reason",
    "owner",
    "created_on",
    "expires_on",
    "evidence",
)
STANDARD_APPLICABILITY = {
    "DPS-001": PROJECT_TYPES,
    "DPS-002": PROJECT_TYPES,
    "DPS-003": PROJECT_TYPES,
    "DPS-004": PROJECT_TYPES,
    "DPS-005": PROJECT_TYPES,
    "DPS-006": PROJECT_TYPES,
    "DPS-007": PROJECT_TYPES,
    "DPS-008": PROJECT_TYPES,
    "DPS-009": PROJECT_TYPES,
    "DPS-010": ("application", "public-web", "documentation"),
    "DPS-011": ("public-web",),
    "DPS-012": ("monorepo",),
}
STANDARD_TARGETS = {
    "DPS-001": (
        ".divan/config.json",
        ".divan/PROJECT_RULES.md",
        ".divan/waivers.json",
    ),
    "DPS-002": (".divan/config.json",),
    "DPS-003": (".divan/config.json",),
    "DPS-004": (".divan/config.json", ".divan/PROJECT_RULES.md"),
    "DPS-005": (".divan/specs",),
    "DPS-006": (".divan/evidence",),
    "DPS-007": (".divan/config.json", ".divan/evidence"),
    "DPS-008": (".divan/evidence",),
    "DPS-009": (".divan/waivers.json",),
    "DPS-010": ("README.md",),
    "DPS-011": (".divan/evidence",),
    "DPS-012": (".divan/config.json",),
}
PHASE_RANK = {
    "DISCOVERED": 0,
    "SPECIFIED": 1,
    "PLANNED": 2,
    "IMPLEMENTING": 3,
    "VERIFIED": 4,
    "PREVIEWED": 5,
    "RELEASED": 6,
    "OBSERVED": 7,
}
RECEIPT_PHASES = {
    "DPS-005": "PLANNED",
    "DPS-006": "VERIFIED",
    "DPS-007": "PREVIEWED",
    "DPS-008": "VERIFIED",
    "DPS-011": "PREVIEWED",
}
HOST_PATHS = {"agents": "AGENTS.md", "claude": "CLAUDE.md"}
LOCAL_CAPABILITIES = (
    "project.inspect",
    "project.plan",
    "project.write",
    "receipt.verify",
)
CI_PATH = ".github/workflows/divan-project.yml"
SEO_TOOL_PATH = ".divan/seo-tools.json"
LIGHTHOUSE_PATH = ".divan/lighthouse.json"
SEO_CI_PATH = ".github/workflows/divan-seo.yml"
INSTALL_STATE_PATH = ".divan/install-state.json"
INIT_JOURNAL = ".divan-init-journal.json"
INIT_STAGING = ".divan-init-staging"
MAX_READ_BYTES = 1024 * 1024
PROVIDER_ID = re.compile(r"^[a-z][a-z0-9-]*$")


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _nonempty_strings(value: Any) -> TypeGuard[list[str]]:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def load_project_contract(root: pathlib.Path) -> dict[str, Any]:
    path = root / "registry" / "project-standards.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("project-standards.json root must be an object")
    return value


def _project_standard_errors(row: Any, index: int) -> tuple[list[str], set[str]]:
    label = f"project standards[{index}]"
    if not isinstance(row, dict):
        return [f"{label} must be an object"], set()
    standard_id = row.get("id")
    if not isinstance(standard_id, str):
        return [f"{label}.id must be text"], set()
    errors = [
        f"{standard_id}.{field} is required"
        for field in PROJECT_STANDARD_FIELDS
        if field not in row
    ]
    if row.get("level") != "required":
        errors.append(f"{standard_id}.level must be required")
    for field in ("title_en", "title_tr", "purpose"):
        if not isinstance(row.get(field), str) or not row[field].strip():
            errors.append(f"{standard_id}.{field} must be non-empty text")
    applies_to = row.get("applies_to")
    if not _nonempty_strings(applies_to):
        errors.append(f"{standard_id}.applies_to must be non-empty")
        return errors, set()
    unknown = set(applies_to) - set(PROJECT_TYPES)
    if unknown:
        errors.append(
            f"{standard_id}.applies_to has unknown project types: "
            + ", ".join(sorted(unknown))
        )
    expected = STANDARD_APPLICABILITY.get(standard_id)
    if expected is not None and set(applies_to) != set(expected):
        errors.append(f"{standard_id}.applies_to must match the locked mapping")
    for field in ("checks", "evidence"):
        if not _nonempty_strings(row.get(field)):
            errors.append(f"{standard_id}.{field} must be non-empty")
    expected_targets = STANDARD_TARGETS.get(standard_id)
    if (
        expected_targets is not None
        and row.get("evidence") != list(expected_targets)
    ):
        errors.append(f"{standard_id}.evidence must match the locked target mapping")
    return errors, set(applies_to)


def validate_project_contract(root: pathlib.Path) -> list[str]:
    try:
        contract = load_project_contract(root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"project-standards.json cannot be read: {error}"]
    errors = []
    if contract.get("schema_version") != 1:
        errors.append("project-standards.json.schema_version must be 1")
    if contract.get("waiver_max_days") != 180:
        errors.append("project-standards.json.waiver_max_days must be 180")
    declared_types = contract.get("project_types")
    if not isinstance(declared_types, list) or set(declared_types) != set(PROJECT_TYPES):
        errors.append("project-standards.json.project_types must be exact")
    standards = contract.get("standards")
    if not isinstance(standards, list):
        return [*errors, "project-standards.json.standards must be an array"]
    applicability: set[str] = set()
    for index, row in enumerate(standards):
        row_errors, row_types = _project_standard_errors(row, index)
        errors.extend(row_errors)
        applicability.update(row_types)
    identifiers = tuple(
        row.get("id") for row in standards if isinstance(row, dict)
    )
    if identifiers != PROJECT_REQUIRED_IDS:
        errors.append("project standard IDs and order must be DPS-001 through DPS-012")
    if applicability != set(PROJECT_TYPES):
        errors.append("project standards must cover every declared project type")
    return errors


def _waiver_date(value: Any, label: str, errors: list[str]) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        errors.append(f"{label} must use YYYY-MM-DD")
        return None


def _waiver_record_errors(
    waiver: Any,
    index: int,
    current: date,
    seen: set[tuple[str, str]],
) -> list[str]:
    label = f"waivers[{index}]"
    if not isinstance(waiver, dict):
        return [f"{label} must be an object"]
    errors = [
        f"{label}.{field} must be non-empty text"
        for field in WAIVER_FIELDS
        if not isinstance(waiver.get(field), str) or not waiver[field].strip()
    ]
    standard_id, target = waiver.get("standard_id"), waiver.get("target")
    if standard_id not in PROJECT_REQUIRED_IDS:
        errors.append(f"{label}.standard_id is unknown: {standard_id}")
    if isinstance(target, str) and any(marker in target for marker in "*?[]"):
        errors.append(f"{label}.target cannot contain a wildcard")
    if (
        isinstance(standard_id, str)
        and standard_id in STANDARD_TARGETS
        and target not in STANDARD_TARGETS[standard_id]
    ):
        errors.append(
            f"{label}.target is not declared for {standard_id}: {target}"
        )
    if isinstance(standard_id, str) and isinstance(target, str):
        identity = (standard_id, target)
        if identity in seen:
            errors.append(f"{label} duplicates {standard_id} {target}")
        seen.add(identity)
    created = _waiver_date(waiver.get("created_on"), f"{label}.created_on", errors)
    expires = _waiver_date(waiver.get("expires_on"), f"{label}.expires_on", errors)
    if created and expires:
        if expires < current:
            errors.append(f"{label} is expired")
        if expires < created or (expires - created).days > 180:
            errors.append(f"{label} expiry must be within 180 days")
    return errors


def validate_waivers(value: Any, *, today: date | None = None) -> list[str]:
    current = date.today() if today is None else today
    if not isinstance(value, dict):
        return ["waivers root must be an object"]
    errors = [] if value.get("schema_version") == 1 else [
        "waivers.schema_version must be 1"
    ]
    waivers = value.get("waivers")
    if not isinstance(waivers, list):
        return [*errors, "waivers.waivers must be an array"]
    seen: set[tuple[str, str]] = set()
    for index, waiver in enumerate(waivers):
        errors.extend(_waiver_record_errors(waiver, index, current, seen))
    return errors


def _normalize_hosts(hosts: str | tuple[str, ...] | list[str]) -> list[str]:
    values = [hosts] if isinstance(hosts, str) else list(hosts)
    if values == ["both"] or "both" in values:
        values = ["agents", "claude"]
    if not values:
        raise ValueError("at least one host is required")
    unknown = sorted(set(values) - set(HOST_PATHS))
    if unknown:
        raise ValueError(f"unsupported hosts: {', '.join(unknown)}")
    return [name for name in ("agents", "claude") if name in values]


def _read_limited(path: pathlib.Path) -> str:
    if not path.is_file() or path.is_symlink():
        return ""
    data = path.read_bytes()
    if len(data) > MAX_READ_BYTES:
        return ""
    return data.decode("utf-8", errors="replace")


def _detect_locale(project: pathlib.Path) -> str:
    candidates = [
        path
        for path in sorted(project.glob("README*"), key=lambda item: item.name.casefold())
        if path.is_file() and path.suffix.casefold() in {".md", ".txt", ""}
    ][:8]
    text = "\n".join(_read_limited(path) for path in candidates)
    normalized = unicodedata.normalize("NFKC", text).casefold()
    turkish_chars = len(re.findall(r"[çğıöşü]", normalized))
    turkish_words = len(
        re.findall(
            r"\b(?:ve|bir|için|ile|proje|kurulum|kullanım|hakkında|özellikler)\b",
            normalized,
        )
    )
    english_words = len(
        re.findall(
            r"\b(?:and|the|for|with|project|install|usage|about|features)\b",
            normalized,
        )
    )
    return "tr" if turkish_chars + turkish_words > english_words else "en"


def _inspection(project: pathlib.Path) -> dict[str, Any]:
    contracts = engine.load_contracts(pathlib.Path(engine.__file__).resolve().parent)
    return engine.inspect_project(project, contracts)


def _selected_standards(project_types: list[str]) -> list[str]:
    kinds = set(project_types)
    return [
        standard_id
        for standard_id, applies_to in STANDARD_APPLICABILITY.items()
        if kinds.intersection(applies_to)
    ]


def _rules(locale: str) -> str:
    if locale == "tr":
        body = (
            "# Divan Proje Kuralları\n\n"
            "Bu proje gözetimli Divan Project OS sözleşmesini kullanır.\n\n"
            "- Mutasyonlardan önce planı göster ve açık yürütme yetkisi iste.\n"
            "- Sağlayıcı, onay veya kanıt yoksa `BLOCKED` raporla.\n"
            "- Sırları, mutlak kişisel yolları veya gizli akıl yürütmeyi kaydetme.\n"
            "- Kanıtları proje göreli, deterministik ve doğrulanabilir tut.\n"
        )
    else:
        body = (
            "# Divan Project Rules\n\n"
            "This project uses the supervised Divan Project OS contract.\n\n"
            "- Show a plan before mutation and require explicit execution authority.\n"
            "- Report `BLOCKED` when a provider, approval, or evidence is absent.\n"
            "- Never record secrets, personal absolute paths, or hidden reasoning.\n"
            "- Keep evidence project-relative, deterministic, and verifiable.\n"
        )
    return body


def _host_block() -> str:
    return (
        f"{BEGIN_MARKER}\n"
        "## Divan Project OS\n\n"
        "Follow `.divan/PROJECT_RULES.md` for supervised project work. "
        "Project-local config and evidence live under `.divan/`.\n"
        f"{END_MARKER}"
    )


def _trusted_action_commit() -> str:
    directory = pathlib.Path(__file__).resolve().parent
    metadata_path = directory / "divan-project-source.json"
    if metadata_path.is_file() and not metadata_path.is_symlink():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("installed Divan source metadata is invalid") from error
        if (
            isinstance(metadata, dict)
            and set(metadata) == {"schema_version", "source_commit"}
            and metadata.get("schema_version") == 1
            and isinstance(metadata.get("source_commit"), str)
            and re.fullmatch(r"[0-9a-f]{40}", metadata["source_commit"])
        ):
            return metadata["source_commit"]
        if (
            isinstance(metadata, dict)
            and metadata.get("schema_version") == 2
            and set(metadata)
            == {
                "schema_version",
                "version",
                "source_repository",
                "source_ref",
                "source_commit",
            }
        ):
            return _runtime_source_identity()["source_commit"]
        raise ValueError("installed Divan source metadata is invalid")
    repository = directory.parents[2]
    try:
        status = subprocess.check_output(
            [
                "git",
                "-C",
                str(repository),
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            text=True,
            encoding="utf-8",
            errors="strict",
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
        head = subprocess.check_output(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            text=True,
            encoding="utf-8",
            errors="strict",
            stderr=subprocess.DEVNULL,
            timeout=15,
        ).strip()
    except (OSError, subprocess.SubprocessError, UnicodeError) as error:
        raise ValueError("immutable Divan action commit cannot be proven") from error
    if status or re.fullmatch(r"[0-9a-f]{40}", head) is None:
        raise ValueError("immutable Divan action commit requires a clean checkout")
    return head


def _ci_workflow(action_commit: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", action_commit) is None:
        raise ValueError("immutable Divan action commit is invalid")
    return (
        "name: Divan Project\n\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "  pull_request:\n\n"
        "permissions:\n"
        "  contents: read\n\n"
        "jobs:\n"
        "  verify-contract:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7\n"
        "      - name: Verify initialized contract\n"
        "        uses: trugurpala/divan/.github/actions/divan-project@"
        f"{action_commit}\n"
        "        with:\n"
        "          project: .\n"
    )


def _preservation_policy(path: str, kind: str) -> str:
    if kind == "managed":
        return "preserve-outside-managed-block"
    if path == ".divan/waivers.json":
        return "preserve-existing"
    return "replace-generated"


def _write_digest(item: dict[str, Any]) -> str:
    record = {
        "path": item.get("path"),
        "kind": item.get("kind"),
        "payload_sha256": item.get("payload_sha256"),
        "preservation_policy": item.get("preservation_policy"),
    }
    return _sha256(
        json.dumps(
            record, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
    )


def _seo_contract(
    root: pathlib.Path,
    profile: str,
    expected_url: str | None = None,
) -> tuple[str, str]:
    directory = pathlib.Path(__file__).resolve().parent
    candidates = [directory / "data" / "seo-policy.json"]
    if len(directory.parents) > 2:
        candidates.append(directory.parents[2] / "registry" / "seo-policy.json")
    policy_path = next((path for path in candidates if path.is_file()), None)
    if policy_path is None:
        raise ValueError("bundled SEO policy is unavailable")
    try:
        policy_bytes = policy_path.read_bytes()
        if len(policy_bytes) > 256 * 1024:
            raise ValueError("bundled SEO policy exceeds the size limit")
        policy = json.loads(policy_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("bundled SEO policy is invalid") from error
    if not isinstance(policy, dict):
        raise ValueError("bundled SEO policy root must be an object")
    plans = []
    for tool in ("lighthouse-ci", "lychee"):
        row = policy["tools"][tool]
        plans.append(
            {
                "tool": tool,
                "identity": row["identity"],
                "source_commit": row["source_commit"],
                "acquisition": row["acquisition"],
                "verification": {
                    "verify_before_observation": True,
                    "artifact_hash": "sha256",
                    "network_during_audit": False,
                },
                "execute": False,
                "runtime": row["runtime"],
                "outputs": row["outputs"],
                **(
                    {"thresholds": policy["profiles"][profile]}
                    if tool == "lighthouse-ci"
                    else {}
                ),
            }
        )
    encoded = json.dumps(
        plans, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = f"sha256:{_sha256(encoded)}"
    html = root / "index.html"
    if expected_url is None and html.is_file() and not html.is_symlink():
        match = re.search(
            r'<link\s+[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)',
            html.read_text(encoding="utf-8"),
            re.IGNORECASE,
        )
        if match:
            expected_url = match.group(1)
    if expected_url is not None:
        parsed = urlsplit(expected_url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.username is not None
        ):
            raise ValueError("expected_url must be an absolute HTTP(S) URL")
    tools = {
        "schema_version": 1,
        "profile": profile,
        "expected_url": expected_url,
        "command_plan_digest": digest,
        "network_during_audit": False,
        "plans": plans,
    }
    lighthouse = {
        "ci": {
            "collect": {"numberOfRuns": 1},
            "upload": {
                "target": "filesystem",
                "outputDir": ".divan/evidence/seo/lighthouse",
            },
        }
    }
    return (
        _json_bytes(tools).decode("utf-8"),
        _json_bytes(lighthouse).decode("utf-8"),
    )


def render_plan_command(command: list[str]) -> str:
    """Render one reviewed argv without introducing a shell command string."""
    rendered = []
    for token in command:
        if token == "${EXPECTED_URL}":
            rendered.append('"$EXPECTED_URL"')
        elif token == "--url=${EXPECTED_URL}":
            rendered.append('"--url=$EXPECTED_URL"')
        elif "${PWD}" in token:
            rendered.append(f'"{token}"')
        else:
            rendered.append(shlex.quote(token))
    return " ".join(rendered)


def _plan_commands(plan: dict[str, Any], phase: str) -> str:
    return "".join(
        f"          {render_plan_command(command)}\n"
        for command in plan["runtime"][phase]
    )


def _plan_assertions(plan: dict[str, Any]) -> str:
    return "".join(
        '          test "$('
        + render_plan_command(assertion["argv"])
        + ')" = '
        + json.dumps(assertion["stdout"])
        + "\n"
        for assertion in plan["runtime"]["assertions"]
    )


def _render_seo_workflow_from_tools(tools_content: str) -> str:
    tools = json.loads(tools_content)
    expected_url = json.dumps(tools["expected_url"])
    plan_digest = json.dumps(tools["command_plan_digest"])
    plans = {plan["tool"]: plan for plan in tools["plans"]}
    lighthouse = plans["lighthouse-ci"]
    lychee = plans["lychee"]
    return (
        "name: Divan SEO evidence\n"
        "on:\n  workflow_dispatch:\n"
        "permissions:\n  contents: read\n"
        "jobs:\n  observe:\n    runs-on: ubuntu-latest\n"
        "    env:\n"
        f"      EXPECTED_URL: {expected_url}\n"
        f"      COMMAND_PLAN_DIGEST: {plan_digest}\n"
        "    steps:\n"
        "      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7\n"
        "      - name: Acquire immutable Lighthouse CI\n"
        "        shell: bash\n"
        "        run: |\n"
        + _plan_commands(lighthouse, "acquisition")
        + _plan_assertions(lighthouse)
        + "      - name: Collect native Lighthouse JSON\n"
        "        shell: bash\n"
        "        run: |\n"
        + _plan_commands(lighthouse, "execution")
        + "      - name: Acquire and verify Lychee\n"
        "        shell: bash\n"
        "        run: |\n"
        + _plan_commands(lychee, "acquisition")
        + "      - name: Collect native Lychee JSON\n"
        "        shell: bash\n"
        "        run: |\n"
        + _plan_commands(lychee, "execution")
        + "      - name: Bind observation manifest\n"
        "        shell: bash\n"
        "        run: |\n"
        "          python - <<'PY'\n"
        "          import hashlib, json, os, pathlib, subprocess\n"
        "          workflow = pathlib.Path('.github/workflows/divan-seo.yml').read_bytes()\n"
        "          tree = subprocess.check_output(['git','rev-parse','HEAD^{tree}'], text=True).strip()\n"
        "          value = {'schema_version':1,'repository':os.environ['GITHUB_REPOSITORY'],'run_id':os.environ['GITHUB_RUN_ID'],'run_attempt':int(os.environ['GITHUB_RUN_ATTEMPT']),'head_sha':os.environ['GITHUB_SHA'],'workflow_digest':'sha256:'+hashlib.sha256(workflow).hexdigest(),'source_identity':{'commit':os.environ['GITHUB_SHA'],'tree':tree},'profile':"
        + json.dumps(tools["profile"])
        + ",'expected_url':os.environ['EXPECTED_URL'],'command_plan_digest':os.environ['COMMAND_PLAN_DIGEST']}\n"
        "          pathlib.Path('.divan/evidence/seo/manifest.json').write_text(json.dumps(value, sort_keys=True), encoding='utf-8')\n"
        "          PY\n"
        "      - name: Upload native evidence\n"
        "        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2\n"
        "        with:\n"
        "          name: divan-seo-evidence\n"
        "          path: |\n"
        "            .divan/evidence/seo/lighthouse.json\n"
        "            .divan/evidence/seo/lychee.json\n"
        "            .divan/evidence/seo/manifest.json\n"
        "          if-no-files-found: error\n"
    )


def render_seo_workflow(profile: str, expected_url: str) -> str:
    """Render canonical workflow bytes from trusted policy and managed URL."""
    tools, _lighthouse = _seo_contract(
        pathlib.Path.cwd(), profile, expected_url
    )
    return _render_seo_workflow_from_tools(tools)


def _runtime_source_identity() -> dict[str, str]:
    directory = pathlib.Path(__file__).resolve().parent
    metadata_path = directory / "divan-project-source.json"
    if metadata_path.is_file() and not metadata_path.is_symlink():
        try:
            value = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError("installed Divan source metadata is invalid") from error
        expected = {
            "schema_version",
            "version",
            "source_repository",
            "source_ref",
            "source_commit",
        }
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError("installed Divan source metadata is invalid")
        source = {key: value[key] for key in expected if key != "schema_version"}
        candidate = {
            "schema_version": 1,
            "product": "divan-project-os",
            "contract_schema": 2,
            "installed": source,
            "project_identity": "sha256:" + "0" * 64,
            "managed_files": [],
        }
        if project_state.validate_install_state(candidate):
            raise ValueError("installed Divan source metadata is invalid")
        return source
    repository = directory.parents[2]
    try:
        status = subprocess.check_output(
            [
                "git",
                "-C",
                str(repository),
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            text=True,
            encoding="utf-8",
            errors="strict",
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
        if status:
            raise ValueError(
                "Divan development source identity requires a clean checkout"
            )
        commit = subprocess.check_output(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            text=True,
            encoding="utf-8",
            errors="strict",
            stderr=subprocess.DEVNULL,
            timeout=15,
        ).strip()
        version = (repository / "VERSION").read_text(encoding="utf-8").strip()
    except (OSError, subprocess.SubprocessError, UnicodeError) as error:
        raise ValueError("Divan development source identity is unavailable") from error
    source = {
        "version": version,
        "source_repository": project_state.SOURCE_REPOSITORY,
        "source_ref": f"development@{commit}",
        "source_commit": commit,
    }
    candidate = {
        "schema_version": 1,
        "product": "divan-project-os",
        "contract_schema": 2,
        "installed": source,
        "project_identity": "sha256:" + "0" * 64,
        "managed_files": [],
    }
    if project_state.validate_install_state(candidate):
        raise ValueError("Divan development source identity is invalid")
    return source


def build_init_plan(
    project: pathlib.Path | str,
    profile: str,
    locale: str,
    hosts: str | tuple[str, ...] | list[str],
    include_ci: bool,
    *,
    expected_url: str | None = None,
) -> dict[str, Any]:
    """Return a deterministic schema-v1 plan without writing the project."""
    root = pathlib.Path(project).resolve()
    if not root.is_dir():
        raise ValueError(f"project directory does not exist: {root}")
    if profile not in {"standard", "strict"}:
        raise ValueError("profile must be standard or strict")
    if locale not in {"auto", "en", "tr"}:
        raise ValueError("locale must be auto, en, or tr")
    selected_hosts = _normalize_hosts(hosts)
    resolved_locale = _detect_locale(root) if locale == "auto" else locale
    snapshot = _inspection(root)
    project_types = [
        item for item in snapshot.get("project_types", []) if item in PROJECT_TYPES
    ]
    managed_files = [HOST_PATHS[name] for name in selected_hosts]
    public_web = "public-web" in project_types
    seo_tools = lighthouse = None
    if public_web:
        seo_tools, lighthouse = _seo_contract(root, profile, expected_url)
        expected_url = json.loads(seo_tools)["expected_url"]
    seo_ready = public_web and expected_url is not None
    if public_web:
        managed_files.extend((LIGHTHOUSE_PATH, SEO_TOOL_PATH))
    if seo_ready:
        managed_files.append(SEO_CI_PATH)
    action_commit = _trusted_action_commit() if include_ci else None
    if include_ci:
        managed_files.append(CI_PATH)
    config = {
        "schema_version": 2,
        "profile": profile,
        "locale": resolved_locale,
        "autonomy": "supervised",
        "project_types": project_types,
        "workspaces": snapshot.get("workspaces", []),
        "providers": ["local"],
        "capabilities": list(LOCAL_CAPABILITIES),
        "commands": snapshot.get("commands", []),
        "standards": _selected_standards(project_types),
        "managed_files": managed_files,
    }
    writes: list[dict[str, Any]] = [
        {
            "path": ".divan/config.json",
            "kind": "replace",
            "content": _json_bytes(config).decode("utf-8"),
        },
        {
            "path": ".divan/PROJECT_RULES.md",
            "kind": "replace",
            "content": _rules(resolved_locale),
        },
        {
            "path": ".divan/waivers.json",
            "kind": "create",
            "content": _json_bytes(
                {"schema_version": 1, "waivers": []}
            ).decode("utf-8"),
        },
    ]
    if public_web:
        assert seo_tools is not None and lighthouse is not None
        writes.extend(
            (
                {
                    "path": LIGHTHOUSE_PATH,
                    "kind": "replace",
                    "content": lighthouse,
                },
                {
                    "path": SEO_TOOL_PATH,
                    "kind": "replace",
                    "content": seo_tools,
                },
            )
        )
        if seo_ready:
            assert expected_url is not None
            writes.append(
                {
                    "path": SEO_CI_PATH,
                    "kind": "replace",
                    "content": render_seo_workflow(profile, expected_url),
                }
            )
    writes.extend(
        {
            "path": HOST_PATHS[name],
            "kind": "managed",
            "managed_block": _host_block(),
        }
        for name in selected_hosts
    )
    if include_ci:
        writes.append(
            {
                "path": CI_PATH,
                "kind": "replace",
                "content": _ci_workflow(str(action_commit)),
            }
        )
    owned_rows = []
    for item in writes:
        if item["path"] == ".divan/waivers.json":
            continue
        material = item.get("content", item.get("managed_block", "")).encode("utf-8")
        owned_rows.append(
            {
                "path": item["path"],
                "mode": (
                    "marked-block" if item["kind"] == "managed" else "whole-file"
                ),
                "payload_sha256": f"sha256:{_sha256(material)}",
            }
        )
    state = {
        "schema_version": 1,
        "product": "divan-project-os",
        "contract_schema": 2,
        "installed": _runtime_source_identity(),
        "project_identity": _project_identity(root),
        "managed_files": sorted(owned_rows, key=lambda row: row["path"]),
    }
    writes.append(
        {
            "path": INSTALL_STATE_PATH,
            "kind": "replace",
            "content": project_state.serialize_install_state(state).decode("utf-8"),
        }
    )
    for item in writes:
        material = item.get("content", item.get("managed_block", "")).encode("utf-8")
        item["payload_sha256"] = _sha256(material)
        item["preservation_policy"] = _preservation_policy(
            item["path"], item["kind"]
        )
        item["digest"] = _write_digest(item)
    return {
        "schema_version": 1,
        "status": "blocked" if public_web and not seo_ready else "planned",
        "project": str(root),
        "profile": profile,
        "locale": resolved_locale,
        "hosts": selected_hosts,
        "include_ci": bool(include_ci),
        "execute_required": True,
        **(
            {
                "continuation_command": (
                    "python scripts/divan.py init --project . --profile "
                    f"{profile} --locale {resolved_locale} "
                    "--expected-url https://example.com/"
                )
            }
            if public_web and not seo_ready
            else {}
        ),
        "writes": writes,
    }


def _safe_destination(root: pathlib.Path, relative: Any) -> pathlib.Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError("write path must be a project-relative string")
    pure = pathlib.PurePosixPath(relative.replace("\\", "/"))
    if (
        pure.is_absolute()
        or ".." in pure.parts
        or "." in pure.parts
        or (pure.parts and re.fullmatch(r"(?i)[a-z]:", pure.parts[0]))
    ):
        raise ValueError(f"write path escapes project: {relative}")
    destination = root.joinpath(*pure.parts)
    resolved = destination.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"write path escapes project: {relative}") from error
    cursor = root
    for part in pure.parts:
        cursor = cursor / part
        if _is_reparse_or_symlink(cursor):
            raise ValueError(
                f"write path uses a symlink or reparse point: {relative}"
            )
    return destination


def _render_managed(existing: bytes | None, block: str) -> bytes:
    raw = b"" if existing is None else existing
    newline = (
        "\r\n"
        if b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")
        else "\n"
    )
    text = raw.decode("utf-8")
    normalized_block = block.replace("\r\n", "\n").replace("\n", newline)
    begins = text.count(BEGIN_MARKER)
    ends = text.count(END_MARKER)
    if begins != ends or begins > 1:
        raise ValueError("managed markers are unmatched or duplicated")
    if begins == 1:
        start = text.index(BEGIN_MARKER)
        try:
            end = text.index(END_MARKER, start) + len(END_MARKER)
        except ValueError as error:
            raise ValueError("managed markers are unmatched or duplicated") from error
        rendered = text[:start] + normalized_block + text[end:]
    else:
        separator = "" if not text or text.endswith(newline * 2) else (
            newline if text.endswith(newline) else newline * 2
        )
        rendered = text + separator + normalized_block + newline
    return rendered.encode("utf-8")


def _atomic_replace(path: pathlib.Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _allowed_write_contracts() -> dict[str, tuple[str, str]]:
    contracts = {
        ".divan/config.json": ("replace", "replace-generated"),
        ".divan/PROJECT_RULES.md": ("replace", "replace-generated"),
        ".divan/waivers.json": ("create", "preserve-existing"),
        INSTALL_STATE_PATH: ("replace", "replace-generated"),
        "AGENTS.md": ("managed", "preserve-outside-managed-block"),
        "CLAUDE.md": ("managed", "preserve-outside-managed-block"),
        CI_PATH: ("replace", "replace-generated"),
        LIGHTHOUSE_PATH: ("replace", "replace-generated"),
        SEO_TOOL_PATH: ("replace", "replace-generated"),
        SEO_CI_PATH: ("replace", "replace-generated"),
    }
    return contracts


def _expected_plan_paths(plan: dict[str, Any]) -> list[str]:
    hosts = _normalize_hosts(plan.get("hosts", []))
    paths = [
        ".divan/config.json",
        ".divan/PROJECT_RULES.md",
        ".divan/waivers.json",
    ]
    config_write = plan.get("writes", [{}])[0]
    if isinstance(config_write, dict):
        try:
            config = json.loads(config_write.get("content", ""))
        except (TypeError, json.JSONDecodeError):
            config = {}
        if isinstance(config, dict) and "public-web" in config.get(
            "project_types", []
        ):
            paths.extend((LIGHTHOUSE_PATH, SEO_TOOL_PATH))
            if SEO_CI_PATH in config.get("managed_files", []):
                paths.append(SEO_CI_PATH)
    paths.extend(HOST_PATHS[host] for host in hosts)
    if plan.get("include_ci") is True:
        paths.append(CI_PATH)
    elif plan.get("include_ci") is not False:
        raise ValueError("init plan include_ci must be boolean")
    paths.append(INSTALL_STATE_PATH)
    return paths


def _prepare_init_plan(
    plan: dict[str, Any], root: pathlib.Path
) -> list[dict[str, Any]]:
    writes = plan.get("writes")
    if not isinstance(writes, list) or not writes:
        raise ValueError("init plan writes must be a non-empty list")
    paths = [item.get("path") if isinstance(item, dict) else None for item in writes]
    if paths != _expected_plan_paths(plan):
        raise ValueError(
            "init plan project destinations do not match the generated allowlist"
        )
    allowed = _allowed_write_contracts()
    prepared: list[dict[str, Any]] = []
    for item in writes:
        if not isinstance(item, dict):
            raise ValueError("init plan write must be an object")
        relative = item.get("path")
        if not isinstance(relative, str):
            raise ValueError("init plan destination must be text")
        contract = allowed.get(relative)
        if contract is None:
            raise ValueError(f"init plan destination is not allowed: {relative}")
        kind, policy = contract
        if item.get("kind") != kind or item.get("preservation_policy") != policy:
            raise ValueError(f"init plan kind or preservation policy changed: {relative}")
        payload_key = "managed_block" if kind == "managed" else "content"
        material = item.get(payload_key)
        payload_hash = item.get("payload_sha256")
        if (
            not isinstance(material, str)
            or not isinstance(payload_hash, str)
            or _sha256(material.encode("utf-8")) != payload_hash
        ):
            raise ValueError(f"init plan payload hash mismatch: {relative}")
        if item.get("digest") != _write_digest(item):
            raise ValueError(f"init plan record digest mismatch: {relative}")
        destination = _safe_destination(root, relative)
        if destination.exists() and not destination.is_file():
            raise ValueError(f"init plan destination must be a file: {relative}")
        existing = destination.read_bytes() if destination.is_file() else None
        if kind == "managed":
            desired = _render_managed(existing, material)
        elif kind == "create" and existing is not None:
            desired = existing
        else:
            desired = material.encode("utf-8")
        prepared.append(
            {
                "path": destination,
                "relative": relative,
                "desired": desired,
                "original": existing,
            }
        )
    return prepared


def _transaction_paths(root: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    journal = root / INIT_JOURNAL
    staging = root / INIT_STAGING
    if journal.is_symlink() or staging.is_symlink():
        raise ValueError("init transaction path cannot be a symlink")
    return journal, staging


def _project_identity(root: pathlib.Path) -> str:
    material = f"divan-project-v1\0{os.path.normcase(str(root.resolve()))}"
    return f"sha256:{_sha256(material.encode('utf-8'))}"


def _trusted_init_root() -> pathlib.Path:
    override = os.environ.get("DIVAN_STATE_HOME")
    if override:
        base = pathlib.Path(override).expanduser()
    elif os.name == "nt":
        base = pathlib.Path(
            os.environ.get("LOCALAPPDATA", pathlib.Path.home() / "AppData" / "Local")
        ) / "Divan"
    else:
        base = pathlib.Path(
            os.environ.get(
                "XDG_STATE_HOME", pathlib.Path.home() / ".local" / "state"
            )
        ) / "divan"
    return pathlib.Path(os.path.abspath(base)) / "project-init"


def _is_reparse_or_symlink(path: pathlib.Path) -> bool:
    try:
        details = path.lstat()
    except OSError:
        return False
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    attributes = getattr(details, "st_file_attributes", 0)
    return stat.S_ISLNK(details.st_mode) or bool(attributes & reparse)


def _windows_ace_grants_mutation(mask: int, flags: int) -> bool:
    if flags & 0x08:
        return False
    mutation_rights = (
        0x00000002  # FILE_ADD_FILE / FILE_WRITE_DATA
        | 0x00000004  # FILE_ADD_SUBDIRECTORY / FILE_APPEND_DATA
        | 0x00000010  # FILE_WRITE_EA
        | 0x00000040  # FILE_DELETE_CHILD
        | 0x00000100  # FILE_WRITE_ATTRIBUTES
        | 0x00010000  # DELETE
        | 0x00040000  # WRITE_DAC
        | 0x00080000  # WRITE_OWNER
        | 0x10000000  # GENERIC_ALL
        | 0x40000000  # GENERIC_WRITE
    )
    return bool(mask & mutation_rights)


def _windows_private_dacl(
    path: pathlib.Path, *, require_current_owner: bool = True
) -> None:
    try:
        import ctypes
        from ctypes import wintypes

        advapi32 = getattr(ctypes, "WinDLL")("advapi32", use_last_error=True)
        kernel32 = getattr(ctypes, "WinDLL")("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.LocalFree.argtypes = (wintypes.HLOCAL,)
        kernel32.LocalFree.restype = wintypes.HLOCAL
        advapi32.OpenProcessToken.argtypes = (
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.HANDLE),
        )
        advapi32.OpenProcessToken.restype = wintypes.BOOL
        advapi32.GetTokenInformation.argtypes = (
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        )
        advapi32.GetTokenInformation.restype = wintypes.BOOL
        advapi32.GetNamedSecurityInfoW.argtypes = (
            wintypes.LPWSTR,
            ctypes.c_int,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
        )
        advapi32.GetNamedSecurityInfoW.restype = wintypes.DWORD
        advapi32.EqualSid.argtypes = (ctypes.c_void_p, ctypes.c_void_p)
        advapi32.EqualSid.restype = wintypes.BOOL
        advapi32.CreateWellKnownSid.argtypes = (
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(wintypes.DWORD),
        )
        advapi32.CreateWellKnownSid.restype = wintypes.BOOL
        advapi32.GetAce.argtypes = (
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.c_void_p),
        )
        advapi32.GetAce.restype = wintypes.BOOL
        token = wintypes.HANDLE()
        if not advapi32.OpenProcessToken(
            kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)
        ):
            raise OSError(getattr(ctypes, "get_last_error")(), "OpenProcessToken failed")
        try:
            needed = wintypes.DWORD()
            advapi32.GetTokenInformation(token, 1, None, 0, ctypes.byref(needed))
            token_buffer = ctypes.create_string_buffer(needed.value)
            if not advapi32.GetTokenInformation(
                token,
                1,
                token_buffer,
                needed,
                ctypes.byref(needed),
            ):
                raise OSError(
                    getattr(ctypes, "get_last_error")(), "GetTokenInformation failed"
                )
            current_sid = ctypes.c_void_p.from_buffer(token_buffer).value
            if not current_sid:
                raise OSError("current user SID is unavailable")

            owner_sid = ctypes.c_void_p()
            dacl = ctypes.c_void_p()
            descriptor = ctypes.c_void_p()
            result = advapi32.GetNamedSecurityInfoW(
                str(path),
                1,
                0x00000001 | 0x00000004,
                ctypes.byref(owner_sid),
                None,
                ctypes.byref(dacl),
                None,
                ctypes.byref(descriptor),
            )
            if result:
                raise OSError(result, "GetNamedSecurityInfoW failed")
            try:
                if not dacl.value:
                    raise ValueError(
                        "trusted init state directory has an unrestricted DACL"
                    )

                class ACL(ctypes.Structure):
                    _fields_ = (
                        ("revision", ctypes.c_ubyte),
                        ("sbz1", ctypes.c_ubyte),
                        ("size", wintypes.WORD),
                        ("ace_count", wintypes.WORD),
                        ("sbz2", wintypes.WORD),
                    )

                acl = ctypes.cast(dacl, ctypes.POINTER(ACL)).contents

                def well_known(kind: int) -> ctypes.Array[Any]:
                    size = wintypes.DWORD(68)
                    buffer = ctypes.create_string_buffer(size.value)
                    if not advapi32.CreateWellKnownSid(
                        kind, None, buffer, ctypes.byref(size)
                    ):
                        raise OSError(
                            getattr(ctypes, "get_last_error")(), "CreateWellKnownSid failed"
                        )
                    return buffer

                trusted_sids = (well_known(22), well_known(26))
                owner_is_current = bool(
                    advapi32.EqualSid(owner_sid, current_sid)
                )
                owner_is_trusted = owner_is_current or any(
                    advapi32.EqualSid(owner_sid, trusted)
                    for trusted in trusted_sids
                )
                if (
                    require_current_owner
                    and not owner_is_current
                ) or (
                    not require_current_owner
                    and not owner_is_trusted
                ):
                    raise ValueError(
                        "trusted init state directory owner is not trusted"
                    )
                for index in range(acl.ace_count):
                    ace = ctypes.c_void_p()
                    if not advapi32.GetAce(dacl, index, ctypes.byref(ace)):
                        raise OSError(getattr(ctypes, "get_last_error")(), "GetAce failed")
                    ace_address = ace.value
                    if ace_address is None:
                        raise OSError("DACL ACE address is unavailable")
                    ace_type = ctypes.c_ubyte.from_address(ace_address).value
                    ace_flags = ctypes.c_ubyte.from_address(
                        ace_address + 1
                    ).value
                    if ace_type == 1:
                        continue
                    if ace_type != 0:
                        raise ValueError(
                            "trusted init state directory DACL is not private"
                        )
                    sid = ctypes.c_void_p(ace_address + 8)
                    mask = ctypes.c_uint32.from_address(
                        ace_address + 4
                    ).value
                    allowed = bool(advapi32.EqualSid(sid, current_sid)) or any(
                        advapi32.EqualSid(sid, trusted)
                        for trusted in trusted_sids
                    )
                    if (
                        not allowed
                        and _windows_ace_grants_mutation(mask, ace_flags)
                    ):
                        raise ValueError(
                            "trusted init state directory DACL grants mutation "
                            "rights to another principal"
                        )
            finally:
                kernel32.LocalFree(descriptor)
        finally:
            kernel32.CloseHandle(token)
    except ValueError:
        raise
    except (AttributeError, OSError, TypeError) as error:
        raise ValueError(
            "trusted init state directory privacy cannot be verified"
        ) from error


def _create_private_windows_directory(path: pathlib.Path) -> bool:
    try:
        import ctypes
        from ctypes import wintypes

        advapi32 = getattr(ctypes, "WinDLL")("advapi32", use_last_error=True)
        kernel32 = getattr(ctypes, "WinDLL")("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        advapi32.OpenProcessToken.argtypes = (
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.HANDLE),
        )
        advapi32.OpenProcessToken.restype = wintypes.BOOL
        advapi32.GetTokenInformation.argtypes = (
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        )
        advapi32.GetTokenInformation.restype = wintypes.BOOL
        advapi32.ConvertSidToStringSidW.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(wintypes.LPWSTR),
        )
        advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL
        advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(wintypes.DWORD),
        )
        advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = (
            wintypes.BOOL
        )
        kernel32.LocalFree.argtypes = (wintypes.HLOCAL,)
        kernel32.LocalFree.restype = wintypes.HLOCAL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL

        class SECURITY_ATTRIBUTES(ctypes.Structure):
            _fields_ = (
                ("length", wintypes.DWORD),
                ("security_descriptor", ctypes.c_void_p),
                ("inherit_handle", wintypes.BOOL),
            )

        kernel32.CreateDirectoryW.argtypes = (
            wintypes.LPCWSTR,
            ctypes.POINTER(SECURITY_ATTRIBUTES),
        )
        kernel32.CreateDirectoryW.restype = wintypes.BOOL
        token = wintypes.HANDLE()
        if not advapi32.OpenProcessToken(
            kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)
        ):
            raise OSError(getattr(ctypes, "get_last_error")(), "OpenProcessToken failed")
        try:
            needed = wintypes.DWORD()
            advapi32.GetTokenInformation(token, 1, None, 0, ctypes.byref(needed))
            token_buffer = ctypes.create_string_buffer(needed.value)
            if not advapi32.GetTokenInformation(
                token, 1, token_buffer, needed, ctypes.byref(needed)
            ):
                raise OSError(
                    getattr(ctypes, "get_last_error")(), "GetTokenInformation failed"
                )
            current_sid = ctypes.c_void_p.from_buffer(token_buffer).value
            sid_text = wintypes.LPWSTR()
            if not advapi32.ConvertSidToStringSidW(
                current_sid, ctypes.byref(sid_text)
            ):
                raise OSError(
                    getattr(ctypes, "get_last_error")(), "ConvertSidToStringSidW failed"
                )
            try:
                sddl = (
                    "D:P"
                    f"(A;OICI;FA;;;{sid_text.value})"
                    "(A;OICI;FA;;;SY)"
                    "(A;OICI;FA;;;BA)"
                )
            finally:
                kernel32.LocalFree(sid_text)
            descriptor = ctypes.c_void_p()
            if not advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
                sddl, 1, ctypes.byref(descriptor), None
            ):
                raise OSError(
                    getattr(ctypes, "get_last_error")(),
                    "security descriptor creation failed",
                )
            try:
                attributes = SECURITY_ATTRIBUTES(
                    ctypes.sizeof(SECURITY_ATTRIBUTES), descriptor, False
                )
                if kernel32.CreateDirectoryW(
                    str(path), ctypes.byref(attributes)
                ):
                    return True
                error = getattr(ctypes, "get_last_error")()
                if error == 183:
                    return False
                raise OSError(error, "private directory creation failed")
            finally:
                kernel32.LocalFree(descriptor)
        finally:
            kernel32.CloseHandle(token)
    except (AttributeError, OSError, TypeError) as error:
        raise ValueError(
            "trusted init state directory cannot be created privately"
        ) from error


def _verify_private_state_directory(path: pathlib.Path) -> os.stat_result:
    if _is_reparse_or_symlink(path):
        raise ValueError(
            "trusted init state directory cannot be a symlink or reparse point"
        )
    try:
        before = path.lstat()
    except OSError as error:
        raise ValueError("trusted init state directory is unavailable") from error
    if not stat.S_ISDIR(before.st_mode):
        raise ValueError("trusted init state directory must be a real directory")
    if os.name == "nt":
        _windows_private_dacl(path)
    else:
        get_effective_uid = getattr(os, "geteuid", None)
        if (
            get_effective_uid is None
            or before.st_uid != get_effective_uid()
        ):
            raise ValueError(
                "trusted init state directory is not owned by current user"
            )
        if stat.S_IMODE(before.st_mode) != 0o700:
            raise ValueError(
                "trusted init state directory permissions must be private 0700"
            )
    after = path.lstat()
    if (
        _is_reparse_or_symlink(path)
        or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
    ):
        raise ValueError("trusted init state directory changed during verification")
    return after


def _state_ancestor_chain(path: pathlib.Path) -> list[pathlib.Path]:
    absolute = pathlib.Path(os.path.abspath(path))
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            raise ValueError(
                "Windows trusted state anchor LOCALAPPDATA is unavailable"
            )
        anchor = pathlib.Path(os.path.abspath(local_app_data))
        try:
            relative = absolute.relative_to(anchor)
        except ValueError as error:
            raise ValueError(
                "Windows trusted state override must stay inside LOCALAPPDATA"
            ) from error
        chain = [anchor]
        cursor = anchor
        for part in relative.parts:
            cursor = cursor / part
            chain.append(cursor)
        return chain
    return [*reversed(absolute.parents), absolute]


def _verify_safe_state_ancestors(path: pathlib.Path) -> None:
    for ancestor in _state_ancestor_chain(path):
        if not ancestor.exists():
            raise ValueError(
                "trusted init state ancestor is unavailable; "
                "create a private trusted anchor first"
            )
        if _is_reparse_or_symlink(ancestor):
            raise ValueError(
                "trusted init state ancestor cannot be a symlink or reparse point"
            )
        try:
            before = ancestor.lstat()
        except OSError as error:
            raise ValueError(
                "trusted init state ancestor cannot be inspected"
            ) from error
        if not stat.S_ISDIR(before.st_mode):
            raise ValueError("trusted init state ancestor must be a directory")
        if os.name == "nt":
            _windows_private_dacl(
                ancestor, require_current_owner=False
            )
        else:
            mode = stat.S_IMODE(before.st_mode)
            writable = bool(mode & 0o022)
            sticky_shared = bool(mode & stat.S_ISVTX) and bool(mode & 0o002)
            if writable and not sticky_shared:
                raise ValueError(
                    "trusted init state ancestor is writable without sticky protection"
                )
        after = ancestor.lstat()
        if (
            _is_reparse_or_symlink(ancestor)
            or (before.st_dev, before.st_ino)
            != (after.st_dev, after.st_ino)
        ):
            raise ValueError(
                "trusted init state ancestor changed during verification"
            )


def _create_private_state_directory(path: pathlib.Path) -> None:
    if not path.parent.is_dir() or _is_reparse_or_symlink(path.parent):
        raise ValueError(
            "trusted init state parent must be an existing safe directory"
        )
    if os.name == "nt":
        _create_private_windows_directory(path)
        _verify_private_state_directory(path)
        return
    try:
        os.mkdir(path, 0o700)
    except FileExistsError:
        _verify_private_state_directory(path)
        return
    os.chmod(path, 0o700)
    _verify_private_state_directory(path)


def _ensure_trusted_init_root() -> pathlib.Path:
    trusted_root = _trusted_init_root()
    state_root = trusted_root.parent
    _verify_safe_state_ancestors(state_root.parent)
    for path in (state_root, trusted_root):
        _create_private_state_directory(path)
        _verify_private_state_directory(path)
        _verify_safe_state_ancestors(path.parent)
    return trusted_root


def _trusted_init_marker(
    root: pathlib.Path, transaction_id: str
) -> pathlib.Path:
    identity = _project_identity(root).removeprefix("sha256:")
    if re.fullmatch(r"[0-9a-f]{64}", identity) is None:
        raise ValueError("init project identity is invalid")
    trusted_root = _ensure_trusted_init_root()
    marker = trusted_root / f"{identity}-{transaction_id}.json"
    if marker.parent != trusted_root:
        raise ValueError("trusted init marker escapes containment")
    return marker


def _process_start_token(pid: int) -> str | None:
    if pid <= 0:
        return None
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = getattr(ctypes, "WinDLL")("kernel32", use_last_error=True)
            kernel32.OpenProcess.argtypes = (
                wintypes.DWORD,
                wintypes.BOOL,
                wintypes.DWORD,
            )
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.GetProcessTimes.argtypes = (
                wintypes.HANDLE,
                ctypes.POINTER(wintypes.FILETIME),
                ctypes.POINTER(wintypes.FILETIME),
                ctypes.POINTER(wintypes.FILETIME),
                ctypes.POINTER(wintypes.FILETIME),
            )
            kernel32.GetProcessTimes.restype = wintypes.BOOL
            kernel32.GetExitCodeProcess.argtypes = (
                wintypes.HANDLE,
                ctypes.POINTER(wintypes.DWORD),
            )
            kernel32.GetExitCodeProcess.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
            kernel32.CloseHandle.restype = wintypes.BOOL
            process = kernel32.OpenProcess(0x1000, False, pid)
            if not process:
                return None
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            exit_code = wintypes.DWORD()
            try:
                if (
                    not kernel32.GetExitCodeProcess(
                        process, ctypes.byref(exit_code)
                    )
                    or exit_code.value != 259
                ):
                    return None
                if not kernel32.GetProcessTimes(
                    process,
                    ctypes.byref(creation),
                    ctypes.byref(exit_time),
                    ctypes.byref(kernel),
                    ctypes.byref(user),
                ):
                    return None
                value = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
                return f"windows-filetime:{value}"
            finally:
                kernel32.CloseHandle(process)
        except (AttributeError, OSError, ValueError):
            return None
    stat = pathlib.Path(f"/proc/{pid}/stat")
    try:
        text = stat.read_text(encoding="ascii")
        closing = text.rfind(")")
        fields = text[closing + 2 :].split()
        return f"proc-start:{fields[19]}"
    except (OSError, UnicodeError, IndexError):
        return None


def _pid_is_live(pid: int, recorded_start: str) -> bool:
    current_start = _process_start_token(pid)
    if recorded_start != "unavailable":
        if current_start is not None:
            return current_start == recorded_start
        if os.name != "nt":
            return False
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = getattr(ctypes, "WinDLL")("kernel32", use_last_error=True)
            kernel32.OpenProcess.argtypes = (
                wintypes.DWORD,
                wintypes.BOOL,
                wintypes.DWORD,
            )
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.GetExitCodeProcess.argtypes = (
                wintypes.HANDLE,
                ctypes.POINTER(wintypes.DWORD),
            )
            kernel32.GetExitCodeProcess.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
            kernel32.CloseHandle.restype = wintypes.BOOL
            process = kernel32.OpenProcess(0x1000, False, pid)
            if not process:
                return getattr(ctypes, "get_last_error")() != 87
            exit_code = wintypes.DWORD()
            try:
                if not kernel32.GetExitCodeProcess(process, ctypes.byref(exit_code)):
                    return True
                return exit_code.value == 259
            finally:
                kernel32.CloseHandle(process)
        except (AttributeError, OSError, ValueError):
            return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _init_lock_path(root: pathlib.Path) -> pathlib.Path:
    identity = _project_identity(root).removeprefix("sha256:")
    trusted_root = _ensure_trusted_init_root()
    path = trusted_root / f"{identity}.lock"
    if path.parent != trusted_root:
        raise ValueError("init lock escapes containment")
    return path


def _read_init_lock(
    path: pathlib.Path, root: pathlib.Path
) -> tuple[dict[str, Any], bytes, os.stat_result]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(
            "project initialization lock is unsafe; quarantine it manually"
        )
    try:
        before = path.stat()
        content = path.read_bytes()
        after = path.stat()
        owner = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(
            "project initialization lock cannot be verified; quarantine it manually"
        ) from error
    if (
        (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
        or not isinstance(owner, dict)
        or set(owner)
        != {
            "schema_version",
            "project_identity",
            "pid",
            "process_start",
            "nonce",
            "hostname",
            "created_ns",
        }
        or owner.get("schema_version") != 1
        or owner.get("project_identity") != _project_identity(root)
        or type(owner.get("pid")) is not int
        or owner["pid"] <= 0
        or not isinstance(owner.get("process_start"), str)
        or re.fullmatch(
            r"(?:unavailable|windows-filetime:[0-9]+|proc-start:[0-9]+)",
            owner["process_start"],
        )
        is None
        or not isinstance(owner.get("nonce"), str)
        or re.fullmatch(r"[0-9a-f]{32}", owner["nonce"]) is None
        or not isinstance(owner.get("hostname"), str)
        or not owner["hostname"]
        or len(owner["hostname"]) > 255
        or type(owner.get("created_ns")) is not int
        or owner["created_ns"] <= 0
    ):
        raise ValueError(
            "project initialization lock identity is invalid; quarantine it manually"
        )
    return owner, content, after


def _reclaim_dead_init_lock(path: pathlib.Path, root: pathlib.Path) -> None:
    owner, content, observed = _read_init_lock(path, root)
    if owner["hostname"] != socket.gethostname():
        raise ValueError(
            "project initialization lock belongs to another host; "
            "quarantine it only after verifying that host"
        )
    if _pid_is_live(owner["pid"], owner["process_start"]):
        raise ValueError(
            "project initialization is owned by a live process; retry after it exits"
        )
    age_ns = time.time_ns() - owner["created_ns"]
    if age_ns < INIT_LOCK_STALE_SECONDS * 1_000_000_000:
        raise ValueError(
            "project initialization lock owner is dead but the lock is too new; "
            "retry later or quarantine it after verifying the owner"
        )
    current_owner, current_content, current = _read_init_lock(path, root)
    if (
        current_owner != owner
        or current_content != content
        or (current.st_dev, current.st_ino) != (observed.st_dev, observed.st_ino)
    ):
        raise ValueError("project initialization lock changed during recovery")
    path.unlink()


def _acquire_init_lock(
    root: pathlib.Path,
) -> tuple[pathlib.Path, bytes]:
    path = _init_lock_path(root)
    start = _process_start_token(os.getpid()) or "unavailable"
    owner = {
        "schema_version": 1,
        "project_identity": _project_identity(root),
        "pid": os.getpid(),
        "process_start": start,
        "nonce": secrets.token_hex(16),
        "hostname": socket.gethostname(),
        "created_ns": time.time_ns(),
    }
    content = _json_bytes(owner)
    for _attempt in range(2):
        try:
            _write_trusted_init_marker(path, content)
            return path, content
        except FileExistsError:
            _reclaim_dead_init_lock(path, root)
    raise ValueError("project initialization lock could not be acquired")


def _release_init_lock(path: pathlib.Path, owner_bytes: bytes) -> None:
    try:
        if path.is_symlink() or not path.is_file():
            return
        if path.read_bytes() == owner_bytes:
            path.unlink()
    except OSError:
        return


def _write_trusted_init_marker(path: pathlib.Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _verify_trusted_init_marker(
    root: pathlib.Path,
    journal: dict[str, Any],
    authority_bytes: bytes,
) -> pathlib.Path:
    transaction_id = journal.get("transaction_id")
    if not isinstance(transaction_id, str):
        raise ValueError("init transaction id is invalid")
    marker = _trusted_init_marker(root, transaction_id)
    if marker.is_symlink() or not marker.is_file():
        raise ValueError("trusted init transaction marker is unavailable")
    try:
        trusted = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("trusted init transaction marker cannot be read") from error
    expected = {
        "schema_version": 1,
        "transaction_id": transaction_id,
        "project_identity": _project_identity(root),
        "plan_digest": journal.get("plan_digest"),
        "authority_sha256": f"sha256:{_sha256(authority_bytes)}",
    }
    if trusted != expected:
        raise ValueError("trusted init transaction binding is invalid")
    return marker


def _init_plan_digest(plan: dict[str, Any]) -> str:
    encoded = json.dumps(
        plan, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return f"sha256:{_sha256(encoded)}"


def _current_digest(path: pathlib.Path) -> str | None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("init transaction destination is unsafe")
    return f"sha256:{_sha256(path.read_bytes())}" if path.is_file() else None


def _persist_init_journal(path: pathlib.Path, journal: dict[str, Any]) -> None:
    _atomic_replace(path, _json_bytes(journal))


def _transaction_directory(staging: pathlib.Path, transaction_id: str) -> pathlib.Path:
    if re.fullmatch(r"[0-9a-f]{32}", transaction_id) is None:
        raise ValueError("init transaction id is invalid")
    directory = staging / transaction_id
    if directory.parent != staging:
        raise ValueError("init transaction staging escapes containment")
    return directory


def _load_init_authority(
    root: pathlib.Path,
    staging: pathlib.Path,
    journal: dict[str, Any],
) -> tuple[dict[str, Any], pathlib.Path, pathlib.Path]:
    transaction_id = journal.get("transaction_id")
    if not isinstance(transaction_id, str):
        raise ValueError("init transaction id is invalid")
    directory = _transaction_directory(staging, transaction_id)
    authority_path = directory / "authority.json"
    if (
        staging.is_symlink()
        or not staging.is_dir()
        or {item.name for item in staging.iterdir()} != {transaction_id}
        or
        directory.is_symlink()
        or not directory.is_dir()
        or authority_path.is_symlink()
        or not authority_path.is_file()
    ):
        raise ValueError("init transaction durable marker is unavailable")
    try:
        authority_bytes = authority_path.read_bytes()
        authority = json.loads(authority_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("init transaction authority cannot be read") from error
    if (
        not isinstance(authority, dict)
        or journal.get("authority_sha256")
        != f"sha256:{_sha256(authority_bytes)}"
        or authority.get("schema_version") != 2
        or authority.get("transaction_id") != transaction_id
        or authority.get("project_identity") != _project_identity(root)
        or authority.get("project_identity") != journal.get("project_identity")
        or authority.get("plan_digest") != journal.get("plan_digest")
        or not isinstance(authority.get("entries"), list)
        or not isinstance(authority.get("created_dirs"), list)
    ):
        raise ValueError("init transaction authority binding is invalid")
    expected_names = {"authority.json"}
    allowed = _allowed_write_contracts()
    for entry in authority["entries"]:
        if not isinstance(entry, dict) or set(entry) != {
            "path",
            "existed",
            "backup",
            "preimage_sha256",
            "postimage_sha256",
            "backup_sha256",
        }:
            raise ValueError("init transaction authority entry is invalid")
        if (
            entry["path"] not in allowed
            or not isinstance(entry["existed"], bool)
            or not isinstance(entry["postimage_sha256"], str)
            or re.fullmatch(
                r"sha256:[0-9a-f]{64}", entry["postimage_sha256"]
            )
            is None
        ):
            raise ValueError("init transaction authority destination is invalid")
        backup = entry["backup"]
        if entry["existed"]:
            if not isinstance(backup, str) or re.fullmatch(
                r"[0-9]{4}\.bin", backup
            ) is None:
                raise ValueError("init transaction backup name is invalid")
            if (
                not isinstance(entry["preimage_sha256"], str)
                or entry["preimage_sha256"] != entry["backup_sha256"]
                or re.fullmatch(
                    r"sha256:[0-9a-f]{64}", entry["preimage_sha256"]
                )
                is None
            ):
                raise ValueError("init transaction preimage binding is invalid")
            expected_names.add(backup)
        elif (
            backup is not None
            or entry["preimage_sha256"] is not None
            or entry["backup_sha256"] is not None
        ):
            raise ValueError("init transaction absent preimage is invalid")
    allowed_directories = {
        pathlib.PurePosixPath(path).parent.as_posix()
        for path in allowed
        if pathlib.PurePosixPath(path).parent.as_posix() != "."
    }
    allowed_directories.update({".divan", ".github"})
    if (
        not all(
            isinstance(item, str) and item in allowed_directories
            for item in authority["created_dirs"]
        )
        or len(authority["created_dirs"]) != len(set(authority["created_dirs"]))
    ):
        raise ValueError("init transaction created directories are invalid")
    if {item.name for item in directory.iterdir()} != expected_names:
        raise ValueError("init transaction staging contents are ambiguous")
    trusted_marker = _verify_trusted_init_marker(
        root, journal, authority_bytes
    )
    return authority, directory, trusted_marker


def _validate_init_journal(
    root: pathlib.Path,
    journal: Any,
    expected_plan_digest: str,
) -> None:
    if (
        not isinstance(journal, dict)
        or set(journal) != {
            "schema_version",
            "transaction_id",
            "project_identity",
            "plan_digest",
            "authority_sha256",
            "status",
            "entries",
            "transitions",
        }
        or journal.get("schema_version") != 2
        or journal.get("project_identity") != _project_identity(root)
        or journal.get("plan_digest") != expected_plan_digest
        or journal.get("status") not in {
            "prepared",
            "applying",
            "recovering",
            "committed",
        }
        or not isinstance(journal.get("entries"), list)
        or not isinstance(journal.get("transitions"), list)
    ):
        raise ValueError("init transaction journal binding is invalid")
    transitions = journal["transitions"]
    allowed = {
        ("prepared", "applying"),
        ("prepared", "recovering"),
        ("applying", "recovering"),
        ("applying", "committed"),
        ("recovering", "recovering"),
    }
    if (
        not transitions
        or transitions[0] != "prepared"
        or transitions[-1] != journal["status"]
        or any(pair not in allowed for pair in zip(transitions, transitions[1:]))
    ):
        raise ValueError("init transaction state transitions are invalid")
    states = [
        item.get("state") if isinstance(item, dict) else None
        for item in journal["entries"]
    ]
    if (
        journal["status"] == "prepared"
        and any(state != "pending" for state in states)
    ) or (
        journal["status"] == "committed"
        and any(state != "applied" for state in states)
    ):
        raise ValueError("init transaction status and entries disagree")


def _verify_transaction_state(
    root: pathlib.Path,
    authority: dict[str, Any],
    journal: dict[str, Any],
) -> None:
    states = journal["entries"]
    if len(states) != len(authority["entries"]):
        raise ValueError("init transaction entry state is invalid")
    for immutable, dynamic in zip(authority["entries"], states):
        if (
            not isinstance(dynamic, dict)
            or set(dynamic) != {"path", "state"}
            or dynamic["path"] != immutable["path"]
            or dynamic["state"]
            not in {"pending", "applying", "applied", "reverting", "restored"}
        ):
            raise ValueError("init transaction entry state is invalid")
        destination = _safe_destination(root, immutable["path"])
        current = _current_digest(destination)
        preimage = immutable["preimage_sha256"]
        postimage = immutable["postimage_sha256"]
        accepted = {
            "pending": {preimage},
            "applying": {preimage, postimage},
            "applied": {postimage},
            "reverting": {preimage, postimage},
            "restored": {preimage},
        }[dynamic["state"]]
        if current not in accepted:
            raise ValueError("init transaction filesystem state is stale")


def _transition_init(
    path: pathlib.Path,
    journal: dict[str, Any],
    status: str,
) -> None:
    if journal["status"] != status:
        journal["status"] = status
        journal["transitions"].append(status)
    _persist_init_journal(path, journal)


def _remove_owned_staging(
    staging: pathlib.Path,
    directory: pathlib.Path,
    authority: dict[str, Any],
) -> None:
    for entry in authority["entries"]:
        backup = entry["backup"]
        if backup is not None:
            (directory / backup).unlink()
    (directory / "authority.json").unlink()
    directory.rmdir()
    if not any(staging.iterdir()):
        staging.rmdir()


def _recover_init(root: pathlib.Path, expected_plan_digest: str) -> None:
    journal_path, staging = _transaction_paths(root)
    if not journal_path.exists():
        if staging.exists():
            raise ValueError(
                "orphan init staging requires manual quarantine; no files changed"
            )
        return
    if journal_path.is_symlink() or not journal_path.is_file():
        raise ValueError("init transaction journal must be a regular file")
    try:
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"init journal cannot be read: {error}") from error
    _validate_init_journal(root, journal, expected_plan_digest)
    authority, transaction_directory, trusted_marker = _load_init_authority(
        root, staging, journal
    )
    _verify_transaction_state(root, authority, journal)
    if journal["status"] == "committed":
        _remove_owned_staging(staging, transaction_directory, authority)
        journal_path.unlink()
        trusted_marker.unlink()
        return
    _transition_init(journal_path, journal, "recovering")
    for index in range(len(authority["entries"]) - 1, -1, -1):
        entry = authority["entries"][index]
        dynamic = journal["entries"][index]
        dynamic["state"] = "reverting"
        _persist_init_journal(journal_path, journal)
        destination = _safe_destination(root, entry["path"])
        current = _current_digest(destination)
        if current != entry["preimage_sha256"]:
            if entry["existed"]:
                backup = transaction_directory / entry["backup"]
                if backup.is_symlink() or not backup.is_file():
                    raise ValueError("init transaction backup is unavailable")
                content = backup.read_bytes()
                if f"sha256:{_sha256(content)}" != entry["backup_sha256"]:
                    raise ValueError("init transaction backup hash mismatch")
                _atomic_replace(destination, content)
            else:
                destination.unlink()
        dynamic["state"] = "restored"
        _persist_init_journal(journal_path, journal)
    directories = []
    allowed_directories = {
        pathlib.PurePosixPath(path).parent.as_posix()
        for path in _allowed_write_contracts()
        if pathlib.PurePosixPath(path).parent.as_posix() != "."
    }
    allowed_directories.update({".divan", ".github"})
    for relative in authority["created_dirs"]:
        if relative not in allowed_directories:
            raise ValueError("init transaction created directory is invalid")
        directory = _safe_destination(root, relative)
        directories.append(directory)
    for directory in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    _remove_owned_staging(staging, transaction_directory, authority)
    journal_path.unlink()
    trusted_marker.unlink()


def _created_directories(
    root: pathlib.Path, changed: list[dict[str, Any]]
) -> list[str]:
    directories: set[pathlib.Path] = set()
    for item in changed:
        cursor = item["path"].parent
        while cursor != root:
            if not cursor.exists():
                directories.add(cursor)
            cursor = cursor.parent
    return [
        path.relative_to(root).as_posix()
        for path in sorted(directories, key=lambda item: (len(item.parts), str(item)))
    ]


def _start_init_transaction(
    root: pathlib.Path,
    changed: list[dict[str, Any]],
    plan_digest: str,
) -> tuple[
    pathlib.Path,
    dict[str, Any],
    dict[str, Any],
    pathlib.Path,
    pathlib.Path,
]:
    journal_path, staging = _transaction_paths(root)
    created_dirs = _created_directories(root, changed)
    transaction_id = secrets.token_hex(16)
    staging.mkdir()
    directory = _transaction_directory(staging, transaction_id)
    directory.mkdir()
    entries = []
    for index, item in enumerate(changed):
        original = item["original"]
        backup_name = f"{index:04d}.bin" if original is not None else None
        if backup_name is not None:
            _atomic_replace(directory / backup_name, original)
        entries.append(
            {
                "path": item["relative"],
                "existed": original is not None,
                "backup": backup_name,
                "preimage_sha256": (
                    None if original is None else f"sha256:{_sha256(original)}"
                ),
                "postimage_sha256": f"sha256:{_sha256(item['desired'])}",
                "backup_sha256": (
                    None if original is None else f"sha256:{_sha256(original)}"
                ),
            }
        )
    authority = {
        "schema_version": 2,
        "transaction_id": transaction_id,
        "project_identity": _project_identity(root),
        "plan_digest": plan_digest,
        "entries": entries,
        "created_dirs": created_dirs,
    }
    authority_bytes = _json_bytes(authority)
    _atomic_replace(directory / "authority.json", authority_bytes)
    trusted_marker = _trusted_init_marker(root, transaction_id)
    _write_trusted_init_marker(
        trusted_marker,
        _json_bytes(
            {
                "schema_version": 1,
                "transaction_id": transaction_id,
                "project_identity": _project_identity(root),
                "plan_digest": plan_digest,
                "authority_sha256": f"sha256:{_sha256(authority_bytes)}",
            }
        ),
    )
    journal = {
        "schema_version": 2,
        "transaction_id": transaction_id,
        "project_identity": _project_identity(root),
        "plan_digest": plan_digest,
        "authority_sha256": f"sha256:{_sha256(authority_bytes)}",
        "status": "prepared",
        "entries": [
            {"path": entry["path"], "state": "pending"} for entry in entries
        ],
        "transitions": ["prepared"],
    }
    _persist_init_journal(journal_path, journal)
    return journal_path, journal, authority, directory, trusted_marker


def _finish_init_transaction(
    root: pathlib.Path,
    journal_path: pathlib.Path,
    journal: dict[str, Any],
    authority: dict[str, Any],
    directory: pathlib.Path,
    trusted_marker: pathlib.Path,
) -> None:
    _transition_init(journal_path, journal, "committed")
    _remove_owned_staging(root / INIT_STAGING, directory, authority)
    journal_path.unlink()
    trusted_marker.unlink()


def apply_init_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Apply a validated plan with durable crash recovery and rollback."""
    if not isinstance(plan, dict) or plan.get("schema_version") != 1:
        raise ValueError("init plan schema_version must be 1")
    root_value = plan.get("project")
    if not isinstance(root_value, str):
        raise ValueError("init plan project is required")
    root = pathlib.Path(root_value).resolve()
    if not root.is_dir():
        raise ValueError("init plan project directory does not exist")
    plan_digest = _init_plan_digest(plan)
    lock_path, lock_owner = _acquire_init_lock(root)
    try:
        _recover_init(root, plan_digest)
        prepared = _prepare_init_plan(plan, root)
        changed = [
            item for item in prepared if item["desired"] != item["original"]
        ]
        if not changed:
            return {
                "schema_version": 1,
                "status": "unchanged",
                "project": str(root),
                "changed": [],
            }
        try:
            (
                journal_path,
                journal,
                authority,
                directory,
                trusted_marker,
            ) = _start_init_transaction(root, changed, plan_digest)
            _transition_init(journal_path, journal, "applying")
            for index, item in enumerate(changed):
                journal["entries"][index]["state"] = "applying"
                _persist_init_journal(journal_path, journal)
                _atomic_replace(item["path"], item["desired"])
                if (
                    not item["path"].is_file()
                    or item["path"].read_bytes() != item["desired"]
                ):
                    raise ValueError(
                        f"init write verification failed: {item['relative']}"
                    )
                journal["entries"][index]["state"] = "applied"
                _persist_init_journal(journal_path, journal)
            _finish_init_transaction(
                root,
                journal_path,
                journal,
                authority,
                directory,
                trusted_marker,
            )
        except BaseException:
            _recover_init(root, plan_digest)
            raise
        return {
            "schema_version": 1,
            "status": "applied",
            "project": str(root),
            "changed": [item["relative"] for item in changed],
        }
    finally:
        _release_init_lock(lock_path, lock_owner)


def _load_config(root: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    path = root / ".divan" / "config.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, [f".divan/config.json is unavailable or invalid: {error}"]
    if not isinstance(value, dict):
        return None, [".divan/config.json root must be an object"]
    errors = []
    if set(value) != set(CONFIG_KEYS):
        errors.append(".divan/config.json keys do not match schema 2")
    if type(value.get("schema_version")) is not int or value.get("schema_version") != 2:
        errors.append(".divan/config.json schema_version must be 2")
    if value.get("profile") not in {"standard", "strict"}:
        errors.append(".divan/config.json profile is invalid")
    if value.get("locale") not in {"en", "tr"}:
        errors.append(".divan/config.json locale is invalid")
    if value.get("autonomy") != "supervised":
        errors.append(".divan/config.json autonomy must be supervised")
    project_types = value.get("project_types")
    if not isinstance(project_types, list) or len(project_types) != len(set(
        item for item in project_types if isinstance(item, str)
    )) or not all(item in PROJECT_TYPES for item in project_types):
        errors.append(".divan/config.json project_types are invalid")
        project_types = []
    for field in ("workspaces", "commands"):
        if not isinstance(value.get(field), list):
            errors.append(f".divan/config.json {field} must be an array")
    for field in ("capabilities", "standards", "managed_files"):
        items = value.get(field)
        if not isinstance(items, list) or not all(
            isinstance(item, str) and item for item in items
        ) or len(items) != len(set(items)):
            errors.append(f".divan/config.json {field} are invalid")
    if value.get("capabilities") != list(LOCAL_CAPABILITIES):
        errors.append(".divan/config.json capabilities do not match schema 2")
    standards = value.get("standards")
    if isinstance(standards, list) and standards != _selected_standards(project_types):
        errors.append(".divan/config.json standards do not match project types")
    managed = value.get("managed_files")
    allowed_managed = {
        *HOST_PATHS.values(),
        CI_PATH,
        LIGHTHOUSE_PATH,
        SEO_TOOL_PATH,
        SEO_CI_PATH,
    }
    if (
        isinstance(managed, list)
        and (
            not set(managed).issubset(allowed_managed)
            or not set(managed).intersection(HOST_PATHS.values())
        )
    ):
        errors.append(".divan/config.json managed_files are invalid")
    providers = value.get("providers")
    if (
        not isinstance(providers, list)
        or not providers
        or not all(
            isinstance(item, str) and PROVIDER_ID.fullmatch(item)
            for item in providers
        )
        or len(providers) != len(set(providers))
    ):
        errors.append(".divan/config.json providers are invalid")
    return value, errors


def _load_waivers(root: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    path = root / ".divan" / "waivers.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, [f".divan/waivers.json is unavailable or invalid: {error}"]
    errors = validate_waivers(value)
    if isinstance(value, dict) and not errors:
        waivers = value.get("waivers", [])
        for index, waiver in enumerate(waivers):
            evidence = waiver["evidence"]
            try:
                path = _safe_destination(root, evidence)
            except ValueError as error:
                errors.append(f"waivers[{index}].evidence is invalid: {error}")
                continue
            if path.is_symlink() or not path.is_file():
                errors.append(
                    f"waivers[{index}].evidence is unavailable: {evidence}"
                )
    return value if isinstance(value, dict) else None, errors


def _waiver_errors(root: pathlib.Path) -> list[str]:
    _, errors = _load_waivers(root)
    return errors


def _missing_providers(config: dict[str, Any] | None) -> list[str]:
    if config is None:
        return []
    providers = config.get("providers")
    if not isinstance(providers, list):
        return []
    return sorted(
        item
        for item in providers
        if isinstance(item, str) and PROVIDER_ID.fullmatch(item) and item != "local"
    )


def _managed_block_errors(path: pathlib.Path) -> list[str]:
    if path.is_symlink() or not path.is_file():
        return [f"{path.name} managed file is unavailable"]
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return [f"{path.name} cannot be read: {error}"]
    if text.count(BEGIN_MARKER) != 1 or text.count(END_MARKER) != 1:
        return [f"{path.name} managed block markers are invalid"]
    start = text.find(BEGIN_MARKER)
    end = text.find(END_MARKER, start)
    if end < start:
        return [f"{path.name} managed block markers are invalid"]
    block = text[start : end + len(END_MARKER)].replace("\r\n", "\n")
    if block != _host_block():
        return [f"{path.name} managed block content is invalid"]
    return []


def _managed_file_errors(
    root: pathlib.Path,
    config: dict[str, Any] | None,
    *,
    include_rules: bool = True,
) -> list[str]:
    if config is None:
        return []
    errors: list[str] = []
    locale = config.get("locale")
    rules = root / ".divan" / "PROJECT_RULES.md"
    if include_rules and (
        locale not in {"en", "tr"}
        or rules.is_symlink()
        or not rules.is_file()
        or rules.read_bytes() != _rules(locale).encode("utf-8")
    ):
        errors.append(".divan/PROJECT_RULES.md is unavailable or invalid")
    managed = config.get("managed_files")
    if not isinstance(managed, list):
        return errors
    for relative in managed:
        if relative in HOST_PATHS.values():
            errors.extend(_managed_block_errors(root / relative))
        elif relative == CI_PATH:
            path = root / relative
            valid = False
            if not path.is_symlink() and path.is_file():
                try:
                    content = path.read_text(encoding="utf-8")
                    match = re.search(
                        r"trugurpala/divan/\.github/actions/"
                        r"divan-project@([0-9a-f]{40})",
                        content,
                    )
                    valid = (
                        match is not None
                        and content == _ci_workflow(match.group(1))
                    )
                except (OSError, UnicodeError, ValueError):
                    valid = False
            if not valid:
                errors.append(f"{CI_PATH} is unavailable or invalid")
        elif relative in {LIGHTHOUSE_PATH, SEO_TOOL_PATH, SEO_CI_PATH}:
            profile = config.get("profile")
            if profile not in {"standard", "strict"}:
                continue
            configured: str | None = None
            tools_path = root / SEO_TOOL_PATH
            if tools_path.is_file() and not tools_path.is_symlink():
                try:
                    candidate = json.loads(
                        tools_path.read_text(encoding="utf-8")
                    ).get("expected_url")
                    configured = candidate if isinstance(candidate, str) else None
                except (OSError, json.JSONDecodeError, AttributeError):
                    configured = None
            tools, lighthouse = _seo_contract(root, profile, configured)
            expected_content = {
                LIGHTHOUSE_PATH: lighthouse,
                SEO_TOOL_PATH: tools,
                SEO_CI_PATH: (
                    render_seo_workflow(profile, configured)
                    if configured is not None
                    else ""
                ),
            }[relative]
            expected = expected_content.encode("utf-8")
            path = root / relative
            if (
                path.is_symlink()
                or not path.is_file()
                or path.read_bytes() != expected
            ):
                errors.append(f"{relative} is unavailable or invalid")
    return errors


def _inspection_drift_errors(
    root: pathlib.Path, config: dict[str, Any] | None
) -> list[str]:
    if config is None:
        return []
    try:
        snapshot = _inspection(root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"fresh bounded inspection failed: {error}"]
    project_types = [
        item
        for item in snapshot.get("project_types", [])
        if item in PROJECT_TYPES
    ]
    expected = {
        "project_types": project_types,
        "workspaces": snapshot.get("workspaces", []),
        "commands": snapshot.get("commands", []),
        "standards": _selected_standards(project_types),
    }
    return [
        f".divan/config.json inspection drift: {field}"
        for field, value in expected.items()
        if config.get(field) != value
    ]


def audit_project(project: pathlib.Path | str) -> dict[str, Any]:
    """Inspect project contracts without executing or mutating target code."""
    root = pathlib.Path(project).resolve()
    config, errors = _load_config(root)
    waiver_errors = _waiver_errors(root)
    missing = _missing_providers(config)
    all_errors = [
        *errors,
        *waiver_errors,
        *_managed_file_errors(root, config, include_rules=False),
        *_inspection_drift_errors(root, config),
    ]
    status = "FAIL" if all_errors else ("BLOCKED" if missing else "PASS")
    return {
        "schema_version": 1,
        "status": status,
        "project": root.name,
        "missing_providers": missing,
        "errors": all_errors,
    }


def _receipt_evidence(
    root: pathlib.Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    evidence_root = root / ".divan" / "evidence"
    if not evidence_root.exists():
        return [], []
    if evidence_root.is_symlink() or not evidence_root.is_dir():
        return [], [".divan/evidence must be a real directory"]
    verifications: list[dict[str, Any]] = []
    errors: list[str] = []
    for goal_directory in sorted(evidence_root.iterdir(), key=lambda item: item.name):
        if (
            goal_directory.is_symlink()
            or not goal_directory.is_dir()
            or not re.fullmatch(r"goal-[0-9a-f]{12}", goal_directory.name)
        ):
            errors.append(
                f".divan/evidence/{goal_directory.name} is not a canonical goal directory"
            )
            continue
        verification = receipts.verify_receipt(goal_directory / "receipt.json")
        verifications.append(verification)
        errors.extend(
            f"{goal_directory.name}: {error}"
            for error in verification["errors"]
        )
    return verifications, errors


def _valid_waiver_targets(root: pathlib.Path) -> dict[str, set[str]]:
    value, errors = _load_waivers(root)
    if errors or value is None:
        return {}
    waivers = value.get("waivers")
    if not isinstance(waivers, list):
        return {}
    targets: dict[str, set[str]] = {
        standard_id: set() for standard_id in PROJECT_REQUIRED_IDS
    }
    for waiver in waivers:
        if not isinstance(waiver, dict):
            continue
        standard_id = waiver.get("standard_id")
        target = waiver.get("target")
        if (
            isinstance(standard_id, str)
            and standard_id in targets
            and isinstance(target, str)
        ):
            targets[standard_id].add(target)
    return targets


def _real_file(path: pathlib.Path) -> bool:
    return path.is_file() and not path.is_symlink()


def _rules_are_valid(root: pathlib.Path, config: dict[str, Any] | None) -> bool:
    if config is None or config.get("locale") not in {"en", "tr"}:
        return False
    path = root / ".divan" / "PROJECT_RULES.md"
    return _real_file(path) and path.read_bytes() == _rules(
        config["locale"]
    ).encode("utf-8")


def _direct_target_evidence(
    root: pathlib.Path,
    config: dict[str, Any] | None,
    audit_errors: list[str],
) -> dict[str, dict[str, bool]]:
    config_valid = config is not None and not any(
        ".divan/config.json" in error for error in audit_errors
    )
    waivers_valid = not _waiver_errors(root)
    readme = root / "README.md"
    workspace_rows = [] if config is None else config.get("workspaces")
    return {
        "DPS-001": {
            ".divan/config.json": config_valid,
            ".divan/PROJECT_RULES.md": _rules_are_valid(root, config),
            ".divan/waivers.json": waivers_valid,
        },
        "DPS-002": {".divan/config.json": config_valid},
        "DPS-003": {".divan/config.json": config_valid},
        "DPS-004": {
            ".divan/config.json": (
                config_valid
                and config is not None
                and config.get("autonomy") == "supervised"
            ),
            ".divan/PROJECT_RULES.md": _rules_are_valid(root, config),
        },
        "DPS-007": {
            ".divan/config.json": (
                config_valid
                and config is not None
                and not _missing_providers(config)
            )
        },
        "DPS-009": {".divan/waivers.json": waivers_valid},
        "DPS-010": {
            "README.md": (
                _real_file(readme)
                and bool(readme.read_bytes())
            )
        },
        "DPS-012": {
            ".divan/config.json": (
                config_valid
                and config is not None
                and "monorepo" in config.get("project_types", [])
                and isinstance(workspace_rows, list)
                and bool(workspace_rows)
            )
        },
    }


def _effective_phase(verification: dict[str, Any]) -> str | None:
    state = verification.get("state")
    if state == "FAILED":
        return None
    if state == "BLOCKED":
        resume_from = verification.get("resume_from")
        return resume_from if resume_from in PHASE_RANK else None
    return state if state in PHASE_RANK else None


def _named_evidence(evidence: list[str], names: tuple[str, ...]) -> bool:
    lowered = [pathlib.PurePosixPath(item).name.casefold() for item in evidence]
    return all(any(name in filename for filename in lowered) for name in names)


def _receipt_claim_status(
    standard_id: str,
    verifications: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    failed = False
    passed = False
    blocked = False
    errors: list[str] = []
    for verification in verifications:
        if not verification.get("ok"):
            continue
        results = verification.get("results")
        if not isinstance(results, dict):
            continue
        result = results.get(standard_id)
        if not isinstance(result, dict):
            continue
        claimed = result.get("status")
        if claimed == "FAIL":
            failed = True
            continue
        if claimed == "BLOCKED":
            blocked = True
            continue
        final_phase = _effective_phase(verification)
        result_phases = verification.get("result_phases")
        phase = (
            result_phases.get(standard_id)
            if isinstance(result_phases, dict)
            else None
        )
        required = RECEIPT_PHASES[standard_id]
        raw_evidence = result.get("evidence")
        evidence = (
            raw_evidence
            if isinstance(raw_evidence, list)
            and all(isinstance(item, str) for item in raw_evidence)
            else []
        )
        valid_evidence = bool(evidence)
        if standard_id == "DPS-006" and valid_evidence:
            valid_evidence = _named_evidence(evidence, ("verif",))
        elif standard_id == "DPS-007" and valid_evidence:
            valid_evidence = _named_evidence(evidence, ("provider",))
        elif standard_id == "DPS-011" and valid_evidence:
            valid_evidence = _named_evidence(
                evidence, ("seo", "accessibility", "preview")
            )
        if (
            phase in PHASE_RANK
            and final_phase is not None
            and PHASE_RANK[phase] >= PHASE_RANK[required]
            and PHASE_RANK[final_phase] >= PHASE_RANK[required]
            and valid_evidence
        ):
            passed = True
            continue
        goal_id = verification.get("goal_id") or "unknown-goal"
        errors.append(
            f"{goal_id}: {standard_id} PASS claim lacks required phase or evidence"
        )
    if failed:
        return "FAIL", errors
    if errors:
        return "FAIL", errors
    if passed:
        return "PASS", errors
    if blocked:
        return "BLOCKED", errors
    return "BLOCKED", errors


def _standard_status(
    standard_id: str,
    targets: dict[str, bool],
    waived: set[str],
    receipt_status: str | None,
) -> str:
    required = STANDARD_TARGETS[standard_id]
    for target in required:
        if target in waived:
            continue
        if target == ".divan/evidence" or target == ".divan/specs":
            if receipt_status != "PASS":
                return receipt_status or "BLOCKED"
        elif not targets.get(target, False):
            if standard_id == "DPS-007" and target == ".divan/config.json":
                return "BLOCKED"
            return "FAIL"
    return "PASS"


def verify_project(project: pathlib.Path | str) -> dict[str, Any]:
    """Report applicable DPS checks without executing detected project code."""
    root = pathlib.Path(project).resolve()
    audit = audit_project(root)
    config, _ = _load_config(root)
    project_types = [] if config is None else config.get("project_types", [])
    if not isinstance(project_types, list):
        project_types = []
    verifications, receipt_errors = _receipt_evidence(root)
    waived = _valid_waiver_targets(root)
    direct = _direct_target_evidence(root, config, audit["errors"])
    checks = []
    claim_errors: list[str] = []
    for standard_id, applies_to in STANDARD_APPLICABILITY.items():
        if not set(project_types).intersection(applies_to):
            status = "NOT_APPLICABLE"
        else:
            receipt_status = None
            if standard_id in RECEIPT_PHASES:
                receipt_status, standard_errors = _receipt_claim_status(
                    standard_id, verifications
                )
                claim_errors.extend(standard_errors)
            status = _standard_status(
                standard_id,
                direct.get(standard_id, {}),
                waived.get(standard_id, set()),
                receipt_status,
            )
        row: dict[str, Any] = {"id": standard_id, "status": status}
        waived_targets = sorted(waived.get(standard_id, set()))
        if waived_targets:
            row["waived_targets"] = waived_targets
        checks.append(row)
    direct_errors = []
    for row in checks:
        if row["status"] != "FAIL" or row["id"] in RECEIPT_PHASES:
            continue
        missing = [
            target
            for target in STANDARD_TARGETS[row["id"]]
            if target not in waived.get(row["id"], set())
            and not direct.get(row["id"], {}).get(target, False)
        ]
        if missing:
            direct_errors.append(
                f"{row['id']} required evidence is unavailable: "
                + ", ".join(missing)
            )
    errors = [
        *audit["errors"],
        *receipt_errors,
        *claim_errors,
        *direct_errors,
    ]
    applicable = [
        item["status"]
        for item in checks
        if item["status"] != "NOT_APPLICABLE"
    ]
    if errors or "FAIL" in applicable:
        status = "FAIL"
    elif (
        audit["missing_providers"]
        or not applicable
        or "BLOCKED" in applicable
    ):
        status = "BLOCKED"
    else:
        status = "PASS"
    return {
        **audit,
        "status": status,
        "errors": errors,
        "standards": checks,
        "receipts": verifications,
    }
