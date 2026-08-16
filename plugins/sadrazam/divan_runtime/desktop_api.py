from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from . import engine, goals, receipts
from .agency_status import build_project_agency_status
from .desktop_protocol_support import ProtocolValidationError
from .desktop_protocol_support import ok_response as _ok
from .desktop_protocol_support import optional_string as _optional_string
from .desktop_protocol_support import required_string as _required_string
from .desktop_state import task_root
from .execution_contract import ExecutionAction, ExecutionRequest
from .execution_router import ExecutionRouter
from .project_registry import ProjectRegistry, resolve_git_root
from .task_model import DivanTask, TaskState
from .task_store import TaskStore


@dataclass(frozen=True)
class DesktopCapabilities:
    product: str
    api_version: int
    engines: tuple[str, ...]
    task_states: tuple[str, ...]
    features: tuple[str, ...]


class DesktopApi:
    """Stable facade between the desktop shell and Divan Core."""

    API_VERSION = 1

    def __init__(self, router: ExecutionRouter) -> None:
        self.router = router

    def capabilities(self) -> dict[str, Any]:
        value = DesktopCapabilities(
            product="Divan",
            api_version=self.API_VERSION,
            engines=self.router.available_engines(),
            task_states=tuple(state.value for state in TaskState),
            features=(
                "engine-routing",
                "mandate-gate",
                "task-lifecycle",
                "interrupted-recovery",
                "evidence",
                "approval-gate",
                "task-diff",
                "goal-planning",
                "goal-work-packages",
                "project-agency-status",
            ),
        )
        return asdict(value)

    def engine_status(self, engine_id: str | None = None) -> dict[str, Any]:
        receipt = self.router.execute(ExecutionRequest(ExecutionAction.STATUS), engine_id)
        return {
            "engine": receipt.engine,
            "ok": receipt.ok,
            "exit_code": receipt.exit_code,
            "payload": receipt.payload,
        }

    def task_diff(
        self,
        task: DivanTask,
        *,
        worktree: str | None = None,
        path: str = "*",
        staged: bool | None = None,
    ) -> dict[str, Any]:
        active_worktree = worktree or self.execution_worktree(task)
        if active_worktree is None:
            raise ValueError("task has no execution worktree yet")
        review_snapshot = task.metadata.get("review_snapshot")
        snapshot_worktree = (
            review_snapshot.get("worktree")
            if isinstance(review_snapshot, Mapping)
            else None
        )
        has_current_review_snapshot = bool(
            isinstance(snapshot_worktree, str)
            and snapshot_worktree.strip()
            and _same_worktree(snapshot_worktree, active_worktree)
        )
        use_staged = has_current_review_snapshot if staged is None else staged
        receipt = self.router.execute(
            ExecutionRequest(
                action=ExecutionAction.FILE_DIFF,
                project_root=task.project_root,
                mandate_id=task.mandate_id,
                args={
                    "worktree": active_worktree,
                    "path": path,
                    "staged": use_staged,
                },
            ),
            task.engine_id,
        )
        diff = ""
        if isinstance(receipt.payload, Mapping):
            value = receipt.payload.get("diff")
            if isinstance(value, str):
                diff = value
        return {
            "engine": receipt.engine,
            "ok": receipt.ok,
            "exit_code": receipt.exit_code,
            "path": path,
            "staged": use_staged,
            "basis": (
                "review-snapshot"
                if use_staged and has_current_review_snapshot
                else "staged" if use_staged else "working-tree"
            ),
            "diff": diff,
        }

    @staticmethod
    def execution_worktree(task: DivanTask) -> str | None:
        execution = task.metadata.get("execution")
        if not isinstance(execution, Mapping):
            return None
        receipt_payload = execution.get("payload")
        if not isinstance(receipt_payload, Mapping):
            return None
        worktree = receipt_payload.get("worktree")
        if not isinstance(worktree, str) or not worktree.strip():
            return None
        return worktree.strip()

    @staticmethod
    def serialize_tasks(tasks: Iterable[DivanTask]) -> list[dict[str, Any]]:
        return [task.to_dict() for task in tasks]


def _project_root(
    payload: Mapping[str, Any],
    *,
    purpose: str = "goal planning",
) -> Path:
    project_id = _optional_string(
        payload,
        "project_id",
        "DESKTOP_PROJECT_ID_INVALID",
    )
    if project_id:
        return Path(ProjectRegistry().get(project_id).root)
    project_root = _optional_string(
        payload,
        "project_root",
        "DESKTOP_PROJECT_ROOT_INVALID",
    )
    if not project_root:
        raise ProtocolValidationError(
            "DESKTOP_PROJECT_REQUIRED",
            f"{purpose} requires project_id or project_root",
        )
    # Goal planning writes into this directory, so hold an unregistered root to
    # the same Git gate project.register enforces instead of trusting the caller.
    try:
        return resolve_git_root(project_root)
    except (ValueError, OSError) as error:
        raise ProtocolValidationError(
            "DESKTOP_PROJECT_ROOT_INVALID",
            f"{purpose} requires a Git repository root: {error}",
        ) from error


