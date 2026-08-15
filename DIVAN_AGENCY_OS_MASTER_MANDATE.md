# DIVAN — AI SOFTWARE AGENCY OS MASTER MANDATE

> **Padişah Fermanı / Standing Owner Delegation — REV 2**
>
> This is the binding transformation mandate for the existing `trugurpala/divan` repository. It is intentionally written for Claude Code Desktop and other capable coding agents operating on the owner's Windows 11 machine.
>
> **Do not build a second product. The product is Divan. Do not wait for the owner to supervise routine engineering. Own the locally achievable outcome.**

---

## 0. PRIMARY DIRECTIVE

The owner has delegated broad standing technical authority for this transformation.

Your job is not to produce another proposal and stop. Your job is:

```text
UNDERSTAND
→ VERIFY CURRENT REALITY
→ RESEARCH ONLY WHAT IS MISSING
→ DECIDE
→ PLAN
→ IMPLEMENT
→ TEST
→ INDEPENDENTLY REVIEW
→ RECOVER/REPLAN WHEN NEEDED
→ COLLECT EVIDENCE
→ INTEGRATE
→ RECORD MEMORY
→ CONTINUE
```

Continue until the locally achievable Agency OS outcome is complete, a hard external gate is reached, or evidence proves a different architectural decision is necessary.

### The anti-permission-loop rule

Within the standing delegation below, **asking the owner for routine technical permission is a product defect**.

Do not ask questions such as:

- Which library should I use?
- Should I refactor this file?
- Should I add tests?
- Should I add a migration?
- Should I create a worktree?
- Should I retry the worker?
- Should I use Codex or Claude?
- Should I add a skill/plugin/tool?
- Should I update a stale document?
- Should I open a PR?
- Should I fix the CI failure I caused?
- Should I inspect current official documentation?

If repository evidence, current official documentation, tests, benchmarks and the Ferman are sufficient to decide, **decide and act**.

When two technical choices are both valid, prefer the one that is:

1. safer;
2. simpler;
3. more replaceable;
4. easier to verify;
5. better aligned with current Divan architecture;
6. lower in token/runtime/maintenance cost.

Record meaningful decisions; do not turn them into chat interruptions.

---

# 1. STANDING TECHNICAL DELEGATION

The owner grants Divan/Claude Code standing authority to perform the following without asking again when needed to satisfy the active Ferman or this Agency OS mandate.

## Repository and Git authority

You may:

- inspect all repository code, history, branches, PRs, workflows and evidence;
- create and remove your own temporary branches/worktrees;
- edit code, tests, documentation, configuration and project-owned scripts;
- create migrations and compatibility adapters;
- stage and commit verified work;
- open/update/close/supersede development PRs when evidence justifies it;
- rebase or reconstruct your own branches on current `main`;
- resolve merge conflicts while preserving user-authored work;
- merge a Ferman-scoped technical PR when all required current repository gates, independent review and branch protection requirements pass;
- update `.divan/progress.md`, ADRs, evidence and other durable state.

Never bypass branch protection, fabricate checks, force-push over user work, or discard unrelated changes.

## Engineering authority

You may autonomously:

- choose implementation details and internal architecture;
- refactor when required for correctness, maintainability or testability;
- add/remove project dependencies after source/license/security/compatibility review;
- create or update tests, fixtures, evals and fault-injection scenarios;
- add observability required to prove behavior;
- add schema migrations with compatibility and rollback evidence;
- improve build/CI/dev tooling;
- add feature flags or compatibility layers;
- fix adjacent defects discovered while implementing when they directly block or invalidate the Ferman;
- update user-facing copy/UX required by acceptance criteria;
- prepare release artifacts and release evidence.

## Capability authority — skills, agents, plugins and tools

You are explicitly authorized to acquire or create missing engineering capability when it provides measurable value.

You may:

- use existing Divan skills and packages;
- create a new Divan skill/recipe when a reusable procedure is missing;
- create bounded specialist agent roles/subagents;
- use Codex, Claude Code and other locally proven compatible agents as workers/reviewers;
- evaluate and adapt open-source tools;
- add a plugin/adapter/MCP/CLI integration behind Divan contracts;
- add local scanners, browser tooling, code-navigation/context tools or build utilities;
- create hooks/doctor checks from repeated incidents;
- replace a failing optional tool with a better adapter-compatible alternative.

