"""Host CLI argument and JSON-shape adapters for Divan plugins."""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
from collections.abc import Callable
from typing import Any


def marketplace_list_command(host: str) -> list[str]:
    return [host, "plugin", "marketplace", "list", "--json"]


def plugin_list_command(host: str) -> list[str]:
    return [host, "plugin", "list", "--json"]


def marketplace_rows(host: str, value: Any) -> dict[str, dict[str, Any]]:
    return _row_index(_host_rows(host, value, "marketplaces"), "name")


def plugin_rows(host: str, value: Any) -> dict[str, dict[str, Any]]:
    return _row_index(_host_rows(host, value, "installed"), "id" if host == "claude" else "pluginId")


def _host_rows(host: str, value: Any, key: str) -> Any:
    if host == "claude":
        return value if isinstance(value, list) else []
    return value.get(key, []) if isinstance(value, dict) else []


def _row_index(rows: Any, key: str) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        return {}
    return {
        row[key]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get(key), str)
    }


def add_marketplace_command(host: str, source: str, ref: str) -> list[str]:
    local_source = pathlib.Path(source).expanduser().exists()
    if host == "claude":
        target = source if local_source else f"{source}#{ref}"
        return ["claude", "plugin", "marketplace", "add", target]
    command = ["codex", "plugin", "marketplace", "add", source]
    if not local_source:
        command.extend(["--ref", ref])
    return [*command, "--json"]


def install_command(host: str, package: str) -> list[str]:
    selector = f"{package}@divan"
    if host == "claude":
        return ["claude", "plugin", "install", selector, "--scope", "user"]
    return ["codex", "plugin", "add", selector, "--json"]


def remove_plugin_command(host: str, selector: str) -> list[str]:
    if host == "claude":
        return ["claude", "plugin", "uninstall", selector, "--scope", "user", "--yes"]
    return ["codex", "plugin", "remove", selector, "--json"]


def remove_marketplace_command(host: str) -> list[str]:
    command = [host, "plugin", "marketplace", "remove", "divan"]
    return [*command, "--json"] if host == "codex" else command


def marketplace_root(host: str, row: dict[str, Any]) -> str | None:
    key = "installLocation" if host == "claude" else "root"
    value = row.get(key)
    return value if isinstance(value, str) and value else None


def marketplace_source(row: dict[str, Any]) -> str | None:
    for key in ("url",):
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    source = row.get("source")
    if source == "directory":
        path = row.get("path")
        return path if isinstance(path, str) and path else None
    if isinstance(source, str) and source:
        return source
    origin = row.get("marketplaceSource")
    if isinstance(origin, dict):
        value = origin.get("source")
        if isinstance(value, str) and value:
            return value
    return None


def marketplace_ref(row: dict[str, Any]) -> str | None:
    value = row.get("ref")
    return value if isinstance(value, str) and value else None


def plugin_provenance_valid(host: str, row: dict[str, Any]) -> bool:
    if host == "claude":
        return row.get("scope") == "user"
    return (
        row.get("installed") is True and row.get("marketplaceName") == "divan"
    )


def plugin_install_path(host: str, row: dict[str, Any]) -> str | None:
    source = row.get("source")
    value = row.get("installPath") if host == "claude" else source.get("path") if isinstance(source, dict) else None
    return value if isinstance(value, str) and value else None


def native_plugin_install_path(
    host: str,
    row: dict[str, Any],
    marketplace_root: pathlib.Path,
    package: str,
    version: str,
    source: str | None = None,
) -> pathlib.Path | None:
    value = plugin_install_path(host, row)
    return native_install_path(host, value, marketplace_root, package, version, source)


def native_install_path(
    host: str,
    value: str | None,
    marketplace_root: pathlib.Path,
    package: str,
    version: str,
    source: str | None = None,
) -> pathlib.Path | None:
    if not value:
        return None
    actual = pathlib.Path(value).expanduser().resolve()
    if host == "claude":
        root = marketplace_root.expanduser().resolve()
        if root.name == "divan" and root.parent.name == "marketplaces":
            plugins_root = root.parent.parent
            if plugins_root.name != "plugins" or plugins_root.parent.name != ".claude":
                return None
        else:
            local = pathlib.Path(source).expanduser() if source else None
            if local is None or not local.exists() or local.resolve() != root:
                return None
            config = pathlib.Path(
                os.environ.get("CLAUDE_CONFIG_DIR", pathlib.Path.home() / ".claude")
            ).expanduser().resolve()
            plugins_root = config / "plugins"
        expected = plugins_root / "cache" / "divan" / package / version
        return actual if actual == expected.resolve() else None
    expected = (marketplace_root / "plugins" / package).resolve()
    return actual if actual == expected else None


Runner = Callable[[list[str]], Any]
Normalizer = Callable[[str], str]


def _doctor_json(runner: Runner, command: list[str]) -> tuple[Any | None, str | None, bool]:
    result = runner(command)
    if result.returncode:
        detail = (result.stderr or result.stdout or "unknown CLI error").strip()
        return None, detail, result.returncode == 127
    try:
        return json.loads(result.stdout), None, False
    except json.JSONDecodeError as exc:
        return None, str(exc), False


def _doctor_command(runner: Runner, command: list[str]) -> tuple[str | None, str | None]:
    result = runner(command)
    if result.returncode:
        return None, (result.stderr or result.stdout or "unknown CLI error").strip()
    return result.stdout.strip(), None


