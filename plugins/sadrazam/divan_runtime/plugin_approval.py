from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .plugin_contract import PluginDecision, PluginIssue
from .plugin_discovery import PluginCandidate


@dataclass(frozen=True)
class PluginApproval:
    plugin_id: str
    decision: PluginDecision
    manifest_sha256: str
    executable_sha256: str
    approved_capabilities: tuple[str, ...]


@dataclass(frozen=True)
class PluginActivation:
    plugin_id: str
    executable_path: str
    capabilities: tuple[str, ...]
    requires_mandate: bool


@dataclass(frozen=True)
class ActivationValidation:
    activation: PluginActivation | None
    errors: tuple[PluginIssue, ...]

    @property
    def ok(self) -> bool:
        return self.activation is not None and not self.errors


def approve_candidate(
    candidate: PluginCandidate,
    *,
    decision: PluginDecision,
    approved_capabilities: Sequence[str] | None = None,
) -> PluginApproval:
    """Create an owner approval bound to the exact manifest and executable bytes."""
    manifest = candidate.validation.manifest
    if manifest is None or not candidate.validation.ok:
        raise ValueError("cannot approve an invalid plugin manifest")
    if not candidate.available or candidate.executable_sha256 is None:
        raise ValueError("cannot approve a plugin whose executable is unavailable")

    capabilities = tuple(
        sorted(
            manifest.capabilities
            if approved_capabilities is None
            else approved_capabilities
        )
    )
    if set(capabilities) != set(manifest.capabilities):
        raise ValueError(
            "approved capabilities must exactly match the validated manifest"
        )

    return PluginApproval(
        plugin_id=manifest.plugin_id,
        decision=decision,
        manifest_sha256=candidate.manifest_sha256,
        executable_sha256=candidate.executable_sha256,
        approved_capabilities=capabilities,
    )


def validate_activation(
    candidate: PluginCandidate,
    approval: PluginApproval | None,
) -> ActivationValidation:
    """Fail closed if approval, manifest, binary, or requested capabilities drift."""
    errors: list[PluginIssue] = []
    manifest = candidate.validation.manifest
    if manifest is None or not candidate.validation.ok:
        return ActivationValidation(
            None,
            (
                PluginIssue(
                    "PLUGIN_NOT_VALIDATED",
                    "$",
                    "plugin must have a valid static manifest before activation",
                ),
            ),
        )

    if approval is None:
        errors.append(
            PluginIssue(
                "PLUGIN_APPROVAL_REQUIRED",
                "$",
                "plugin activation requires explicit owner approval",
            )
        )
    else:
        if approval.plugin_id != manifest.plugin_id:
            errors.append(
                PluginIssue(
                    "PLUGIN_APPROVAL_ID_MISMATCH",
                    "$.id",
                    "approval belongs to a different plugin",
                )
            )
        if approval.decision not in {PluginDecision.ADOPT, PluginDecision.ADAPT}:
            errors.append(
                PluginIssue(
                    "PLUGIN_DECISION_NOT_ACTIVE",
                    "$",
                    "only ADOPT or ADAPT plugins may be enabled",
                )
            )
        if approval.manifest_sha256 != candidate.manifest_sha256:
            errors.append(
                PluginIssue(
                    "PLUGIN_MANIFEST_CHANGED",
                    "$",
                    "plugin manifest changed after approval",
                )
            )
        if approval.executable_sha256 != candidate.executable_sha256:
            errors.append(
                PluginIssue(
                    "PLUGIN_EXECUTABLE_CHANGED",
                    "$",
                    "plugin executable changed after approval",
                )
            )
        if set(approval.approved_capabilities) != set(manifest.capabilities):
            errors.append(
                PluginIssue(
                    "PLUGIN_CAPABILITY_APPROVAL_MISMATCH",
                    "$.capabilities",
                    "approved capabilities no longer match the manifest",
                )
            )

    if not candidate.available or candidate.executable_path is None:
        errors.append(
            PluginIssue(
                "PLUGIN_EXECUTABLE_UNAVAILABLE",
                "$.executable",
                "validated plugin executable is unavailable",
            )
        )

    if errors:
        return ActivationValidation(None, tuple(errors))

    assert candidate.executable_path is not None
    return ActivationValidation(
        PluginActivation(
            plugin_id=manifest.plugin_id,
            executable_path=candidate.executable_path,
            capabilities=manifest.capabilities,
            requires_mandate=manifest.requires_mandate,
        ),
        (),
    )
