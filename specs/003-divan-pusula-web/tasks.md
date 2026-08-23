# Tasks: Divan Pusula Web

Each numbered item is one locked main task from `.pusula/plan-lock.json`. The checkboxes are the
minimum implementation slices; more can be added without changing the main task index. A main task is
complete only when its acceptance gate is recorded as verified evidence.

## A — Source and governance

### 1. Immutable Divan baseline

- [x] Pin baseline SHA `68e91fdf48dbcc385be567f4b525a682eeb9af05`.
- [x] Record source version, test count, skips and coverage in the plan lock.
- [ ] Create non-semver immutable Pusula baseline ref/tag without impersonating a release.
- [ ] Produce repository/config backup manifest and digest evidence.
- [ ] Restore the baseline in an isolated checkout and rerun the canonical verifier.

### 2. Constitution 2.0 and authority chain

- [x] Create `.specify/memory/constitution.md` version 2.0.0.
- [x] Define model proposal vs Mizan decision vs policy authority.
- [x] Define provider-independence and fail-closed principles.
- [ ] Add executable constitution checks for machine-testable rules.
- [ ] Run constitution compliance at the first quarter gate.

### 3. Product repository topology and license wall

- [x] Record `divan-pusula` as the target standalone product repository.
- [x] Define the current Divan branch as an incubation surface only.
- [ ] Define first-party package boundaries: web/api/mizan/runner/adapters/policies.
- [ ] Add upstream pin/license/provenance registry schema.
- [ ] Prove third-party upstream source is not silently vendored into first-party packages.

### 4. Acceptance and Evidence protocol

- [x] Define feature-level `AC-001..AC-016` in `spec.md`.
- [ ] Define machine schema for EvidenceEnvelope and safe error codes.
- [ ] Bind evidence to source SHA, run ID, producer and freshness metadata.
- [ ] Define VERIFIED/PARTIAL/FAILED/UNKNOWN/BLOCKED state transitions.
- [ ] Add negative fixtures proving skipped/timeout/stale evidence cannot become success.

## B — Identity and application spine

### 5. Self-host identity provider

- [ ] Benchmark Logto self-host against at least one qualified alternative.
- [ ] Implement OIDC provider adapter and passwordless sign-in flow.
- [ ] Implement organization membership and invite mapping.
- [ ] Add optional MFA/passkey capability flags without making them V1 mandatory.
- [ ] Pass browser E2E register/login/invite/logout/re-login flow.

### 6. Tenant isolation and authorization

- [ ] Implement Owner, Member and Viewer product roles.
- [ ] Require team/project ownership on tenant-scoped records.
- [ ] Enforce resource scope at API/service layer.
- [ ] Feed identity/resource context into deterministic policy checks.
- [ ] Pass cross-tenant read/write negative tests with zero escapes.

### 7. PostgreSQL canonical brain store

- [ ] Create append-only domain event schema.
- [ ] Create projections, inbox, outbox and idempotency storage.
- [ ] Create Goal/Evidence/Decision/Cost/Audit/Deployment tables.
- [ ] Keep mutation + event + outbox in one database transaction.
- [ ] Kill a worker mid-mutation and prove no partial canonical transition survives.

### 8. React web shell and Django control API

- [ ] Bootstrap React 19 + TypeScript + Vite product shell.
- [ ] Bootstrap Django 5.2 ASGI API with production settings split.
- [ ] Add health/readiness/correlation-id/structured logging.
- [ ] Add live run updates through SSE with polling fallback.
- [ ] Open the dashboard after a clean install and preserve state across API restart.

## C — Owned Git and CI factory

### 9. Forgejo canonical software forge

- [ ] Deploy Forgejo with persistent database/repository storage.
- [ ] Bootstrap private registration, organization and repository policy.
- [ ] Configure branch protection and PR/release/package surfaces.
- [ ] Add repository/LFS/package backup job.
- [ ] With GitHub disconnected, prove clone/push/PR/merge/release still works.

