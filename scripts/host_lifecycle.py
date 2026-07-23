#!/usr/bin/env python3
"""Manage Divan host installation, updates, diagnosis, and recovery."""
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

import host_adapters as _host_adapters
import host_controller as _host_controller
import host_install_journal as _host_install_journal
import host_journal as _host_journal
import host_transactions as _host_transactions
import host_upgrade as _host_upgrade

PACKAGES = ("sadrazam", "core-pack", "ui-pack", "react-pack", "zanaat-pack")
Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]
_add_marketplace_command = _host_adapters.add_marketplace_command
_install_command = _host_adapters.install_command
_remove_plugin_command = _host_adapters.remove_plugin_command
_remove_marketplace_command = _host_adapters.remove_marketplace_command
_persist_record = _host_transactions.persist_record
_begin_mutation = _host_transactions.begin_mutation
_finish_mutation = _host_transactions.finish_mutation
_load_recoverable_transaction = _host_transactions.load_recoverable_transaction
_created_rows = _host_transactions.schema1_created_rows
_owned_plugins = _host_transactions.schema1_owned_plugins
_owned_marketplaces = _host_transactions.schema1_owned_marketplaces


InstallError = _host_transactions.TransactionError


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
        doctor: bool = False,
        json_output: bool = False,
        upgrade: bool = False,
    ) -> None:
        self.host = host
        self.source = source
        self.ref = ref
        self.execute = execute
        self.migrate_legacy = migrate_legacy
        self.state_dir = state_dir
        self.doctor, self.json_output = doctor, json_output
        self.upgrade = upgrade
        self.hosts = ("claude", "codex") if host == "both" else (host,)


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
    return _host_adapters.marketplace_rows(
        host, _read_json(runner, _host_adapters.marketplace_list_command(host))
    )


def _plugins(host: str, runner: Runner) -> set[str]:
    return set(_plugin_rows(host, runner))


def _plugin_rows(host: str, runner: Runner) -> dict[str, dict[str, Any]]:
    return _host_adapters.plugin_rows(
        host, _read_json(runner, _host_adapters.plugin_list_command(host))
    )


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
    root_value = _host_adapters.marketplace_root(host, row)
    if root_value is None:
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
        if not _host_adapters.plugin_provenance_valid(host, row):
            errors.append(f"{selector} source")
        supplied_skills = row.get("skills")
        if isinstance(supplied_skills, list) and all(
            isinstance(item, str) for item in supplied_skills
        ):
            package_skills = set(supplied_skills)
        else:
            source = _host_adapters.plugin_install_path(host, row)
            if source is None:
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


def _planned_commands(options: Options) -> list[list[str]]:
    commands: list[list[str]] = []
    for host in _hosts(options.host):
        commands.append(_add_marketplace_command(host, options.source, options.ref))
        commands.extend(_install_command(host, package) for package in PACKAGES)
    return commands


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


def _legacy_journal(record: dict[str, Any]) -> tuple[bool, str | None]:
    pending = record.get("pending")
    recorded = isinstance(pending, dict) and pending.get("action") in {
        "legacy-migration", "recover-legacy",
    }
    journal = pending.get("journal") if isinstance(pending, dict) and recorded else None
    completed = record.get("legacy_migration")
    if not isinstance(journal, str) and isinstance(completed, dict):
        result = completed.get("result")
        if isinstance(result, dict):
            recorded = True
            journal = result.get("journal")
    return recorded, journal if isinstance(journal, str) else None


def _recover_recorded_legacy(
    transaction_path: pathlib.Path, record: dict[str, Any], runner: Runner
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
        _host_install_journal.intent("recovery", "recover-legacy", "codex", journal=journal_text),
    )
    command = [
        sys.executable,
        str(pathlib.Path(__file__).with_name("legacy_state.py")),
        "recover",
        "--journal",
        journal_text,
    ]
    _run(runner, command)
    _finish_mutation(transaction_path, record)


def _rollback_install_transaction(
    transaction_path: pathlib.Path,
    record: dict[str, Any],
    runner: Runner,
) -> dict[str, Any]:
    try:
        _host_install_journal.validate(record, transaction_path)
    except _host_install_journal.InstallJournalError as exc:
        raise InstallError(str(exc)) from exc
    _recover_recorded_legacy(transaction_path, record, runner)
    try:
        return _host_install_journal.recover_native(
            transaction_path, record, _install_io(runner)
        )
    except _host_install_journal.InstallJournalError as exc:
        raise InstallError(str(exc)) from exc


def _install_io(runner: Runner) -> _host_install_journal.InstallIO:
    return _host_install_journal.InstallIO(
        marketplace_rows=lambda host: _marketplace_rows(host, runner),
        plugin_rows=lambda host: _plugin_rows(host, runner),
        run=lambda command: _run(runner, command),
        normalize_source=_normalize_source,
    )


def rollback_transaction(
    transaction_path: pathlib.Path,
    *,
    runner: Runner = _subprocess_runner,
    _locked: bool = False,
) -> dict[str, Any]:
    """Recover an interrupted schema-1 install or schema-2 upgrade."""
    transaction_path = transaction_path.expanduser().resolve()
    if not _locked:
        try:
            with _host_journal.UpgradeLock(transaction_path.parent):
                return rollback_transaction(transaction_path, runner=runner, _locked=True)
        except _host_journal.JournalError as exc:
            raise InstallError(str(exc)) from exc
    record = _load_recoverable_transaction(transaction_path, _normalize_source)
    if record["schema"] == 1:
        return _rollback_install_transaction(transaction_path, record, runner)
    io = _host_transactions.RecoveryIO(
        marketplace_rows=lambda host: _marketplace_rows(host, runner),
        plugin_rows=lambda host: _plugin_rows(host, runner),
        normalize_source=_normalize_source,
        run=lambda command: _run(runner, command),
    )
    return _host_transactions.recover_upgrade(transaction_path, record, io)


