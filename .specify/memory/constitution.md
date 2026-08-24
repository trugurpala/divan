<!--
Sync Impact Report
- Version change: none -> 2.0.0
- Scope: Divan Pusula web/control-plane incubation
- Added principles: product truth, evidence authority, isolation, cost radar, continuity,
  adapter-first adoption, secrets, UX, release proof
- Removed principles: none
- Deferred: production provider credentials and the eventual standalone divan-pusula repository
-->

# Divan Pusula Constitution

## Core Principles

### I. The Deliverable Is a Human-Usable Product

Divan Pusula MUST end as a real application with login, team/project boundaries, a human dashboard,
observable work, verifiable pull requests, deployment state, rollback state, safe errors, and an audit
trail. A chat demo, agent loop, CLI-only prototype, or visual mock is not a completed product.

### II. Pusula Owns the Truth; Providers Are Adapters

The canonical product state MUST remain under Pusula control. The target architecture uses Forgejo as
canonical Git/PR/release storage, Dagger as canonical pipeline logic, PostgreSQL as canonical Mizan
memory, and deterministic policy evaluation. GitHub, GitLab, Vercel, Supabase, cloud CI, hosted
sandboxes, and model vendors MUST remain replaceable adapters. Losing one optional provider MUST NOT
destroy the project history or canonical decision state.

### III. Evidence Precedes Authority

Agent output is a proposal, never a Fact, Verification, merge permission, or deployment permission.
Machine decisions MUST be based on source-bound evidence. Missing, stale, partial, truncated,
timeout, unverifiable, or mismatched-HEAD evidence MUST fail closed. High-impact policy decisions
MUST be deterministic and testable; an LLM MUST NOT be the final ALLOW/DENY authority.

### IV. Untrusted Code Never Runs in the Control Plane

Customer or target-repository code MUST NOT execute in the Pusula web/API/database host. Execution
MUST occur in disposable runner boundaries. Local trusted development MAY use a container profile;
untrusted or multi-tenant server execution MUST use a stronger disposable isolation provider such as
a KVM/microVM class boundary. A run MUST NOT inherit unrelated host secrets or another run's state.

### V. Every Technology Decision Has a Cost and an Exit

For every material external capability, Mizan Radar MUST record provider, edition, feature surface,
license, price snapshot, data boundary, source, benchmark result, decision, decision reason,
`verified_at`, and `review_after`. Free/Pro/Team/Enterprise differences MUST be checked before custom
implementation. The decision set is KEEP, BUY, ADOPT, ADAPT, REPLACE, LATER, or REJECT. A purchase is
valid when it buys lower total maintenance/risk, not merely more features.

### VI. Context Is Persisted; Prompts Stay Small

Long-session correctness MUST NOT depend on the conversation window. The project MUST create compact,
machine-validated continuity capsules at 0%, 25%, 50%, 75%, and 100% progress. A resumed agent reads,
in order: this constitution, the active feature spec, the latest capsule, and the next-action list.
Capsules MUST contain only verified state, accepted decisions, unresolved risks, evidence references,
budget state, and the smallest next-action set. Full chat transcripts and bulk ECC skills MUST NOT be
injected by default.

### VII. Adopt Interfaces, Not Upstream Ownership

ECC, Spec Kit, UI UX Pro Max, OpenHands, ToolHive, Dagger, OPA, Hatchet, Coolify, Logto, Forgejo, and
other upstream projects MAY be used only through pinned packages, containers, protocols, documented
configuration, or narrow copied material whose license/provenance is recorded. Pusula MUST NOT fork a
large upstream product merely to obtain a small capability. Third-party code imported into the repo
requires a pinned source revision, compatible license record, acceptance test, and update strategy.

### VIII. Secrets Are References, Not Context

Credentials MUST be stored in a dedicated secret system or provider-native secret store and passed to
approved tools with the narrowest practical scope. Secret values MUST NOT enter prompts, canonical
memory, ordinary logs, exported evidence, PR text, or UI diagnostics. Connector manifests carry
secret references, never raw secret values.

### IX. Vibe-Coder UX Is a Quality Gate

The default product language is Turkish with English as a first-class secondary language. Main user
navigation MUST speak in outcomes: Ana Sayfa, Projeler, Isler, Hafiza, Yayinlar, Ayarlar. Raw provider
errors and stack traces MUST remain behind technical details. WCAG 2.2 AA, keyboard operation,
responsive layouts, reduced-motion behavior, empty/error/loading states, and resilient text reflow
are release requirements, not polish after release.

### X. No Release Without Recovery Proof

A green build alone MUST NOT mean release-ready. Production promotion requires exact-HEAD evidence,
required checks, policy approval, staging health, provider capability validation, and previous-good
state. A provider MUST NOT be described as canary-capable unless real traffic splitting is supported.
Irreversible database changes require a verified backup and recovery plan. Production-ready status is
forbidden until an isolated restore drill passes.

## Development Contract

- Use Spec Kit's constitution -> specify -> plan -> tasks -> implement -> converge flow.
- Use ECC selectively for planning, TDD, review, security, benchmark methodology, continuity, and
  research; never load the full catalog into every context.
- Every major milestone declares acceptance tests before implementation.
- Measurements are baseline-versus-candidate under the same inputs; stars and vendor claims are
  discovery signals, not proof.
- First-party code remains as small as practical, but complexity is not rejected merely because it is
  large when a larger solution produces lower total cost and lower maintenance risk.
- No hidden dual-write or shadow source of truth is allowed.

## Continuity Contract

The latest valid `.pusula/continuity/checkpoint-XX.json` is the compact resumption authority for the
active Pusula build. A checkpoint is valid only when its schema, percentage, baseline SHA, active spec,
plan version, evidence references, next actions, and digest validate. The capsule budget is bounded;
old narrative is replaced by references rather than copied forward.

A checkpoint MUST be emitted when crossing each quarter boundary. Before continuing after a context
reset, the agent MUST re-read the last checkpoint and verify that its baseline/spec references still
exist. If they do not, execution stops as BLOCKED instead of guessing.

## Governance

This constitution supersedes convenience instructions, tool defaults, and agent self-assessment for
Pusula work. Amendments require an explicit reason, a semantic version change, and a Sync Impact
Report. MAJOR versions redefine or remove non-negotiable principles; MINOR versions add materially new
principles; PATCH versions clarify without changing authority.

Compliance is reviewed at each 25% checkpoint and before release. A failed constitutional gate cannot
be waived by an agent. The owner may change product scope, but the change MUST become a new recorded
GoalRevision and MUST NOT silently rewrite accepted historical evidence.

**Version**: 2.0.0  
**Ratified**: 2026-08-23  
**Last Amended**: 2026-08-23
