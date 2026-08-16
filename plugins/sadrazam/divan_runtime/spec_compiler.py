"""Compile one Ferman specification into canonical Divan contracts.

The proposal may come from a capable planner; the acceptance never does. This
module is the deterministic half: it validates shape, refuses unresolved
clarification markers, derives a dependency-ordered work package graph and
names the quality gates before any code exists.

It reads nothing from disk, writes nothing, and grants no execution authority.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from .spec_contract import (
    CLARIFICATION_MARKER,
    PRIORITIES,
    QUALITY_PROFILES,
    ArchitectureDecision,
    CompiledSpecification,
    ProjectContract,
    QualityRequirements,
    SpecCompilation,
    SpecIssue,
    UserStory,
    UxAcceptanceContract,
    WorkPackageDag,
    WorkPackageNode,
)

# Gates every project must pass, plus what each profile adds on top. A profile
# may only ever add obligations; nothing here can remove a baseline gate.
_BASELINE_GATES = ("tests", "typecheck", "lint", "independent-review")
_PROFILE_GATES: dict[str, tuple[str, ...]] = {
    "DESKTOP_WINDOWS": ("build", "installer-smoke", "restart-persistence"),
    "WEB_STANDARD": ("build", "browser-e2e", "accessibility"),
    "WEB_PAYMENT": (
        "build",
        "browser-e2e",
        "accessibility",
        "authz-negative",
        "secret-scan",
        "dependency-scan",
    ),
    "BACKEND_API": ("build", "authz-negative", "migration-verification"),
    "INTERNAL_TOOL": ("build",),
    "HIGH_SECURITY": (
        "build",
        "authz-negative",
        "secret-scan",
        "dependency-scan",
        "sast",
    ),
}
_PROFILE_EVIDENCE: dict[str, tuple[str, ...]] = {
    "DESKTOP_WINDOWS": ("installer-log", "restart-receipt"),
    "WEB_STANDARD": ("browser-trace",),
    "WEB_PAYMENT": ("browser-trace", "authz-matrix", "scan-report"),
    "BACKEND_API": ("authz-matrix", "migration-receipt"),
    "INTERNAL_TOOL": (),
    "HIGH_SECURITY": ("authz-matrix", "scan-report", "sast-report"),
}
_BASELINE_EVIDENCE = ("test-report", "diff-digest", "reviewer-verdict")


def compile_specification(payload: Any) -> SpecCompilation:
    """Validate one specification payload and compile it, or fail closed."""
    if not isinstance(payload, Mapping):
        return SpecCompilation(
            None,
            (SpecIssue("SPEC_ROOT_INVALID", "$", "specification root must be an object"),),
        )

    issues: list[SpecIssue] = []
    ferman = _required_text(payload, "ferman", issues)
    outcome = _required_text(payload, "outcome", issues)
    stories = _stories(payload.get("stories"), issues)
    requirements = _text_list(payload.get("requirements"), "$.requirements", issues)
    entities = _text_list(payload.get("entities"), "$.entities", issues, required=False)
    exclusions = _text_list(payload.get("exclusions"), "$.exclusions", issues, required=False)
    assumptions = _text_list(payload.get("assumptions"), "$.assumptions", issues, required=False)
    outcomes = _text_list(payload.get("measurable_outcomes"), "$.measurable_outcomes", issues)
    edge_cases = _text_list(payload.get("edge_cases"), "$.edge_cases", issues, required=False)
    decisions = _decisions(payload.get("architecture_decisions"), issues)
    profile = _profile(payload.get("quality_profile"), issues)

    _reject_unresolved_clarifications(payload, issues)

    if issues:
        return SpecCompilation(None, tuple(issues))

    assert ferman is not None and outcome is not None and profile is not None
    return SpecCompilation(
        CompiledSpecification(
            project=ProjectContract(
                ferman=ferman,
                outcome=outcome,
                stories=stories,
                requirements=requirements,
                entities=entities,
                exclusions=exclusions,
                assumptions=assumptions,
            ),
            ux=UxAcceptanceContract(
                measurable_outcomes=outcomes,
                edge_cases=edge_cases,
            ),
            architecture=decisions,
            work_packages=_work_packages(stories),
            quality=_quality(profile),
        ),
        (),
    )


def _required_text(payload: Mapping[Any, Any], field: str, issues: list[SpecIssue]) -> str | None:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        issues.append(
            SpecIssue(f"SPEC_{field.upper()}_REQUIRED", f"${field}", f"{field} is required")
        )
        return None
    return value.strip()


def _text_list(
    value: Any,
    path: str,
    issues: list[SpecIssue],
    *,
    required: bool = True,
) -> tuple[str, ...]:
    if value is None and not required:
        return ()
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        issues.append(SpecIssue("SPEC_TEXT_LIST_INVALID", path, "must be a list of non-empty strings"))
        return ()
    if required and not value:
        issues.append(SpecIssue("SPEC_TEXT_LIST_EMPTY", path, "at least one entry is required"))
        return ()
    return tuple(item.strip() for item in value)


def _stories(value: Any, issues: list[SpecIssue]) -> tuple[UserStory, ...]:
    if not isinstance(value, list) or not value:
        issues.append(SpecIssue("SPEC_STORIES_INVALID", "$.stories", "at least one user story is required"))
        return ()
    stories: list[UserStory] = []
    seen: set[str] = set()
    for index, row in enumerate(value):
        path = f"$.stories[{index}]"
        if not isinstance(row, Mapping):
            issues.append(SpecIssue("SPEC_STORY_INVALID", path, "story must be an object"))
            continue
        story_id = row.get("id")
        priority = row.get("priority")
        title = row.get("title")
        narrative = row.get("narrative")
        if not isinstance(story_id, str) or not story_id.strip():
            issues.append(SpecIssue("SPEC_STORY_ID_INVALID", path, "story id is required"))
            continue
        story_id = story_id.strip()
        if story_id in seen:
            issues.append(SpecIssue("SPEC_STORY_ID_DUPLICATE", path, f"duplicate story id: {story_id}"))
            continue
        seen.add(story_id)
        if priority not in PRIORITIES:
            issues.append(
                SpecIssue("SPEC_STORY_PRIORITY_INVALID", path, f"priority must be one of {PRIORITIES}")
            )
            continue
        if not isinstance(title, str) or not title.strip():
            issues.append(SpecIssue("SPEC_STORY_TITLE_INVALID", path, "story title is required"))
            continue
        if not isinstance(narrative, str) or not narrative.strip():
            issues.append(SpecIssue("SPEC_STORY_NARRATIVE_INVALID", path, "story narrative is required"))
            continue
        acceptance = _text_list(row.get("acceptance"), f"{path}.acceptance", issues)
        if not acceptance:
            continue
        stories.append(
            UserStory(
                story_id=story_id,
                title=title.strip(),
                priority=priority,
                narrative=narrative.strip(),
                acceptance=acceptance,
            )
        )
    return tuple(stories)


def _decisions(value: Any, issues: list[SpecIssue]) -> tuple[ArchitectureDecision, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        issues.append(
            SpecIssue("SPEC_DECISIONS_INVALID", "$.architecture_decisions", "must be a list")
        )
        return ()
    decisions: list[ArchitectureDecision] = []
    for index, row in enumerate(value):
        path = f"$.architecture_decisions[{index}]"
        if not isinstance(row, Mapping):
            issues.append(SpecIssue("SPEC_DECISION_INVALID", path, "decision must be an object"))
            continue
        fields = {name: row.get(name) for name in ("id", "title", "choice", "rationale")}
        if any(not isinstance(text, str) or not text.strip() for text in fields.values()):
            issues.append(
                SpecIssue(
                    "SPEC_DECISION_FIELD_INVALID",
                    path,
                    "id, title, choice and rationale are required",
                )
            )
            continue
        decisions.append(
            ArchitectureDecision(
                decision_id=str(fields["id"]).strip(),
                title=str(fields["title"]).strip(),
                choice=str(fields["choice"]).strip(),
                rationale=str(fields["rationale"]).strip(),
                alternatives=_text_list(
                    row.get("alternatives"), f"{path}.alternatives", issues, required=False
                ),
            )
        )
    return tuple(decisions)


def _profile(value: Any, issues: list[SpecIssue]) -> str | None:
    if value not in QUALITY_PROFILES:
        issues.append(
            SpecIssue(
                "SPEC_QUALITY_PROFILE_INVALID",
                "$.quality_profile",
                f"quality_profile must be one of {QUALITY_PROFILES}",
            )
        )
        return None
    return str(value)


def _reject_unresolved_clarifications(payload: Mapping[Any, Any], issues: list[SpecIssue]) -> None:
    """Refuse to compile a specification that still admits it is undecided."""
    for path, text in _walk_text(payload, "$"):
        if CLARIFICATION_MARKER in text:
            issues.append(
                SpecIssue(
                    "SPEC_CLARIFICATION_UNRESOLVED",
                    path,
                    "resolve the clarification marker before compiling",
                )
            )


def _walk_text(value: Any, path: str) -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield from _walk_text(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_text(item, f"{path}[{index}]")


def _work_packages(stories: tuple[UserStory, ...]) -> WorkPackageDag:
    """Order work by story priority, keeping equal priorities independent.

    Each priority band depends on the band above it, so a P2 package cannot be
    claimed ready while the P1 outcome it builds on is unbuilt. Packages inside
    one band carry no dependency on each other and stay safely parallel.
    """
    nodes: list[WorkPackageNode] = []
    previous_band: tuple[str, ...] = ()
    for priority in PRIORITIES:
        band = [story for story in stories if story.priority == priority]
        current: list[str] = []
        for story in band:
            package_id = f"WP-{priority}-{story.story_id}"
            nodes.append(
                WorkPackageNode(
                    package_id=package_id,
                    title=story.title,
                    story_id=story.story_id,
                    depends_on=previous_band,
                )
            )
            current.append(package_id)
        if current:
            previous_band = tuple(current)
    return WorkPackageDag(tuple(nodes))


def _quality(profile: str) -> QualityRequirements:
    return QualityRequirements(
        profile=profile,
        required_gates=_BASELINE_GATES + _PROFILE_GATES[profile],
        evidence_obligations=_BASELINE_EVIDENCE + _PROFILE_EVIDENCE[profile],
    )
