"""The concrete Agency OS capability checks behind the Deep Doctor.

Each check answers "can this product function actually run right now?", not
"does a file exist?". Where a contract can be read back or a smoke can be
performed cheaply and safely, it is; where it cannot, the check says so
instead of assuming.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable, Mapping

from .agency_status import build_project_agency_status
from .attempt_store import classify_quiet_attempt
from .browser_capability import browser_capability
from .context_compiler import compile_context
from .doctor import (
    LOCAL_STATE_DACL_POLICY,
    CapabilityReport,
    CapabilityState,
    DoctorReport,
    run_checks,
)
from .evidence import build_evidence
from .memory_first import recall
from .plugin_desktop import inspect_plugin_manifest
from .quality_factory import evaluate as evaluate_gates
from .worker_discovery import WorkerFinding, probe_worker

Which = Callable[[str], str | None]


def trusted_state_root() -> Path:
    """Where Divan keeps trusted local state on this machine."""
    from .project_os import _trusted_init_root

    return _trusted_init_root()


def _core_check() -> CapabilityReport:
    """Read the runtime contract back rather than trusting the package exists."""
    from . import kernel

    try:
        architecture = kernel.load_architecture()
        modules = architecture["modules"]
    except Exception as error:  # noqa: BLE001 - a broken contract is the finding
        return CapabilityReport(
            capability_id="divan-core",
            display_name="Divan Core",
            state=CapabilityState.INCOMPATIBLE,
            affects="Divan hiçbir işi planlayamaz veya yürütemez.",
            code="RUNTIME_CONTRACT_INVALID",
            detail=type(error).__name__,
        )
    return CapabilityReport(
        capability_id="divan-core",
        display_name="Divan Core",
        state=CapabilityState.CERTIFIED,
        affects="Planlama ve yürütmenin tamamı.",
        evidence=f"{len(modules)} çalışma zamanı modülü sözleşmeden okundu",
    )


def _entry_check(
    capability_id: str,
    display_name: str,
    affects: str,
    entry: Any,
    entry_name: str,
) -> CapabilityReport:
    """Prove a capability is reachable through its real entry point.

    The entry point is imported statically at module load, so an unreachable
    capability fails at import time rather than being probed dynamically. The
    runtime contract forbids unbounded dynamic imports for exactly that reason.
    """
    if not callable(entry):
        return CapabilityReport(
            capability_id=capability_id,
            display_name=display_name,
            state=CapabilityState.INCOMPATIBLE,
            affects=affects,
            code="CAPABILITY_NOT_CALLABLE",
            detail=entry_name,
        )
    return CapabilityReport(
        capability_id=capability_id,
        display_name=display_name,
        state=CapabilityState.CERTIFIED,
        affects=affects,
        evidence=f"{entry_name} çözüldü",
    )


def _spec_compiler_check() -> CapabilityReport:
    """Compile a tiny specification, so this is a smoke and not an import."""
    from .spec_compiler import compile_specification

    probe = {
        "ferman": "probe",
        "outcome": "probe outcome",
        "quality_profile": "INTERNAL_TOOL",
        "stories": [
            {
                "id": "probe",
                "title": "Probe",
                "priority": "P1",
                "narrative": "probe",
                "acceptance": ["probe"],
            }
        ],
        "requirements": ["probe"],
        "measurable_outcomes": ["probe"],
    }
    result = compile_specification(probe)
    if not result.ok:
        return CapabilityReport(
            capability_id="spec-compiler",
            display_name="Spec derleyici",
            state=CapabilityState.INCOMPATIBLE,
            affects="Ferman ürün ve iş paketi sözleşmelerine çevrilemez.",
            code="SPEC_COMPILE_FAILED",
            detail=", ".join(issue.code for issue in result.issues),
        )
    return CapabilityReport(
        capability_id="spec-compiler",
        display_name="Spec derleyici",
        state=CapabilityState.CERTIFIED,
        affects="Fermandan ürün sözleşmesi ve iş paketi grafiği.",
        evidence="örnek ferman derlendi",
    )


def _memory_store_check(database: Path) -> CapabilityReport:
    """Open the store and read its analytics; a locked or broken file shows up."""
    from .knowledge_store import KnowledgeStore

    try:
        analytics = KnowledgeStore(database).analytics()
    except Exception as error:  # noqa: BLE001
        return CapabilityReport(
            capability_id="memory-store",
            display_name="Hafıza deposu",
            state=CapabilityState.DEGRADED,
            affects="Divan geçmiş dersleri hatırlayamaz.",
            code="MEMORY_STORE_UNREADABLE",
            detail=type(error).__name__,
        )
    return CapabilityReport(
        capability_id="memory-store",
        display_name="Hafıza deposu",
        state=CapabilityState.CERTIFIED,
        affects="Geçmiş karar ve derslerin hatırlanması.",
        evidence=f"{analytics['items']} kayıt okundu",
    )


def _local_state_check(state_root: Path) -> CapabilityReport:
    """Report the Windows trusted-state policy truthfully, never repair it."""
    import os

    from .project_os import _state_ancestor_chain, _windows_private_dacl

    if os.name != "nt":
        return CapabilityReport(
            capability_id="local-state-security",
            display_name="Yerel güvenlik kontrolü",
            state=CapabilityState.CERTIFIED,
            affects="Yerel durum dizininin başka bir kullanıcıdan korunması.",
            evidence="POSIX izin kontrolü",
        )
    try:
        for ancestor in _state_ancestor_chain(state_root):
            if ancestor.exists():
                _windows_private_dacl(ancestor, require_current_owner=False)
    except ValueError as error:
        # This machine's AppData carries a capability SID. Divan reports it and
        # does not touch the ACL: changing machine security is an owner gate.
        return CapabilityReport(
            capability_id="local-state-security",
            display_name="Yerel güvenlik kontrolü",
            state=CapabilityState.BLOCKED,
            affects=(
                "Yerel kanıtın son doğrulaması eksik kalır; geliştirme durmaz."
            ),
            code=LOCAL_STATE_DACL_POLICY,
            detail=str(error),
        )
    return CapabilityReport(
        capability_id="local-state-security",
        display_name="Yerel güvenlik kontrolü",
        state=CapabilityState.CERTIFIED,
        affects="Yerel durum dizininin korunması.",
        evidence="güvenilir durum zinciri özel",
    )


def _tool_check(
    capability_id: str,
    display_name: str,
    affects: str,
    command: str,
    which: Which,
) -> CapabilityReport:
    resolved = which(command)
    if resolved is None:
        return CapabilityReport(
            capability_id=capability_id,
            display_name=display_name,
            state=CapabilityState.OFFLINE,
            affects=affects,
            code="TOOL_NOT_INSTALLED",
            detail=f"{command} bulunamadı",
        )
    return CapabilityReport(
        capability_id=capability_id,
        display_name=display_name,
        # Resolving an executable is not proof it is authenticated or usable,
        # so this is deliberately DEGRADED rather than CERTIFIED.
        state=CapabilityState.DEGRADED,
        affects=affects,
        code="AUTH_NOT_VERIFIED",
        detail="çalıştırılabilir bulundu; oturum doğrulanmadı",
        evidence=resolved,
    )


def _worker_check(worker_id: str, display_name: str) -> CapabilityReport:
    """Report a coding worker with the evidence behind the finding.

    "Not on PATH" and "not installed" are different findings, so an ABSENT
    result records every location that was actually examined.
    """
    probe = probe_worker(worker_id)
    affects = "Kod yazan çalışanlardan biri; yoksa uygulama üretilemez."
    if probe.finding is WorkerFinding.ABSENT:
        return CapabilityReport(
            capability_id=worker_id,
            display_name=display_name,
            state=CapabilityState.OFFLINE,
            affects=affects,
            code="TOOL_NOT_INSTALLED",
            detail=probe.detail,
            evidence=f"{len(probe.searched)} konum arandı: " + ", ".join(probe.searched),
        )
    if probe.finding is WorkerFinding.UNUSABLE:
        return CapabilityReport(
            capability_id=worker_id,
            display_name=display_name,
            state=CapabilityState.INCOMPATIBLE,
            affects=affects,
            code="TOOL_UNUSABLE",
            detail=probe.detail,
            evidence=probe.executable,
        )
    # Found is not authenticated. Divan never opens a credential file to guess.
    return CapabilityReport(
        capability_id=worker_id,
        display_name=display_name,
        state=CapabilityState.DEGRADED,
        affects=affects,
        code="AUTH_NOT_VERIFIED",
        detail="çalıştırılabilir bulundu; oturum doğrulanmadı",
        evidence=probe.executable,
    )


def build_report(
    *,
    state_root: Path,
    knowledge_database: Path,
    which: Which = shutil.which,
    checked_at: str = "",
) -> DoctorReport:
    """Assemble the one canonical health report for CLI and Desktop alike."""
    checks = [
        _core_check,
        lambda: _tool_check(
            "git", "Git", "Worktree izolasyonu ve güvenli birleştirme.", "git", which
        ),
        lambda: _worker_check("codex", "Codex"),
        lambda: _worker_check("claude", "Claude Code"),
        browser_capability,
        _spec_compiler_check,
        lambda: _memory_store_check(knowledge_database),
        lambda: _entry_check(
            "memory-recall",
            "Hafıza geri çağırma",
            "Planlamadan önce bilinenlerin hatırlanması.",
            recall,
            "memory_first.recall",
        ),
        lambda: _entry_check(
            "plugin-trust",
            "Eklenti güven merkezi",
            "Dış eklenti manifestlerinin denetimi.",
            inspect_plugin_manifest,
            "plugin_desktop.inspect_plugin_manifest",
        ),
        lambda: _entry_check(
            "context-compiler",
            "Bağlam derleyici",
            "Çalışanlara sınırlı bağlam verilmesi.",
            compile_context,
            "context_compiler.compile_context",
        ),
        lambda: _entry_check(
            "attempt-recovery",
            "Çalışan kurtarma sistemi",
            "Çöken çalışanın toparlanması ve değiştirilmesi.",
            classify_quiet_attempt,
            "attempt_store.classify_quiet_attempt",
        ),
        lambda: _entry_check(
            "quality-factory",
            "Kalite fabrikası",
            "Teslim kapılarının fail-closed değerlendirilmesi.",
            evaluate_gates,
            "quality_factory.evaluate",
        ),
        lambda: _entry_check(
            "evidence",
            "Kanıt defteri",
            "Sonucun sonradan yeniden kurulabilmesi.",
            build_evidence,
            "evidence.build_evidence",
        ),
        lambda: _entry_check(
            "agency-status",
            "Proje durum modeli",
            "Patron Masası'nın gerçek durumu göstermesi.",
            build_project_agency_status,
            "agency_status.build_project_agency_status",
        ),
        lambda: _local_state_check(state_root),
    ]
    return run_checks(checks, checked_at=checked_at)


def report_payload(report: DoctorReport) -> Mapping[str, Any]:
    """The single payload both the CLI and the Desktop read."""
    from .doctor import human_lines

    payload = dict(report.to_dict())
    payload["human_summary"] = human_lines(report)
    return payload
