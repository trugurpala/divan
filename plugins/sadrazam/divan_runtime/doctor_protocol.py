"""Desktop protocol surface for the Deep Doctor.

Kept beside the knowledge and plugin protocols so each capability owns its own
handler table and the shared dispatcher stays readable. The CLI and the Desktop
both read this one model; there is no second health truth.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .desktop_protocol_support import ok_response as _ok
from .desktop_state import knowledge_database
from .doctor_checks import build_report, report_payload, trusted_state_root
from .execution_router import ExecutionRouter

DoctorHandler = Callable[[Mapping[str, Any], ExecutionRouter | None], dict[str, Any]]


def _doctor(
    payload: Mapping[str, Any], router: ExecutionRouter | None
) -> dict[str, Any]:
    del payload, router
    return _ok(
        report_payload(
            build_report(
                state_root=trusted_state_root(),
                knowledge_database=knowledge_database(),
            )
        )
    )


DOCTOR_HANDLERS: dict[str, DoctorHandler] = {
    "doctor": _doctor,
}
