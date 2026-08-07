from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from .knowledge_contract import KnowledgeItem, KnowledgeKind


def lesson_from_failure(
    *,
    problem: str,
    solution: str,
    stack: tuple[str, ...] = (),
    tags: tuple[str, ...] = (),
    source_project: str | None = None,
    evidence_sha256: str | None = None,
    observed_at: str | None = None,
) -> KnowledgeItem:
    problem_text = _bounded(problem)
    solution_text = _bounded(solution)
    if not problem_text or not solution_text:
        raise ValueError("problem and solution are required")
    problem_signature = _digest(problem_text)
    solution_signature = _digest(solution_text)
    return KnowledgeItem(
        item_id=f"lesson-{problem_signature[:12]}-{solution_signature[:8]}",
        kind=KnowledgeKind.LESSON,
        title=f"Lesson: {_headline(problem_text)}",
        summary=f"Problem: {problem_text}\nResolution: {solution_text}",
        tags=(*tags, "failure-learning"),
        stack=stack,
        source_project=source_project,
        problem_signature=problem_signature,
        solution_signature=solution_signature,
        evidence_sha256=evidence_sha256,
        confidence=0.5,
        created_at=observed_at or _now(),
    )


def pattern_from_project(
    *,
    name: str,
    summary: str,
    stack: tuple[str, ...] = (),
    tags: tuple[str, ...] = (),
    source_project: str | None = None,
    evidence_sha256: str | None = None,
    observed_at: str | None = None,
) -> KnowledgeItem:
    title = _bounded(name, limit=160)
    description = _bounded(summary)
    if not title or not description:
        raise ValueError("pattern name and summary are required")
    fingerprint = _digest(f"{title}\n{description}\n{'|'.join(sorted(stack))}")
    return KnowledgeItem(
        item_id=f"pattern-{fingerprint[:20]}",
        kind=KnowledgeKind.PATTERN,
        title=title,
        summary=description,
        tags=tags,
        stack=stack,
        source_project=source_project,
        evidence_sha256=evidence_sha256,
        confidence=0.5,
        created_at=observed_at or _now(),
    )


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _bounded(value: str, *, limit: int = 2000) -> str:
    return " ".join(value.split())[:limit].strip()


def _headline(value: str) -> str:
    return value[:96].rstrip(" .,:;-") or "project failure"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
