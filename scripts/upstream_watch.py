#!/usr/bin/env python3
"""Aylik nobet: vendored skill'leri taze upstream klonlariyla karsilastir.

Cikis kodlari: 0 temiz, 2 kurasyon gerektiren fark, 1 denetim calismadi.
"""

# English canonical implementation.
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile

from upstream_baseline import (
    baseline_errors,
    pinned_sources,
)
from upstream_baseline import (
    skill_map as harita,
)
from upstream_baseline import tree_sha256 as agac_sha256
from upstream_baseline import tree_signature as imza

REPOLAR = [
    "obra/superpowers",
    "anthropics/skills",
    "vercel-labs/agent-skills",
    "nextlevelbuilder/ui-ux-pro-max-skill",
]
OZGUN = {
    "arama-ustasi",
    "baglam-muhafizi",
    "sadrazam",
    "vezir-yetistirme",
    "defterdar",
    "musavir",
    "ordu-nizami",
    "temkin",
    "kural-hazinesi",
    "kaynak-kuratori",
    "product-design-audit",
}
KURASYON_KAYNAKLARI = (
    "PatrickJS/awesome-cursorrules",
    "muratcankoylan/Agent-Skills-for-Context-Engineering",
)
# Bilincli farklarda upstream dosyasinin bilinen taban imzasi da sabitlenir.
# Boylece upstream ayni dosyayi degistirirse izin listesi bu degisimi gizlemez.
YAMALAR = {
    ("claude-api", "SKILL.md"): "1d08b3be1c02b6bd2d8c966b1645e234fbb36454d2dd4cbd39802d2f321bd0f4",
    ("vercel-react-best-practices", "AGENTS.md"): "fc93e7421177bbf869cce892bc60a6c83a4517d974bc3bf65c4e2c1e58a6ccf6",
}
KOK = pathlib.Path(__file__).resolve().parent.parent


def curated_drift(temporary: pathlib.Path, source_pins: dict[str, str]) -> list[str]:
    changes: list[str] = []
    for order, repository in enumerate(KURASYON_KAYNAKLARI):
        baseline = source_pins[repository]
        current = klonla(repository, temporary / f"curated-{order}")
        if current != baseline:
            changes.append(
                f"- **{repository}**: kure edilen kaynak ilerledi "
                f"({baseline[:12]} -> {current[:12]})"
            )
    return changes


def klonla(repo: str, hedef: pathlib.Path) -> str:
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", f"https://github.com/{repo}", str(hedef)],
        check=True,
        timeout=120,
    )
    return subprocess.check_output(
        ["git", "-C", str(hedef), "rev-parse", "HEAD"],
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    ).strip()


def denetle() -> list[str]:
    degisen: list[str] = []
    baseline_hatalari, reviews = baseline_errors(KOK)
    if baseline_hatalari:
        return [f"- **upstream baseline**: {error}" for error in baseline_hatalari]
    review_map = {review["skill"]: review for review in reviews}
    source_pins = pinned_sources(KOK)
    with tempfile.TemporaryDirectory(prefix="divan-nobet-") as gecici:
        tmp = pathlib.Path(gecici)
        upstream: dict[str, pathlib.Path] = {}
        upstream_sources: dict[str, str] = {}
        upstream_commits: dict[str, str] = {}

        for sira, repo in enumerate(REPOLAR):
            hedef = tmp / f"upstream-{sira}"
            upstream_commits[repo] = klonla(repo, hedef)
            bulunan = harita(hedef)
            upstream.update(bulunan)
            upstream_sources.update({name: repo for name in bulunan})

        degisen.extend(curated_drift(tmp, source_pins))

        for skill_md in sorted(KOK.glob("plugins/*/skills/*/SKILL.md")):
            eslesme = re.search(
                r"^name:\s*(.+)$", skill_md.read_text(errors="ignore")[:4000], re.M
            )
            if not eslesme:
                continue
            ad = eslesme.group(1).strip()
            if ad in OZGUN:
                continue
            if ad not in upstream:
                degisen.append(f"- **{ad}**: upstream skill artik bulunamadi")
                continue

            review = review_map.get(ad)
            if review:
                source = upstream_sources.get(ad)
                if (
                    source == review.get("source")
                    and upstream_commits.get(str(source)) == review.get("reviewed_head")
                    and agac_sha256(skill_md.parent) == review.get("local_tree_sha256")
                ):
                    continue

            yerel, ust = imza(skill_md.parent), imza(upstream[ad])
            tum_dosyalar = set(yerel) | set(ust)
            farklar = sorted(dosya for dosya in tum_dosyalar if yerel.get(dosya) != ust.get(dosya))
            beklenmeyen: list[str] = []
            for dosya in farklar:
                taban_imza = YAMALAR.get((ad, dosya))
                upstream_imza = ust.get(dosya)
                if taban_imza and upstream_imza == taban_imza:
                    continue
                beklenmeyen.append(dosya)
            if beklenmeyen:
                ozet = ", ".join(beklenmeyen[:8])
                if len(beklenmeyen) > 8:
                    ozet += f" (+{len(beklenmeyen) - 8})"
                degisen.append(f"- **{ad}**: {ozet}")

    return degisen


