from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .execution_contract import ExecutionAction, ExecutionRequest
from .execution_router import ExecutionRouter
from .task_model import DivanTask, TaskState


@dataclass(frozen=True)
class DesktopCapabilities:
    product: str
    api_version: int
    engines: tuple[str, ...]
    task_states: tuple[str, ...]
    features: tuple[str, ...]


class DesktopApi:
    """Small stable facade intended for the future desktop shell.

    The desktop UI should talk to this facade instead of importing individual
    runtime modules, keeping UI churn separate from Divan Core.
    """

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
                "evidence",
                "approval-gate",
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

    @staticmethod
    def serialize_tasks(tasks: Iterable[DivanTask]) -> list[dict[str, Any]]:
        return [task.to_dict() for task in tasks]
