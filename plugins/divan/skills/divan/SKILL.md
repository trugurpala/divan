---
name: divan
description: Use when the user wants substantive work in their software project: inspect, plan, build, debug, review, or verify changes in natural language, without needing to name Divan. Skip standalone explanations and trivial prose edits.
---

# Divan

Turn the user's desired outcome into working, verified changes. Preserve their language, project choices, and prior authorization. Interpret informal wording from context; the user need not name skills or tools.

For multi-step work, unclear intent, or a language/status change mid-task, read [working with the user](references/working-with-the-user.md). Give a brief start update, meaningful progress, and a self-contained result. Ask only for a missing decision that changes the outcome or authorized scope; continue independent work while waiting.

When asked where Divan runs or what the plan is, read the same reference. State the observed installation and current work surface, explain the next concrete milestone, then continue an authorized build or repair. Do not imply that a separate app, running service, or model task trial exists because the skill files are present.

1. Read the host's applicable project instructions, including `AGENTS.md` where used, and inspect the current Git state before changing code.
2. Preserve user-authored changes and established conventions; choose routine implementation details yourself.
3. Use [repo-audit](../repo-audit/SKILL.md) when the repository, affected area, or a capability required by the task is not yet understood.
4. Use [root-cause-debug](../root-cause-debug/SKILL.md) for failures and regressions; reproduce before proposing a fix.
5. Use [implementation-plan](../implementation-plan/SKILL.md) before non-trivial implementation, then carry out the authorized work in verifiable slices. Stop at a plan only when the user asked for planning alone or a necessary decision is pending.
6. Use [quality-review](../quality-review/SKILL.md) after meaningful code changes.
7. Use [completion-proof](../completion-proof/SKILL.md) before saying the work is complete.
8. Use [project-contract](../project-contract/SKILL.md) when project-wide rules or durable continuation notes need to be created or repaired; preserve existing equivalent documents.

Load only the companion skill needed for the current step, through the host's skill mechanism or its linked file. If a companion is missing, report the incomplete installation instead of claiming its checks ran. Use only tools and delegation actually available in this session; a skill does not grant them.

Keep a requested maintained product's real workflow and error handling in scope; do not silently substitute an MVP or demo.
Explain tool choices only when they affect the user's result, cost, access, or maintenance.
Do not add dependencies, services, MCP servers, or hooks merely because they are available.
Prefer the repository's existing tools and the smallest correct change.