Do **not** install or vendor things merely because they are popular. Every persistent capability must earn its place through the capability-acquisition pipeline in this mandate.

## Local machine authority

For this project you may run the commands required to inspect, build, test, benchmark, package and debug Divan and its controlled fixtures.

Prefer project-scoped/reversible installation. Do not silently weaken Windows security, change unrelated global configuration, expose credentials, or mutate unrelated projects.

---

# 2. THE ONLY HARD OWNER GATES

The standing delegation is intentionally broad, but it is not a license to create irreversible external consequences.

Stop for owner input only when the next necessary action is one of these and no safe reversible alternative exists:

1. deleting or irreversibly transforming real owner/customer data;
2. purchasing something, increasing a paid quota/plan, or creating material new spend;
3. changing credentials/accounts, transferring ownership or exposing a secret;
4. weakening a required security/quality gate or accepting a known serious vulnerability;
5. changing unrelated projects or machine-wide security policy;
6. bypassing branch protection or destroying user-authored work;
7. making an ambiguous **business/product outcome** choice where evidence cannot infer intent;
8. public production deployment, public release/tag promotion or another irreversible external publication step.

A missing tool, failed test, merge conflict, stale PR, unavailable worker, retry, refactor, dependency choice, architecture implementation detail or local build problem is **not** an owner gate.

When a hard gate is reached, do not ask an empty question. Present:

```text
Karar gerekiyor
Sorun: ...
Divan'ın önerisi: ...
Alternatif: ...
Risk: ...
Ek süre/maliyet: ...
```

---

# 3. SCOPE MODEL — OWNER INTENT VS TECHNICAL SCOPE

Replace the simplistic idea that “only the owner may expand any scope” with two different scopes.

## Product Intent Scope — owner-owned

Only a new/updated Ferman may materially change:

- the desired user/business outcome;
- target users;
- product constraints;
- explicit exclusions;
- acceptance criteria with business meaning;
- real external side effects.

Divan may clarify these from evidence, but must not silently invent a different product.

## Technical Execution Scope — Divan-owned under this mandate

Divan may autonomously expand, contract or reshape technical scope when reasonably necessary to achieve the Product Intent Scope safely.

This includes:

- additional files;
- tests and fixtures;
- refactors;
- migrations;
- internal APIs;
- CI/build/release preparation;
- documentation;
- accessibility work;
- security hardening;
- observability;
- memory/context infrastructure;
- new skills;
- agent roles;
- plugins/adapters;
- MCP/CLI/tool integrations;
- dependency changes;
- recovery logic;
- compatibility work.

Technical expansion must be **evidence-based, reversible where practical, recorded and still traceable to the Ferman**.

Do not interrupt the owner merely because the correct implementation is larger than the first naive file list.

---

# 4. CURRENT DIVAN IS THE FOUNDATION — NEVER GREENFIELD-REWRITE IT

Before every implementation pass, verify current `HEAD`; do not assume the reference SHA in this document is still current.

Preserve and evolve proven Divan concepts instead of creating parallel systems:

- one product: **Divan**;
- canonical core under `plugins/sadrazam/divan_runtime/`;
- Ferman / Nizâm-ı Sefer planning;
- current owner/governance checks;
- `ExecutionRouter` and replaceable engines/providers;
- `TaskStore`, existing task states and receipts;
- worktree-based implementation isolation;
- independent Claude/Codex review before guarded merge;
- evidence store and source-bound hashes;
- verified Claude Code and Codex host paths;
- existing skills and modular packages;
- candidate/license/eval discipline;
- Tauri 2 + React Desktop;
- self-contained Divan Core sidecar;
- Windows NSIS build/release/acceptance lanes;
- immutable release/checksum philosophy;
- canonical repository verification in current `AGENTS.md`.

The current **Patron Masası** is the seed of the Agency OS command center.

Do not replace working stdlib-only core behavior with a fashionable framework unless a measured gap survives a smaller internal solution.

---

# 5. PRODUCT DESTINATION

## One sentence

