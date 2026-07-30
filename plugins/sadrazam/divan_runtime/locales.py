"""Validated Turkish and English reader-facing messages for Divan."""

from __future__ import annotations

import json
import os
import pathlib
import string
from collections.abc import Mapping
from typing import Any

SUPPORTED_LANGUAGES = ("en", "tr")
_FORMATTER = string.Formatter()


def placeholders(value: str) -> frozenset[str]:
    """Return the named replacement fields used by a message."""
    return frozenset(
        field_name
        for _, field_name, _, _ in _FORMATTER.parse(value)
        if field_name is not None
    )


def load_messages(directory: pathlib.Path) -> dict[str, dict[str, str]]:
    """Load the message catalog and fail closed on locale drift."""
    path = pathlib.Path(directory) / "messages.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot load message catalog: {path.name}") from error
    if not isinstance(value, dict) or not value:
        raise ValueError("message catalog must be a non-empty object")

    catalog: dict[str, dict[str, str]] = {}
    expected_languages = set(SUPPORTED_LANGUAGES)
    for key, translations in value.items():
        if not isinstance(key, str) or not key:
            raise ValueError("message keys must be non-empty strings")
        if not isinstance(translations, dict):
            raise ValueError(f"message translations must be an object: {key}")
        if set(translations) != expected_languages:
            raise ValueError(f"message locale parity failed: {key}")
        if not all(
            isinstance(translations[language], str)
            and translations[language].strip()
            for language in SUPPORTED_LANGUAGES
        ):
            raise ValueError(f"message translations must be non-empty: {key}")
        if placeholders(translations["en"]) != placeholders(translations["tr"]):
            raise ValueError(f"message placeholder parity failed: {key}")
        catalog[key] = {
            language: translations[language] for language in SUPPORTED_LANGUAGES
        }
    return catalog


def resolve_language(
    requested: str | None,
    environment: Mapping[str, str] | None = None,
) -> str:
    """Resolve an explicit or bounded environment language."""
    value = "auto" if requested is None else requested.casefold()
    if value in SUPPORTED_LANGUAGES:
        return value
    if value != "auto":
        raise ValueError("language must be auto, en, or tr")
    source = os.environ if environment is None else environment
    observed = " ".join(
        source.get(name, "") for name in ("LC_ALL", "LC_MESSAGES", "LANG")
    ).casefold()
    return "tr" if observed.startswith("tr") or " tr_" in observed else "en"


def message(
    catalog: Mapping[str, Mapping[str, str]],
    key: str,
    language: str,
    **values: Any,
) -> str:
    """Render one validated message without permitting undeclared fields."""
    if key not in catalog:
        raise ValueError(f"unknown message key: {key}")
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError("language must be en or tr")
    template = catalog[key][language]
    if placeholders(template) != set(values):
        raise ValueError(f"message values do not match placeholders: {key}")
    return template.format(**values)
