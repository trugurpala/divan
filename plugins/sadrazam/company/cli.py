#!/usr/bin/env python3
"""Portable command-line interface for Divan Company OS."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

DIRECTORY = pathlib.Path(__file__).resolve().parent
if str(DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DIRECTORY))

import adoption  # noqa: E402
import engine  # noqa: E402
import goal_archive  # noqa: E402
import goals  # noqa: E402
import project_lifecycle  # noqa: E402
import project_os  # noqa: E402
import providers  # noqa: E402
import receipts  # noqa: E402

TEXT = {
    "en": {
        "project": "Project",
        "frameworks": "Frameworks",
        "workflow": "Workflow",
        "roles": "Roles",
        "packages": "Packages",
        "effects": "Effects",
        "checks": "Checks",
    },
    "tr": {
        "project": "Proje",
        "frameworks": "Frameworkler",
        "workflow": "İş akışı",
        "roles": "Roller",
        "packages": "Paketler",
        "effects": "Etkiler",
        "checks": "Kontroller",
    },
}

SENSITIVE_OUTPUT_KEYS = ("authorization", "credential", "password", "secret", "token")


def _safe_output(value: Any, key: str = "") -> Any:
    """Return a recursively redacted, JSON-compatible public CLI value."""
    if any(marker in key.casefold() for marker in SENSITIVE_OUTPUT_KEYS):
        return "[REDACTED_SECRET]"
    if isinstance(value, dict):
        return {
            str(item_key): _safe_output(item, str(item_key))
            for item_key, item in value.items()
        }
    if isinstance(value, list):
        return [_safe_output(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_output(item) for item in value]
    if isinstance(value, str):
        return receipts.redact_text(value)
    return value


def _write_json(value: dict[str, Any]) -> None:
    safe_value = _safe_output(value)
    serialized = json.dumps(safe_value, ensure_ascii=False, sort_keys=True)
    sys.stdout.write(serialized + "\n")


def _write_human(value: dict[str, Any], language: str) -> None:
    labels = TEXT[language]
    for key in (
        "project",
        "frameworks",
        "workflow",
        "roles",
        "packages",
        "effects",
        "checks",
    ):
        if key not in value:
            continue
        item = value[key]
        safe_item = _safe_output(item, key)
        rendered = (
            ", ".join(str(part) for part in safe_item)
            if isinstance(safe_item, list)
            else str(safe_item)
        )
        sys.stdout.write(f"{labels[key]}: {rendered}\n")


def _common_output(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="write stable JSON")
    parser.add_argument("--lang", choices=("en", "tr"), default="en")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    inspect = commands.add_parser("inspect", help="detect project frameworks")
    inspect.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
    _common_output(inspect)

    plan = commands.add_parser("plan", help="route an intent to a qualified team")
    plan.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
    plan.add_argument("--intent", required=True)
    _common_output(plan)

    impact = commands.add_parser("impact", help="calculate transitive change impact")
    impact.add_argument("paths", nargs="+")
    _common_output(impact)

    validate = commands.add_parser("validate", help="validate Company OS contracts")
    _common_output(validate)

    init = commands.add_parser("init", help="plan or initialize Project OS")
    init.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
    init.add_argument("--profile", choices=("standard", "strict"), default="standard")
    init.add_argument("--locale", choices=("auto", "en", "tr"), default="auto")
    init.add_argument("--host", choices=("agents", "claude", "both"), default="both")
    init.add_argument("--with-ci", action="store_true")
    init.add_argument("--expected-url")
    init.add_argument("--execute", action="store_true")
    _common_output(init)

    project = commands.add_parser("project", help="manage Project OS lifecycle")
    project_commands = project.add_subparsers(
        dest="project_command", required=True
    )
    project_status = project_commands.add_parser(
        "status", help="inspect ownership and drift without mutation"
    )
    project_status.add_argument(
        "--project", type=pathlib.Path, default=pathlib.Path.cwd()
    )
    _common_output(project_status)
    for name in ("update", "repair"):
        lifecycle_command = project_commands.add_parser(name)
        lifecycle_command.add_argument(
            "--project", type=pathlib.Path, default=pathlib.Path.cwd()
        )
        lifecycle_command.add_argument("--execute", action="store_true")
        _common_output(lifecycle_command)

    for name in ("audit", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
        _common_output(command)

    goal = commands.add_parser("goal", help="manage deterministic project goals")
    goal_commands = goal.add_subparsers(dest="goal_command", required=True)
    goal_start = goal_commands.add_parser("start")
    goal_start.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
    goal_start.add_argument("--intent", required=True)
    goal_start.add_argument(
        "--target",
        choices=("verified", "previewed", "released", "observed"),
        default="verified",
    )
    goal_start.add_argument("--execute", action="store_true")
    _common_output(goal_start)
    goal_status = goal_commands.add_parser("status")
    goal_status.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
    goal_status.add_argument("--goal")
    _common_output(goal_status)
    goal_resume = goal_commands.add_parser("resume")
    goal_resume.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
    goal_resume.add_argument("--goal", required=True)
    goal_resume.add_argument("--execute", action="store_true")
    _common_output(goal_resume)
    archive = goal_commands.add_parser("archive")
    archive.add_argument(
        "--project", type=pathlib.Path, default=pathlib.Path.cwd()
    )
    archive.add_argument("--goal", required=True)
    archive.add_argument("--execute", action="store_true")
    _common_output(archive)

    receipt = commands.add_parser("receipt", help="verify project receipts")
    receipt_commands = receipt.add_subparsers(dest="receipt_command", required=True)
    receipt_verify = receipt_commands.add_parser("verify")
    receipt_verify.add_argument("path", type=pathlib.Path)
    _common_output(receipt_verify)

    adoption_command = commands.add_parser(
        "adoption", help="export or verify privacy-bounded adoption receipts"
    )
    adoption_commands = adoption_command.add_subparsers(
        dest="adoption_command", required=True
    )
    adoption_export = adoption_commands.add_parser("export")
    adoption_export.add_argument(
        "--project", type=pathlib.Path, default=pathlib.Path.cwd()
    )
    adoption_export.add_argument("--goal", required=True)
    adoption_export.add_argument(
        "--host", choices=tuple(sorted(adoption.HOSTS)), required=True
    )
    adoption_export.add_argument("--host-version", required=True)
    adoption_export.add_argument(
        "--submitter",
        choices=tuple(sorted(adoption.SUBMITTERS)),
        default="maintainer",
    )
    _common_output(adoption_export)
    adoption_verify = adoption_commands.add_parser("verify")
    adoption_verify.add_argument("path", type=pathlib.Path)
    _common_output(adoption_verify)

    release = commands.add_parser("release", help="plan or record a project release")
    release.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
    release.add_argument("--goal", required=True)
    release.add_argument(
        "--provider",
        choices=tuple(providers.RELEASE_OPERATIONS),
        required=True,
    )
    release.add_argument("--execute", action="store_true")
    _common_output(release)
    return parser


def _execute(options: argparse.Namespace) -> dict[str, Any]:
    if options.command == "inspect":
        contracts = engine.load_contracts(DIRECTORY)
        return engine.inspect_project(options.project, contracts)
    if options.command == "plan":
        contracts = engine.load_contracts(DIRECTORY)
        return engine.plan_intent(options.intent, options.project, contracts)
    if options.command == "impact":
        contracts = engine.load_contracts(DIRECTORY)
        return engine.calculate_impact(options.paths, contracts)
    if options.command == "init":
        plan = project_os.build_init_plan(
            options.project,
            options.profile,
            options.locale,
            options.host,
            options.with_ci,
            expected_url=options.expected_url,
        )
        return project_os.apply_init_plan(plan) if options.execute else plan
    if options.command == "project":
        if options.project_command == "status":
            return project_lifecycle.project_status(options.project)
        if options.project_command == "update":
            plan = project_lifecycle.build_update_plan(options.project)
            return (
                project_lifecycle.apply_update_plan(plan)
                if options.execute and plan.get("status") == "PLANNED"
                else plan
            )
        plan = project_lifecycle.build_repair_plan(options.project)
        return (
            project_lifecycle.apply_repair_plan(plan)
            if options.execute and plan.get("status") == "PLANNED"
            else plan
        )
    if options.command == "audit":
        return project_os.audit_project(options.project)
    if options.command == "verify":
        return project_os.verify_project(options.project)
    if options.command == "goal":
        if options.goal_command == "start":
            return goals.start_goal(
                options.project, options.intent, options.target, options.execute
            )
        if options.goal_command == "status":
            return goals.goal_status(options.project, options.goal)
        if options.goal_command == "archive":
            plan = goal_archive.build_archive_plan(
                options.project, options.goal
            )
            return (
                goal_archive.apply_archive_plan(plan)
                if options.execute and plan.get("status") == "PLANNED"
                else plan
            )
        return goals.resume_goal(options.project, options.goal, options.execute)
    if options.command == "receipt":
        return receipts.verify_receipt(options.path)
    if options.command == "adoption":
        if options.adoption_command == "verify":
            return adoption.verify_adoption(options.path)
        return adoption.export_adoption(
            options.project,
            options.goal,
            options.host,
            options.host_version,
            options.submitter,
        )
    if options.command == "release":
        return providers.release_project(
            options.project,
            options.goal,
            options.provider,
            options.execute,
        )
    contracts = engine.load_contracts(DIRECTORY)
    return {
        "status": "valid",
        "schema_version": 1,
        "role_count": len(contracts.roles),
        "workflow_count": len(contracts.workflows),
        "framework_count": len(contracts.frameworks),
        "impact_rule_count": len(contracts.impact_rules),
    }


def main(argv: list[str] | None = None) -> int:
    options = _parser().parse_args(argv)
    try:
        result = _execute(options)
    except ValueError as exc:
        if options.json:
            _write_json(
                {"errors": [str(exc)], "ok": False, "schema_version": 1}
            )
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if options.json:
        _write_json(result)
    else:
        _write_human(result, options.lang)
        if options.command == "validate":
            print(
                "Company OS contracts are valid."
                if options.lang == "en"
                else "Company OS sözleşmeleri geçerli."
            )
        elif options.command in {
            "init",
            "audit",
            "verify",
            "goal",
            "receipt",
            "release",
            "project",
            "adoption",
        }:
            fallback = "valid" if result.get("ok") else "invalid"
            print(f"Status: {result.get('status', fallback)}")
    if result.get("ok") is False or result.get("status") in {"FAIL", "BLOCKED"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
