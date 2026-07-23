#!/usr/bin/env python3
"""Deprecated compatibility wrapper; use `scripts/candidate_review.py`."""
try:
    from candidate_review import *  # noqa: F403
    from candidate_review import ana as main
except ModuleNotFoundError:
    from scripts.candidate_review import *  # noqa: F403
    from scripts.candidate_review import ana as main

if __name__ == "__main__":
    raise SystemExit(main())
