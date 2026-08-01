#!/usr/bin/env python3
"""Validate Divan's pinned upstream review inventory."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DECISIONS = {"KEEP", "ADAPT", "ADOPT", "REFERENCE", "REJECT"}


def sha256(path: pathlib.Path) -> str:
    payload = path.read_bytes()
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        pass
    else:
        payload = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def skill_map(root: pathlib.Path) -> dict[str, pathlib.Path]:
    result: dict[str, pathlib.Path] = {}
    for skill in root.rglob("SKILL.md"):
        match = re.search(
            r"^name:\s*(.+)$", skill.read_text(errors="ignore")[:4000], re.M
        )
        if match:
            result[match.group(1).strip()] = skill.parent
    return result


def tree_signature(directory: pathlib.Path) -> dict[str, str]:
    return {
        path.relative_to(directory).as_posix(): sha256(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    }


def tree_sha256(directory: pathlib.Path) -> str:
    payload = json.dumps(
        tree_signature(directory), sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def review_errors(review: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(review.get("skill"), str) or not review.get("skill"):
        errors.append("skill is required")
    if not isinstance(review.get("source"), str) or "/" not in review.get("source", ""):
        errors.append("source must be owner/repository")
    if not re.fullmatch(r"[0-9a-f]{40}", str(review.get("reviewed_head", ""))):
        errors.append("reviewed_head must be a 40-character commit")
    if review.get("decision") not in DECISIONS:
        errors.append(f"decision must be one of {sorted(DECISIONS)}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(review.get("local_tree_sha256", ""))):
        errors.append("local_tree_sha256 must be a SHA-256")
    if not isinstance(review.get("reason"), str) or not review.get("reason", "").strip():
        errors.append("reason is required")
    if not isinstance(review.get("changed_files"), list) or not review.get("changed_files"):
        errors.append("changed_files must be a non-empty array")
    return errors


def _read_registry(root: pathlib.Path) -> tuple[list[str], list[dict], list[dict]]:
    path = root / "registry" / "upstream-baselines.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read {path}: {exc}"], [], []
    if not isinstance(data, dict):
        return ["upstream baseline root must be an object"], [], []
    reviews, sources = data.get("reviews", []), data.get("sources", [])
    if not isinstance(reviews, list) or not isinstance(sources, list):
        return ["upstream baseline sources/reviews must be arrays"], [], []
    return [], reviews, sources


def _source_heads(sources: list[dict]) -> tuple[list[str], dict[str, str]]:
    errors: list[str] = []
    heads: dict[str, str] = {}
    for source in sources:
        if not isinstance(source, dict):
            errors.append(f"invalid source entry: {source!r}")
            continue
        repository = source.get("repository")
        head, origin = source.get("reviewed_head"), source.get("origin_commit")
        if not isinstance(repository, str) or not re.fullmatch(r"[0-9a-f]{40}", str(head)):
            errors.append(f"invalid pinned source: {source!r}")
            continue
        if not re.fullmatch(r"[0-9a-f]{40}", str(origin)):
            errors.append(f"{repository}: origin_commit must be a 40-character commit")
        if not isinstance(source.get("license"), str) or not source.get("license"):
            errors.append(f"{repository}: license is required")
        heads[repository] = str(head)
    return errors, heads


def _validate_reviews(
    root: pathlib.Path, reviews: list[dict], source_heads: dict[str, str]
) -> tuple[list[str], list[dict]]:
    errors: list[str] = []
    local_skills, seen = skill_map(root / "plugins"), set()
    valid_reviews: list[dict] = []
    for review in reviews:
        if not isinstance(review, dict):
            errors.append(f"invalid review entry: {review!r}")
            continue
        skill = str(review.get("skill", "<unknown>"))
        errors.extend(f"{skill}: {error}" for error in review_errors(review))
        if skill in seen:
            errors.append(f"{skill}: duplicate review")
        seen.add(skill)
        if source_heads.get(str(review.get("source"))) != review.get("reviewed_head"):
            errors.append(f"{skill}: review commit does not match pinned source")
        local = local_skills.get(skill)
        if local is None:
            errors.append(f"{skill}: local skill is missing")
        elif tree_sha256(local) != review.get("local_tree_sha256"):
            errors.append(f"{skill}: local tree changed after review")
        valid_reviews.append(review)
    return errors, valid_reviews


def baseline_errors(root: pathlib.Path = ROOT) -> tuple[list[str], list[dict]]:
    errors, reviews, sources = _read_registry(root)
    if errors:
        return errors, []
    source_errors, heads = _source_heads(sources)
    review_validation, valid_reviews = _validate_reviews(root, reviews, heads)
    return source_errors + review_validation, valid_reviews


def pinned_sources(root: pathlib.Path = ROOT) -> dict[str, str]:
    """Return pins from the canonical machine-readable inventory."""
    data = json.loads(
        (root / "registry" / "upstream-baselines.json").read_text(encoding="utf-8")
    )
    return {
        str(source["repository"]): str(source["reviewed_head"])
        for source in data["sources"]
    }
