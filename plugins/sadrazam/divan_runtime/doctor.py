"""One canonical health read model for the whole Agency OS.

CLI and Desktop read this same model. Creating a second health truth is how a
product ends up telling the owner two different stories about the same
machine, so nothing here is duplicated in a renderer.

A capability reports what was actually observed. Presence of a binary is not
readiness, so a check may carry a contract readback or a smoke result; when it
cannot, it says so rather than guessing. One missing capability never
takes the whole system down: each check names the product function it blocks.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Callable, Iterable

DOCTOR_SCHEMA_VERSION = 1


class CapabilityState(StrEnum):
    #: Observed working, with a contract readback or smoke result behind it.
    CERTIFIED = "CERTIFIED"
    #: Works, but not fully: reduced function or unverified depth.
    DEGRADED = "DEGRADED"
    #: Present in the design, absent on this machine.
    OFFLINE = "OFFLINE"
    #: Present but the wrong shape or version to be used safely.
    INCOMPATIBLE = "INCOMPATIBLE"
    #: Refused by policy or environment; not a fault Divan may route around.
    BLOCKED = "BLOCKED"


#: States that let the product function this capability serves actually run.
USABLE_STATES = frozenset({CapabilityState.CERTIFIED, CapabilityState.DEGRADED})


@dataclass(frozen=True)
class CapabilityReport:
    capability_id: str
    display_name: str
    state: CapabilityState
    #: What the owner loses while this capability is not certified.
    affects: str
    #: Machine-readable reason code; required when the state is not CERTIFIED.
    code: str | None = None
    detail: str | None = None
    #: How this was established, so a claim can be traced.
    evidence: str | None = None
    version: str | None = None

    def __post_init__(self) -> None:
        if not self.capability_id.strip() or not self.display_name.strip():
            raise ValueError("capability id and display name are required")
        if not self.affects.strip():
            raise ValueError(f"capability {self.capability_id} must name what it affects")
        if self.state is not CapabilityState.CERTIFIED and not self.code:
            raise ValueError(
                f"capability {self.capability_id} is {self.state.value} and needs a code"
            )

    @property
    def usable(self) -> bool:
        return self.state in USABLE_STATES

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        payload["usable"] = self.usable
        return payload


@dataclass(frozen=True)
class DoctorReport:
    capabilities: tuple[CapabilityReport, ...]
    checked_at: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def blocked(self) -> tuple[CapabilityReport, ...]:
        return tuple(c for c in self.capabilities if c.state is CapabilityState.BLOCKED)

    @property
    def unusable(self) -> tuple[CapabilityReport, ...]:
        return tuple(c for c in self.capabilities if not c.usable)

    @property
    def healthy(self) -> bool:
        return not self.unusable

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": DOCTOR_SCHEMA_VERSION,
            "checked_at": self.checked_at,
            "healthy": self.healthy,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "blocked_codes": [c.code for c in self.blocked if c.code],
            "unusable_ids": [c.capability_id for c in self.unusable],
            "notes": list(self.notes),
        }


#: Reason code for the Windows local-state DACL policy. Divan reports this
#: truthfully and never edits the machine ACL to make it go away.
LOCAL_STATE_DACL_POLICY = "LOCAL_STATE_DACL_POLICY"

CapabilityCheck = Callable[[], CapabilityReport]


def run_checks(checks: Iterable[CapabilityCheck], *, checked_at: str = "") -> DoctorReport:
    """Run every check, letting one failure describe itself rather than abort.

    A check that raises is recorded as BLOCKED with its error class. A probe
    that could not run has not established the capability, so it must never
    count as usable, and a doctor that crashes tells the owner nothing at all.
    """
    reports: list[CapabilityReport] = []
    for check in checks:
        try:
            reports.append(check())
        except Exception as error:  # noqa: BLE001 - a broken probe is a finding
            reports.append(
                CapabilityReport(
                    capability_id=getattr(check, "capability_id", "unknown"),
                    display_name=getattr(check, "display_name", "Bilinmeyen yetenek"),
                    state=CapabilityState.BLOCKED,
                    affects="Bu yeteneğin durumu okunamadı.",
                    code="PROBE_FAILED",
                    detail=type(error).__name__,
                )
            )
    return DoctorReport(tuple(reports), checked_at=checked_at)


_HUMAN_STATE: dict[CapabilityState, str] = {
    CapabilityState.CERTIFIED: "hazır",
    CapabilityState.DEGRADED: "sınırlı çalışıyor",
    CapabilityState.OFFLINE: "kurulu değil",
    CapabilityState.INCOMPATIBLE: "uyumsuz",
    CapabilityState.BLOCKED: "engelli",
}


def human_lines(report: DoctorReport) -> list[str]:
    """Say what the owner needs to hear, one short sentence per capability."""
    lines = [
        f"{item.display_name} {_HUMAN_STATE[item.state]}."
        for item in report.capabilities
    ]
    for item in report.unusable:
        if item.detail:
            lines.append(f"{item.display_name}: {item.detail}")
    if report.healthy:
        lines.append("Divan hazır.")
    else:
        # A missing capability must not read as a dead product.
        lines.append(
            "Eksik yetenekler yalnız ilgili işlevi durdurur; "
            "geliştirme çalışmaya devam eder."
        )
    return lines