**Divan is a local-first AI Software Agency OS where the human states the desired outcome, and Divan remembers, researches, plans, delegates, recovers, verifies and delivers through real coding agents while exposing only the decisions the human actually needs to make.**

## Product promise

> **Ne istediğini söyle. Divan gerisini yönetsin.**

The normal user is the **👑 Padişah · Patron**.

The user should not need to become:

- a prompt engineer;
- a worktree operator;
- a process supervisor;
- a CI detective;
- a token accountant;
- a plugin administrator;
- a terminal log reader.

Technical depth remains available on demand, but complexity is Divan's responsibility.

---

# 6. ROLE MODEL — ROLE ≠ PROCESS ≠ MODEL

Keep stable machine/domain identifiers where compatibility matters. Human-facing presentation may use the Divan metaphor.

| Responsibility | Human-facing concept |
|---|---|
| owner | 👑 Padişah · Patron |
| mandate/goal | 📜 Ferman |
| agency state | 🏛 Divan |
| orchestration | Sadrazam |
| plan challenge | Müşavir |
| research | 🔎 İstihbarat |
| product | Ürün Divanı |
| UX/design | 🎨 Mühendishane |
| architecture | 🏗 Mimarlık Divanı |
| execution | ⚔ Ocak |
| skills/recipes | 🎓 Talimhane |
| tools/plugins | 🧰 Cephanelik |
| independent quality | 🕵 Teftiş Ocağı |
| memory | 🧠 Arşiv |
| budget/usage | 💰 Defterdar |
| policy | ⚖ Kanun |
| delivery | 📦 Teslimat Divanı |
| reliability/incident | 🏥 Bakım Ocağı |

Do not instantiate a permanent model for every title.

Default topology:

```text
1 planner/architect when needed
+ 1 builder per truly independent workstream
+ 1 independent reviewer that did not author the change
+ specialists only when the task proves the need
```

More agents are not automatically better.

---

# 7. PROJECT IS THE ROOT OBJECT

The human experiences a **Project**, not a bag of tasks.

Evolve additive project lifecycle state around existing compatible receipts:

```text
INTAKE
→ INTELLIGENCE
→ PRODUCT_DEFINITION
→ UX_DESIGN
→ ARCHITECTURE
→ PLAN_REVIEW
→ READY_FOR_EXECUTION
→ IMPLEMENTATION
→ VERIFICATION
→ ACCEPTANCE
→ DELIVERY_READY
→ RELEASED
→ MAINTENANCE
→ LEARNING
```

Prefer existing types and adapters over duplicates. Canonical concepts should converge on:

- ProjectRecord;
- Ferman/Mandate;
- ProductContract;
- UXContract;
- ArchitectureDecision;
- ExecutionRoute/DAG;
- WorkPackage;
- Attempt/AgentRun;
- PolicyDecision;
- GateResult;
- EvidenceManifest;
- OwnerDecision;
- Incident;
- KnowledgeItem;
- DeliveryReceipt.

Old valid receipts remain valid. Migrate additively; never rewrite historical evidence in place.

---

# 8. MEMORY-FIRST AGENCY

Before fresh research or rereading a large repository, Divan must ask:

1. What do we already know?
2. What was already decided and why?
3. Have we seen this failure before?
4. Is stored knowledge fresh enough for this decision?
5. What is genuinely missing?

Use and reconcile existing Knowledge Fabric / Agency Memory work rather than building a second store.

Memory classes should cover at least:

- constitution/rules;
- project profile;
- architecture decisions;
- incidents/root causes;
- researched technology intelligence with provenance/freshness;
- reusable recipes/skills;
- retrospectives and observed outcomes.

## Learning promotion ladder

A repeated lesson should move toward enforcement:

```text
incident
→ structured memory
→ regression test when deterministic
→ policy gate when safety/permission related
→ skill/recipe when procedural
→ doctor/hook when environment related
```

The strongest memory is a rule the model no longer needs to remember because the system now enforces it.

Never silently turn popularity or repeated success into authority. Validation remains explicit and evidence-backed.

---

# 9. CONTEXT COMPILER — TOKEN ECONOMY IS ARCHITECTURE

Do not send every worker the entire repository, all skills and all history.

Build/evolve a `ContextCompiler` that selects the smallest useful task pack from:

- active Ferman and acceptance criteria;
- project summary;
- relevant decisions;
- relevant prior incidents;
- related symbols/interfaces/tests;
- active diff/failure;
- current official framework documentation when needed;
- required quality/policy rules.

Track useful metrics with honest confidence:

- candidate vs selected context size;
- memory hits;
- research calls avoided;
- duplicate context removed;
- tool output summarized/externalized;
- provider token/cost only when observable;
- confidence: `exact | estimated | unknown`.

External code-navigation/repo-packing/vector tools may be evaluated, but they are adapters/indexes, not canonical memory.

---

# 10. CAPABILITY ACQUISITION PIPELINE — DIVAN MAY GROW NEW HANDS

When a task needs a capability Divan does not currently have, **do not immediately ask the owner**.

Run this pipeline:

```text
CAPABILITY GAP
→ search existing Divan capability
→ inspect installed host capability
→ current official docs
→ current OSS candidates if still needed
→ compare smallest viable options
→ source/license/security review
→ quarantine/isolated smoke test
→ contract test
→ benchmark/eval when the choice affects quality/performance
→ ADOPT | ADAPT | REJECT | LATER
→ pin identity/version
→ register capability
→ document rollback/removal
→ use through a Divan adapter/skill contract
```

Possible outputs include:

- a new skill;
- a reusable recipe;
- an agent adapter;
- a quality adapter;
- a plugin;
- an MCP integration;
- a CLI wrapper;
- a local service;
- a doctor check;
- a regression test.

Rules:

- prefer official APIs/protocols over scraping terminal text;
- prefer replaceable adapters over core coupling;
- do not vendor unlicensed material;
- do not download and execute unknown scripts without inspection;
- do not expose all capabilities to every worker;
- do not add a heavyweight runtime until a real measured gap justifies it.

---

# 11. FERMANDAN İCRAYA — TWO-PASS PLANNING

Do not replace deterministic Nizâm-ı Sefer validation with free-form model prose.

Use two layers:

### A. Proposal intelligence

A capable planner may synthesize:

- product outcome;
- UX contract;
- architecture options;
- risks;
- work breakdown;
- dependencies;
- evidence requirements.

### B. Deterministic Divan materialization

Divan code validates:

- schema;
- dependencies;
- technical authority;
- product intent boundaries;
- executable capability availability;
- scope constraints;
- evidence requirements;
- safe parallelism;
- budgets/limits that are actually measurable.

For non-trivial work, run an independent **Müşavir** plan challenge before execution.

Müşavir checks missing requirements, migrations, rollback, security, browser/accessibility/error states, release obligations, same-file parallel conflicts and unsupported capabilities.

---

# 12. REAL WORKERS — CODEX + CLAUDE FIRST, OTHERS AS ADAPTERS

Detect real installed capability; never guess CLI flags or model availability.

For each worker/provider record what can actually be proven:

- executable/version;
- usable/auth state where safely observable;
- structured/noninteractive mode;
- session/resume support;
- approval/permission controls;
- skills/plugins/MCP support;
- worktree/sandbox behavior;
- last verification source/time.

Prefer richer supported integrations behind adapters. Keep bounded fallback paths where useful.

## Attempt reliability

Task identity and execution attempt identity must be separate.

Incrementally support:

- lease;
- heartbeat/liveness;
- checkpoint;
- stall detection;
- idempotent retry/backoff;
- interrupted/orphaned recovery;
- safe resume when supported;
- replacement worker selection;
- auth/quota/provider failure classification;
- circuit breaker;
- explicit cancellation.

A PID is not health.

Prove recovery by controlled real process interruption, not only mocked transitions.

If a worker fails and the next safe action is inferable, recover automatically instead of asking the owner.

---

# 13. WORKSPACE, POLICY AND SCOPE ENFORCEMENT

A prompt is not a sandbox.

Strengthen current worktree/authority controls with enforceable layers where practical:

- allowed/denied paths;
- symlink/path traversal rejection;
- explicit mutation authority;
- tool/capability allowlists;
- secret redaction/brokering;
- resource/time/tool-call ceilings where measurable;
- network restrictions where truly enforceable;
- post-run diff validation;
- no merge if diff escapes validated technical scope.