def _category(files: list[str]) -> str:
    if any("license" in name.lower() for name in files):
        return "license"
    if any(name.endswith((".py", ".js", ".sh")) for name in files):
        return "runtime-or-tooling"
    if any(name.endswith((".md", ".mdx")) for name in files):
        return "skill-contract-or-documentation"
    return "package-content"


def decision_records(root: pathlib.Path = KOK) -> list[dict]:
    """Return reviewable records without installing or modifying upstream code."""
    errors, reviews = baseline_errors(root)
    if errors:
        raise ValueError("; ".join(errors))
    registry = json.loads(
        (root / "registry" / "upstream-baselines.json").read_text(encoding="utf-8")
    )
    licenses = {
        str(source["repository"]): str(source["license"])
        for source in registry["sources"]
    }
    review_map = {str(review["skill"]): review for review in reviews}
    local_skills = harita(root / "plugins")
    records: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="divan-nobet-") as temporary:
        temp = pathlib.Path(temporary)
        upstream_skills: dict[str, pathlib.Path] = {}
        upstream_sources: dict[str, str] = {}
        heads: dict[str, str] = {}
        for index, repository in enumerate((*REPOLAR, *KURASYON_KAYNAKLARI)):
            checkout = temp / f"source-{index}"
            heads[repository] = klonla(repository, checkout)
            if repository in REPOLAR:
                found = harita(checkout)
                upstream_skills.update(found)
                upstream_sources.update({name: repository for name in found})

        for name, local in sorted(local_skills.items()):
            if name in OZGUN:
                continue
            review = review_map.get(name)
            repository = str(
                review.get("source") if review else upstream_sources.get(name, "unknown")
            )
            reviewed = str(review.get("reviewed_head", "")) if review else ""
            current = heads.get(repository, "")
            upstream = upstream_skills.get(name)
            if upstream is None:
                changed_files = ["upstream skill missing"]
            else:
                local_inventory = imza(local)
                upstream_inventory = imza(upstream)
                changed_files = sorted(
                    path
                    for path in set(local_inventory) | set(upstream_inventory)
                    if local_inventory.get(path) != upstream_inventory.get(path)
                )
            local_matches = bool(
                review and agac_sha256(local) == review.get("local_tree_sha256")
            )
            review_debt = not (
                review
                and current == reviewed
                and local_matches
                and upstream is not None
            )
            decision = "REVIEW_REQUIRED" if review_debt else str(review["decision"])
            rationale = (
                "Upstream or the local counterpart changed after the recorded review."
                if review_debt
                else str(review["reason"])
            )
            records.append(
                {
                    "source_repository": repository,
                    "skill_or_package": name,
                    "reviewed_commit": reviewed,
                    "current_commit": current,
                    "changed_files": changed_files
                    or (list(review.get("changed_files", [])) if review else []),
                    "change_category": _category(changed_files),
                    "license_status": licenses.get(repository, "unrecorded"),
                    "divan_counterpart": local.relative_to(root).as_posix(),
                    "decision": decision,
                    "rationale": rationale,
                    "evidence": "registry/upstream-baselines.json",
                    "review_debt": review_debt,
                }
            )

        for repository in KURASYON_KAYNAKLARI:
            source = next(
                entry for entry in registry["sources"] if entry["repository"] == repository
            )
            current = heads[repository]
            reviewed = str(source["reviewed_head"])
            debt = current != reviewed
            records.append(
                {
                    "source_repository": repository,
                    "skill_or_package": "candidate-curation",
                    "reviewed_commit": reviewed,
                    "current_commit": current,
                    "changed_files": ["curated repository inventory"],
                    "change_category": "candidate-catalog",
                    "license_status": licenses[repository],
                    "divan_counterpart": "registry/candidates.json",
                    "decision": "REVIEW_REQUIRED" if debt else "REFERENCE",
                    "rationale": (
                        "The curated source advanced and needs a new evidence review."
                        if debt
                        else "The pinned source remains a reference; no code is distributed."
                    ),
                    "evidence": "registry/upstream-baselines.json",
                    "review_debt": debt,
                }
            )
    return records


