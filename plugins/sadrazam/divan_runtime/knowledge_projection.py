from __future__ import annotations

from collections import defaultdict

from .knowledge_contract import KnowledgeItem, KnowledgeKind
from .knowledge_store import KnowledgeStore


def render_book(
    store: KnowledgeStore,
    *,
    query: str = "",
    limit: int = 100,
) -> str:
    """Render a human-readable projection; structured local storage stays authoritative."""
    items = store.search(query, limit=limit)
    analytics = store.analytics()
    lines = [
        "# Divan Knowledge Book",
        "",
        "> Generated projection from the local Knowledge Fabric. "
        "Edit structured records, not this file.",
        "",
        "## Snapshot",
        "",
        f"- Items: {analytics['items']}",
        f"- Validated: {analytics['validated']}",
        f"- Lessons: {analytics['lessons']}",
        f"- Reused across projects: {analytics['reused_items']}",
        "",
    ]
    sections: dict[KnowledgeKind, list[KnowledgeItem]] = defaultdict(list)
    for item in items:
        sections[item.kind].append(item)
    for kind in KnowledgeKind:
        if not sections[kind]:
            continue
        lines.extend((f"## {kind.value.replace('-', ' ').title()}", ""))
        for item in sections[kind]:
            lines.extend(_item_lines(item))
    return "\n".join(lines).rstrip() + "\n"


def _item_lines(item: KnowledgeItem) -> list[str]:
    meta = [f"status={item.status.value}", f"confidence={item.confidence:.2f}"]
    if item.stack:
        meta.append(f"stack={', '.join(item.stack)}")
    if item.tags:
        meta.append(f"tags={', '.join(item.tags)}")
    lines = [
        f"### {item.title}",
        "",
        item.summary,
        "",
        f"- `{item.item_id}` · " + " · ".join(meta),
    ]
    if item.source_url:
        lines.append(f"- Source: {item.source_url} ({item.source_license})")
    lines.append("")
    return lines