Windows-native operation remains first-class. WSL/Docker/stronger isolation may become optional execution profiles only if their measured benefit and user experience justify them.

---

# 14. TEFTİŞ — NO AGENT GRADES ITS OWN HOMEWORK

Worker self-report is not proof.

Select relevant quality profiles from the actual project/risk. Potential gates include, when applicable:

- unit/integration tests;
- typecheck/lint;
- production build;
- migration verification;
- Playwright/browser E2E;
- accessibility;
- secret scanning;
- vulnerability/dependency scanning;
- SAST;
- auth/authz negative tests;
- installer/upgrade/rollback smoke;
- independent Claude/Codex review;
- evidence manifest validation.

Status vocabulary is strict:

```text
PASS | FAIL | BLOCKED | NOT_INSTALLED | UNKNOWN
```

Only `PASS` is pass.

If a required quality tool is missing, the Capability Acquisition Pipeline may install/adapt a suitable project-scoped tool automatically. If no safe option exists, mark the gate truthfully; do not fake success.

---

# 15. EVIDENCE — DELIVERY RECEIPT

For material work, Divan must be able to reconstruct:

- project/Ferman/work package/attempt IDs;
- base/result commit;
- branch/worktree;
- changed files + diff digest;
- commands + exit codes;
- gate results;
- build/browser/security artifacts where relevant;
- reviewer identity/result;
- policy denials;
- worker/provider/session identity where safe;
- duration/retries;
- token/cost with confidence when available;
- owner decisions/hard gates;
- timestamps/source versions.

Human UI shows a compact explanation. Technical mode exposes the receipt.

---

# 16. PADİŞAH UX — OWNER ATTENTION IS A SCARCE RESOURCE

Normal UI has three depths:

1. **👑 Padişah · Patron** — outcome, progress, problem, decision, result.
2. **🏛 Divan** — plan, workstreams, memory, risks, evidence.
3. **🛠 Teknik** — exact agent, command, worktree, trace, diff, receipt, logs.

Every important status answers:

1. Ne oluyor?
2. Ne durumda?
3. Sorun var mı?
4. Divan ne yapıyor?
5. Benden bir şey gerekiyor mu?

Collapse technical noise:

```text
0 kritik sorun
1 karar sizi bekliyor
2 bilgi
```

Do not turn routine failures into owner interruptions. Retry/recover/replan first.

Completion language:

- **Yapıldı** — implementation exists;
- **Kontrol ediliyor** — independent verification is running;
- **Hazır** — required gates/evidence passed.

Only the last one is delivery-ready.

---

# 17. PATRON MASASI → AGENCY COMMAND CENTER

Evolve the real existing Desktop vertically; do not build fake dashboards ahead of Core truth.

Target navigation, only as underlying data becomes real:

- **Taht** — projects, health, decisions, ready deliveries;
- **Ferman** — natural-language intake;
- **Divan** — Intelligence → Product → UX → Architecture → Plan;
- **Ocak** — workstreams/workers in human language;
- **Teftiş** — quality/evidence;
- **Arşiv** — memory/decisions/incidents;
- **Talimhane** — skills/recipes;
- **Cephanelik** — plugins/tools/adapters and trust state;
- **Defterdar** — usage/time/token/quota truth;
- **Teslimat** — integration/release/rollback evidence.

Do not let `PatronDesk.tsx` or `App.tsx` become permanent monoliths as the product grows. Extract typed components/read models with tests.

Default autonomy is effectively **Tam Divan for reversible technical work** under this mandate.

---

# 18. WINDOWS 11 PRODUCT EXPERIENCE

Do not invent a second installer. Extend the existing Tauri/NSIS chain.

First-run should feel like a product:

```text
Divan hazırlanıyor…
✓ Divan Core
✓ Git
✓ Codex: durum
✓ Claude Code: durum
✓ proje çalışma alanı
✓ temel teftiş yetenekleri

Divan hazır.
[Proje ekle] [Yeni Ferman]
```

Do not collect provider secrets into Divan if official login owns them.

Doctor must distinguish:

- installed;
- usable/authenticated where observable;
- capability verified;
- degraded;
- unavailable;
- incompatible.

Executable presence alone is not readiness.

---

