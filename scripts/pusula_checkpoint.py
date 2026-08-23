#!/usr/bin/env python3
"""CLI for sealing, validating, and rendering Pusula continuity capsules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from scripts import pusula_checkpoint_core as core
except ModuleNotFoundError:  # Direct execution: python scripts/pusula_checkpoint.py
    import pusula_checkpoint_core as core


def _command_seal(args: argparse.Namespace) -> int:
    sealed = core.seal_capsule(core.load_capsule(args.input))
    text = json.dumps(sealed, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    core.atomic_write(args.output, text)
    print(sealed["digest"])
    return 0


def _command_validate(args: argparse.Namespace) -> int:
    capsule = core.validate_capsule(core.load_capsule(args.path))
    print(
        json.dumps(
            {
                "status": "valid",
                "checkpoint_percent": capsule["checkpoint_percent"],
                "digest": capsule["digest"],
            },
            sort_keys=True,
        )
    )
    return 0


def _command_render(args: argparse.Namespace) -> int:
    rendered = core.render_markdown(core.load_capsule(args.path))
    if args.output is None:
        sys.stdout.write(rendered)
    else:
        core.atomic_write(args.output, rendered)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    seal_parser = subparsers.add_parser("seal", help="normalize and seal a draft capsule")
    seal_parser.add_argument("input", type=Path)
    seal_parser.add_argument("output", type=Path)
    seal_parser.set_defaults(func=_command_seal)

    validate_parser = subparsers.add_parser("validate", help="validate a sealed capsule")
    validate_parser.add_argument("path", type=Path)
    validate_parser.set_defaults(func=_command_validate)

    render_parser = subparsers.add_parser("render", help="render a compact Markdown resume view")
    render_parser.add_argument("path", type=Path)
    render_parser.add_argument("--output", type=Path)
    render_parser.set_defaults(func=_command_render)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return int(args.func(args))
    except core.CapsuleError as exc:
        print(f"pusula-checkpoint: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
