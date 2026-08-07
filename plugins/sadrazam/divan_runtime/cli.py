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

from divan_runtime import (  # noqa: E402,F401
    adoption,
    adoption_proof,
    cli_dispatch,
    cli_parser,
    engine,
    engine_registry,
    goal_archive,
    goals,
    governance,
    kernel,
    local_server,
    project_lifecycle,
    project_os,
    receipts,
    seyir_state,
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
        "next": "Next",
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
        "next": "Sıradaki",
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
    if value.get("command") == "engines validate":
        print(
            f"Engine registry: {value.get('status')} "
            f"({value.get('engine_count', 0)} engines, "
            f"{value.get('error_count', 0)} errors, "
            f"{value.get('warning_count', 0)} warnings)"
        )
        for error in value.get("errors", []):
            print(f"- {error['code']} {error['path']}: {error['message']}")
        return
    if value.get("kind") == "adoption-proof-preview":
        _write_proof_preview(value, language)
        return
    if value.get("kind") == "adoption-proof-result":
        _write_proof_result(value, language)
        return
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
        continuation = _safe_output(execution.get("continuation"), "continuation")
        task = continuation.get("task") if isinstance(continuation, dict) else None
        if isinstance(task, dict):
            sys.stdout.write(
                f"{labels['next']}: {task.get('id')} / "
                f"{task.get('stage')} / {task.get('owner_role')}\n")


def _write_proof_preview(value: dict[str, Any], language: str) -> None:
    project = value["project"]
    goal = value["goal"]
    if language == "tr":
        print("Divan neyi kanıtlayacak?")
        print(
            "Proje: Divan'dan ayrı gerçek proje · "
            f"{project['workspace_count']} çalışma alanı"
        )
        print(f"Hedef: {goal['id']} · {goal['state']}")
        print("Çalışacak kontroller:")
        for check in value["checks"]:
            seconds = int(check["timeout_ms"]) // 1000
            command = " ".join(check["command"])
            print(
                f"- {check['workspace']} · {command} · "
                f"en fazla {seconds} saniye"
            )
        print("Henüz hiçbir dosya yazılmadı.")
        print("Başlatmak için:")
    else:
        print("What will Divan prove?")
        print(
            "Project: real project distinct from Divan · "
            f"{project['workspace_count']} workspaces"
        )
        print(f"Goal: {goal['id']} · {goal['state']}")
        print("Checks to run:")
        for check in value["checks"]:
            seconds = int(check["timeout_ms"]) // 1000
            command = " ".join(check["command"])
            print(
                f"- {check['workspace']} · {command} · "
                f"up to {seconds} seconds"
            )
        print("No file has been written yet.")
        print("To start:")
    print(value["next_command"])


def _write_proof_result(value: dict[str, Any], language: str) -> None:
    if value.get("status") == "passed":
        if language == "tr":
            print("Temiz-proje kanıtı geçti.")
            print(f"Kontroller: {value.get('checks_passed', 0)} geçti.")
            print(f"Makbuz: {value.get('receipt_status')}")
        else:
            print("Clean-room proof passed.")
            print(f"Checks: {value.get('checks_passed', 0)} passed.")
            print(f"Receipt: {value.get('receipt_status')}")
        for path in value.get("files", []):
            print(f"- {path}")
        return
    reason = value.get("reason", "bounded proof did not pass")
    if language == "tr":
        print(f"Temiz-proje kanıtı tamamlanmadı: {reason}")
    else:
        print(f"Clean-room proof did not complete: {reason}")


def _proof_preview_result(
    plan: dict[str, Any], host: str, operator_role: str
) -> dict[str, Any]:
    checks = [
        {
            "id": row["id"],
            "class": row["class"],
            "runner": row["runner"],
            "name": row["name"],
            "workspace": row["workspace"],
            "command": list(row["argv"]),
            "timeout_ms": row["timeout_ms"],
        }
        for row in plan["checks"]
    ]
    goal = {
        "id": plan["goal"]["id"],
        "state": plan["goal"]["state"],
        "target": plan["goal"]["target"],
    }
    command = (
        "python divan-project.pyz adoption prove --project . "
        f"--goal {goal['id']} --host {host} "
        f"--operator-role {operator_role} --execute"
    )
    return {
        "schema_version": 1,
        "kind": "adoption-proof-preview",
        "status": "ready",
        "proof_id": plan["proof_id"],
        "summary": (
            f"Divan can prove this goal with {len(checks)} bounded checks."
        ),
        "divan": plan["divan"],
        "host_probe": {
            "command": list(plan["host_probe"]["argv"]),
            "status": "planned",
        },
        "operator": {"role": operator_role},
        "environment": plan["environment"],
        "project": {
            "classification": "external",
            "types": plan["project"]["types"],
            "workspace_count": plan["project"]["workspace_count"],
        },
        "goal": goal,
        "checks": checks,
        "writes": plan["writes"],
        "next_command": command,
    }


def _result_exit_code(
    result: dict[str, Any], explicit_exit_code: Any
) -> int:
    if explicit_exit_code is not None:
        return int(explicit_exit_code)
    if result.get("ok") is False or result.get("status") in {
        "FAIL",
        "BLOCKED",
        "blocked",
        "failed",
        "failed-checks",
        "cancelled",
        "invalid",
        "evidence-pending",
        "unavailable",
    }:
        return 1
    return 0


def _parser() -> argparse.ArgumentParser:
    return cli_parser.build_parser()


def _execute(
    options: argparse.Namespace,
    authority: dict[str, Any] | None = None,
) -> dict[str, Any]:
    read_only = cli_dispatch.read_only_result(options)
    if read_only is not None:
        return read_only
    if options.command == "engines":
        return cli_dispatch.execute_engines(options, authority)
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
        return cli_dispatch.execute_project(options)
    if options.command == "audit":
        return project_os.audit_project(options.project)
    if options.command == "verify":
        return project_os.verify_project(options.project)
    if options.command == "goal":
        return cli_dispatch.execute_goal(options)
    if options.command == "receipt":
        return receipts.verify_receipt(options.path)
    if options.command == "adoption":
        return cli_dispatch.execute_adoption(options, _proof_preview_result)
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


def _serve_status(options: argparse.Namespace) -> int:
    try:
        return local_server.serve(
            options.project,
            options.lang,
            options.open_browser,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    options = _parser().parse_args(argv)
    if options.command == "status":
        return _serve_status(options)
    try:
        authority = cli_dispatch.mutation_authority(options)
        result = _execute(options, authority)
        if authority is not None and "authority" not in result:
            result = {**result, "authority": authority}
        explicit_exit_code = result.pop("_exit_code", None)
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
            "engines",
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
    return _result_exit_code(result, explicit_exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