def _validate_install_options(options: Options) -> None:
    if options.migrate_legacy and "codex" not in _hosts(options.host):
        raise InstallError("legacy Codex migration requires --host codex or --host both")


def _install_target(
    repository: pathlib.Path, expected_packages: dict[str, dict[str, str]], options: Options, runner: Runner
) -> tuple[_host_install_journal.InstallIO, dict[str, Any]]:
    install_io = _install_io(runner)
    versions = {package: row["version"] for package, row in expected_packages.items()}
    return install_io, _host_install_journal.target_evidence(
        repository, options.source, options.ref, versions, install_io)


@_host_controller.serialized(_normalize_source, InstallError)
def install(
    options: Options,
    *,
    runner: Runner = _subprocess_runner,
    root: pathlib.Path | None = None,
) -> dict[str, Any]:
    """Plan or execute installation and return the auditable transaction record."""
    _validate_install_options(options)
    repository = root or pathlib.Path(__file__).resolve().parent.parent
    expected_packages = _expected_packages(repository)
    record = _host_install_journal.new_record(
        options.source, options.ref, _hosts(options.host), _planned_commands(options)
    )
    if not options.execute:
        return record
    install_io, record["target"] = _install_target(
        repository, expected_packages, options, runner
    )
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
                _host_install_journal.intent("forward", "add-marketplace", host),
            )
            _run(runner, _add_marketplace_command(host, options.source, options.ref))
            record["created"]["marketplaces"].append(
                _host_install_journal.capture_marketplace(record, host, install_io)
            )
            _finish_mutation(transaction_path, record)
            for package in PACKAGES:
                selector = f"{package}@divan"
                if selector in before_plugins:
                    continue
                _begin_mutation(
                    transaction_path,
                    record,
                    _host_install_journal.intent("forward", "install-plugin", host, selector=selector),
                )
                _run(runner, _install_command(host, package))
                record["created"]["plugins"].append(
                    _host_install_journal.capture_plugin(
                        record, host, selector, install_io
                    )
                )
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
                _host_install_journal.intent("forward", "legacy-migration", "codex", journal=str(legacy_journal)),
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
            recovered = rollback_transaction(transaction_path, runner=runner, _locked=True)
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


def upgrade(
    options: Options,
    *,
    runner: Runner = _subprocess_runner,
    root: pathlib.Path | None = None,
) -> dict[str, Any]:
    """Plan or execute a provenance-gated, rollback-safe Divan upgrade."""
    repository = root or pathlib.Path(__file__).resolve().parent.parent
    expected = _expected_packages(repository)
    io = _host_upgrade.UpgradeIO(
        marketplace_rows=lambda host: _marketplace_rows(host, runner),
        plugin_rows=lambda host: _plugin_rows(host, runner),
        run=lambda command: _run(runner, command),
        rollback=lambda path: rollback_transaction(path, runner=runner, _locked=True),
        normalize_source=_normalize_source,
    )
    return _host_upgrade.upgrade(options, PACKAGES, expected, io, repository)


def doctor(
    options: Options,
    *,
    runner: Runner = _subprocess_runner,
    root: pathlib.Path | None = None,
) -> dict[str, Any]:
    expected = _expected_packages(root or pathlib.Path(__file__).resolve().parent.parent)
    result = _host_adapters.doctor(
        options,
        runner=runner,
        expected=expected,
        normalize=_normalize_source,
        hosts=_hosts(options.host),
    )
    return _host_journal.augment_doctor(result, options.state_dir, _normalize_source)


def _parse_options(argv: list[str] | None = None) -> Options:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("claude", "codex", "both"), default="both")
    parser.add_argument("--source", default="https://github.com/trugurpala/divan.git")
    parser.add_argument("--ref", required=True, help="immutable release tag or commit")
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--doctor", action="store_true", help="inspect host state without changes")
    operation.add_argument("--upgrade", action="store_true", help="replace a proven Divan install")
    parser.add_argument("--execute", action="store_true", help="apply the printed plan")
    parser.add_argument("--json", action="store_true", help="write machine-readable doctor output")
    parser.add_argument("--migrate-legacy", action="store_true")
    parser.add_argument(
        "--state-dir",
        type=pathlib.Path,
        default=pathlib.Path.home() / ".divan" / "transactions",
    )
    parsed = parser.parse_args(argv)
    if parsed.json and not parsed.doctor:
        parser.error("--json requires --doctor")
    if parsed.doctor and parsed.execute:
        parser.error("--doctor does not allow --execute")
    if parsed.migrate_legacy and not parsed.execute:
        parser.error("--migrate-legacy requires --execute")
    if parsed.migrate_legacy and parsed.upgrade:
        parser.error("--migrate-legacy does not allow --upgrade")
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
        doctor=parsed.doctor,
        json_output=parsed.json,
        upgrade=parsed.upgrade,
    )


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if any(
        argument == "--rollback-transaction"
        or argument.startswith("--rollback-transaction=")
        for argument in arguments
    ):
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
        if options.doctor:
            record = doctor(options)
        elif options.upgrade:
            record = upgrade(options)
        else:
            record = install(options)
    except InstallError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1
    if options.doctor:
        _host_adapters.print_doctor(record, options.json_output)
        return 0
    if record["status"] == "dry-run":
        print("DRY-RUN - no host state changed. Add --execute to apply:")
        for command in record["planned_commands"]:
            print("  " + subprocess.list2cmdline(command))
    elif record["status"] == "no-op":
        print("NO-OP - installed Divan already matches target.")
    else:
        print(f"VERIFIED - transaction: {record['transaction_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
