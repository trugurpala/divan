# Feature Specification: Divan Pusula Web

**Feature ID**: `003-divan-pusula-web`  
**Status**: Incubating  
**Constitution**: `2.0.0`  
**Plan lock**: `.pusula/plan-lock.json`  
**Target release**: `Divan Pusula 1.0.0`

## Product Outcome

A non-technical user can sign in, connect or create a software project, describe a goal in normal
language, watch Pusula research and implement it through isolated coding agents, see machine-verified
evidence, and understand whether the change is blocked, in review, staged, deployed, or rolled back.
The system remains usable when GitHub is absent because canonical Git, pipeline logic, memory, and
policy remain under Pusula control.

## Primary User Journeys

### UJ-1 — First login and team

The owner signs in passwordlessly, receives an isolated workspace, can invite a member/viewer, signs
out, and signs in again without losing state.

**Acceptance**: another team cannot read or mutate the workspace through UI or API.

### UJ-2 — Project activation

The owner activates a canonical Forgejo repository or imports an existing repository. Optional GitHub
or GitLab mirrors can be attached. Pusula reads the project and explains its stack, current checks,
risks, and readiness before allowing mutation.

**Acceptance**: installation access or mirror access alone never grants mutation permission.

### UJ-3 — Natural-language goal

The user writes a goal such as `Alt bayi sistemi ekle`. Pusula creates an immutable GoalRevision,
measurable scope units, and at least four bounded slices. Research and implementation are visible in
human language.

**Acceptance**: no automatic slice exceeds 25% of the measurable scope budget.

### UJ-4 — Agent execution and review

Codex is the default lead engineer. A different provider can act as independent reviewer. Execution
runs outside the control plane through the Pusula Runner contract. Agent claims remain proposals
until independent machine evidence verifies them.

**Acceptance**: `agent says tests passed` cannot create `VerificationPassed`.

### UJ-5 — PR and deployment

A verified run creates a reviewable PR. Exact-HEAD evidence and deterministic policy decide whether
merge is allowed. A merged change stages through a DeploymentAdapter. If real traffic splitting is
available a canary may be used; otherwise the UI must not call the promotion a canary.

**Acceptance**: a failed health check restores the previous-good revision automatically.

### UJ-6 — Technology Council

The owner can inspect why Pusula uses a technology/provider. Mizan Radar records Free/Pro/Team/
Enterprise features, price, license, data boundary, benchmark, total-cost estimate, and the current
decision. A later change creates a new review without erasing the old decision.

**Acceptance**: price or capability changes never silently change production authority.

### UJ-7 — Continuity after context loss

Development and long agent runs survive context compression or a new session. At 0/25/50/75/100%,
Pusula stores a compact validated capsule containing only current verified state and references.

**Acceptance**: a resumed agent can continue from the latest capsule without reading the full chat.

## Functional Requirements

- **FR-001** Authentication MUST be passwordless-capable and provider-neutral through an OIDC adapter.
- **FR-002** Teams MUST support Owner, Member, and Viewer roles.
- **FR-003** Tenant ownership MUST be enforced server-side, not only through hidden UI controls.
- **FR-004** Forgejo MUST be supported as the canonical Git/PR/release/package forge.
- **FR-005** GitHub and GitLab MUST be optional mirror/integration adapters.
- **FR-006** Canonical CI logic MUST live in Dagger functions; provider workflow YAML is a thin trigger.
- **FR-007** Trusted-local and untrusted-server runner profiles MUST share one RunnerProvider contract.
- **FR-008** Untrusted server jobs MUST execute in disposable isolation and MUST NOT mount control-plane
  secrets or state.
- **FR-009** Mizan MUST persist append-only domain events plus projections, inbox/outbox, audit, and
  idempotency records in PostgreSQL.
- **FR-010** Goals MUST be immutable through revisions; history MUST NOT be overwritten.
- **FR-011** Scope MUST be measured with scope units rather than an LLM-authored percentage alone.
- **FR-012** Fact, Assumption, Uncertainty, Contradiction, Evidence, Proposal, Decision, and
  Verification MUST be distinct domain concepts.
- **FR-013** Merge/deploy/cost/tool policies MUST be deterministic and testable through a policy
  engine; an LLM is not the final policy authority.
