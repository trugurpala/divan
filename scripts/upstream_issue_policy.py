#!/usr/bin/env python3
"""Build a deterministic single-issue plan for the monthly Nöbet workflow."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any


def decide(issues: list[dict[str, Any]], debt: bool) -> dict[str, Any]:
    numbers = sorted(
        {
            int(issue["number"])
            for issue in issues
            if isinstance(issue, dict)
            and "pull_request" not in issue
            and isinstance(issue.get("number"), int)
            and not isinstance(issue.get("number"), bool)
            and int(issue["number"]) > 0
        }
    )
    primary = numbers[0] if numbers else None
    actions = [
        {"operation": "close-duplicate", "issue_number": number}
        for number in numbers[1:]
    ]
    if debt and primary is None:
        actions.append({"operation": "create"})
    elif debt:
        actions.append({"operation": "update", "issue_number": primary})
    elif primary is not None:
        actions.append({"operation": "close-clean", "issue_number": primary})
    return {
        "schema_version": 1,
        "debt": debt,
        "primary_issue": primary,
        "duplicate_issues": numbers[1:],
        "actions": actions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan one reusable Nöbet issue")
    parser.add_argument("--issues", type=pathlib.Path, required=True)
    parser.add_argument("--debt", choices=("yes", "no"), required=True)
    args = parser.parse_args()
    try:
        issues = json.loads(args.issues.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Nöbet issue listesi okunamadı: {exc}") from exc
    if not isinstance(issues, list):
        raise SystemExit("Nöbet issue listesi dizi olmalı")
    print(json.dumps(decide(issues, args.debt == "yes"), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
