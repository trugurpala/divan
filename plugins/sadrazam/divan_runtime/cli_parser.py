"""Argument-parser construction for the Divan runtime CLI."""

from __future__ import annotations

import argparse
import pathlib
from typing import Any

from . import adoption
from . import release as release_api

DESCRIPTION = "Portable command-line interface for the Divan runtime."
AUTHORITY_ACTORS = (
    "owner",
    "mandate",
    "orchestrator",
    "council",
    "specialist",
    "provider",
)


def _common_output(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="write stable JSON")
    parser.add_argument("--lang", choices=("en", "tr"), default="en")


def _mutation_control(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--actor",
        choices=AUTHORITY_ACTORS,
        default="owner",
        help="local governance actor; only owner may use --execute",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="explicitly authorize the planned mutation as owner/Hükümdar",
    )


def _add_adoption_parser(commands: Any) -> None:
    command = commands.add_parser(
        "adoption", help="export or verify privacy-bounded adoption receipts"
    )
    subcommands = command.add_subparsers(
        dest="adoption_command", required=True
    )
    export = subcommands.add_parser("export")
    export.add_argument(
        "--project", type=pathlib.Path, default=pathlib.Path.cwd()
    )
    export.add_argument("--goal", required=True)
    export.add_argument(
        "--host", choices=tuple(sorted(adoption.HOSTS)), required=True
    )
    export.add_argument("--host-version", required=True)
    export.add_argument(
        "--submitter",
        choices=tuple(sorted(adoption.SUBMITTERS)),
        default="maintainer",
    )
    export.add_argument("--markdown", action="store_true")
    _common_output(export)
    verify = subcommands.add_parser("verify")
    verify.add_argument("path", type=pathlib.Path)
    _common_output(verify)


def _add_runtime_contract_parsers(commands: Any) -> None:
    validate = commands.add_parser(
        "validate", help="validate Divan runtime contracts"
    )
    _common_output(validate)
    architecture = commands.add_parser(
        "architecture", help="show the Divan module and authority contracts"
    )
    _common_output(architecture)


def _add_discovery_parsers(commands: Any) -> None:
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
    _add_runtime_contract_parsers(commands)


def _add_init_parser(commands: Any) -> None:
    init = commands.add_parser("init", help="plan or initialize the project contract")
    init.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
    init.add_argument("--profile", choices=("standard", "strict"), default="standard")
    init.add_argument("--locale", choices=("auto", "en", "tr"), default="auto")
    init.add_argument("--host", choices=("agents", "claude", "both"), default="both")
    init.add_argument("--with-ci", action="store_true")
    init.add_argument("--expected-url")
    _mutation_control(init)
    _common_output(init)


def _add_project_parsers(commands: Any) -> None:
    project = commands.add_parser("project", help="manage project-contract lifecycle")
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
        _mutation_control(lifecycle_command)
        _common_output(lifecycle_command)


def _add_read_only_project_parsers(commands: Any) -> None:
    for name in ("audit", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
        _common_output(command)


def _add_goal_parsers(commands: Any) -> None:
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
    _mutation_control(goal_start)
    _common_output(goal_start)
    goal_status = goal_commands.add_parser("status")
    goal_status.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
    goal_status.add_argument("--goal")
    _common_output(goal_status)
    goal_resume = goal_commands.add_parser("resume")
    goal_resume.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
    goal_resume.add_argument("--goal", required=True)
    _mutation_control(goal_resume)
    _common_output(goal_resume)
    archive = goal_commands.add_parser("archive")
    archive.add_argument(
        "--project", type=pathlib.Path, default=pathlib.Path.cwd()
    )
    archive.add_argument("--goal", required=True)
    archive.add_argument("--recorded-on")
    _mutation_control(archive)
    _common_output(archive)


def _add_receipt_parser(commands: Any) -> None:
    receipt = commands.add_parser("receipt", help="verify project receipts")
    receipt_commands = receipt.add_subparsers(dest="receipt_command", required=True)
    receipt_verify = receipt_commands.add_parser("verify")
    receipt_verify.add_argument("path", type=pathlib.Path)
    _common_output(receipt_verify)


def _add_release_parser(commands: Any) -> None:
    release = commands.add_parser("release", help="plan or record a project release")
    release.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
    release.add_argument("--goal", required=True)
    release.add_argument(
        "--provider",
        choices=tuple(release_api.RELEASE_OPERATIONS),
        required=True,
    )
    _mutation_control(release)
    _common_output(release)


def build_parser() -> argparse.ArgumentParser:
    """Build the stable public Divan command parser."""
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    commands = parser.add_subparsers(dest="command", required=True)
    _add_discovery_parsers(commands)
    _add_init_parser(commands)
    _add_project_parsers(commands)
    _add_read_only_project_parsers(commands)
    _add_goal_parsers(commands)
    _add_receipt_parser(commands)
    _add_adoption_parser(commands)
    _add_release_parser(commands)
    return parser
