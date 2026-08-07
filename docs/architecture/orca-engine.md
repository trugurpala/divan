# Orca execution engine

This document defines the boundary between Divan Core and Orca.

Divan remains the control plane. It owns planning, authority, governance, evidence, review verdicts, and release decisions. Orca is an optional execution engine that provides isolated Git worktrees, agent terminals, browser automation, and remote runtime capabilities.

## Architecture

```text
Divan Desktop / CLI
        |
        v
Divan Core
  planning | authority | evidence | release
        |
        v
Execution Engine interface
        |
        +-- OrcaEngine (optional sidecar)
        +-- future local/remote engines
        |
        v
Orca runtime
  worktrees | terminals | Codex | Claude | custom CLI
        |
        v
project-owned Git worktrees
```

The project repository, business logic, receipts, and release authority remain Divan/project owned. An Orca outage must not make Divan state unreadable.

## Decision versus installation mode

The engine registry separates *why* an engine is selected from *how* it is integrated.

Decisions:

- `ADOPT`: use the upstream capability essentially as-is.
- `ADAPT`: wrap or constrain the upstream capability behind a Divan-owned contract.
- `REFERENCE`: use the project as guidance, not a runtime dependency.
- `REJECT`: explicitly decline the engine for the evaluated use case.

Installation modes are independent: `dependency`, `fork`, `none`, `provider`, `sidecar`, or `vendored`.

Legacy registries that used `decision: FORK` are interpreted as `decision: ADAPT` with installation mode `fork`; validators emit a migration warning. New registry entries must not use `FORK` as a decision.

## Orca adoption decision

Orca is `ADAPT` + `sidecar` for the first production integration. Divan must not embed Orca-specific state into its core domain model. A branded fork is a later packaging decision and requires a separate dependency, trademark, updater, and third-party-license review.

## Authority boundary

Read-only operations may run without an execution mandate. Mutating operations require explicit execution authority and a non-empty `mandate_id`.

Examples of read-only operations:

- runtime status / capability probe
- worktree list/show
- terminal read/wait
- file diff
- browser snapshot/screenshot

Examples of mutations:

- repo registration
- worktree creation/removal
- agent dispatch
- terminal send/create
- browser click/fill/navigation
- automation creation

The Orca adapter never accepts a shell command string for its own control plane. It constructs an argument vector from typed values and invokes the CLI without `shell=True`.

## Evidence contract

Every execution result returned to Divan should be normalized to a stable envelope containing:

- engine id and adapter contract version
- logical action
- exact evidence argv, with prompt bodies redacted
- mutation flag and mandate id when applicable
- exit code
- parsed JSON payload when Orca returns JSON
- captured stdout/stderr for diagnostics

Divan receipts may reference this envelope, but Orca remains replaceable.

## Target lifecycle

1. Divan plans a bounded task and assigns a role.
2. An authority gate approves mutation and issues a mandate.
3. `OrcaEngine` creates an isolated worktree and launches the selected worker.
4. Divan observes terminal state and collects the diff/test evidence.
5. A separate reviewer evaluates the result.
6. Verdict is `PASS`, `RETRY`, or `BLOCKED`.
7. Merge/release remains behind Divan authority and release gates.

## Desktop product boundary

The intended Windows product is **Divan Desktop**. Orca is an execution engine, not the user-facing product identity. This keeps the UI, governance model, and project data portable if the runtime changes later.
