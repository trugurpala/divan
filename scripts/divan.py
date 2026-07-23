#!/usr/bin/env python3
"""English canonical CLI for Divan Company OS and host lifecycle."""
from __future__ import annotations

import argparse
import importlib.util
import pathlib
import sys
from types import ModuleType

SCRIPTS = pathlib.Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import host_lifecycle  # noqa: E402

DEFAULT_SOURCE = "https://github.com/trugurpala/divan.git"
COMPANY_CLI = ROOT / "plugins" / "sadrazam" / "company" / "cli.py"


def _load_company_cli() -> ModuleType:
    spec = importlib.util.spec_from_file_location("divan_company_cli_runtime", COMPANY_CLI)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load installed Company OS")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _host_arguments(options: argparse.Namespace) -> list[str]:
    if options.command == "recover":
        return ["--rollback-transaction", str(options.transaction)]
    arguments = [
        "--host",
        options.host,
        "--source",
        options.source,
        "--ref",
        options.ref,
    ]
    if options.command == "doctor":
        arguments.append("--doctor")
        if options.json:
            arguments.append("--json")
    elif options.command == "update":
        arguments.append("--upgrade")
        if options.execute:
            arguments.append("--execute")
    elif options.execute:
        arguments.append("--execute")
    if options.command == "install" and options.migrate_legacy:
        arguments.append("--migrate-legacy")
    if options.command != "doctor" and options.state_dir is not None:
        arguments.extend(["--state-dir", str(options.state_dir)])
    return arguments


def _add_host_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", choices=("claude", "codex", "both"), default="both")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--ref", required=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "plan", "impact"):
        command = commands.add_parser(name)
        command.add_argument("company_args", nargs=argparse.REMAINDER)
    commands.add_parser("company-validate").add_argument(
        "company_args", nargs=argparse.REMAINDER
    )

    install = commands.add_parser("install", help="plan or install Divan on hosts")
    _add_host_common(install)
    install.add_argument("--execute", action="store_true")
    install.add_argument("--migrate-legacy", action="store_true")
    install.add_argument("--state-dir", type=pathlib.Path)

    update = commands.add_parser("update", help="plan or update a proven install")
    _add_host_common(update)
    update.add_argument("--execute", action="store_true")
    update.add_argument("--state-dir", type=pathlib.Path)

    doctor = commands.add_parser("doctor", help="inspect hosts without mutation")
    _add_host_common(doctor)
    doctor.add_argument("--json", action="store_true")

    recover = commands.add_parser("recover", help="recover an interrupted transaction")
    recover.add_argument("transaction", type=pathlib.Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] in {"inspect", "plan", "impact", "company-validate"}:
        command = "validate" if arguments[0] == "company-validate" else arguments[0]
        return _load_company_cli().main([command, *arguments[1:]])
    options = _parser().parse_args(arguments)
    return host_lifecycle.main(_host_arguments(options))


if __name__ == "__main__":
    raise SystemExit(main())
