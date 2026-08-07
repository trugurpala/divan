from __future__ import annotations

import shutil

from .execution_contract import ExecutionEngine
from .execution_router import ExecutionRouter
from .native_engine import NativeExecutionEngine
from .orca_adapter import OrcaExecutionAdapter
from .orca_engine import OrcaEngine


def build_execution_router() -> ExecutionRouter:
    """Build the local Desktop execution router from installed capabilities.

    Orca is preferred when installed, but it is never mandatory. If one or more
    supported local coding agents are available, the Native engine is also
    registered so Divan can operate without Orca.
    """

    engines: list[ExecutionEngine] = []
    default_engine: str | None = None

    orca = shutil.which("orca")
    if orca:
        engines.append(OrcaExecutionAdapter(OrcaEngine(binary=orca)))
        default_engine = "orca"

    native = NativeExecutionEngine()
    if native.agent_binaries:
        engines.append(native)
        if default_engine is None:
            default_engine = "native"

    return ExecutionRouter(engines, default_engine=default_engine)
