#!/usr/bin/env python3
"""Validate and score a task-specific capability requirement ledger."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any


STATUS_WEIGHTS = {
    "verified": 1.0,
    "partial": 0.5,
    "missing": 0.0,
    "unknown": 0.0,
}
REQUIREMENT_FIELDS = {"id", "status", "evidence"}


class LedgerError(ValueError):
    """Raised when a capability ledger does not match the public contract."""


def validate_ledger(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or set(payload) != {"requirements"}:
        raise LedgerError("kok nesne yalniz 'requirements' alani icermeli")

    requirements = payload["requirements"]
    if not isinstance(requirements, list) or not requirements:
        raise LedgerError("requirements bos olmayan bir liste olmali")

    seen_ids: set[str] = set()
    for index, requirement in enumerate(requirements):
        prefix = f"requirements[{index}]"
        if not isinstance(requirement, dict):
            raise LedgerError(f"{prefix} bir nesne olmali")
        if not {"id", "status"}.issubset(requirement):
            raise LedgerError(f"{prefix} id ve status alanlarini icermeli")
        unknown_fields = set(requirement) - REQUIREMENT_FIELDS
        if unknown_fields:
            fields = ", ".join(sorted(unknown_fields))
            raise LedgerError(f"{prefix} bilinmeyen alan iceriyor: {fields}")

        requirement_id = requirement["id"]
        if not isinstance(requirement_id, str) or not requirement_id.strip():
            raise LedgerError(f"{prefix}.id bos olmayan bir metin olmali")
        if requirement_id in seen_ids:
            raise LedgerError(f"yinelenen requirement id: {requirement_id}")
        seen_ids.add(requirement_id)

        status = requirement["status"]
        if not isinstance(status, str) or status not in STATUS_WEIGHTS:
            allowed = ", ".join(STATUS_WEIGHTS)
            raise LedgerError(f"{prefix}.status sunlardan biri olmali: {allowed}")

        evidence = requirement.get("evidence", [])
        if not isinstance(evidence, list) or any(
            not isinstance(item, str) or not item.strip() for item in evidence
        ):
            raise LedgerError(f"{prefix}.evidence bos olmayan metinlerden olusmali")

    return requirements


def score(requirements: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {status: 0 for status in STATUS_WEIGHTS}
    weighted_total = 0.0
    for requirement in requirements:
        status = requirement["status"]
        counts[status] += 1
        weighted_total += STATUS_WEIGHTS[status]

    requirement_count = len(requirements)
    coverage = round(100.0 * weighted_total / requirement_count, 1)
    confidence = round(
        100.0 * (requirement_count - counts["unknown"]) / requirement_count,
        1,
    )
    return {
        "requirement_count": requirement_count,
        "counts": counts,
        "coverage_percent": coverage,
        "gap_percent": round(100.0 - coverage, 1),
        "confidence_percent": confidence,
    }


def read_input(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    return pathlib.Path(source).read_text(encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Goreve ozel yetenek gereksinim kapsamasini hesapla."
    )
    parser.add_argument(
        "source",
        nargs="?",
        default="-",
        help="JSON dosyasi; verilmezse stdin okunur",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        raw = read_input(args.source)
        payload = json.loads(raw)
        result = score(validate_ledger(payload))
    except json.JSONDecodeError as exc:
        print(f"hata: gecersiz JSON: {exc.msg}", file=sys.stderr)
        return 2
    except (LedgerError, OSError) as exc:
        print(f"hata: {exc}", file=sys.stderr)
        return 2

    json.dump(result, sys.stdout, ensure_ascii=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
