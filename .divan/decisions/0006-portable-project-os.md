# ADR 0006: Portable, supervised Project OS

## Status

Accepted for implementation on 2026-07-23.

## Context

Divan's Company OS provides repository-level routing and standards, but an installed project needs a portable contract from user intent through specification, implementation, verification, preview, release, and live observation. The product must work from Claude Code and Codex without adding a hosted control plane, persistent process, or second authority above the user.

Agent Skills informs the portable skill contract; Spec Kit and OpenSpec inform spec-first evidence flows; Lighthouse CI and Lychee inform opt-in public-web evidence. Auto Company remains a reference only: its daemon-oriented, broad-autonomy model is incompatible with Divan. Candidate decisions, licenses, and immutable pins are in `registry/candidates.json`; no upstream source code is distributed by this ADR.

## Decision

- The Padişah/user is the sole authority. Divan is a functional council that plans and executes only bounded, explicitly authorized work.
- Supervised autonomy is receipt-producing and fail-closed: unavailable capability, approval, or evidence is `BLOCKED`, never synthetic success.
- DCS-* governs the Divan repository and DPS-* governs initialized projects; applicability is explicit and neither layer silently overrides the other.
- Legal goal states and transitions are defined in the Project OS specification. `BLOCKED` records `resume_from` as its immediately preceding nonterminal phase; once the stated condition is resolved, `goal resume` can return only to that phase and emits a new receipt. `FAILED` and `OBSERVED` are terminal, and retry after `FAILED` creates a new goal. Receipts are append-only and redacted.
- Canonical interfaces are `init`, `audit`, `verify`, `goal`, `receipt`, and `release`; mutations dry-run by default and require `--execute`.
- Providers are narrow capability contracts: GitHub owns remote delivery evidence, Vercel owns preview/promotion evidence, Context7 supplies official documentation evidence, and local covers local-only inspection.
- Project OS is command-invoked and exits. It has no daemon, periodic scheduler, hosted dashboard, ambient credential store, or hidden memory.

## Options considered

1. Keep repository-only Company OS rules. This leaves installed projects with no portable goal/evidence contract.
2. Adopt a continuously running autonomous-company daemon. This increases authority, secret, cost, and observability risk and conflicts with user supervision.
3. Adopt a portable, provider-bounded, command-invoked Project OS. This gives target projects a deterministic contract while keeping execution scoped.

Option 3 is selected.

## Consequences

- Project creation and delivery become inspectable through stable artifacts and receipts, not chat memory or hidden reasoning.
- Provider absence is visible as `BLOCKED` and can be resolved without guessing at implicit integrations.
- English canonical interfaces need Turkish wrappers and documentation through v0.x.
- Every later upstream use remains a separate pin, attribution, license, eval, and inspection decision; candidate status is not installation.
- The architecture makes no behavior-quality, speed, or win-rate claim.
