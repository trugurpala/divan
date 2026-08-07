from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable


class GateVerdict(StrEnum):
    PASS = "pass"
    RETRY = "retry"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    required: bool = True
    summary: str = ""


@dataclass(frozen=True)
class ReviewDecision:
    verdict: GateVerdict
    checks: tuple[CheckResult, ...]
    reasons: tuple[str, ...]


def decide_review(checks: Iterable[CheckResult]) -> ReviewDecision:
    materialized = tuple(checks)
    failed_required = tuple(check for check in materialized if check.required and not check.passed)
    if failed_required:
        reasons = tuple(check.summary or check.name for check in failed_required)
        return ReviewDecision(GateVerdict.RETRY, materialized, reasons)
    return ReviewDecision(GateVerdict.PASS, materialized, ())


def require_release_ready(*, review: ReviewDecision, approved: bool, mandate_id: str | None) -> None:
    if review.verdict is not GateVerdict.PASS:
        raise ValueError("release gate requires PASS review")
    if not approved:
        raise ValueError("release gate requires explicit operator approval")
    if not mandate_id:
        raise ValueError("release gate requires mandate_id")
