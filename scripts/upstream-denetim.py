#!/usr/bin/env python3
"""Aylik nobet: vendored skill'leri taze upstream klonlariyla karsilastir.

Cikis kodlari: 0 temiz, 2 kurasyon gerektiren fark, 1 denetim calismadi.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile

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
}
KURASYON_KAYNAKLARI = {
    "PatrickJS/awesome-cursorrules": "b044f956f021b6e8877f16781bcfc466a6a120e9",
    "muratcankoylan/Agent-Skills-for-Context-Engineering": "c578e85e40fe2bda7c1fec91ff64cf5285434934",
}
# Bilincli farklarda upstream dosyasinin bilinen taban imzasi da sabitlenir.
# Boylece upstream ayni dosyayi degistirirse izin listesi bu degisimi gizlemez.
YAMALAR = {
    ("claude-api", "SKILL.md"): "1d08b3be1c02b6bd2d8c966b1645e234fbb36454d2dd4cbd39802d2f321bd0f4",
    ("vercel-react-best-practices", "AGENTS.md"): "fc93e7421177bbf869cce892bc60a6c83a4517d974bc3bf65c4e2c1e58a6ccf6",
}
KOK = pathlib.Path(__file__).resolve().parent.parent
KARARLAR = {"KEEP", "ADAPT", "ADOPT", "REFERENCE", "REJECT"}


def sha256(dosya: pathlib.Path) -> str:
    payload = dosya.read_bytes()
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        pass
    else:
        payload = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def harita(kok: pathlib.Path) -> dict[str, pathlib.Path]:
    sonuc: dict[str, pathlib.Path] = {}
    for skill in kok.rglob("SKILL.md"):
        eslesme = re.search(
            r"^name:\s*(.+)$", skill.read_text(errors="ignore")[:4000], re.M
        )
        if eslesme:
            sonuc[eslesme.group(1).strip()] = skill.parent
    return sonuc


def imza(dizin: pathlib.Path) -> dict[str, str]:
    return {
        dosya.relative_to(dizin).as_posix(): sha256(dosya)
        for dosya in sorted(dizin.rglob("*"))
        if dosya.is_file()
        and ".git" not in dosya.parts
        and "__pycache__" not in dosya.parts
        and dosya.suffix != ".pyc"
    }


def agac_sha256(dizin: pathlib.Path) -> str:
    payload = json.dumps(imza(dizin), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def review_errors(review: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(review.get("skill"), str) or not review.get("skill"):
        errors.append("skill is required")
    if not isinstance(review.get("source"), str) or "/" not in review.get("source", ""):
        errors.append("source must be owner/repository")
    if not re.fullmatch(r"[0-9a-f]{40}", str(review.get("reviewed_head", ""))):
        errors.append("reviewed_head must be a 40-character commit")
    if review.get("decision") not in KARARLAR:
        errors.append(f"decision must be one of {sorted(KARARLAR)}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(review.get("local_tree_sha256", ""))):
        errors.append("local_tree_sha256 must be a SHA-256")
    if not isinstance(review.get("reason"), str) or not review.get("reason", "").strip():
        errors.append("reason is required")
    changed_files = review.get("changed_files")
    if not isinstance(changed_files, list) or not changed_files:
        errors.append("changed_files must be a non-empty array")
    return errors


def baseline_errors(root: pathlib.Path = KOK) -> tuple[list[str], list[dict]]:
    path = root / "registry" / "upstream-baselines.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read {path}: {exc}"], []
    if not isinstance(data, dict):
        return ["upstream baseline root must be an object"], []
    reviews = data.get("reviews", [])
    sources = data.get("sources", [])
    if not isinstance(reviews, list) or not isinstance(sources, list):
        return ["upstream baseline sources/reviews must be arrays"], []
    errors: list[str] = []
    source_heads: dict[str, str] = {}
    for source in sources:
        if not isinstance(source, dict):
            errors.append(f"invalid source entry: {source!r}")
            continue
        repository = source.get("repository")
        head = source.get("reviewed_head")
        if not isinstance(repository, str) or not re.fullmatch(r"[0-9a-f]{40}", str(head)):
            errors.append(f"invalid pinned source: {source!r}")
            continue
        if not isinstance(source.get("license"), str) or not source.get("license"):
            errors.append(f"{repository}: license is required")
        source_heads[repository] = str(head)

    local_skills = harita(root / "plugins")
    seen: set[str] = set()
    valid_reviews: list[dict] = []
    for review in reviews:
        if not isinstance(review, dict):
            errors.append(f"invalid review entry: {review!r}")
            continue
        skill = str(review.get("skill", "<unknown>"))
        for error in review_errors(review):
            errors.append(f"{skill}: {error}")
        if skill in seen:
            errors.append(f"{skill}: duplicate review")
        seen.add(skill)
        source = review.get("source")
        if source_heads.get(str(source)) != review.get("reviewed_head"):
            errors.append(f"{skill}: review commit does not match pinned source")
        local = local_skills.get(skill)
        if local is None:
            errors.append(f"{skill}: local skill is missing")
        elif agac_sha256(local) != review.get("local_tree_sha256"):
            errors.append(f"{skill}: local tree changed after review")
        valid_reviews.append(review)
    return errors, valid_reviews


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

        for sira, (repo, taban_commit) in enumerate(KURASYON_KAYNAKLARI.items()):
            guncel = klonla(repo, tmp / f"curated-{sira}")
            if guncel != taban_commit:
                degisen.append(
                    f"- **{repo}**: kure edilen kaynak ilerledi "
                    f"({taban_commit[:12]} -> {guncel[:12]})"
                )

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


def main() -> int:
    try:
        degisen = denetle()
    except (OSError, subprocess.SubprocessError) as hata:
        print(f"NOBET CALISMADI: {hata}", file=sys.stderr)
        return 1
    if degisen:
        print("UPSTREAM DEGISIMI VAR:\n" + "\n".join(degisen))
        print("\nFarki lisans ve urun degeri acisindan inceleyip kurasyon karari verin.")
        return 2
    print("Nobet temiz: vendored vezirler ve kure edilen kaynaklar izlenen tabanla uyumlu.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
