"""Local, provenance-aware prompt catalogue for Ottoman Desktop.

The catalogue data is the CC0 prompt dataset from f/prompts.chat.  Ottoman owns
the search, selection and task hand-off code so the library stays optional and
does not replace the product's planning or approval workflow.
"""
from __future__ import annotations

import csv
import hashlib
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping

SOURCE_REPOSITORY = "https://github.com/f/prompts.chat"
SOURCE_COMMIT = "f1c515686725fcd84a90d361b9eeb11eb15edb17"
SOURCE_LICENSE = "CC0-1.0"
DATA_FILE = Path(__file__).with_name("data") / "prompts-chat.csv"
_SLUG_WORD = re.compile(r"[^a-z0-9]+")
_EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_ANONYMOUS_CONTRIBUTOR = "community"


@dataclass(frozen=True)
class PromptTemplate:
    identifier: str
    title: str
    prompt: str
    for_developers: bool
    kind: str
    contributor: str

    def summary(self) -> dict[str, object]:
        preview = " ".join(self.prompt.split())
        return {
            "id": self.identifier,
            "title": self.title,
            "preview": preview[:280] + ("…" if len(preview) > 280 else ""),
            "for_developers": self.for_developers,
            "type": self.kind,
            "contributor": self.contributor,
        }

    def detail(self) -> dict[str, object]:
        return {**self.summary(), "prompt": self.prompt, "source": provenance()}


def provenance() -> dict[str, str]:
    return {
        "repository": SOURCE_REPOSITORY,
        "commit": SOURCE_COMMIT,
        "license": SOURCE_LICENSE,
        "dataset": "prompts.csv",
    }


def _identifier(title: str, prompt: str) -> str:
    base = _SLUG_WORD.sub("-", title.casefold()).strip("-")[:72] or "prompt"
    digest = hashlib.sha256(f"{title}\n{prompt}".encode("utf-8")).hexdigest()[:12]
    return f"{base}-{digest}"


def _redact_email(value: str) -> str:
    """Keep a useful prompt while preventing imported contact details from surfacing."""
    return _EMAIL.sub("[redacted]", value)


@lru_cache(maxsize=1)
def _templates() -> tuple[PromptTemplate, ...]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"prompt catalogue is missing: {DATA_FILE}")
    csv.field_size_limit(min(sys.maxsize, 2_147_483_647))
    rows: list[PromptTemplate] = []
    with DATA_FILE.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            title = _redact_email(str(row.get("act") or "")).strip()
            prompt = _redact_email(str(row.get("prompt") or "")).strip()
            if not title or not prompt:
                continue
            rows.append(
                PromptTemplate(
                    identifier=_identifier(title, prompt),
                    title=title,
                    prompt=prompt,
                    for_developers=str(row.get("for_devs") or "").strip().casefold() == "true",
                    kind=str(row.get("type") or "TEXT").strip() or "TEXT",
                    contributor=_ANONYMOUS_CONTRIBUTOR,
                )
            )
    return tuple(rows)


def search(query: str = "", *, limit: int = 30) -> list[dict[str, object]]:
    if not isinstance(query, str):
        raise ValueError("query must be text")
    if not isinstance(limit, int) or not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")
    terms = [term for term in query.casefold().split() if term]
    matches: list[PromptTemplate] = []
    for template in _templates():
        haystack = "\n".join((template.title, template.prompt, template.kind, template.contributor)).casefold()
        if all(term in haystack for term in terms):
            matches.append(template)
            if len(matches) == limit:
                break
    return [template.summary() for template in matches]


def get(identifier: str) -> PromptTemplate:
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("prompt id is required")
    wanted = identifier.strip()
    for template in _templates():
        if template.identifier == wanted:
            return template
    raise KeyError(wanted)


def catalogue_size() -> int:
    return len(_templates())


def render(identifier: str, values: Mapping[str, object] | None = None) -> dict[str, object]:
    """Return a selected template with only explicit ``{{name}}`` placeholders filled.

    Curly braces already present in community prompts are intentionally untouched;
    treating them as variables would silently corrupt many programming examples.
    """
    template = get(identifier)
    replacements = values or {}
    if not isinstance(replacements, Mapping):
        raise ValueError("variables must be an object")
    rendered = template.prompt
    for name, value in replacements.items():
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", name):
            raise ValueError("variable names must be simple identifiers")
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError("variable values must be scalar text")
        rendered = rendered.replace("{{" + name + "}}", str(value))
    return {
        "id": template.identifier,
        "title": template.title,
        "prompt": rendered,
        "source": provenance(),
    }