### 10. GitHub/GitLab mirror and portability

- [ ] Implement `ForgeProvider` mirror adapter contract.
- [ ] Configure Forgejo -> GitHub push mirror path.
- [ ] Add GitLab mirror implementation or compatibility fixture.
- [ ] Store last-sync/failure evidence without changing canonical repo state.
- [ ] Delete a mirror and prove it can be reconstructed without product data loss.

### 11. Dagger canonical pipeline

- [ ] Create first-party Dagger module/functions for test/lint/type/security/build.
- [ ] Add local `pusula run` entry point.
- [ ] Pin tool images and define cache boundaries.
- [ ] Make Forgejo/GitHub workflow files thin Dagger triggers only.
- [ ] Prove the same commit produces equivalent gates locally and remotely.

### 12. Runner fabric and isolation

- [ ] Define RunnerProvider contract and capability schema.
- [ ] Implement trusted-local container runner profile.
- [ ] Implement disposable server isolation candidate using KVM/microVM class boundary.
- [ ] Enforce CPU/RAM/disk/network/secret/workspace quotas.
- [ ] Prove cross-run workspace and secret leakage is impossible in the test matrix.

## D — Mizan decision brain

### 13. Goal, Revision and measurable Scope

- [ ] Create immutable Goal and GoalRevision records.
- [ ] Define measurable scope units from acceptance/risk/change budget.
- [ ] Require at least four slices for automatic execution.
- [ ] Enforce max 25% scope budget per slice.
- [ ] Add property tests for boundary and revision history behavior.

### 14. Fact, Evidence and Capability graph

- [ ] Implement Fact/Assumption/Uncertainty/Contradiction records.
- [ ] Implement Source/Evidence provenance and freshness.
- [ ] Implement Capability/Provider/Edition relationship records.
- [ ] Block critical decisions on unresolved material contradiction.
- [ ] Add retention/privacy classification for evidence payloads.

### 15. Proposal, Decision, Verification and Cost ledger

- [ ] Separate AgentProposal, MizanDecision and Verification models.
- [ ] Record model/tool input-output usage and observed cost when available.
- [ ] Implement Goal soft and hard budgets plus stop reason.
- [ ] Record retries as distinct attempts rather than hiding spend.
- [ ] Prove hard budget prevents a new paid call.

### 16. OPA policy and Hatchet durable workflow

- [ ] Implement versioned Rego packages for merge/deploy/tool/cost/evidence rules.
- [ ] Return stable policy reason codes with every allow/deny result.
- [ ] Implement Goal -> research -> run -> review -> deploy Hatchet workflow.
- [ ] Add retry/timeout/pause/human-wait/resume/cancel paths.
- [ ] Kill/restart the worker and prove resume without duplicate side effect.

## E — Tool and connector platform

### 17. Capability and Connector SDK

- [ ] Define connector manifest with version/license/auth/data-boundary/cost fields.
- [ ] Require JSON Schema for tool inputs and outputs.
- [ ] Classify read/write/high-impact side effects.
- [ ] Define timeout/rate-limit/idempotency/health behavior.
- [ ] Enforce team/project enablement policy per connector.

### 18. ToolHive MCP gateway

- [ ] Deploy/attach ToolHive registry/runtime.
- [ ] Curate allowlisted MCP servers with provenance.
- [ ] Apply container/network/permission profiles.
- [ ] Bind tool call audit to Goal/Run correlation IDs.
- [ ] Prove unauthorized MCP calls are denied before provider execution.

### 19. OpenBao secret broker

- [ ] Create team/project secret namespaces.
- [ ] Store only secret references in connector manifests and Mizan records.
- [ ] Use short-lived/dynamic credentials where a provider supports them.
- [ ] Add rotation and secret-read audit paths.
- [ ] Pass adversarial prompt/log/artifact secret-exfiltration tests.

### 20. Firecrawl, Notion, Slack and Hugging Face connectors

