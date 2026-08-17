# Teftiş — AgencyBench-02, the vertical slice stands up

Date: 2026-08-16
Project: a disposable local project outside the Divan repository
Worker: Codex 0.147.0, driven by Divan

## What was asked for

The owner's Ferman, in ordinary Turkish, for a local operations case system:
four roles, tenant isolation, a case queue with atomic claim, work attempts, an
auditable append-only ledger, commission, authorized documents, an admin
correction flow, a CSV report, backup and restore, a responsive interface, one
command to run, and no real bank or payment integration.

No stack was named, so Divan chose one.

## The plan was not written by hand either

A real Codex attempt read the Ferman and wrote a specification. The compiler
refused the first one and the refusal was the point: the brief had named fields
the contract does not use. Its exact reasons went back to a fresh attempt, and
the second compiled.

The brief is now generated from the compiler's own constants, so a hand-copied
schema cannot drift from the contract and leave the worker blamed for the drift.

```
stories        : 12
work packages  : 12
first band     : WP-P1-S1 .. WP-P1-S6
```

The first band is the vertical slice, because polish is worth nothing before
login, tenant, case, queue and claim work end to end.

## The slice, one work package at a time

Each package became a task contract, the contract and its background became a
bounded context pack, and the pack went to a real Codex attempt in a worktree
Divan owns. Divan committed each accepted result under its own name.

| Package | Title | Attempt | Duration | Files | Result commit |
|---|---|---|---|---|---|
| WP-P1-S1 | Login and roles | A001 | 226 s | 5 | `1e89b29c` |
| WP-P1-S2 | Tenant isolation | A001 | 131 s | 2 | `0753974f` |
| WP-P1-S3 | Case creation | A001 | 154 s | 2 | recorded |
| WP-P1-S4 | Queue and atomic claim | A001 | 134 s | 2 | recorded |
| WP-P1-S5 | Work attempts | A001 | 137 s | 2 | recorded |
| WP-P1-S6 | Append-only ledger | A001 | 175 s | 3 | recorded |

Six of six accepted, first attempt each. No application code was written by
hand at any point.

## What the worker chose

Node.js 22 with its built-in test runner and built-in SQLite. No dependencies
at all, so `npm start` is genuinely one command and there is nothing to install
first. That is the smallest sustainable local-first shape for this Ferman, and
it was the worker's choice, not a prescription.

Four roles are seeded and named in the project's own README: Administrator,
Operations Manager, Case Worker, Auditor.

## Verification

The project's own tests, run by Divan rather than reported by the worker:

```
# tests 11
# pass 11
# fail 0
```

Run ten times in a row: ten passes, no failures.

The atomic claim test was read rather than trusted, because a concurrency test
that quietly runs in sequence proves nothing. It issues two claims through
`Promise.all` from two different sessions against one queued case and asserts
exactly one 200 and exactly one 404, then re-reads the case and asserts the
persisted owner is the winner.

## Correction made to the harness during this stage

The build driver accepted a package because files had changed. Files changed is
not a result. It now runs the project's own tests after each package, and a
failure becomes the context for the next attempt on the same package, with a
finite budget. Every repair starts from output a command actually produced.

## Not yet proven

The second band carries commission, documents, admin correction, CSV, backup
and restore, and the responsive interface. Browser acceptance, security,
restart persistence, independent review and the evidence manifest are gates
that follow it. None of them are claimed here.
