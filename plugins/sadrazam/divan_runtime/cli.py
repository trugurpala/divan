#!/usr/bin/env python3
"""Portable command-line interface for the Divan runtime."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

DIRECTORY = pathlib.Path(__file__).resolve().parent
PLUGIN_ROOT = DIRECTORY.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import (  # noqa: E402
    adoption,
    cli_parser,
    engine,
    goal_archive,
    goals,
    governance,
    kernel,
    local_server,
    project_lifecycle,
    project_os,
    receipts,
)
from divan_runtime import (  # noqa: E402
    release as release_api,
)

TEXT = {
    "en": {
        "project": "Project",
        "frameworks": "Frameworks",
        "workflow": "Workflow",
        "roles": "Roles",
        "packages": "Packages",
        "effects": "Effects",
        "checks": "Checks",
        "execution": "Execution",
    },
    "tr": {
        "project": "Proje",
        "frameworks": "Frameworkler",
        "workflow": "İş akışı",
        "roles": "Roller",
        "packages": "Paketler",
        "effects": "Etkiler",
        "checks": "Kontroller",
        "execution": "Yürütme",
    },
}

SENSITIVE_OUTPUT_KEYS = ("authorization", "credential", "password", "secret", "token")
SAFE_NUMERIC_OUTPUT_KEYS = {
    "at_context_tokens",
    "estimated_working_set_tokens",
    "handoff_at_tokens",
    "reserve_tokens",
    "total_tokens",
    "usable_tokens",
}


def _safe_output(value: Any, key: str = "") -> Any:
    """Return a recursively redacted, JSON-compatible public CLI value."""
    if any(marker in key.casefold() for marker in SENSITIVE_OUTPUT_KEYS):
        if (
            key in SAFE_NUMERIC_OUTPUT_KEYS
            and isinstance(value, int)
            and not isinstance(value, bool)
        ):
            return value
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
    execution = value.get("execution_plan")
    if isinstance(execution, dict):
        orchestration = execution["orchestration"]
        complexity = execution["complexity"]
        model = execution["model_policy"]
        sys.stdout.write(
            f"{labels['execution']}: {complexity['level']} / "
            f"{orchestration['recommended_sefers']} sefer / "
            f"{orchestration['lane']} / {model['capability_class']}\n"
        )


def _parser() -> argparse.ArgumentParser:
    return cli_parser.build_parser()


def _read_only_result(options: argparse.Namespace) -> dict[str, Any] | None:
    if options.command == "inspect":
        contracts = engine.load_contracts(DIRECTORY)
        return engine.inspect_project(options.project, contracts)
    if options.command == "plan":
        contracts = engine.load_contracts(DIRECTORY)
        return engine.plan_intent(
            options.intent,
            options.project,
            contracts,
            options.target,
            host_profile=options.host_profile,
            context_window=options.context_window,
        )
    if options.command == "impact":
        contracts = engine.load_contracts(DIRECTORY)
        return engine.calculate_impact(options.paths, contracts)
    if options.command == "architecture":
        return kernel.load_architecture(DIRECTORY)
    return None


def _mutation_authority(options: argparse.Namespace) -> dict[str, Any] | None:
    if not getattr(options, "execute", False):
        return None
    excluded = {"actor", "execute", "json", "lang"}
    scope = {
        key: str(value) if isinstance(value, pathlib.Path) else value
        for key, value in vars(options).items()
        if key not in excluded and value is not None
    }
    operation = ".".join(
        str(value)
        for value in (
            options.command,
            getattr(options, "project_command", None),
            getattr(options, "goal_command", None),
        )
        if value is not None
    )
    return governance.authorize_mutation(
        options.actor,
        operation,
        scope,
        explicit_authority=True,
        directory=DIRECTORY,
    )


def _execute(options: argparse.Namespace) -> dict[str, Any]:
    read_only = _read_only_result(options)
    if read_only is not None:
        return read_only
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
                options.project,
                options.intent,
                options.target,
                options.execute,
                host_profile=options.host_profile,
                context_window=options.context_window,
            )
        if options.goal_command == "status":
            return goals.goal_status(options.project, options.goal)
        if options.goal_command == "archive":
            plan = goal_archive.build_archive_plan(
                options.project, options.goal, options.recorded_on
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
        return release_api.release_project(
            options.project,
            options.goal,
            options.provider,
            options.execute,
        )
    contracts = engine.load_contracts(DIRECTORY)
    architecture = kernel.load_architecture(DIRECTORY)
    return {
        "module_count": architecture["module_count"],
        "product": architecture["product"],
        "status": "valid",
        "schema_version": 1,
        "role_count": len(contracts.roles),
        "workflow_count": len(contracts.workflows),
        "framework_count": len(contracts.frameworks),
        "impact_rule_count": len(contracts.impact_rules),
    }


def main(argv: list[str] | None = None) -> int:
    options = _parser().parse_args(argv)
    if options.command == "status":
        try:
            return local_server.serve(
                options.project,
                options.lang,
                options.open_browser,
            )
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
    try:
        authority = _mutation_authority(options)
        result = _execute(options)
        if authority is not None:
            result = {**result, "authority": authority}
    except ValueError as exc:
        if options.json:
            _write_json(
                {"errors": [str(exc)], "ok": False, "schema_version": 1}
            )
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if options.command == "adoption" and options.adoption_command == "export":
        output_key = "markdown" if options.markdown else "json"
        sys.stdout.write(str(result[output_key]))
        return 0
    if options.json:
        _write_json(result)
    else:
        _write_human(result, options.lang)
        if options.command == "validate":
            print(
                "Divan runtime contracts are valid."
                if options.lang == "en"
                else "Divan çalışma zamanı sözleşmeleri geçerli."
            )
        elif options.command in {
            "architecture",
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
