from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class KnowledgeKind(StrEnum):
    PROJECT_PROFILE = "project-profile"
    PATTERN = "pattern"
    LESSON = "lesson"
    DECISION = "decision"
    RECIPE = "recipe"
    SOURCE = "source"
    TOOL = "tool"


class KnowledgeStatus(StrEnum):
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    DEPRECATED = "deprecated"


class KnowledgeOrigin(StrEnum):
    INTERNAL = "internal"
    USER = "user"
    EXTERNAL = "external"


class ObservationOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class KnowledgeItem:
    item_id: str
    kind: KnowledgeKind
    title: str
    summary: str
    tags: tuple[str, ...] = ()
    stack: tuple[str, ...] = ()
    origin: KnowledgeOrigin = KnowledgeOrigin.INTERNAL
    status: KnowledgeStatus = KnowledgeStatus.CANDIDATE
    source_project: str | None = None
    source_url: str | None = None
    source_license: str | None = None
    source_sha256: str | None = None
    problem_signature: str | None = None
    solution_signature: str | None = None
    evidence_sha256: str | None = None
    confidence: float = 0.5
    created_at: str = ""
    last_verified_at: str | None = None

    def __post_init__(self) -> None:
        if not _ID_RE.fullmatch(self.item_id):
            raise ValueError("knowledge item id must be lowercase kebab-case")
        if not self.title.strip() or not self.summary.strip():
            raise ValueError("knowledge title and summary are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("knowledge confidence must be between 0 and 1")
        if self.source_url is not None and not self.source_url.startswith("https://"):
            raise ValueError("knowledge source_url must use HTTPS")
        if self.origin is KnowledgeOrigin.EXTERNAL and (
            not self.source_url or not self.source_license
        ):
            raise ValueError("external knowledge requires source URL and license")
        for value in (
            self.source_sha256,
            self.problem_signature,
            self.solution_signature,
            self.evidence_sha256,
        ):
            if value is not None and not _SHA256_RE.fullmatch(value):
                raise ValueError("knowledge digests must be lowercase SHA-256")
        object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(self, "summary", self.summary.strip())
        object.__setattr__(self, "tags", _normalized(self.tags))
        object.__setattr__(self, "stack", _normalized(self.stack))


def _normalized(values: tuple[str, ...]) -> tuple[str, ...]:
    cleaned = {value.strip().casefold() for value in values if value.strip()}
    return tuple(sorted(cleaned))
