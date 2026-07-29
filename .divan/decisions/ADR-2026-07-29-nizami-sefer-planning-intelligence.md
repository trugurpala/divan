# ADR — Nizâm-ı Sefer planning intelligence

Date: 2026-07-29
Status: Accepted for implementation candidate
Issue: #48

## Context

Divan could already select workflows, roles, packs and checks, but it could not
express how much work fit in one host session, when to hand off, or which
public surfaces must move with a change. Treating every substantial request as
one undifferentiated execution increased context drift and made cross-host
continuation weaker than the Project OS memory contract.

## Decision

Add a deterministic, stdlib-only planning layer inside the existing Sadrazam
Company OS control plane rather than introducing another agent runtime or UI.

The layer will:

- consume the existing host-neutral Company OS route;
- resolve exact or conservative host capacity;
- produce an English-canonical schema with Ottoman display names;
- split stages into evidence-gated campaigns/tasks;
- keep `goal_id` independent from host capacity;
- persist the host-specific route separately from the legacy receipt artifacts;
- fail closed on unclassified paths and stale public-surface obligations.

## Alternatives rejected

### Desktop orchestration application

Rejected because Divan is already a native Claude/Codex skill distribution and
Project OS. A new UI would duplicate the host and delay improvement of the
actual decision engine.

### Hard-coded Claude/Codex model windows

Rejected because product, plan and model limits can change and may not be
reported to the plugin. Fallback values are planning assumptions only.

### Unlimited multi-agent swarm

Rejected because it increases context, merge and verification risk. Parallel
work remains bounded by the route and is never an implicit prerequisite.

### Put the route inside the DPS-005 receipt artifact set

Rejected for this change because DPS-005 currently requires the exact legacy
`spec.md`, `plan.md`, `tasks.md` set. The route is SHA-bound from `spec.md`
without breaking existing receipts.

## Consequences

- Same project goal survives movement between Claude and Codex.
- A host can use a different route capacity without changing goal identity.
- Replanning an existing goal with a different route is explicit rather than a
  silent overwrite.
- Release and documentation surfaces grow, but the manifest and impact graph
  make that cost visible and testable.
