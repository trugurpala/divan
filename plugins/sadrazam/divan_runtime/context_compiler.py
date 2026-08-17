"""Give a worker the smallest useful context, and be honest about the cost.

Sending the whole repository and the whole knowledge book is expensive, buries
the relevant fact and invites the model to invent structure. This compiler
assembles a bounded pack by priority and reports exactly what it left out and
why, because a silently truncated context is worse than a small one.

Token counts are labelled with their confidence. Nothing here claims exact
numbers it cannot measure.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Iterable, Mapping

CONTEXT_SCHEMA_VERSION = 1

#: Rough characters-per-token for mixed prose and code. Only ever used to
#: produce an ``estimated`` figure, never reported as exact.
_CHARS_PER_TOKEN = 4


class Detail(StrEnum):
    """Progressive retrieval levels, cheapest first."""

    #: Just enough to know the thing exists.
    METADATA = "L0"
    #: A summary a planner can reason over.
    SUMMARY = "L1"
    #: Signatures, symbols, or the exact failing lines.
    SYMBOLS = "L2"
    #: The bounded full text.
    FULL = "L3"


class TokenConfidence(StrEnum):
    EXACT = "exact"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ContextItem:
    """One piece of context, with where it came from and how big it is."""

    key: str
    kind: str
    detail: Detail
    text: str
    provenance: str
    #: Lower sorts first. The pack is filled in this order, so the budget is
    #: spent on the task contract before it is spent on background reading.
    priority: int = 50

    @property
    def estimated_tokens(self) -> int:
        return max(1, len(self.text) // _CHARS_PER_TOKEN)


@dataclass(frozen=True)
class OmittedItem:
    key: str
    kind: str
    reason: str
    estimated_tokens: int


@dataclass(frozen=True)
class ContextPack:
    task_id: str
    items: tuple[ContextItem, ...]
    omitted: tuple[OmittedItem, ...]
    budget_tokens: int
    estimated_tokens: int
    exact_tokens: int | None
    token_confidence: TokenConfidence
    truncated: bool
    #: Present when the pack could not be built within budget at all.
    budget_exceeded: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)

    def render(self) -> str:
        return "\n\n".join(
            f"# {item.kind}: {item.key} ({item.detail.value})\n{item.text}"
            for item in self.items
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": CONTEXT_SCHEMA_VERSION,
            "task_id": self.task_id,
            "items": [
                {
                    **asdict(item),
                    "detail": item.detail.value,
                    "estimated_tokens": item.estimated_tokens,
                    # The text itself is not repeated in the manifest.
                    "text": None,
                }
                for item in self.items
            ],
            "omitted": [asdict(item) for item in self.omitted],
            "budget_tokens": self.budget_tokens,
            "estimated_tokens": self.estimated_tokens,
            "exact_tokens": self.exact_tokens,
            "token_confidence": self.token_confidence.value,
            "truncated": self.truncated,
            "budget_exceeded": self.budget_exceeded,
            "notes": list(self.notes),
            "source_provenance": sorted({item.provenance for item in self.items}),
        }


def _item(
    key: str,
    kind: str,
    detail: Detail,
    text: Any,
    provenance: str,
    priority: int,
) -> ContextItem | None:
    if text is None:
        return None
    body = text if isinstance(text, str) else str(text)
    if not body.strip():
        return None
    return ContextItem(key, kind, detail, body.strip(), provenance, priority)


def build_candidates(
    *,
    task_contract: Mapping[str, Any],
    project_contract: Mapping[str, Any] | None = None,
    ux_contract: Mapping[str, Any] | None = None,
    architecture_decisions: Iterable[Mapping[str, Any]] = (),
    recalled_memory: Iterable[Mapping[str, Any]] = (),
    incidents: Iterable[Mapping[str, Any]] = (),
    source_files: Iterable[Mapping[str, Any]] = (),
    related_tests: Iterable[Mapping[str, Any]] = (),
    current_diff: str | None = None,
    current_failure: str | None = None,
) -> list[ContextItem]:
    """Order every candidate by how much the worker needs it.

    The failing evidence and the task contract come first because a worker
    that only gets background reading will guess at the actual job.
    """
    candidates: list[ContextItem | None] = [
        _item(
            "task-contract",
            "TaskContract",
            Detail.FULL,
            task_contract.get("summary") or task_contract.get("title"),
            "divan:task",
            0,
        ),
        _item(
            "acceptance",
            "TaskContract",
            Detail.FULL,
            "\n".join(str(line) for line in task_contract.get("acceptance", ())),
            "divan:task",
            1,
        ),
        _item("current-failure", "Failure", Detail.FULL, current_failure, "divan:evidence", 2),
        _item("current-diff", "Diff", Detail.FULL, current_diff, "divan:worktree", 3),
        _item(
            "product-contract",
            "ProjectContract",
            Detail.SUMMARY,
            None if project_contract is None else project_contract.get("outcome"),
            "divan:spec-compiler",
            10,
        ),
        _item(
            "ux-acceptance",
            "UXContract",
            Detail.SUMMARY,
            None
            if ux_contract is None
            else "\n".join(str(x) for x in ux_contract.get("measurable_outcomes", ())),
            "divan:spec-compiler",
            11,
        ),
    ]
    for index, decision in enumerate(architecture_decisions):
        candidates.append(
            _item(
                str(decision.get("decision_id", f"adr-{index}")),
                "ArchitectureDecision",
                Detail.SUMMARY,
                f"{decision.get('title')}: {decision.get('choice')} — {decision.get('rationale')}",
                "divan:spec-compiler",
                20 + index,
            )
        )
    for index, lesson in enumerate(incidents):
        candidates.append(
            _item(
                str(lesson.get("item_id", f"incident-{index}")),
                "Incident",
                Detail.SUMMARY,
                lesson.get("summary"),
                "divan:agency-memory",
                30 + index,
            )
        )
    for index, memory in enumerate(recalled_memory):
        candidates.append(
            _item(
                str(memory.get("item_id", f"memory-{index}")),
                "Memory",
                Detail.SUMMARY,
                memory.get("summary"),
                "divan:agency-memory",
                40 + index,
            )
        )
    for index, test in enumerate(related_tests):
        candidates.append(
            _item(
                str(test.get("path", f"test-{index}")),
                "RelatedTest",
                Detail.SYMBOLS,
                test.get("symbols") or test.get("text"),
                "divan:repo",
                50 + index,
            )
        )
    for index, source in enumerate(source_files):
        candidates.append(
            _item(
                str(source.get("path", f"source-{index}")),
                "Source",
                Detail(source.get("detail", Detail.SYMBOLS.value)),
                source.get("symbols") or source.get("text"),
                "divan:repo",
                60 + index,
            )
        )
    return [item for item in candidates if item is not None]


def compile_context(
    task_id: str,
    candidates: Iterable[ContextItem],
    *,
    budget_tokens: int,
    exact_tokens: int | None = None,
) -> ContextPack:
    """Fill the pack in priority order and report everything left out.

    Nothing is dropped quietly: each omission records why, and the pack says
    whether it was truncated at all. If even the highest priority item does
    not fit, the pack is marked budget_exceeded rather than shipped half-made.
    """
    if budget_tokens <= 0:
        raise ValueError("context budget must be positive")

    ordered = sorted(candidates, key=lambda item: (item.priority, item.key))
    chosen: list[ContextItem] = []
    omitted: list[OmittedItem] = []
    spent = 0
    for item in ordered:
        cost = item.estimated_tokens
        if spent + cost <= budget_tokens:
            chosen.append(item)
            spent += cost
            continue
        omitted.append(
            OmittedItem(
                key=item.key,
                kind=item.kind,
                reason="token budget reached before this item",
                estimated_tokens=cost,
            )
        )

    confidence = (
        TokenConfidence.EXACT if exact_tokens is not None else TokenConfidence.ESTIMATED
    )
    notes: list[str] = []
    if omitted:
        notes.append(f"{len(omitted)} item(s) omitted to stay inside the budget")
    budget_exceeded = not chosen and bool(ordered)
    if budget_exceeded:
        notes.append("no item fits the budget; raise the budget or shrink the task")

    return ContextPack(
        task_id=task_id,
        items=tuple(chosen),
        omitted=tuple(omitted),
        budget_tokens=budget_tokens,
        estimated_tokens=spent,
        exact_tokens=exact_tokens,
        token_confidence=confidence,
        truncated=bool(omitted),
        budget_exceeded=budget_exceeded,
        notes=tuple(notes),
    )


def unknown_usage_pack(task_id: str, budget_tokens: int) -> ContextPack:
    """A pack for a provider that reports no usage at all.

    Honest 'unknown' beats a fabricated number.
    """
    return ContextPack(
        task_id=task_id,
        items=(),
        omitted=(),
        budget_tokens=budget_tokens,
        estimated_tokens=0,
        exact_tokens=None,
        token_confidence=TokenConfidence.UNKNOWN,
        truncated=False,
        notes=("provider does not report token usage",),
    )
