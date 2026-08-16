from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from .knowledge_contract import KnowledgeItem, KnowledgeKind, normalized_terms
from .receipts import redact_text


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
        source_project=_redacted_project(source_project),
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
    normalized_stack = normalized_terms(stack)
    fingerprint = _digest(
        f"{title}\n{description}\n{'|'.join(normalized_stack)}"
    )
    return KnowledgeItem(
        item_id=f"pattern-{fingerprint[:20]}",
        kind=KnowledgeKind.PATTERN,
        title=title,
        summary=description,
        tags=tags,
        stack=normalized_stack,
        source_project=_redacted_project(source_project),
        evidence_sha256=evidence_sha256,
        confidence=0.5,
        created_at=observed_at or _now(),
    )


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _bounded(value: str, *, limit: int = 2000) -> str:
    """Collapse, redact and bound one captured text field.

    Captured text is failure output and operator prose, so it carries home
    paths and credential assignments. Every other persistence path in the
    runtime redacts before writing; knowledge capture must too. Redacting
    before the digest also keeps item_id stable across machines, because a
    home path no longer leaks into the fingerprint.
    """
    return redact_text(" ".join(value.split()))[:limit].strip()


def _headline(value: str) -> str:
    return value[:96].rstrip(" .,:;-") or "project failure"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redacted_project(value: str | None) -> str | None:
    """Redact the source project label, which is often a real filesystem path."""
    if value is None:
        return None
    cleaned = redact_text(" ".join(value.split())).strip()
    return cleaned or None
