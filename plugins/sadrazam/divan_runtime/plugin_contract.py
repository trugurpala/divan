from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

PLUGIN_SCHEMA_VERSION = 1
PLUGIN_API_VERSION = 1


class PluginKind(StrEnum):
    EXECUTION_ENGINE = "execution-engine"
    REVIEWER = "reviewer"
    PROVIDER = "provider"
    EVIDENCE = "evidence"


class PluginTransport(StrEnum):
    SIDECAR_JSON_V1 = "sidecar-json-v1"


class PluginDecision(StrEnum):
    ADOPT = "ADOPT"
    ADAPT = "ADAPT"
    REFERENCE = "REFERENCE"
    REJECT = "REJECT"


ALLOWED_CAPABILITIES = frozenset(
    {
        "project.read",
        "project.mutate",
        "git.read",
        "git.mutate",
        "process.spawn",
        "network.outbound",
        "evidence.read",
        "evidence.emit",
        "review.read",
        "provider.read",
    }
)

DIVAN_RESERVED_CAPABILITIES = frozenset(
    {
        "authority.expand",
        "approval.grant",
        "evidence.rewrite",
        "merge.commit",
        "release.promote",
    }
)

MUTATING_CAPABILITIES = frozenset({"project.mutate", "git.mutate"})


@dataclass(frozen=True)
class PluginIssue:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class PluginManifest:
    plugin_id: str
    display_name: str
    version: str
    kind: PluginKind
    transport: PluginTransport
    executable: str
    capabilities: tuple[str, ...]
    source_url: str
    license_expression: str
    license_evidence: str
    requires_mandate: bool

    @property
    def mutating(self) -> bool:
        return bool(MUTATING_CAPABILITIES.intersection(self.capabilities))


@dataclass(frozen=True)
class ManifestValidation:
    manifest: PluginManifest | None
    errors: tuple[PluginIssue, ...]

    @property
    def ok(self) -> bool:
        return self.manifest is not None and not self.errors
