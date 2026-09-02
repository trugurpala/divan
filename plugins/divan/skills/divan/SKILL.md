---
name: divan
description: Coordinate a software task with Divan when the user asks Divan to inspect, build, change, repair, review, or finish work in a repository. Route only to the smallest relevant Divan skills and keep the user-facing explanation simple.
---

# Divan

Turn the user's desired outcome into a bounded engineering workflow.

1. Read applicable `AGENTS.md` files and inspect the current Git state before changing code.
2. Preserve user-authored changes and established project conventions.
3. Use `repo-audit` when the repository or affected area is not yet understood.
4. Use `root-cause-debug` for failures and regressions; reproduce before proposing a fix.
5. Use `implementation-plan` before non-trivial implementation.
6. Use `quality-review` after meaningful code changes.
7. Use `completion-proof` before saying the work is complete.
8. Use `project-contract` only when project-wide engineering rules need to be created or repaired.

Do not expose internal workflow jargon unless it helps the user make a decision.
Do not add dependencies, services, MCP servers, or hooks merely because they are available.
Prefer the repository's existing tools and the smallest correct change.
