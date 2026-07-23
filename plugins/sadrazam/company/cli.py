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

import engine  # noqa: E402

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


def _write_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


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
        rendered = ", ".join(item) if isinstance(item, list) else str(item)
        print(f"{labels[key]}: {rendered}")


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
    return parser


def _execute(options: argparse.Namespace) -> dict[str, Any]:
    contracts = engine.load_contracts(DIRECTORY)
    if options.command == "inspect":
        return engine.inspect_project(options.project, contracts)
    if options.command == "plan":
        return engine.plan_intent(options.intent, options.project, contracts)
    if options.command == "impact":
        return engine.calculate_impact(options.paths, contracts)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