def _goal_intent(payload: Mapping[str, Any]) -> str:
    raw = _required_string(
        payload,
        "intent",
        "DESKTOP_GOAL_INTENT_REQUIRED",
    )
    # start_goal plans and persists from the redacted intent. Preview and create
    # must plan from the same text, or the approved preview would not describe
    # the plan that actually gets written.
    return receipts.redact_text(raw.strip())


def _goal_target(payload: Mapping[str, Any]) -> str:
    return (
        _optional_string(
            payload,
            "target",
            "DESKTOP_GOAL_TARGET_INVALID",
        )
        or "verified"
    ).casefold()


def _goal_route(root: Path, intent: str, target: str) -> dict[str, Any]:
    contracts = engine.load_contracts(Path(engine.__file__).resolve().parent)
    return engine.plan_intent(
        intent,
        root,
        contracts,
        target,
        environment={},
    )


def _goal_summary(route: Mapping[str, Any]) -> dict[str, Any]:
    execution = route.get("execution_plan")
    if not isinstance(execution, Mapping):
        raise ValueError("goal route has no execution plan")
    orchestration = execution.get("orchestration")
    if not isinstance(orchestration, Mapping):
        raise ValueError("goal route has no orchestration plan")
    tasks = execution.get("tasks")
    workstreams = execution.get("workstreams")
    sefers = execution.get("sefers")
    if (
        not isinstance(tasks, list)
        or not isinstance(workstreams, list)
        or not isinstance(sefers, list)
    ):
        raise ValueError("goal route planning collections are invalid")
    return {
        "route_id": execution.get("route_id"),
        "workflow": route.get("workflow"),
        "workflows": list(route.get("workflows", [])),
        "roles": list(route.get("roles", [])),
        "frameworks": list(route.get("frameworks", [])),
        "project_types": list(route.get("project_types", [])),
        "task_count": len(tasks),
        "workstream_count": len(workstreams),
        "sefer_count": len(sefers),
        "lane": orchestration.get("lane"),
        "max_parallel_workstreams": orchestration.get("max_parallel_workstreams"),
        "required_evidence": list(route.get("required_evidence", [])),
    }


def preview_goal(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic read-only route for one registered project goal."""
    root = _project_root(payload)
    intent = _goal_intent(payload)
    target = _goal_target(payload)
    route = _goal_route(root, intent, target)
    return {
        "project_root": str(root),
        "intent": intent,
        "target": target,
        "summary": _goal_summary(route),
        "route": route,
        "writes": [],
        "execution_authority": "not-granted",
    }


def create_goal(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Persist goal artifacts and local work packages after plan-write approval."""
    if payload.get("approve_plan_write") is not True:
        raise ProtocolValidationError(
            "DESKTOP_GOAL_WRITE_APPROVAL_REQUIRED",
            "persisting a goal plan requires explicit approve_plan_write=true",
        )
    root = _project_root(payload)
    intent = _goal_intent(payload)
    target = _goal_target(payload)
    result = goals.start_goal(root, intent, target, True, environment={})
    route = _goal_route(root, intent, target)
    work_packages = TaskStore(task_root()).materialize_goal(root, str(result["goal_id"]))
    return {
        "goal": result,
        "summary": _goal_summary(route),
        "work_packages": work_packages,
        "execution_authority": "not-granted",
    }


def handle_goal_preview(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    return _ok(preview_goal(payload))


def handle_goal_create(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    return _ok(create_goal(payload))


def goal_tasks(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return the materialized work packages and ready state for one saved goal."""
    root = _project_root(payload)
    goal_id = _required_string(payload, "goal_id", "DESKTOP_GOAL_ID_REQUIRED")
    return TaskStore(task_root()).goal_tasks(root, goal_id)


def handle_goal_tasks(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    return _ok(goal_tasks(payload))


def handle_project_agency_status(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del router
    root = _project_root(payload, purpose="agency status")
    return _ok(build_project_agency_status(root, TaskStore(task_root())))


def _same_worktree(left: str, right: str) -> bool:
    try:
        return Path(left).expanduser().resolve() == Path(right).expanduser().resolve()
    except OSError:
        return False