- **FR-014** Long workflows MUST support durable retry, wait, resume, cancellation, and idempotency.
- **FR-015** MCP/tool servers MUST be discoverable through a curated registry and run under explicit
  permission/network profiles.
- **FR-016** Secret values MUST be referenced from a secret broker and MUST be redacted from prompts,
  logs, artifacts, exported evidence, and canonical memory.
- **FR-017** Agent runtime MUST support Codex and at least one independent reviewer provider through a
  provider-neutral adapter/ACP surface.
- **FR-018** Code intelligence MUST expose freshness/completeness metadata; stale, partial, or
  truncated analysis MUST fail closed when required by policy.
- **FR-019** Memory search MUST work with PostgreSQL FTS/trigram without a mandatory embedding model.
- **FR-020** Semantic retrieval MAY be enabled only after a recorded benchmark proves useful gain.
- **FR-021** Build evidence MUST bind source SHA, checks, artifact digest, SBOM/security results, and
  provenance where applicable.
- **FR-022** Deployment MUST be provider-neutral and record staging, health, promotion, previous-good,
  and rollback state.
- **FR-023** Backup is not valid release evidence until an isolated restore drill passes.
- **FR-024** Firecrawl, Notion, Slack, Hugging Face, Vercel, and similar systems MUST remain connectors,
  not canonical memory.
- **FR-025** Every material provider decision MUST record edition/price/license/source/benchmark and a
  review date through Mizan Radar.
- **FR-026** A hard Goal budget MUST stop new paid model calls instead of allowing automatic retry.
- **FR-027** The UI MUST default to Turkish, offer English, and expose safe human errors before raw
  provider detail.
- **FR-028** The product MUST meet WCAG 2.2 AA for the release-critical journeys.
- **FR-029** The build process MUST write validated continuity capsules at each quarter boundary.
- **FR-030** A plan amendment MUST preserve prior checkpoints and decision history.

## Release Acceptance Controls

- **AC-001** Exact immutable baseline and restore proof.
- **AC-002** Constitution/spec/plan/tasks references agree and contain no unexplained placeholders.
- **AC-003** Passwordless login, invitation, logout, re-login and tenant-negative E2E tests pass.
- **AC-004** Domain event + projection + outbox mutation is atomic under forced worker failure.
- **AC-005** Goal revision and scope-unit properties pass boundary/property tests.
- **AC-006** Agent proposal cannot directly become Fact, Verification, merge, or deploy permission.
- **AC-007** Forgejo works with GitHub disconnected; mirror reconstruction succeeds.
- **AC-008** The same Dagger check set produces equivalent gate results locally and on a remote runner.
- **AC-009** Cross-run isolation test finds no workspace/secret leakage.
- **AC-010** Tool permission, network, and secret-exfiltration adversarial tests fail closed.
- **AC-011** Exact-HEAD policy blocks stale PR evidence after the head moves.
- **AC-012** Missing/stale/partial/truncated/timeout evidence is BLOCKED.
- **AC-013** Staging health and previous-good rollback are proven on a real deployment adapter.
- **AC-014** Search works without semantic embeddings; optional embeddings need benchmark evidence.
- **AC-015** Backup restore and outage recovery drills pass.
- **AC-016** Twelve representative software tasks run three independent times and report only measured
  VERIFIED/PARTIAL/FAILED/UNKNOWN outcomes plus cost and intervention data.

## Non-Goals for 1.0

- Native mobile application.
- Billing/subscription commerce.
- Mandatory vector database or hosted embedding API.
- Running customer repositories on the Pusula control-plane host.
- A proprietary clone of GitHub, Dagger, OPA, Hatchet, OpenHands, or Coolify.
- Autonomous installation of unreviewed external plugins.
- Claiming a provider offers canary, SSO, compliance, or security guarantees not present in current
  source evidence.

## Definition of Done

Pusula 1.0.0 is done only when a fresh human user can complete login -> project -> natural-language
goal -> isolated implementation -> verified review -> PR -> staging -> production, and a deliberately
broken production candidate automatically returns to previous-good state while the entire chain,
cost, evidence, and decision reasons remain auditable.
