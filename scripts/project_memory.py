#!/usr/bin/env python3
"""CLI for Divan's durable project memory."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

from project_memory_store import ProjectMemoryError, initialize
from project_memory_validation import validate_memory
from project_memory_workflow import (
    add_decision,
    add_lesson,
    add_task,
    block_task,
    checkpoint,
    complete_task,
    resume_summary,
    start_task,
    transition,
)


def _root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path.cwd())


def _execute(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--execute", action="store_true")


def _json(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true")


def _add_core_parsers(commands: argparse._SubParsersAction) -> None:
    init = commands.add_parser("init", help="plan or create .divan durable memory")
    _root(init)
    _execute(init)
    _json(init)
    init.add_argument("--name", required=True)
    init.add_argument("--goal", required=True)
    init.add_argument("--profile")
    init.add_argument("--source-repository")
    init.add_argument("--source-commit")
    init.add_argument("--deployment")

    validate = commands.add_parser("validate", help="validate durable project memory")
    _root(validate)
    _json(validate)

    resume = commands.add_parser("continue", help="show the exact durable resume point")
    _root(resume)
    _json(resume)


def _add_task_parsers(commands: argparse._SubParsersAction) -> None:
    task_add = commands.add_parser("task-add", help="plan or add a vertical-slice task")
    _root(task_add)
    _execute(task_add)
    _json(task_add)
    task_add.add_argument("--title", required=True)
    task_add.add_argument("--description", default="")
    task_add.add_argument("--depends-on", action="append", default=[])
    task_add.add_argument("--acceptance", action="append", default=[])

    task_start = commands.add_parser("task-start", help="plan or start one ready task")
    _root(task_start)
    _execute(task_start)
    _json(task_start)
    task_start.add_argument("task_id")

    task_block = commands.add_parser("task-block", help="plan or block the active task")
    _root(task_block)
    _execute(task_block)
    _json(task_block)
    task_block.add_argument("task_id")
    task_block.add_argument("--reason", required=True)
    task_block.add_argument("--next-action", required=True)

    task_complete = commands.add_parser(
        "task-complete", help="plan or complete the active task with evidence"
    )
    _root(task_complete)
    _execute(task_complete)
    _json(task_complete)
    task_complete.add_argument("task_id")
    task_complete.add_argument("--evidence", action="append", default=[])
    task_complete.add_argument("--next-action", default="Select the next ready task.")


def _add_workflow_parsers(commands: argparse._SubParsersAction) -> None:
    state = commands.add_parser("transition", help="plan or advance project lifecycle")
    _root(state)
    _execute(state)
    _json(state)
    state.add_argument("--to", required=True)
    state.add_argument("--evidence", action="append", default=[])
    state.add_argument("--confirm-ship", action="store_true")

    save = commands.add_parser("checkpoint", help="persist resume state and handoff")
    _root(save)
    _execute(save)
    _json(save)
    save.add_argument("--next-action", required=True)
    save.add_argument("--done", action="append", default=[])
    save.add_argument("--remaining", action="append", default=[])
    save.add_argument("--warning", action="append", default=[])
    save.add_argument("--gate")
    save.add_argument("--evidence", action="append", default=[])


def _add_knowledge_parsers(commands: argparse._SubParsersAction) -> None:
    decision = commands.add_parser("decision", help="plan or add an ADR")
    _root(decision)
    _execute(decision)
    _json(decision)
    decision.add_argument("--title", required=True)
    decision.add_argument("--context", required=True)
    decision.add_argument("--choice", required=True)
    decision.add_argument("--consequence", action="append", default=[])

    lesson = commands.add_parser("lesson", help="plan or add a verified project lesson")
    _root(lesson)
    _execute(lesson)
    _json(lesson)
    lesson.add_argument("--topic", required=True)
    lesson.add_argument("--text", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    _add_core_parsers(commands)
    _add_task_parsers(commands)
    _add_workflow_parsers(commands)
    _add_knowledge_parsers(commands)
    return parser

def _run_init(options: argparse.Namespace) -> dict[str, Any]:
    return initialize(
        options.root.resolve(),
        options.name,
        options.goal,
        options.profile,
        options.source_repository,
        options.source_commit,
        options.deployment,
        options.execute,
    )


def _run_validate(options: argparse.Namespace) -> dict[str, Any]:
    errors = validate_memory(options.root.resolve())
    return {"status": "valid" if not errors else "invalid", "errors": errors}


def _run_continue(options: argparse.Namespace) -> dict[str, Any]:
    return {"status": "ok", **resume_summary(options.root.resolve())}


def _run_task_add(options: argparse.Namespace) -> dict[str, Any]:
    return add_task(
        options.root.resolve(),
        options.title,
        options.description,
        options.depends_on,
        options.acceptance,
        options.execute,
    )


def _run_task_start(options: argparse.Namespace) -> dict[str, Any]:
    return start_task(options.root.resolve(), options.task_id, options.execute)


def _run_task_block(options: argparse.Namespace) -> dict[str, Any]:
    return block_task(
        options.root.resolve(),
        options.task_id,
        options.reason,
        options.next_action,
        options.execute,
    )


def _run_task_complete(options: argparse.Namespace) -> dict[str, Any]:
    return complete_task(
        options.root.resolve(),
        options.task_id,
        options.evidence,
        options.next_action,
        options.execute,
    )


def _run_transition(options: argparse.Namespace) -> dict[str, Any]:
    return transition(
        options.root.resolve(),
        options.to,
        options.evidence,
        options.confirm_ship,
        options.execute,
    )


def _run_checkpoint(options: argparse.Namespace) -> dict[str, Any]:
    return checkpoint(
        options.root.resolve(),
        options.next_action,
        options.done,
        options.remaining,
        options.warning,
        options.gate,
        options.evidence,
        options.execute,
    )


def _run_decision(options: argparse.Namespace) -> dict[str, Any]:
    return add_decision(
        options.root.resolve(),
        options.title,
        options.context,
        options.choice,
        options.consequence,
        options.execute,
    )


def _run_lesson(options: argparse.Namespace) -> dict[str, Any]:
    return add_lesson(
        options.root.resolve(), options.topic, options.text, options.execute
    )


def _dispatch(options: argparse.Namespace) -> dict[str, Any]:
    handlers = {
        "init": _run_init,
        "validate": _run_validate,
        "continue": _run_continue,
        "task-add": _run_task_add,
        "task-start": _run_task_start,
        "task-block": _run_task_block,
        "task-complete": _run_task_complete,
        "transition": _run_transition,
        "checkpoint": _run_checkpoint,
        "decision": _run_decision,
        "lesson": _run_lesson,
    }
    return handlers[options.command](options)

def _human(result: dict[str, Any]) -> str:
    if result.get("status") == "invalid":
        return "\n".join(f"ERROR: {error}" for error in result.get("errors", []))
    if "project" in result and "next_action" in result:
        task = result.get("active_task") or result.get("next_ready_task")
        task_text = f"{task['id']}: {task['title']}" if task else "None"
        return (
            f"Project: {result['project']}\n"
            f"Lifecycle: {result['lifecycle_state']}\n"
            f"Task: {task_text}\n"
            f"Last commit: {result.get('last_commit') or 'unknown'}\n"
            f"Last gate: {result.get('last_successful_gate') or 'none'}\n"
            f"Blocked: {'yes' if result.get('blocked') else 'no'}\n"
            f"Next exact action: {result['next_action']}"
        )
    return json.dumps(result, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    options = build_parser().parse_args(argv)
    try:
        result = _dispatch(options)
    except ProjectMemoryError as exc:
        result = {"status": "error", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2) if options.json else _human(result))
    return 0 if result.get("status") not in {"error", "invalid"} else 1


if __name__ == "__main__":
    sys.exit(main())
