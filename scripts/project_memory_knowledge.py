#!/usr/bin/env python3
"""Decision and lesson records for Divan durable project memory."""
from __future__ import annotations

import pathlib
import re
from typing import Any

from project_memory_store import (
    append_event,
    atomic_write_text,
    memory_root,
    slugify,
    utc_now,
)
from project_memory_workflow import _mutation_result, _operation_memory


def add_decision(
    project_root: pathlib.Path,
    title: str,
    context: str,
    choice: str,
    consequences: list[str],
    execute: bool = False,
) -> dict[str, Any]:
    with _operation_memory(project_root, execute):
        directory = memory_root(project_root) / "decisions"
        numbers = [
            int(match.group(1))
            for path in directory.glob("[0-9][0-9][0-9][0-9]-*.md")
            if (match := re.match(r"^(\d{4})-", path.name))
        ]
        number = max(numbers, default=0) + 1
        relative = f".divan/decisions/{number:04d}-{slugify(title)}.md"
        result = _mutation_result("decision_add", execute, {"path": relative})
        if not execute:
            return result
        consequences_text = "\n".join(
            f"- {item.strip()}" for item in consequences if item.strip()
        )
        body = (
            f"# ADR {number:04d}: {title.strip()}\n\n"
            f"Date: {utc_now()}\n\n## Context\n\n{context.strip()}\n\n"
            f"## Decision\n\n{choice.strip()}\n\n## Consequences\n\n"
            f"{consequences_text or '- None recorded.'}\n"
        )
        atomic_write_text(project_root / relative, body)
        append_event(
            project_root,
            "decision_added",
            {"path": relative, "title": title.strip()},
        )
        return result


def add_lesson(
    project_root: pathlib.Path,
    topic: str,
    text: str,
    execute: bool = False,
) -> dict[str, Any]:
    with _operation_memory(project_root, execute):
        relative = f".divan/lessons/{slugify(topic)}.md"
        result = _mutation_result("lesson_add", execute, {"path": relative})
        if not execute:
            return result
        path = project_root / relative
        existing = (
            path.read_text(encoding="utf-8")
            if path.exists()
            else f"# {topic.strip()}\n"
        )
        body = existing.rstrip() + f"\n\n## {utc_now()}\n\n{text.strip()}\n"
        atomic_write_text(path, body)
        append_event(
            project_root,
            "lesson_added",
            {"path": relative, "topic": topic.strip()},
        )
        return result
