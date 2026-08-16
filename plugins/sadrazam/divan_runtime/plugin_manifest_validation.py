from __future__ import annotations

import re
from enum import StrEnum
from typing import Any, Mapping

from .plugin_contract import (
    ALLOWED_CAPABILITIES,
    DIVAN_RESERVED_CAPABILITIES,
    MUTATING_CAPABILITIES,
    PLUGIN_API_VERSION,
    PLUGIN_SCHEMA_VERSION,
    ManifestValidation,
    PluginIssue,
    PluginKind,
    PluginManifest,
    PluginTransport,
)

_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_EXECUTABLE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_HTTPS_RE = re.compile(r"^https://\S+$")
_SPDX_RE = re.compile(r"^[A-Za-z0-9.+() -]+$")
_READ_ONLY_KINDS = frozenset(
    {PluginKind.REVIEWER, PluginKind.PROVIDER, PluginKind.EVIDENCE}
)
_ROOT_FIELDS = frozenset(
    {
        "schema_version",
        "id",
        "display_name",
        "version",
        "api_version",
        "kind",
        "transport",
        "executable",
        "capabilities",
        "source",
        "license",
        "requires_mandate",
    }
)


def validate_manifest_payload(payload: Any) -> ManifestValidation:
    if not isinstance(payload, Mapping):
        return ManifestValidation(
            None,
            (
                PluginIssue(
                    "PLUGIN_MANIFEST_ROOT_INVALID",
                    "$",
                    "manifest root must be an object",
                ),
            ),
        )

    errors: list[PluginIssue] = []
    _validate_root_fields(payload, errors)
    _validate_versions(payload, errors)
    plugin_id, display_name, version = _validate_identity(payload, errors)
    kind, transport = _validate_plugin_types(payload, errors)
    executable, capabilities, requires_mandate = _validate_runtime_fields(
        payload, errors
    )
    _validate_capability_policy(kind, capabilities, requires_mandate, errors)
    source_url = _object_url(payload.get("source"), "source", errors)
    license_expression, license_evidence = _license(payload.get("license"), errors)

    if errors:
        return ManifestValidation(None, tuple(errors))

    assert plugin_id is not None
    assert display_name is not None
    assert version is not None
    assert kind is not None
    assert transport is not None
    assert executable is not None
    assert source_url is not None
    assert license_expression is not None
    assert license_evidence is not None
    return ManifestValidation(
        PluginManifest(
            plugin_id=plugin_id,
            display_name=display_name,
            version=version,
            kind=kind,
            transport=transport,
            executable=executable,
            capabilities=capabilities,
            source_url=source_url,
            license_expression=license_expression,
            license_evidence=license_evidence,
            requires_mandate=requires_mandate,
        ),
        (),
    )


def _validate_root_fields(
    payload: Mapping[Any, Any], errors: list[PluginIssue]
) -> None:
    for field in sorted(set(payload) - _ROOT_FIELDS):
        errors.append(
            PluginIssue(
                "PLUGIN_MANIFEST_UNKNOWN_FIELD",
                f"$.{field}",
                f"unknown plugin manifest field: {field}",
            )
        )


def _validate_versions(
    payload: Mapping[Any, Any], errors: list[PluginIssue]
) -> None:
    if payload.get("schema_version") != PLUGIN_SCHEMA_VERSION:
        errors.append(
            PluginIssue(
                "PLUGIN_SCHEMA_VERSION_INVALID",
                "$.schema_version",
                f"schema_version must be {PLUGIN_SCHEMA_VERSION}",
            )
        )
    if payload.get("api_version") != PLUGIN_API_VERSION:
        errors.append(
            PluginIssue(
                "PLUGIN_API_VERSION_INCOMPATIBLE",
                "$.api_version",
                f"api_version must be {PLUGIN_API_VERSION}",
            )
        )


def _validate_identity(
    payload: Mapping[Any, Any], errors: list[PluginIssue]
) -> tuple[str | None, str | None, str | None]:
    plugin_id = payload.get("id")
    display_name = payload.get("display_name")
    version = payload.get("version")

    if not isinstance(plugin_id, str) or not _ID_RE.fullmatch(plugin_id):
        errors.append(
            PluginIssue("PLUGIN_ID_INVALID", "$.id", "id must be lowercase kebab-case")
        )
        plugin_id = None
    if not isinstance(display_name, str) or not display_name.strip():
        errors.append(
            PluginIssue(
                "PLUGIN_DISPLAY_NAME_INVALID",
                "$.display_name",
                "display_name is required",
            )
        )
        display_name = None
    if not isinstance(version, str) or not version.strip():
        errors.append(
            PluginIssue("PLUGIN_VERSION_INVALID", "$.version", "version is required")
        )
        version = None

    return (
        plugin_id,
        None if display_name is None else display_name.strip(),
        None if version is None else version.strip(),
    )


def _validate_plugin_types(
    payload: Mapping[Any, Any], errors: list[PluginIssue]
) -> tuple[PluginKind | None, PluginTransport | None]:
    kind = _parse_enum(
        payload.get("kind"), PluginKind, "PLUGIN_KIND_INVALID", "$.kind", errors
    )
    transport = _parse_enum(
        payload.get("transport"),
        PluginTransport,
        "PLUGIN_TRANSPORT_INVALID",
        "$.transport",
        errors,
    )
    return kind, transport


