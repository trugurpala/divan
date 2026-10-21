---
name: repo-audit
description: Inspect an unfamiliar repository or code area before implementation. Use when stack, conventions, baseline state, ownership boundaries, risks, or a capability required by the task are not yet established.
---

# Repository Audit

Establish facts before edits.

- Read the host's applicable project instructions (including `AGENTS.md` where used), README, package/build manifests, test configuration, and changed-file status.
- Identify language/framework, package manager, database, test runner, formatter/linter, type checker, build command, and CI gates from repository evidence.
- Record pre-existing failures separately from failures introduced by the current task.
- Find the smallest code surface that owns the requested behavior.
- Identify security, data-loss, migration, concurrency, compatibility, or deployment risk only when relevant.
- Do not install replacement tooling when the repository already has an equivalent.
- Return a short user-facing summary and exact evidence for the implementation workflow.

When a task depends on an unverified or missing skill, tool, MCP capability, or service, read [capabilities.md](references/capabilities.md). Skip capability discovery when the existing workflow already covers the task.

When the outcome could be delivered by an existing integration, open-source component, low-code system, or custom implementation, read [reuse-decisions.md](references/reuse-decisions.md) before choosing. Do not rescope a maintained product into an MVP unless the user requests it.