- [ ] Firecrawl: public-default search/scrape/monitor with provenance and cost.
- [ ] Notion: scoped search/fetch/export with canonical-state separation.
- [ ] Slack: public-read default; write/approval actions require explicit policy.
- [ ] Hugging Face: model/dataset/space metadata, revision/license and optional job adapter.
- [ ] Disable each connector in turn and prove the core Goal history remains intact.

## F — Agent and model runtime

### 21. OpenHands Agent Server runtime

- [ ] Run a pinned OpenHands Agent Server inside the Runner boundary.
- [ ] Bind disposable workspace lifecycle to the Pusula run.
- [ ] Normalize agent events into provider-neutral run events.
- [ ] Prevent runtime from writing canonical Mizan state directly.
- [ ] Replace OpenHands with a fake runtime and prove the adapter boundary holds.

### 22. ACP provider adapters

- [ ] Add Codex Lead Engineer adapter.
- [ ] Add Claude independent-reviewer adapter.
- [ ] Add one optional ACP provider fixture (Gemini or local).
- [ ] Separate subscription-login and scoped API-key authentication modes.
- [ ] Record exact provider/model/runtime identity in run evidence.

### 23. Model Router and cost policy

- [ ] Define mechanical/balanced/critical task classes.
- [ ] Map classes to provider/model candidates rather than hard-coded model names.
- [ ] Estimate cost from current Radar price snapshots before execution.
- [ ] Require reviewer independence where policy says so.
- [ ] A/B route representative tasks and store cost/quality evidence.

### 24. Code intelligence and durable search

- [ ] Implement CodeIntelligenceAdapter with freshness/completeness fields.
- [ ] Benchmark codebase-memory-mcp against baseline exploration tasks.
- [ ] Expose impact/call-chain/cycle results as evidence.
- [ ] Use PostgreSQL FTS/trigram as mandatory memory-search baseline.
- [ ] Enable multilingual embedding only after a recorded benchmark win.

## G — Evidence and security

### 25. SBOM, vulnerability and provenance chain

- [ ] Generate dependency/SBOM evidence.
- [ ] Run Trivy-class dependency/container/config scans.
- [ ] Bind source SHA to artifact digest.
- [ ] Produce signed/attested provenance where supported.
- [ ] Tamper with an artifact and prove verification fails.

### 26. Security and license gates

- [ ] Require secret scanning.
- [ ] Implement allow/deny/needs-review license policy.
- [ ] Require immutable pinning for trusted third-party actions/images where applicable.
- [ ] Add protected-path elevated review policy.
- [ ] Require backup/recovery evidence for irreversible database changes.

### 27. PR, review and merge authority

- [ ] Implement provider-neutral branch/PR builder.
- [ ] Require primary agent != independent reviewer when configured.
- [ ] Bind required evidence and policy snapshot to exact PR head SHA.
- [ ] Restrict machine merge to the Mizan service identity.
- [ ] Move the PR head after green checks and prove old evidence no longer authorizes merge.

### 28. Audit and observability

- [ ] Add OpenTelemetry-compatible trace/metric/log correlation.
- [ ] Link Goal/Run/PR/Deployment IDs end to end.
- [ ] Expose model/tool cost metrics.
- [ ] Add Hatchet/runner/connector health dashboards.
- [ ] Starting from one deployment ID, reconstruct source -> evidence -> decision -> cost chain.

## H — Deployment and resilience

### 29. DeploymentAdapter contract

- [ ] Define build/publish/stage/promote/health/rollback interface.
- [ ] Define provider capability matrix including real traffic split.
- [ ] Define environment/secret injection contract.
- [ ] Define deployment evidence envelope.
- [ ] Prove an unsupported capability fails instead of being simulated or mislabeled.

### 30. Coolify default deployment

- [ ] Implement Coolify API adapter.
- [ ] Create preview/staging deployment path.
- [ ] Validate automatic TLS/domain and environment mapping.
- [ ] Connect provider-native backup hooks where appropriate.
- [ ] Treat Coolify Cloud as optional maintenance purchase, not feature authority.

