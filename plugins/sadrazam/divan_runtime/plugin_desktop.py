from __future__ import annotations

import ntpath
import pathlib
from dataclasses import asdict
from typing import Any

from .plugin_contract import PLUGIN_API_VERSION, PluginManifest
from .plugin_discovery import ExecutableLocator, load_plugin_candidate


def inspect_plugin_manifest(
    manifest_path: pathlib.Path | str,
    *,
    executable_locator: ExecutableLocator | None = None,
) -> dict[str, Any]:
    """Return a privacy-bounded trust report without executing plugin code."""
    if executable_locator is None:
        candidate = load_plugin_candidate(manifest_path)
    else:
        candidate = load_plugin_candidate(
            manifest_path,
            executable_locator=executable_locator,
        )

    manifest = candidate.validation.manifest
    stage = _stage(candidate.validation.ok, candidate.available)
    return {
        "api_version": PLUGIN_API_VERSION,
        "stage": stage,
        "validation": {
            "ok": candidate.validation.ok,
            "errors": [asdict(issue) for issue in candidate.validation.errors],
        },
        "manifest": None if manifest is None else _manifest_payload(manifest),
        "artifact": {
            "manifest_name": pathlib.Path(candidate.manifest_path).name,
            "manifest_sha256": candidate.manifest_sha256 or None,
            "executable_available": candidate.available,
            "executable_name": _basename(candidate.executable_path),
            "executable_sha256": candidate.executable_sha256,
        },
        "activation": {
            "supported": False,
            "reason": (
                "SDK v1 trust inspection does not persist approvals or execute "
                "third-party plugins"
            ),
        },
    }


def _stage(valid: bool, executable_available: bool) -> str:
    if not valid:
        return "invalid"
    if not executable_available:
        return "executable-missing"
    return "approval-required"


def _manifest_payload(manifest: PluginManifest) -> dict[str, Any]:
    return {
        "id": manifest.plugin_id,
        "display_name": manifest.display_name,
        "version": manifest.version,
        "kind": manifest.kind.value,
        "transport": manifest.transport.value,
        "executable": manifest.executable,
        "capabilities": list(manifest.capabilities),
        "source_url": manifest.source_url,
        "license_expression": manifest.license_expression,
        "license_evidence": manifest.license_evidence,
        "requires_mandate": manifest.requires_mandate,
        "mutating": manifest.mutating,
    }


def _basename(value: str | None) -> str | None:
    if value is None:
        return None
    return ntpath.basename(value)
