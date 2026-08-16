"""Validate where a plugin came from and under what licence.

Provenance is a separate question from manifest shape: it decides whether a
plugin may be trusted at all, not whether its declaration parses. Keeping it
in its own module also keeps the manifest validator readable as one screen of
rules rather than a growing wall.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from .plugin_contract import PluginIssue

_HTTPS_RE = re.compile(r"^https://\S+$")
_SPDX_RE = re.compile(r"^[A-Za-z0-9.+() -]+$")


def validate_source_url(value: Any, errors: list[PluginIssue]) -> str | None:
    """Validate the manifest source object and return its absolute HTTPS URL."""
    if not isinstance(value, Mapping) or set(value) != {"url"}:
        errors.append(
            PluginIssue(
                "PLUGIN_SOURCE_INVALID",
                "$.source",
                "source must contain only url",
            )
        )
        return None
    url = value.get("url")
    if not isinstance(url, str) or not _HTTPS_RE.fullmatch(url):
        errors.append(
            PluginIssue(
                "PLUGIN_SOURCE_URL_INVALID",
                "$.source.url",
                "URL must be absolute HTTPS",
            )
        )
        return None
    return url


def validate_license(
    value: Any, errors: list[PluginIssue]
) -> tuple[str | None, str | None]:
    """Validate the licence claim and the HTTPS evidence backing it."""
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
    # A whitespace-only expression matches the character class but claims
    # nothing, and would be rendered to the owner as a valid licence.
    if (
        not isinstance(expression, str)
        or not expression.strip()
        or not _SPDX_RE.fullmatch(expression)
    ):
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