def render_report(records: list[dict], output_format: str) -> str:
    debt_count = sum(bool(record["review_debt"]) for record in records)
    if output_format == "json":
        return json.dumps(
            {
                "schema_version": 1,
                "status": "review-required" if debt_count else "clean",
                "review_debt_count": debt_count,
                "records": records,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    if output_format == "markdown":
        lines = [
            "# Divan Nöbet raporu",
            "",
            f"Durum: **{'inceleme gerekli' if debt_count else 'temiz'}** · "
            f"İnceleme borcu: **{debt_count}**",
            "",
            "| Source | Skill/package | Commits | Category | License | Decision |",
            "|---|---|---|---|---|---|",
        ]
        for record in records:
            lines.append(
                "| {source_repository} | {skill_or_package} | {reviewed_commit:.12} → "
                "{current_commit:.12} | {change_category} | {license_status} | "
                "{decision} |".format(**record)
            )
        lines.extend(["", "## Gerekçe ve kanıt", ""])
        for record in records:
            files = ", ".join(record["changed_files"][:8])
            if len(record["changed_files"]) > 8:
                files += f" (+{len(record['changed_files']) - 8})"
            lines.extend(
                [
                    f"### {record['skill_or_package']}",
                    "",
                    f"- Divan karşılığı: `{record['divan_counterpart']}`",
                    f"- Değişen dosyalar: {files}",
                    f"- Karar gerekçesi: {record['rationale']}",
                    f"- Doğrulama kanıtı: `{record['evidence']}`",
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"
    lines = [
        f"Nöbet durumu: {'inceleme gerekli' if debt_count else 'temiz'}",
        f"İnceleme borcu: {debt_count}",
    ]
    for record in records:
        lines.extend(
            [
                "",
                f"Source: {record['source_repository']}",
                f"Skill/package: {record['skill_or_package']}",
                f"Reviewed/current: {record['reviewed_commit']} -> {record['current_commit']}",
                f"Category: {record['change_category']}",
                f"License: {record['license_status']}",
                f"Divan counterpart: {record['divan_counterpart']}",
                f"Decision: {record['decision']}",
                f"Rationale: {record['rationale']}",
                f"Evidence: {record['evidence']}",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Review Divan upstream drift")
    parser.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    arguments = parser.parse_args()
    try:
        records = decision_records()
    except (OSError, ValueError, subprocess.SubprocessError) as hata:
        print(f"NOBET CALISMADI: {hata}", file=sys.stderr)
        return 1
    print(render_report(records, arguments.format), end="")
    return 2 if any(record["review_debt"] for record in records) else 0


if __name__ == "__main__":
    sys.exit(main())
