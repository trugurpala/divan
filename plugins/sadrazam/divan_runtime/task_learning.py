"""Turn one task's failure history into a remembered lesson at task close.

A task that review rejected and that later merged is the one moment where
Divan holds both halves of a lesson: what was wrong, and what finally passed.
Capture is deliberately kept out of the orchestrator so workflow and learning
stay separately readable and separately testable.
"""
from __future__ import annotations

from typing import Any

from .evidence import EvidenceStore, build_evidence
from .knowledge_capture import lesson_from_failure
from .knowledge_store import KnowledgeStore
from .task_model import DivanTask


def failed_reviews(task: DivanTask) -> list[dict[str, Any]]:
    """Return the recorded review rejections for one task."""
    recorded = task.metadata.get("failed_reviews")
    if not isinstance(recorded, list):
        return []
    return [entry for entry in recorded if isinstance(entry, dict)]


def capture_merge_lesson(
    task: DivanTask,
    diff_sha256: str,
    knowledge: KnowledgeStore,
    evidence: EvidenceStore,
) -> None:
    """Record what review rejected and what finally landed.

    Only tasks that actually failed review carry a lesson: a task that passed
    first time teaches nothing worth storing, and filling the store with clean
    runs would bury the failures worth remembering.

    Memory capture is never allowed to fail a merge that already passed every
    gate, so a broken knowledge store degrades to an honest evidence entry.
    """
    failures = failed_reviews(task)
    if not failures:
        return
    reasons = [
        reason
        for failure in failures
        for reason in failure.get("reasons", [])
        if isinstance(reason, str)
    ]
    checks = sorted(
        {
            name
            for failure in failures
            for name in failure.get("failed_checks", [])
            if isinstance(name, str)
        }
    )
    problem = (
        f"Review rejected {task.title} {len(failures)} time(s). "
        f"Failing checks: {', '.join(checks) or 'unnamed'}. "
        f"Reasons: {'; '.join(reasons) or 'not recorded'}"
    )
    solution = f"The change that passed every required check merged as {diff_sha256}."
    try:
        lesson = lesson_from_failure(
            problem=problem,
            solution=solution,
            tags=("review", *checks),
            source_project=task.project_root,
            evidence_sha256=diff_sha256,
        )
        knowledge.upsert(lesson)
    except Exception as error:  # noqa: BLE001 - memory must not fail a merge
        evidence.append(
            build_evidence(
                task.task_id,
                "knowledge",
                "fail",
                "task-close lesson capture failed",
                {"error": type(error).__name__},
            )
        )
        return
    evidence.append(
        build_evidence(
            task.task_id,
            "knowledge",
            "pass",
            "task-close lesson captured",
            {
                "item_id": lesson.item_id,
                "failed_review_count": len(failures),
                "failed_checks": checks,
                "evidence_sha256": diff_sha256,
            },
        )
    )