### 31. Canary, promotion and rollback

- [ ] Implement staging health gate.
- [ ] Use canary only when provider supplies measurable traffic splitting.
- [ ] Persist previous-good revision before promotion.
- [ ] Trigger automatic rollback on health-policy failure.
- [ ] Block promotion when database recovery requirements are unmet.

### 32. Backup, restore and disaster recovery

- [ ] Encrypt PostgreSQL backup and retain off-host copy.
- [ ] Back up Forgejo repository/LFS/package/config state.
- [ ] Document OpenBao disaster-recovery requirements without exporting plaintext secrets.
- [ ] Define retention and recovery objectives.
- [ ] Run isolated restore drill and make it a production-readiness gate.

## I — Human product and Radar

### 33. Vibe-coder dashboard

- [ ] Build Ana Sayfa outcome dashboard.
- [ ] Build Projeler list/readiness views.
- [ ] Build Isler progress views.
- [ ] Build Hafiza and Yayinlar outcome views.
- [ ] Build Ayarlar for team/integrations/policy without exposing raw infrastructure by default.

### 34. Goal and Run workbench

- [ ] Build natural-language goal composer.
- [ ] Show bounded slices and progress timeline.
- [ ] Stream agent/tool activity with technical details collapsed.
- [ ] Show diff/test/evidence/cost explanations.
- [ ] Explain `neden durdu` and the next safe action without raw stack trace dependence.

### 35. Technology Council and Mizan Radar

- [ ] Store Free/Pro/Team/Enterprise capability snapshots.
- [ ] Store price/license/release/source snapshots and review dates.
- [ ] Calculate twelve-month TCO including migration/maintenance assumptions.
- [ ] Use Firecrawl Monitor for selected pricing/changelog change detection.
- [ ] Preserve historical KEEP/BUY/ADOPT/ADAPT/REPLACE/LATER/REJECT decisions.

### 36. Slack and Notion collaboration surface

- [ ] Export status/spec/release summaries to Notion.
- [ ] Ingest permitted Notion evidence with source provenance.
- [ ] Send scoped Slack progress/alert messages.
- [ ] Support Slack human-approval requests as a UI surface, not canonical authority.
- [ ] Take Slack/Notion offline and prove core execution remains available.

## J — Final validation and release

### 37. TR/EN, WCAG and onboarding

- [ ] Turkish-default and English-secondary product copy.
- [ ] WCAG 2.2 AA keyboard/contrast/form/reflow validation.
- [ ] 320/375/768/1024/1440 responsive acceptance.
- [ ] Empty/loading/error/offline product states.
- [ ] First login -> forge/project -> first Goal onboarding test.

### 38. Adversarial and isolation battle tests

- [ ] Prompt-injection attempt against policy authority.
- [ ] Fake test-pass/verification spoof attempt.
- [ ] Secret extraction attempt through agent/tool/log/artifact paths.
- [ ] Malicious MCP/network escape attempt.
- [ ] Cross-run/cross-tenant and webhook-replay attempts.

### 39. 12 tasks x 3 real agent evaluation

- [ ] Freeze twelve representative software tasks and scoring rubric.
- [ ] Run each task three independent times.
- [ ] Record VERIFIED/PARTIAL/FAILED/UNKNOWN only from observed evidence.
- [ ] Record cost, latency, retry and human intervention.
- [ ] Compare provider/router and local/remote execution without self-scored quality claims.

### 40. Real pilot -> production -> rollback -> Pusula 1.0.0

- [ ] Fresh user onboarding from zero state.
- [ ] Real repository import/activation.
- [ ] Natural-language Goal -> research -> patch -> test -> review -> PR.
- [ ] Staging -> production -> deliberate health failure -> automatic rollback.
- [ ] Restore/audit/install/runbook evidence and final Pusula 1.0.0 release proof.
