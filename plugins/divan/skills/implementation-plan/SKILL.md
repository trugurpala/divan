---
name: implementation-plan
description: Plan a non-trivial repository change before editing code. Use when a task spans multiple files, changes behavior or interfaces, requires migrations, or has meaningful rollback and verification concerns.
---

# Implementation Plan

Create the smallest plan that can be verified independently.

For each step state:
- outcome;
- files or boundaries involved;
- dependencies;
- verification;
- rollback or reversibility when material.

Preserve existing architecture unless the requested outcome requires changing it.
Use subagents only for independent, well-bounded read-heavy or verification work.
Do not parallelize writes to the same files.
Prefer existing primitives over new frameworks and abstractions.
The plan grants no implicit permission to publish, push, release, destroy data, or widen scope.