# 19. OPEN WORK — FINISH BEFORE DUPLICATING

At the time this mandate was authored, high-value work already existed in stacked/draft PRs. Always inspect their current truth before acting.

Priority sequence:

1. **#156** — real Nizâm-ı Sefer goal preview/persistence;
2. **#157** — dependency-aware receipt-bound work packages;
3. **#158** — Patron Masası real Ferman preview/save flow;
4. **#121 / #123** — Knowledge Fabric + project-aware Agency Memory;
5. **#119** — fail-closed Plugin SDK / Trust Center.

Do not merge stale code blindly. Rebase, port or supersede the smallest valuable behavior on current `main`, rerun current gates, then retire obsolete branches cleanly.

Do not mix unrelated dependency maintenance into feature proof unless required.

---

# 20. IMPLEMENTATION PASSES

The order is binding unless current evidence shows that a dependency changed.

## PASS 0 — Current truth

- read `CLAUDE.md`, `AGENTS.md`, this mandate, `BLUEPRINT.md`, `.divan/progress.md` and relevant current product/release docs;
- inspect git status/branch/history/open PRs;
- verify installed tool/agent versions and capabilities;
- run current handoff/baseline verification;
- classify: already done / partial / missing / stale / blocked;
- preserve unrelated user work.

**Exit:** reproducible baseline and exact next implementation slice.

## PASS 1 — Real Ferman pipeline

Finish/reconcile #156 → #157 → #158 on current main.

**Exit:** natural-language Ferman → read-only preview → explicit persistence → dependency-aware real work packages → real Patron Masası data; planning grants no source mutation by itself.

## PASS 2 — Project-level Agency lifecycle

Add Product/UX/Architecture/Agency lifecycle projections additively around existing goal/task receipts.

**Exit:** one project can move from Ferman through execution readiness with machine-readable state and clear owner-facing status.

## PASS 3 — Memory-first intelligence

Reconcile #121/#123. Add freshness, project-open lookup, task-close learning and promotion of deterministic lessons to tests/policies/skills/hooks.

**Exit:** a later task reuses a validated prior decision/lesson with provenance instead of rediscovering it.

## PASS 4 — Resilient real workers

Improve Codex/Claude capability discovery and attempt lifecycle: lease, heartbeat, checkpoint, stall, retry, resume/replacement, cancel, provider classification.

**Exit:** real controlled worker interruption produces truthful recovery and evidence.

## PASS 5 — Capability acquisition + Plugin Trust

Reconcile #119 and implement the smallest persistent capability acquisition path required by real gaps.

**Exit:** skill/plugin/tool candidates can be provenance-bound, permission-reviewed, tested, activated/rejected and rolled back without becoming Divan authority.

## PASS 6 — Context compiler

Measure baseline first. Add relevant code/memory/doc retrieval and progressive disclosure.

**Exit:** representative tasks receive smaller relevant context with no correctness regression, measured before/after.

## PASS 7 — Teftiş Factory

Make quality profiles and EvidenceManifest stronger; connect relevant browser/security/build gates through adapters.

**Exit:** planted failures are caught; missing required gates cannot become PASS.

## PASS 8 — Full Padişah UX

Refactor Desktop into maintainable typed views/read models and implement the three information depths plus compressed decisions/recovery states.

**Exit:** a non-expert can create a Ferman, understand progress/failure/recovery, review evidence and continue without terminal supervision.

## PASS 9 — Installer/onboarding/doctor

Use current Windows release system. Improve first-run capability truth and recovery.

**Exit:** clean Windows install → attach repo → real bounded agent task → restart → state preserved, proven by current real-user acceptance lane.

## PASS 10 — Multi-machine only after local reliability

Add a stable worker registration contract and one remote-worker proof if genuinely useful.

**Exit:** second trusted machine executes an isolated package and returns evidence; disconnect is handled truthfully.

## PASS 11 — Agency OS eval/release readiness

Use repository eval discipline plus real fault injection for bug fix, feature, refactor, memory reuse, worker crash, provider failure, scope violation, browser regression, reviewer catch, restart, installer and plugin drift cases.

**Exit:** release-ready evidence package and documented limitations. Public promotion remains a hard owner gate.

---

# 21. VERTICAL-SLICE RULE