def _marketplace_issues(
    host: str,
    row: dict[str, Any],
    options: Any,
    runner: Runner,
    normalize: Normalizer,
) -> list[str]:
    issues: list[str] = []
    root = marketplace_root(host, row)
    if root is None:
        return ["marketplace root"]
    local_source = pathlib.Path(options.source).expanduser()
    if local_source.exists():
        return _local_marketplace_issues(root, options, runner)
    source = marketplace_source(row)
    if source is None or normalize(source) != normalize(options.source):
        issues.append("marketplace source")
    remote, remote_error = _doctor_command(
        runner, ["git", "-C", root, "remote", "get-url", "origin"]
    )
    if remote_error or remote is None or normalize(remote) != normalize(options.source):
        if "marketplace source" not in issues:
            issues.append("marketplace source")
    reference = marketplace_ref(row)
    if reference is None:
        ref_command = ["git", "-C", root, "rev-parse", "HEAD"]
        if not re.fullmatch(r"[0-9a-f]{40}", options.ref):
            ref_command = ["git", "-C", root, "describe", "--tags", "--exact-match"]
        reference, ref_error = _doctor_command(runner, ref_command)
        if ref_error:
            reference = None
    if reference != options.ref:
        issues.append("marketplace ref")
    return issues


def _local_marketplace_issues(root: str, options: Any, runner: Runner) -> list[str]:
    source_head, source_error = _doctor_command(
        runner, ["git", "-C", options.source, "rev-parse", "HEAD"]
    )
    installed_head, installed_error = _doctor_command(
        runner, ["git", "-C", root, "rev-parse", "HEAD"]
    )
    if source_error or installed_error or source_head != options.ref or installed_head != options.ref:
        return ["marketplace ref"]
    return []


def _plugin_issues(
    host: str,
    marketplace_present: bool,
    rows: dict[str, dict[str, Any]],
    expected: dict[str, dict[str, Any]],
) -> list[str]:
    selectors = {f"{package}@divan" for package in expected}
    installed = set(rows) & selectors
    if not marketplace_present:
        return ["orphaned packages"] if installed else ["divan marketplace missing"]
    issues: list[str] = []
    for package, contract in expected.items():
        selector = f"{package}@divan"
        row = rows.get(selector)
        if row is None:
            issues.append(f"{selector} missing")
            continue
        if row.get("version") != contract["version"]:
            issues.append(f"{selector} version")
        if row.get("enabled") is not True:
            issues.append(f"{selector} disabled")
        if not plugin_provenance_valid(host, row):
            issues.append(f"{selector} source")
    return issues


def _doctor_host(
    host: str,
    options: Any,
    expected: dict[str, dict[str, Any]],
    runner: Runner,
    normalize: Normalizer,
) -> dict[str, Any]:
    marketplaces_value, error, unavailable = _doctor_json(
        runner, marketplace_list_command(host)
    )
    if error:
        status = "unavailable" if unavailable else "attention"
        issue = "CLI unavailable" if unavailable else f"marketplace list: {error}"
        return {"status": status, "issues": [issue]}
    plugins_value, error, unavailable = _doctor_json(runner, plugin_list_command(host))
    if error:
        status = "unavailable" if unavailable else "attention"
        issue = "CLI unavailable" if unavailable else f"plugin list: {error}"
        return {"status": status, "issues": [issue]}
    marketplaces = marketplace_rows(host, marketplaces_value)
    plugins = plugin_rows(host, plugins_value)
    marketplace = marketplaces.get("divan")
    issues = _plugin_issues(host, marketplace is not None, plugins, expected)
    if marketplace is not None:
        issues.extend(_marketplace_issues(host, marketplace, options, runner, normalize))
    return {"status": "healthy" if not issues else "attention", "issues": issues}


def _unfinished_transaction(state_dir: pathlib.Path) -> pathlib.Path | None:
    if not state_dir.is_dir():
        return None
    for path in sorted(state_dir.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(record, dict) and record.get("status") in {
            "in-progress",
            "recovering",
            "rollback-incomplete",
        }:
            return path
    return None


def _next_command(options: Any) -> str:
    command = [
        "python",
        "scripts/kur-hostlar.py",
        "--host",
        options.host,
        "--source",
        options.source,
        "--ref",
        options.ref,
    ]
    return subprocess.list2cmdline(command)


def doctor(
    options: Any,
    *,
    runner: Runner,
    expected: dict[str, dict[str, Any]],
    normalize: Normalizer,
    hosts: tuple[str, ...],
) -> dict[str, Any]:
    """Inspect host state through read-only CLI queries."""
    results = {
        host: _doctor_host(host, options, expected, runner, normalize) for host in hosts
    }
    issues = [issue for result in results.values() for issue in result["issues"]]
    transaction = _unfinished_transaction(options.state_dir)
    if transaction is not None:
        issues.append("unfinished transaction")
    statuses = {result["status"] for result in results.values()}
    status = "unavailable" if "unavailable" in statuses else "attention" if issues else "healthy"
    next_command = _next_command(options)
    if transaction is not None:
        next_command = subprocess.list2cmdline(
            ["python", "scripts/kur-hostlar.py", "--rollback-transaction", str(transaction)]
        )
    return {
        "status": status,
        "ref": options.ref,
        "hosts": results,
        "issues": issues,
        "next_command": next_command,
    }


def print_doctor(record: dict[str, Any], json_output: bool) -> None:
    if json_output:
        print(json.dumps(record, ensure_ascii=False))
        return
    for host, result in record["hosts"].items():
        suffix = "" if not result["issues"] else " - " + "; ".join(result["issues"])
        print(f"{host}: {result['status']}{suffix}")
    host_issues = {issue for result in record["hosts"].values() for issue in result["issues"]}
    aggregate = [issue for issue in record["issues"] if issue not in host_issues]
    if aggregate:
        print(f"STATUS: {record['status']} - {'; '.join(aggregate)}")
    print(f"NEXT: {record['next_command']}")
