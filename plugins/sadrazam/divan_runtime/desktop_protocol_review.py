from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from .desktop_protocol_support import ProtocolValidationError
from .desktop_protocol_support import ok_response as _ok
from .desktop_protocol_support import required_string as _required_string
from .desktop_state import evidence_root, task_root
from .execution_router import ExecutionRouter
from .orchestrator import DivanOrchestrator
from .review_gate import CheckResult, ReviewDecision
from .task_model import DivanTask
from .task_store import TaskStore


def _tasks() -> TaskStore:
    return TaskStore(task_root())


def _load_task(payload: Mapping[str, Any]) -> DivanTask:
    return _tasks().load(_required_string(payload, "task_id", "DESKTOP_TASK_ID_REQUIRED"))


def _require_router(router: ExecutionRouter | None) -> ExecutionRouter:
    if router is None:
        raise ProtocolValidationError(
            "DESKTOP_ROUTER_UNAVAILABLE",
            "execution router is not configured",
        )
    return router


def _orchestrator(router: ExecutionRouter) -> DivanOrchestrator:
    return DivanOrchestrator(
        router,
        state_root=task_root(),
        evidence_root=evidence_root(),
    )


def _parse_review_checks(payload: Mapping[str, Any]) -> list[CheckResult]:
    checks_raw = payload.get("checks")
    if not isinstance(checks_raw, list) or not checks_raw:
        raise ProtocolValidationError(
            "DESKTOP_REVIEW_CHECKS_REQUIRED",
            "checks must be a non-empty list",
        )
    checks: list[CheckResult] = []
    for row in checks_raw:
        if not isinstance(row, Mapping):
            raise ProtocolValidationError(
                "DESKTOP_REVIEW_CHECK_INVALID",
                "review check must be an object",
            )
        name = row.get("name")
        passed = row.get("passed")
        if not isinstance(name, str) or type(passed) is not bool:
            raise ProtocolValidationError(
                "DESKTOP_REVIEW_CHECK_INVALID",
                "review check requires name and boolean passed",
            )
        checks.append(
            CheckResult(
                name=name,
                passed=passed,
                required=bool(row.get("required", True)),
                summary=str(row.get("summary", "")),
            )
        )
    return checks


def _review_result(task: DivanTask, decision: ReviewDecision) -> dict[str, Any]:
    return {
        "task": task.to_dict(),
        "review": {
            "verdict": decision.verdict.value,
            "checks": [asdict(item) for item in decision.checks],
            "reasons": list(decision.reasons),
        },
    }


def handle_task_review(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    updated, decision = _orchestrator(_require_router(router)).review(
        _load_task(payload),
        _parse_review_checks(payload),
    )
    return _ok(_review_result(updated, decision))


def handle_task_review_auto(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    updated, decision = _orchestrator(_require_router(router)).review_automated(
        _load_task(payload)
    )
    return _ok(_review_result(updated, decision))


def handle_approval_request(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    task = _orchestrator(_require_router(router)).request_approval(_load_task(payload))
    return _ok(task.to_dict())


def handle_task_approve(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    if payload.get("approved") is not True:
        raise ProtocolValidationError(
            "DESKTOP_MERGE_APPROVAL_REQUIRED",
            "merge requires explicit approved=true",
        )
    task = _orchestrator(_require_router(router)).approve_merge(
        _load_task(payload), approved=True
    )
    return _ok(task.to_dict())


def handle_task_release(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    task = _orchestrator(_require_router(router)).release(_load_task(payload))
    return _ok(task.to_dict())


def handle_evidence_list(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    task_id = _required_string(payload, "task_id", "DESKTOP_TASK_ID_REQUIRED")
    active_router = router or ExecutionRouter([])
    return _ok(list(_orchestrator(active_router).evidence.list(task_id)))
