---
name: repo-audit
description: Inspect an unfamiliar repository or code area before implementation. Use when stack, conventions, quality tooling, baseline state, ownership boundaries, or risks are not yet established.
---

# Repository Audit

Establish facts before edits.

- Read the nearest applicable `AGENTS.md`, README, package/build manifests, test configuration, and changed-file status.
- Identify language/framework, package manager, database, test runner, formatter/linter, type checker, build command, and CI gates from repository evidence.
- Record pre-existing failures separately from failures introduced by the current task.
- Find the smallest code surface that owns the requested behavior.
- Identify security, data-loss, migration, concurrency, compatibility, or deployment risk only when relevant.
- Do not install replacement tooling when the repository already has an equivalent.
- Return a short user-facing summary and exact evidence for the implementation workflow.
