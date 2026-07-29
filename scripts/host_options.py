"""Host lifecycle option parsing and validation."""

from __future__ import annotations

import argparse
import pathlib
import re


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
        profile: str = "native",
    ) -> None:
        self.host = host
        self.source = source
        self.ref = ref
        self.execute = execute
        self.migrate_legacy = migrate_legacy
        self.state_dir = state_dir
        self.doctor, self.json_output = doctor, json_output
        self.upgrade = upgrade
        self.profile = profile
        self.hosts = ("claude", "codex") if host == "both" else (host,)


def parse_options(argv: list[str] | None = None) -> Options:
    parser = argparse.ArgumentParser(
        description="Manage Divan host installation, updates, diagnosis, and recovery."
    )
    parser.add_argument("--host", choices=("claude", "codex", "both"), default="both")
    parser.add_argument("--source", default="https://github.com/trugurpala/divan.git")
    parser.add_argument("--ref", required=True, help="immutable release tag or commit")
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument(
        "--doctor", action="store_true", help="inspect host state without changes"
    )
    operation.add_argument(
        "--upgrade", action="store_true", help="replace a proven Divan install"
    )
    parser.add_argument("--execute", action="store_true", help="apply the printed plan")
    parser.add_argument(
        "--profile",
        choices=("native", "auto"),
        default="native",
        help="native host install, or explicit Codex auto-selection",
    )
    parser.add_argument(
        "--json", action="store_true", help="write machine-readable doctor output"
    )
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
    if parsed.profile == "auto" and parsed.host != "codex":
        parser.error("--profile auto requires --host codex")
    if parsed.profile == "auto" and (parsed.doctor or parsed.upgrade):
        parser.error("--profile auto supports install only")
    if re.fullmatch(r"[0-9a-f]{40}", parsed.ref) and not pathlib.Path(
        parsed.source
    ).expanduser().exists():
        parser.error(
            "a full commit ref requires a local --source; remote Claude sources need a tag"
        )
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
        profile=parsed.profile,
    )
