"""Doctor checks for the two capabilities that carry Divan to a machine.

The installer decides whether the product can be handed over at all, and the
update governor decides whether a managed tool may be replaced underneath it.
Both were missing from the canonical health report while the campaign proved
them, so the report claimed fifteen capabilities for a product that has
seventeen.

They live here rather than in doctor_checks because that module is close to the
four-hundred-line ceiling, and a health check is not worth spending the whole
budget on.
"""
from __future__ import annotations

import json
from pathlib import Path

from .doctor import CapabilityReport, CapabilityState

#: Where the Tauri and NSIS pipeline leaves its bundle in a development tree.
_BUNDLE = Path("apps/desktop/src-tauri/target/release/bundle/nsis")
_SIDECAR_DIRECTORY = Path("apps/desktop/src-tauri/binaries")
_RUNTIME = Path("plugins/sadrazam/divan_runtime")


def _declared_modules(root: Path) -> set[str]:
    contract = json.loads((root / _RUNTIME / "modules.json").read_text(encoding="utf-8"))
    return {name for entry in contract["modules"] for name in entry["python_modules"]}


def installer_capability(root: Path | None = None) -> CapabilityReport:
    """Can this product be packaged, and does the package carry the runtime?

    Read in a development tree, where the sidecar and the bundle are visible. An
    installed copy has neither, and says so rather than claiming a failure: the
    absence of a build tree is not a broken installer.
    """
    root = root or Path.cwd()
    sidecars = sorted((root / _SIDECAR_DIRECTORY).glob("divan-core-*")) \
        if (root / _SIDECAR_DIRECTORY).is_dir() else []
    bundles = sorted((root / _BUNDLE).glob("*.exe")) if (root / _BUNDLE).is_dir() else []

    if not (root / _RUNTIME / "modules.json").exists():
        return CapabilityReport(
            capability_id="installer",
            display_name="Kurulum paketi",
            state=CapabilityState.OFFLINE,
            affects="Ürün paketlenip başka bir makineye verilemez.",
            code="INSTALLER_TREE_ABSENT",
            detail="çalışma zamanı sözleşmesi bulunamadı; bu bir geliştirme ağacı değil",
        )

    declared = len(_declared_modules(root))
    if not sidecars:
        return CapabilityReport(
            capability_id="installer",
            display_name="Kurulum paketi",
            state=CapabilityState.DEGRADED,
            affects="Masaüstü paketi üretilene kadar teslim edilecek bir kurulum yok.",
            code="SIDECAR_NOT_BUILT",
            detail=f"{declared} modül bildirildi, çekirdek ikilisi henüz derlenmedi",
        )

    if not bundles:
        return CapabilityReport(
            capability_id="installer",
            display_name="Kurulum paketi",
            state=CapabilityState.DEGRADED,
            affects="Çekirdek hazır, kurulum paketi henüz üretilmedi.",
            code="BUNDLE_NOT_BUILT",
            detail=f"{sidecars[0].name} hazır, NSIS paketi yok",
        )

    newest = max(bundles, key=lambda item: item.stat().st_mtime)
    return CapabilityReport(
        capability_id="installer",
        display_name="Kurulum paketi",
        state=CapabilityState.CERTIFIED,
        affects="Ürünün kurulup çalıştırılabilmesi.",
        evidence=f"{newest.name}, {newest.stat().st_size // 1048576} MB;"
                 f" {declared} modül bildiren çekirdekle",
    )


def update_governor_capability() -> CapabilityReport:
    """Does the governor actually refuse an unsafe promotion?

    An import proves nothing here. The check drives the decision the governor
    exists to make and confirms it says no: a candidate whose rollback is not
    proven must not be promoted, however green everything else looks.
    """
    from .update_governor import (
        MANAGED_TOOLS,
        RollbackMechanism,
        ToolStatus,
        ToolVersionRecord,
        UpdateMode,
        promotion_decision,
    )
    from .update_pipeline import CONTRACT_SMOKE_CHECKS, PipelineStage

    unproven = ToolVersionRecord(
        tool_id="codex",
        installed_version="0.0.0",
        candidate_version="0.0.1",
        source="doctor-probe",
        discovered_at="1970-01-01T00:00:00Z",
        status=ToolStatus.CANDIDATE,
        stage=PipelineStage.PROMOTE,
        rollback_mechanism=RollbackMechanism.UNTESTED,
        host="doctor-probe",
    )
    action, reason = promotion_decision(
        unproven,
        UpdateMode.BALANCED,
        active_attempts=0,
        contract_smoke_passed=True,
        security_ok=True,
        rollback_proven=False,
    )
    if action == "promote":
        return CapabilityReport(
            capability_id="update-governor",
            display_name="Cephanelik güncelleme yönetimi",
            state=CapabilityState.INCOMPATIBLE,
            affects="Geri alınamayan bir araç sürümü çalışanların altına konabilir.",
            code="PROMOTES_WITHOUT_PROVEN_ROLLBACK",
            detail=reason,
        )

    busy_action, busy_reason = promotion_decision(
        unproven,
        UpdateMode.BALANCED,
        active_attempts=1,
        contract_smoke_passed=True,
        security_ok=True,
        rollback_proven=True,
    )
    if busy_action == "promote":
        return CapabilityReport(
            capability_id="update-governor",
            display_name="Cephanelik güncelleme yönetimi",
            state=CapabilityState.INCOMPATIBLE,
            affects="Çalışan bir deneme sürerken aracı değiştirilebilir.",
            code="PROMOTES_WHILE_ATTEMPT_RUNS",
            detail=busy_reason,
        )

    return CapabilityReport(
        capability_id="update-governor",
        display_name="Cephanelik güncelleme yönetimi",
        state=CapabilityState.CERTIFIED,
        affects="Araç sürümlerinin körlemesine değil kanıtla değiştirilmesi.",
        evidence=f"{len(MANAGED_TOOLS)} yönetilen araç,"
                 f" {len(CONTRACT_SMOKE_CHECKS)} sözleşme kontrolü;"
                 " kanıtsız geri alma ve süren deneme terfiyi durdurdu",
    )
