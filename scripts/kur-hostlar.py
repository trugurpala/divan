#!/usr/bin/env python3
"""Divan'i Claude ve Codex'e resmi plugin CLI'lariyla islemesel olarak kur."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

PACKAGES = ("sadrazam", "core-pack", "ui-pack", "react-pack", "zanaat-pack")
Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


class InstallError(RuntimeError):
    """Raised after a failed installation has been rolled back."""


class Options:
    def __init__(
        self,
        *,
        host: str,
        source: str,
        ref: str,
        execute: bool,
        migrate_legacy: bool,
        state_dir: pathlib.Path,
    ) -> None:
        self.host = host
        self.source = source
        self.ref = ref
        self.execute = execute
        self.migrate_legacy = migrate_legacy
        self.state_dir = state_dir


def _subprocess_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    resolved = shutil.which(command[0])
    if resolved is None:
        return subprocess.CompletedProcess(command, 127, "", f"executable not found: {command[0]}")
    actual = [resolved, *command[1:]]
    if os.name == "nt" and pathlib.Path(resolved).suffix.lower() in {".cmd", ".bat"}:
        actual = ["cmd.exe", "/d", "/s", "/c", resolved, *command[1:]]
    return subprocess.run(
        actual,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _run(runner: Runner, command: list[str]) -> str:
    result = runner(command)
    if result.returncode:
        detail = (result.stderr or result.stdout or "unknown CLI error").strip()
        raise InstallError(f"command failed ({result.returncode}): {' '.join(command)}: {detail}")
    return result.stdout


def _read_json(runner: Runner, command: list[str]) -> Any:
    output = _run(runner, command)
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise InstallError(f"host CLI returned invalid JSON for {' '.join(command)}: {exc}") from exc


def _marketplaces(host: str, runner: Runner) -> set[str]:
    return set(_marketplace_rows(host, runner))


def _marketplace_rows(host: str, runner: Runner) -> dict[str, dict[str, Any]]:
    value = _read_json(runner, [host, "plugin", "marketplace", "list", "--json"])
    rows = value if host == "claude" else value.get("marketplaces", [])
    return {
        row["name"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }


def _plugins(host: str, runner: Runner) -> set[str]:
    return set(_plugin_rows(host, runner))


def _plugin_rows(host: str, runner: Runner) -> dict[str, dict[str, Any]]:
    value = _read_json(runner, [host, "plugin", "list", "--json"])
    rows = value if host == "claude" else value.get("installed", [])
    key = "id" if host == "claude" else "pluginId"
    return {
        row[key]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get(key), str)
    }


def _expected_packages(root: pathlib.Path) -> dict[str, dict[str, Any]]:
    path = root / ".agents" / "plugins" / "marketplace.json"
    try:
        marketplace = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallError(f"cannot read expected native catalog: {path}") from exc
    expected: dict[str, dict[str, Any]] = {}
    for plugin in marketplace.get("plugins", []):
        if not isinstance(plugin, dict):
            continue
        name, version, source = plugin.get("name"), plugin.get("version"), plugin.get("source")
        if not isinstance(name, str) or not isinstance(version, str) or not isinstance(source, dict):
            continue
        relative = source.get("path")
        if not isinstance(relative, str):
            continue
        skill_names = sorted(
            path.parent.name
            for path in (root / relative / "skills").glob("*/SKILL.md")
        )
        expected[name] = {"version": version, "skills": skill_names}
    if set(expected) != set(PACKAGES):
        raise InstallError("native catalog does not define the expected five packages")
    if len({skill for row in expected.values() for skill in row["skills"]}) != 41:
        raise InstallError("native catalog does not define exactly 41 unique skills")
    return expected


def _normalize_source(source: str) -> str:
    value = source.strip().replace("\\", "/").removesuffix("/").removesuffix(".git")
    if value.startswith("git@github.com:"):
        value = "github.com/" + value.removeprefix("git@github.com:")
    value = re.sub(r"^https?://", "", value, flags=re.I)
    if value.count("/") == 1:
        value = "github.com/" + value
    return value.lower()


def _verify_marketplace(
    host: str,
    row: dict[str, Any],
    options: Options,
    runner: Runner,
) -> None:
    root_value = row.get("installLocation") if host == "claude" else row.get("root")
    if not isinstance(root_value, str) or not root_value:
        raise InstallError(f"{host}: divan marketplace root is missing")
    if pathlib.Path(options.source).expanduser().exists():
        requested_head = _run(
            runner, ["git", "-C", options.source, "rev-parse", "HEAD"]
        ).strip()
        if requested_head != options.ref:
            raise InstallError(f"{host}: local source HEAD does not match requested ref")
    else:
        origin = _run(
            runner, ["git", "-C", root_value, "remote", "get-url", "origin"]
        ).strip()
        if _normalize_source(origin) != _normalize_source(options.source):
            raise InstallError(f"{host}: marketplace source does not match requested source")
    if re.fullmatch(r"[0-9a-f]{40}", options.ref):
        actual_ref = _run(runner, ["git", "-C", root_value, "rev-parse", "HEAD"]).strip()
    else:
        actual_ref = _run(
            runner,
            ["git", "-C", root_value, "describe", "--tags", "--exact-match"],
        ).strip()
    if actual_ref != options.ref:
        raise InstallError(f"{host}: marketplace ref mismatch: {actual_ref} != {options.ref}")


def _verify_host(
    host: str,
    options: Options,
    expected: dict[str, dict[str, Any]],
    runner: Runner,
) -> dict[str, Any]:
    marketplace = _marketplace_rows(host, runner).get("divan")
    if marketplace is None:
        raise InstallError(f"{host}: divan marketplace is missing after install")
    _verify_marketplace(host, marketplace, options, runner)
    rows = _plugin_rows(host, runner)
    discovered: set[str] = set()
    errors: list[str] = []
    for package, contract in expected.items():
        selector = f"{package}@divan"
        row = rows.get(selector)
        if row is None:
            errors.append(f"{selector} missing")
            continue
        if row.get("version") != contract["version"]:
            errors.append(f"{selector} version")
        if row.get("enabled") is not True:
            errors.append(f"{selector} enabled")
        if host == "codex" and (
            row.get("installed") is not True or row.get("marketplaceName") != "divan"
        ):
            errors.append(f"{selector} source")
        supplied_skills = row.get("skills")
        if isinstance(supplied_skills, list) and all(
            isinstance(item, str) for item in supplied_skills
        ):
            package_skills = set(supplied_skills)
        else:
            source = row.get("installPath") if host == "claude" else row.get("source", {}).get("path")
            if not isinstance(source, str):
                errors.append(f"{selector} install path")
                continue
            package_skills = {
                path.parent.name
                for path in pathlib.Path(source).glob("skills/*/SKILL.md")
            }
        if package_skills != set(contract["skills"]):
            errors.append(f"{selector} skill inventory")
        discovered.update(package_skills)
    if len(discovered) != 41:
        errors.append(f"discoverable skills {len(discovered)}/41")
    if errors:
        raise InstallError(f"{host} verification failed: {', '.join(errors)}")
    return {
        "package_count": len(expected),
        "skill_count": len(discovered),
        "packages": {
            package: {"version": contract["version"], "enabled": True}
            for package, contract in expected.items()
        },
        "all_enabled": True,
        "source": options.source,
        "ref": options.ref,
    }


def _hosts(selection: str) -> tuple[str, ...]:
    return ("claude", "codex") if selection == "both" else (selection,)


def _add_marketplace_command(host: str, source: str, ref: str) -> list[str]:
    local_source = pathlib.Path(source).expanduser().exists()
    if host == "claude":
        return [
            "claude",
            "plugin",
            "marketplace",
            "add",
            source if local_source else f"{source}#{ref}",
        ]
    command = ["codex", "plugin", "marketplace", "add", source]
    if not local_source:
        command.extend(["--ref", ref])
    return [*command, "--json"]


def _install_command(host: str, package: str) -> list[str]:
    selector = f"{package}@divan"
    if host == "claude":
        return ["claude", "plugin", "install", selector, "--scope", "user"]
    return ["codex", "plugin", "add", selector, "--json"]


def _remove_plugin_command(host: str, selector: str) -> list[str]:
    if host == "claude":
        return ["claude", "plugin", "uninstall", selector, "--scope", "user", "--yes"]
    return ["codex", "plugin", "remove", selector, "--json"]


def _remove_marketplace_command(host: str) -> list[str]:
    return [host, "plugin", "marketplace", "remove", "divan"] + (
        ["--json"] if host == "codex" else []
    )


def _planned_commands(options: Options) -> list[list[str]]:
    commands: list[list[str]] = []
    for host in _hosts(options.host):
        commands.append(_add_marketplace_command(host, options.source, options.ref))
        commands.extend(_install_command(host, package) for package in PACKAGES)
    return commands


def _persist_record(path: pathlib.Path, record: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _begin_mutation(
    path: pathlib.Path, record: dict[str, Any], pending: dict[str, str]
) -> None:
    record["pending"] = pending
    _persist_record(path, record)


def _finish_mutation(path: pathlib.Path, record: dict[str, Any]) -> None:
    record["pending"] = None
    _persist_record(path, record)


def _migrate_legacy(
    root: pathlib.Path, runner: Runner, journal_path: pathlib.Path
) -> dict[str, Any] | None:
    state_dir = pathlib.Path(os.environ.get("DIVAN_STATE_DIR", pathlib.Path.home() / ".codex"))
    pointer = state_dir / "divan-install-latest"
    manifest: pathlib.Path | None = None
    if pointer.is_file():
        candidate = pathlib.Path(pointer.read_text(encoding="utf-8").strip())
        manifest = candidate if candidate.is_file() else None
    if manifest is None:
        candidates = sorted(state_dir.glob("divan-install-*.tsv"), key=lambda path: path.stat().st_mtime)
        manifest = candidates[-1] if candidates else None
    if manifest is None:
        return None
    command = [
        sys.executable,
        str(root / "scripts" / "legacy_state.py"),
        "migrate",
        "--manifest",
        str(manifest),
        "--skills-dir",
        str(pathlib.Path(os.environ.get("CODEX_SKILLS_DIR", pathlib.Path.home() / ".codex" / "skills"))),
        "--state-dir",
        str(state_dir),
        "--journal",
        str(journal_path),
    ]
    output = _run(runner, command)
    try:
        result = json.loads(output)
    except json.JSONDecodeError as exc:
        raise InstallError("legacy migration returned invalid JSON") from exc
    return {"command": command, "result": result}


def _load_recoverable_transaction(transaction_path: pathlib.Path) -> dict[str, Any]:
    try:
        record = json.loads(transaction_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallError(f"transaction journal is unreadable: {transaction_path}") from exc
    if not isinstance(record, dict) or record.get("schema") != 1:
        raise InstallError("unsupported transaction journal schema")
    if record.get("status") not in {
        "in-progress",
        "rollback-incomplete",
        "recovering",
        "verified",
    }:
        raise InstallError(f"transaction is not recoverable: {record.get('status')}")

    before = record.get("before")
    created = record.get("created")
    if not isinstance(before, dict) or not isinstance(created, dict):
        raise InstallError("transaction journal lacks ownership state")
    return record


def _legacy_journal(record: dict[str, Any]) -> tuple[bool, str | None]:
    pending = record.get("pending")
    legacy_journal_text: str | None = None
    legacy_migration_recorded = False
    if isinstance(pending, dict) and pending.get("kind") in {
        "legacy-migration",
        "recovery-legacy",
    }:
        legacy_migration_recorded = True
        pending_journal = pending.get("journal")
        if isinstance(pending_journal, str):
            legacy_journal_text = pending_journal
    if legacy_journal_text is None:
        completed_migration = record.get("legacy_migration")
        if isinstance(completed_migration, dict):
            migration_result = completed_migration.get("result")
            if isinstance(migration_result, dict):
                legacy_migration_recorded = True
                completed_journal = migration_result.get("journal")
                if isinstance(completed_journal, str):
                    legacy_journal_text = completed_journal
    return legacy_migration_recorded, legacy_journal_text


def _recover_recorded_legacy(
    transaction_path: pathlib.Path,
    record: dict[str, Any],
    runner: Runner,
) -> None:
    recorded, journal_text = _legacy_journal(record)
    if not recorded:
        return
    if journal_text is None:
        raise InstallError("recorded legacy migration lacks a journal path")
    journal = pathlib.Path(journal_text)
    if not journal.is_file():
        raise InstallError(f"recorded legacy journal is missing: {journal}")
    _begin_mutation(
        transaction_path,
        record,
        {"kind": "recovery-legacy", "host": "codex", "journal": journal_text},
    )
    _run(
        runner,
        [
            sys.executable,
            str(pathlib.Path(__file__).with_name("legacy_state.py")),
            "recover",
            "--journal",
            journal_text,
        ],
    )
    _finish_mutation(transaction_path, record)


def _created_rows(record: dict[str, Any]) -> tuple[list[Any], list[Any]]:
    created = record["created"]
    plugin_rows = list(created.get("plugins", []))
    marketplace_hosts = list(created.get("marketplaces", []))
    pending = record.get("pending")
    if isinstance(pending, dict) and pending.get("kind") in {
        "plugin",
        "rollback-plugin",
        "recovery-plugin",
    }:
        plugin_rows.append({"host": pending.get("host"), "id": pending.get("id")})
    elif isinstance(pending, dict) and pending.get("kind") in {
        "marketplace",
        "rollback-marketplace",
        "recovery-marketplace",
    }:
        marketplace_hosts.append(pending.get("host"))
    return plugin_rows, marketplace_hosts


def _owned_plugins(plugin_rows: list[Any], before: dict[str, Any]) -> list[dict[str, str]]:
    owned_plugins: list[dict[str, str]] = []
    for row in plugin_rows:
        if not isinstance(row, dict):
            raise InstallError("transaction contains an invalid plugin entry")
        host, selector = row.get("host"), row.get("id")
        if host not in {"claude", "codex"} or not isinstance(selector, str):
            raise InstallError("transaction contains an invalid plugin identity")
        if not selector.endswith("@divan"):
            raise InstallError("transaction refuses to remove a non-Divan plugin")
        host_before = before.get(host, {})
        if selector in host_before.get("plugins", []):
            raise InstallError(f"transaction does not own pre-existing plugin: {selector}")
        if row not in owned_plugins:
            owned_plugins.append({"host": host, "id": selector})
    return owned_plugins


def _owned_marketplaces(marketplace_hosts: list[Any], before: dict[str, Any]) -> list[str]:
    owned_marketplaces: list[str] = []
    for host in marketplace_hosts:
        if host not in {"claude", "codex"}:
            raise InstallError("transaction contains an invalid marketplace host")
        host_before = before.get(host, {})
        if "divan" in host_before.get("marketplaces", []):
            raise InstallError(f"transaction does not own pre-existing marketplace: {host}")
        if host not in owned_marketplaces:
            owned_marketplaces.append(host)
    return owned_marketplaces


def _recover_owned_entries(
    transaction_path: pathlib.Path,
    record: dict[str, Any],
    owned_plugins: list[dict[str, str]],
    owned_marketplaces: list[str],
    runner: Runner,
) -> None:
    for plugin in reversed(owned_plugins):
        if plugin["id"] not in _plugins(plugin["host"], runner):
            continue
        _begin_mutation(transaction_path, record, {"kind": "recovery-plugin", **plugin})
        _run(runner, _remove_plugin_command(plugin["host"], plugin["id"]))
        _finish_mutation(transaction_path, record)
    for host in reversed(owned_marketplaces):
        if "divan" not in _marketplaces(host, runner):
            continue
        _begin_mutation(
            transaction_path,
            record,
            {"kind": "recovery-marketplace", "host": host},
        )
        _run(runner, _remove_marketplace_command(host))
        _finish_mutation(transaction_path, record)


def rollback_transaction(
    transaction_path: pathlib.Path,
    *,
    runner: Runner = _subprocess_runner,
) -> dict[str, Any]:
    """Recover an interrupted transaction using only entries absent from pre-state."""
    record = _load_recoverable_transaction(transaction_path)
    before = record["before"]
    _recover_recorded_legacy(transaction_path, record, runner)
    plugin_rows, marketplace_hosts = _created_rows(record)
    owned_plugins = _owned_plugins(plugin_rows, before)
    owned_marketplaces = _owned_marketplaces(marketplace_hosts, before)

    record["status"] = "recovering"
    _persist_record(transaction_path, record)
    _recover_owned_entries(
        transaction_path,
        record,
        owned_plugins,
        owned_marketplaces,
        runner,
    )
    record["status"] = "recovered"
    record["pending"] = None
    record["recovered_at"] = datetime.now(UTC).isoformat()
    _persist_record(transaction_path, record)
    return record


def install(
    options: Options,
    *,
    runner: Runner = _subprocess_runner,
    root: pathlib.Path | None = None,
) -> dict[str, Any]:
    """Plan or execute installation and return the auditable transaction record."""
    if options.migrate_legacy and "codex" not in _hosts(options.host):
        raise InstallError("legacy Codex migration requires --host codex or --host both")
    repository = root or pathlib.Path(__file__).resolve().parent.parent
    expected_packages = _expected_packages(repository)
    planned = _planned_commands(options)
    record: dict[str, Any] = {
        "schema": 1,
        "status": "dry-run",
        "source": options.source,
        "ref": options.ref,
        "hosts": list(_hosts(options.host)),
        "planned_commands": planned,
        "created": {"marketplaces": [], "plugins": []},
        "verified": {},
    }
    if not options.execute:
        return record

    options.state_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    transaction_path = options.state_dir / f"install-{stamp}-{uuid.uuid4().hex[:8]}.json"
    record["transaction_path"] = str(transaction_path)
    record["started_at"] = datetime.now(UTC).isoformat()
    record["before"] = {}
    record["status"] = "in-progress"
    record["pending"] = None
    _persist_record(transaction_path, record)

    try:
        for host in _hosts(options.host):
            before_marketplaces = _marketplaces(host, runner)
            before_plugins = _plugins(host, runner)
            record["before"][host] = {
                "marketplaces": sorted(before_marketplaces),
                "plugins": sorted(before_plugins),
            }
            _persist_record(transaction_path, record)
            if "divan" in before_marketplaces:
                raise InstallError(
                    f"{host}: existing divan marketplace source/ref cannot be proven; "
                    "no existing entry was changed"
                )
            orphaned_divan_plugins = sorted(
                plugin for plugin in before_plugins if plugin.endswith("@divan")
            )
            if orphaned_divan_plugins:
                raise InstallError(
                    f"{host}: existing divan plugin source/ref cannot be proven: "
                    f"{', '.join(orphaned_divan_plugins)}; no existing entry was changed"
                )
            _begin_mutation(
                transaction_path,
                record,
                {"kind": "marketplace", "host": host},
            )
            _run(runner, _add_marketplace_command(host, options.source, options.ref))
            record["created"]["marketplaces"].append(host)
            _finish_mutation(transaction_path, record)
            for package in PACKAGES:
                selector = f"{package}@divan"
                if selector in before_plugins:
                    continue
                _begin_mutation(
                    transaction_path,
                    record,
                    {"kind": "plugin", "host": host, "id": selector},
                )
                _run(runner, _install_command(host, package))
                record["created"]["plugins"].append({"host": host, "id": selector})
                _finish_mutation(transaction_path, record)

            record["verified"][host] = _verify_host(
                host, options, expected_packages, runner
            )
            _persist_record(transaction_path, record)

        record["status"] = "verified"
        if options.migrate_legacy:
            legacy_journal = options.state_dir / f"legacy-{stamp}-{uuid.uuid4().hex[:8]}.json"
            _begin_mutation(
                transaction_path,
                record,
                {
                    "kind": "legacy-migration",
                    "host": "codex",
                    "journal": str(legacy_journal),
                },
            )
            record["legacy_migration"] = _migrate_legacy(
                repository, runner, legacy_journal
            )
            _finish_mutation(transaction_path, record)
        record["finished_at"] = datetime.now(UTC).isoformat()
        _persist_record(transaction_path, record)
        return record
    except BaseException as exc:
        try:
            recovered = rollback_transaction(transaction_path, runner=runner)
        except BaseException as rollback_exc:
            try:
                current = json.loads(transaction_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                current = record
            current["status"] = "rollback-incomplete"
            current["error"] = str(exc)
            current["rollback_errors"] = [str(rollback_exc)]
            current["finished_at"] = datetime.now(UTC).isoformat()
            _persist_record(transaction_path, current)
            raise InstallError(
                f"{exc}; rollback incomplete: {rollback_exc}; transaction: {transaction_path}"
            ) from exc
        recovered["status"] = "rolled-back"
        recovered["error"] = str(exc)
        recovered["rollback_errors"] = []
        recovered["finished_at"] = datetime.now(UTC).isoformat()
        _persist_record(transaction_path, recovered)
        raise InstallError(f"{exc}; transaction: {transaction_path}") from exc


def _parse_options(argv: list[str] | None = None) -> Options:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("claude", "codex", "both"), default="both")
    parser.add_argument("--source", default="https://github.com/trugurpala/divan.git")
    parser.add_argument("--ref", required=True, help="immutable release tag or commit")
    parser.add_argument("--execute", action="store_true", help="apply the printed plan")
    parser.add_argument("--migrate-legacy", action="store_true")
    parser.add_argument(
        "--state-dir",
        type=pathlib.Path,
        default=pathlib.Path.home() / ".divan" / "transactions",
    )
    parsed = parser.parse_args(argv)
    if parsed.migrate_legacy and not parsed.execute:
        parser.error("--migrate-legacy requires --execute")
    if parsed.migrate_legacy and parsed.host == "claude":
        parser.error("--migrate-legacy requires --host codex or --host both")
    if re.fullmatch(r"[0-9a-f]{40}", parsed.ref) and not pathlib.Path(
        parsed.source
    ).expanduser().exists():
        parser.error("a full commit ref requires a local --source; remote Claude sources need a tag")
    return Options(
        host=parsed.host,
        source=parsed.source,
        ref=parsed.ref,
        execute=parsed.execute,
        migrate_legacy=parsed.migrate_legacy,
        state_dir=parsed.state_dir,
    )


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--rollback-transaction" in arguments:
        parser = argparse.ArgumentParser(description="Recover an interrupted Divan install")
        parser.add_argument("--rollback-transaction", type=pathlib.Path, required=True)
        recovery = parser.parse_args(arguments)
        try:
            record = rollback_transaction(recovery.rollback_transaction)
        except InstallError as exc:
            print(f"HATA: {exc}", file=sys.stderr)
            return 1
        print(f"RECOVERED - transaction: {record['transaction_path']}")
        return 0
    options = _parse_options(arguments)
    try:
        record = install(options)
    except InstallError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1
    if record["status"] == "dry-run":
        print("DRY-RUN - no host state changed. Add --execute to apply:")
        for command in record["planned_commands"]:
            print("  " + subprocess.list2cmdline(command))
    else:
        print(f"VERIFIED - transaction: {record['transaction_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
