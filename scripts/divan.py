#!/usr/bin/env python3
"""Canonical CLI for the Divan runtime and host lifecycle."""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import pathlib
import sys
from collections.abc import Iterator
from types import ModuleType

SCRIPTS = pathlib.Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import bootstrap_contract  # noqa: E402
import host_lifecycle  # noqa: E402
import host_profiles  # noqa: E402

DEFAULT_SOURCE = "https://github.com/trugurpala/divan.git"
RUNTIME_CLI = PLUGIN_ROOT / "divan_runtime" / "cli.py"
RUNTIME_PACKAGE = RUNTIME_CLI.parent / "__init__.py"
DIVAN_COMMANDS = {
    "architecture",
    "inspect",
    "plan",
    "impact",
    "init",
    "audit",
    "verify",
    "goal",
    "receipt",
    "release",
    "status",
    "project",
    "adoption",
    "validate",
    "engines",
}


def _runtime_module_names() -> list[str]:
    return [
        name
        for name in sys.modules
        if name == "divan_runtime" or name.startswith("divan_runtime.")
    ]


def _load_source_module(
    name: str,
    path: pathlib.Path,
    *,
    package_directory: pathlib.Path | None = None,
) -> ModuleType:
    search_locations = (
        [str(package_directory)] if package_directory is not None else None
    )
    spec = importlib.util.spec_from_file_location(
        name,
        path,
        submodule_search_locations=search_locations,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the installed Divan runtime")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    if pathlib.Path(str(module.__file__)).resolve() != path.resolve():
        sys.modules.pop(name, None)
        raise RuntimeError("Divan runtime resolved outside the installed source")
    return module


@contextlib.contextmanager
def _load_runtime_cli() -> Iterator[ModuleType]:
    if not RUNTIME_CLI.is_file() or not RUNTIME_PACKAGE.is_file():
        raise RuntimeError("cannot load the installed Divan runtime")
    previous_path = list(sys.path)
    previous = {
        name: sys.modules[name]
        for name in _runtime_module_names()
    }
    for name in previous:
        sys.modules.pop(name, None)
    try:
        _load_source_module(
            "divan_runtime",
            RUNTIME_PACKAGE,
            package_directory=RUNTIME_PACKAGE.parent,
        )
        yield _load_source_module("divan_runtime.cli", RUNTIME_CLI)
    finally:
        for name in _runtime_module_names():
            sys.modules.pop(name, None)
        sys.modules.update(previous)
        sys.path[:] = previous_path


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
    if options.command == "install" and options.profile != "native":
        arguments.extend(["--profile", options.profile])
    if options.command != "doctor" and options.state_dir is not None:
        arguments.extend(["--state-dir", str(options.state_dir)])
    return arguments


def _bootstrap_identity() -> dict[str, str] | None:
    try:
        bundled = bootstrap_contract.load(ROOT)
    except bootstrap_contract.ContractError as error:
        raise RuntimeError("cannot read the bundled Divan identity") from error
    return bundled[0] if bundled is not None else None


def _add_host_common(parser: argparse.ArgumentParser) -> None:
    bundled = _bootstrap_identity()
    parser.add_argument("--host", choices=("claude", "codex", "both"), default="both")
    parser.add_argument(
        "--source",
        default=bundled["source_repository"] if bundled else DEFAULT_SOURCE,
    )
    parser.add_argument(
        "--ref",
        default=bundled["source_ref"] if bundled else None,
        required=bundled is None,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("architecture", "inspect", "plan", "impact", "validate"):
        command = commands.add_parser(name)
        command.add_argument("company_args", nargs=argparse.REMAINDER)
    commands.add_parser("company-validate").add_argument(
        "company_args", nargs=argparse.REMAINDER
    )

    install = commands.add_parser("install", help="plan or install Divan on hosts")
    _add_host_common(install)
    install.add_argument("--execute", action="store_true")
    install.add_argument("--migrate-legacy", action="store_true")
    install.add_argument("--profile", choices=("native", "auto"), default="native")
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
    commands.add_parser("_fallback-remove", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] in {*DIVAN_COMMANDS, "company-validate"}:
        command = "validate" if arguments[0] == "company-validate" else arguments[0]
        with _load_runtime_cli() as runtime_cli:
            return runtime_cli.main([command, *arguments[1:]])
    parser = _parser()
    options = parser.parse_args(arguments)
    if options.command == "_fallback-remove":
        return host_profiles.execute_fallback_remove(ROOT)
    bundled = _bootstrap_identity()
    if (
        bundled is not None
        and options.command != "recover"
        and (
            options.ref != bundled["source_ref"]
            or options.source != bundled["source_repository"]
        )
    ):
        parser.error(
            "this bootstrap can use only its bundled source and release "
            f"{bundled['source_ref']}"
        )
    return host_lifecycle.main(_host_arguments(options))


if __name__ == "__main__":
    raise SystemExit(main())
