---
name: implementation-plan
description: Plan a non-trivial repository change before editing code. Use when a task spans multiple files, changes behavior or interfaces, requires migrations, or has meaningful rollback and verification concerns.
---

# Implementation Plan

Create the smallest plan that can be verified independently.

For a build or repair request, use the plan to execute the authorized work and
verify each meaningful result. A plan is an intermediate artifact unless the user
requested planning only. Keep the full requested workflow as the acceptance target.

For each step state:
- outcome;
- files or boundaries involved;
- dependencies;
- verification;
- rollback or reversibility when material.

Preserve existing architecture unless the requested outcome requires changing it.
Use available subagents for independent, well-bounded research, implementation, or verification when coordination costs less than it saves.
Do not parallelize writes to the same files.
Prefer existing primitives over new frameworks and abstractions.
The plan grants no implicit permission to publish, push, release, destroy data, or widen scope.

For work with multiple independent streams, read [delegation.md](references/delegation.md). A small task needs no agent hierarchy.
