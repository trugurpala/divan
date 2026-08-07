from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .execution_contract import (
    ExecutionEngine,
    ExecutionPolicyError,
    ExecutionReceipt,
    ExecutionRequest,
    require_mandate,
)


@dataclass(frozen=True)
class EngineSelection:
    engine_id: str
    reason: str


class ExecutionRouter:
    """Divan-owned execution boundary.

    Engines are replaceable adapters. Selection and mutation policy stay in Divan.
    """

    def __init__(self, engines: Iterable[ExecutionEngine], default_engine: str | None = None) -> None:
        self._engines = {engine.engine_id: engine for engine in engines}
        self._default_engine = default_engine

    def available_engines(self) -> tuple[str, ...]:
        return tuple(sorted(self._engines))

    def select(self, requested: str | None = None) -> EngineSelection:
        if requested:
            if requested not in self._engines:
                raise ExecutionPolicyError(f"execution engine not available: {requested}")
            return EngineSelection(requested, "explicit")
        if self._default_engine and self._default_engine in self._engines:
            return EngineSelection(self._default_engine, "default")
        if len(self._engines) == 1:
            engine_id = next(iter(self._engines))
            return EngineSelection(engine_id, "only-available")
        if not self._engines:
            raise ExecutionPolicyError("no execution engines are available")
        raise ExecutionPolicyError("multiple execution engines are available; select one explicitly")

    def execute(self, request: ExecutionRequest, engine_id: str | None = None) -> ExecutionReceipt:
        require_mandate(request)
        selection = self.select(engine_id)
        return self._engines[selection.engine_id].execute(request)