def _validate_runtime_fields(
    payload: Mapping[Any, Any], errors: list[PluginIssue]
) -> tuple[str | None, tuple[str, ...], bool]:
    executable = payload.get("executable")
    if not isinstance(executable, str) or not _EXECUTABLE_RE.fullmatch(executable):
        errors.append(
            PluginIssue(
                "PLUGIN_EXECUTABLE_INVALID",
                "$.executable",
                "executable must be a bare command name, never a path or shell string",
            )
        )
        executable = None

    capabilities = _validate_capabilities(payload.get("capabilities"), errors)
    requires_mandate = payload.get("requires_mandate")
    if not isinstance(requires_mandate, bool):
        errors.append(
            PluginIssue(
                "PLUGIN_MANDATE_FLAG_INVALID",
                "$.requires_mandate",
                "requires_mandate must be a boolean",
            )
        )
        requires_mandate = False
    return executable, capabilities, requires_mandate


def _validate_capability_policy(
    kind: PluginKind | None,
    capabilities: tuple[str, ...],
    requires_mandate: bool,
    errors: list[PluginIssue],
) -> None:
    mutating = MUTATING_CAPABILITIES.intersection(capabilities)
    if kind in _READ_ONLY_KINDS and mutating:
        assert kind is not None
        errors.append(
            PluginIssue(
                "PLUGIN_READ_ONLY_KIND_MUTATES",
                "$.capabilities",
                f"{kind.value} plugins cannot request project/git mutation",
            )
        )
    if mutating and not requires_mandate:
        errors.append(
            PluginIssue(
                "PLUGIN_MUTATION_REQUIRES_MANDATE",
                "$.requires_mandate",
                "mutating plugins must require a Divan-owned mandate",
            )
        )


def _validate_capabilities(
    value: Any, errors: list[PluginIssue]
) -> tuple[str, ...]:
    if not isinstance(value, list):
        errors.append(
            PluginIssue(
                "PLUGIN_CAPABILITIES_INVALID",
                "$.capabilities",
                "capabilities must be an array",
            )
        )
        return ()

    parsed: list[str] = []
    seen: set[str] = set()
    for index, capability in enumerate(value):
        _validate_capability(capability, index, parsed, seen, errors)
    return tuple(sorted(parsed))


def _validate_capability(
    capability: Any,
    index: int,
    parsed: list[str],
    seen: set[str],
    errors: list[PluginIssue],
) -> None:
    path = f"$.capabilities[{index}]"
    if not isinstance(capability, str):
        errors.append(
            PluginIssue("PLUGIN_CAPABILITY_INVALID", path, "capability must be a string")
        )
        return
    if capability in seen:
        errors.append(
            PluginIssue(
                "PLUGIN_CAPABILITY_DUPLICATE",
                path,
                f"duplicate capability: {capability}",
            )
        )
        return

    seen.add(capability)
    parsed.append(capability)
    if capability in DIVAN_RESERVED_CAPABILITIES:
        errors.append(
            PluginIssue(
                "PLUGIN_CAPABILITY_RESERVED",
                path,
                f"{capability} is owned by Divan and cannot be delegated",
            )
        )
    elif capability not in ALLOWED_CAPABILITIES:
        errors.append(
            PluginIssue(
                "PLUGIN_CAPABILITY_UNKNOWN",
                path,
                f"unsupported capability: {capability}",
            )
        )


def _object_url(
    value: Any, name: str, errors: list[PluginIssue]
) -> str | None:
    if not isinstance(value, Mapping) or set(value) != {"url"}:
        errors.append(
            PluginIssue(
                f"PLUGIN_{name.upper()}_INVALID",
                f"$.{name}",
                f"{name} must contain only url",
            )
        )
        return None
    url = value.get("url")
    if not isinstance(url, str) or not _HTTPS_RE.fullmatch(url):
        errors.append(
            PluginIssue(
                f"PLUGIN_{name.upper()}_URL_INVALID",
                f"$.{name}.url",
                "URL must be absolute HTTPS",
            )
        )
        return None
    return url


def _license(
    value: Any, errors: list[PluginIssue]
) -> tuple[str | None, str | None]:
    required = {"spdx_expression", "evidence"}
    if not isinstance(value, Mapping) or set(value) != required:
        errors.append(
            PluginIssue(
                "PLUGIN_LICENSE_INVALID",
                "$.license",
                "license must contain SPDX expression and evidence",
            )
        )
        return None, None
    expression = value.get("spdx_expression")
    evidence = value.get("evidence")
    if not isinstance(expression, str) or not _SPDX_RE.fullmatch(expression):
        errors.append(
            PluginIssue(
                "PLUGIN_LICENSE_EXPRESSION_INVALID",
                "$.license.spdx_expression",
                "invalid SPDX expression",
            )
        )
        expression = None
    if not isinstance(evidence, str) or not _HTTPS_RE.fullmatch(evidence):
        errors.append(
            PluginIssue(
                "PLUGIN_LICENSE_EVIDENCE_INVALID",
                "$.license.evidence",
                "license evidence must be HTTPS",
            )
        )
        evidence = None
    return expression, evidence


def _parse_enum(
    value: Any,
    enum_type: type[StrEnum],
    code: str,
    path: str,
    errors: list[PluginIssue],
):
    try:
        return enum_type(value)
    except (TypeError, ValueError):
        errors.append(PluginIssue(code, path, "unsupported value"))
        return None