Before broad UI expansion, prove one real end-to-end loop:

```text
Padişah Ferman
→ memory/intelligence
→ product/acceptance
→ plan proposal
→ deterministic validation
→ work package
→ isolated worktree
→ real builder
→ project-native quality
→ independent other-agent review
→ evidence
→ owner-friendly result
→ guarded integration
→ lesson/memory capture
```

Do not build ten beautiful screens around mocked workers.

---

# 22. SELF-HEALING OPERATING DOCTRINE

When something fails, use this order before interrupting the owner:

```text
classify failure
→ preserve work/evidence
→ determine whether retry is safe
→ retry with bounded backoff if transient
→ resume session if proven safe
→ replace worker/provider if capability-equivalent
→ shrink/rebuild context if context failure
→ repair environment/project-scoped dependency if local
→ replan task graph if assumptions changed
→ record incident/lesson
→ continue unaffected work
```

Stop loops with circuit breakers. Never spend indefinitely because retries are possible.

If the same class of failure appears again, convert the lesson into enforcement where possible.

---

# 23. DEFINITION OF DONE — AGENCY OS READY

Do not declare Agency OS ready because code compiled or UI looks complete.

A release candidate must prove at minimum:

1. clean Windows install;
2. truthful Doctor/capability state;
3. project registration;
4. ordinary-language Ferman;
5. memory-first lookup;
6. product/UX/architecture artifacts when applicable;
7. deterministic dependency-aware work packages;
8. real Codex/Claude bounded execution;
9. safe isolation for concurrent writers;
10. worker interruption recovery;
11. technical scope/path violation blocking;
12. relevant test/browser/security gates;
13. independent review;
14. human-readable evidence;
15. no integration before required gates;
16. controlled branch/PR/merge path;
17. restart persistence;
18. lesson/memory capture;
19. plugin/tool trust and rollback for adopted extensions;
20. update/uninstall/recovery health;
21. public docs matching observed product behavior.

Unknown, skipped, missing or timed-out evidence is never silently converted to PASS.

---

# 24. DURABLE MEMORY — DO NOT DEPEND ON THIS CHAT

The owner should never need to repeat this authorization because a model session changed.

Persist project truth in the repository and Divan state, not conversational memory alone.

At each meaningful pass update the appropriate durable surfaces, especially:

- `.divan/progress.md`;
- architecture/ADR decisions;
- evidence/receipts;
- capability/trust records;
- knowledge/incident records;
- relevant tests;
- this mandate only when the owner changes the mandate.

A later explicit owner instruction overrides this document. Until then, this standing technical delegation remains the project instruction for the Agency OS transformation.

---

# 25. STATUS REPORTING — DO THE WORK, THEN COMPRESS THE STORY

Do not stream a developer diary to the owner.

At meaningful checkpoints report:

```text
Ne yaptım
- ...

Şu an durum
- Milestone: ...
- Çalışan: ...
- Teftiş: ...
- Kritik sorun: ...

Otomatik çözdüğüm
- ...

Sizden karar gerekiyor mu?
- Hayır
```

Only report a percentage if it is calculated from defined milestones/gates.

When no hard gate exists, the final line should usually be **Hayır** and work should continue.

---

# 26. START NOW

When Claude Code Desktop reads this mandate:

1. Do not ask the owner to restate the dream.
2. Do not ask for routine technical authorization.
3. Read current repository truth and verify the machine capabilities.
4. Run baseline/handoff checks.
5. Reconcile open work before creating duplicates.
6. Start PASS 0 and move into PASS 1 immediately when baseline permits.
7. Use skills, agents, plugins, tools and external research as needed through the rules above.
8. Implement in vertical slices.
9. Run targeted tests, canonical verification and independent review.
10. Commit/integrate verified Ferman-scoped technical work under the standing repository authority.
11. Update durable progress/evidence/memory.
12. Recover and continue when workers/tools fail.
13. Stop only at a hard owner gate or when no safe next action can be derived from evidence.

The governing question is:

> **Can the human say what they want once, and can Divan safely do the engineering work, obtain the capabilities it needs, recover from failure, prove the result and remember the lesson without requiring the human to become the orchestrator?**

Until this is demonstrated by real evidence, the transformation continues.
