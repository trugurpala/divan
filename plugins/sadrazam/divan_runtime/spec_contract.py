"""Canonical Divan contracts compiled from one natural-language Ferman.

Divan borrows the specification-first shape proven by GitHub Spec Kit, but not
its runtime: no upstream CLI, template set, ``.specify`` state or workflow
registry is installed, and nothing here may grant execution or merge authority.
These dataclasses are the only shape a compiled specification may take, so a
specification stays a proposal until deterministic Divan validation accepts it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SPEC_SCHEMA_VERSION = 1

# A clarification marker means the author knew something was undecided. Planning
# on top of an unresolved marker is how a plan silently invents product intent.
CLARIFICATION_MARKER = "[NEEDS CLARIFICATION"

PRIORITIES = ("P1", "P2", "P3")

QUALITY_PROFILES = (
    "DESKTOP_WINDOWS",
    "WEB_STANDARD",
    "WEB_PAYMENT",
    "BACKEND_API",
    "INTERNAL_TOOL",
    "HIGH_SECURITY",
)


@dataclass(frozen=True)
class SpecIssue:
    """One deterministic reason a specification cannot be compiled."""

    code: str
    path: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UserStory:
    story_id: str
    title: str
    priority: str
    narrative: str
    acceptance: tuple[str, ...]


@dataclass(frozen=True)
class ProjectContract:
    """What the owner asked for, in machine-readable form."""

    ferman: str
    outcome: str
    stories: tuple[UserStory, ...]
    requirements: tuple[str, ...]
    entities: tuple[str, ...]
    exclusions: tuple[str, ...]
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class UxAcceptanceContract:
    """Observable outcomes a human can check without reading code."""

    measurable_outcomes: tuple[str, ...]
    edge_cases: tuple[str, ...]


@dataclass(frozen=True)
class ArchitectureDecision:
    decision_id: str
    title: str
    choice: str
    rationale: str
    alternatives: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkPackageNode:
    package_id: str
    title: str
    story_id: str
    depends_on: tuple[str, ...]


@dataclass(frozen=True)
class WorkPackageDag:
    nodes: tuple[WorkPackageNode, ...]

    @property
    def ready(self) -> tuple[str, ...]:
        return tuple(node.package_id for node in self.nodes if not node.depends_on)


@dataclass(frozen=True)
class QualityRequirements:
    """Gates this project must pass, named before any code is written."""

    profile: str
    required_gates: tuple[str, ...]
    evidence_obligations: tuple[str, ...]


@dataclass(frozen=True)
class CompiledSpecification:
    project: ProjectContract
    ux: UxAcceptanceContract
    architecture: tuple[ArchitectureDecision, ...]
    work_packages: WorkPackageDag
    quality: QualityRequirements

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SPEC_SCHEMA_VERSION,
            "project_contract": asdict(self.project),
            "ux_acceptance_contract": asdict(self.ux),
            "architecture_decisions": [asdict(item) for item in self.architecture],
            "work_package_dag": {
                "nodes": [asdict(node) for node in self.work_packages.nodes],
                "ready_package_ids": list(self.work_packages.ready),
            },
            "quality_requirements": asdict(self.quality),
            # A compiled specification is a proposal. Materialising it into real
            # Divan work packages stays a separate, explicitly approved step.
            "execution_authority": "not-granted",
        }


@dataclass(frozen=True)
class SpecCompilation:
    specification: CompiledSpecification | None
    issues: tuple[SpecIssue, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return self.specification is not None and not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SPEC_SCHEMA_VERSION,
            "ok": self.ok,
            "issues": [issue.to_dict() for issue in self.issues],
            "specification": (
                None if self.specification is None else self.specification.to_dict()
            ),
        }
