# DIVAN — AI SOFTWARE AGENCY OS MASTER MANDATE

> **Owner mandate / Padişah emri**
>
> This document is the transformation contract for the existing `trugurpala/divan` repository. It is not a greenfield rewrite request. Preserve proven work, reconcile current branches and evidence, and evolve the real product into a human-friendly, local-first AI Software Agency OS.
>
> **Product name stays `Divan`.** Machine/domain identifiers remain stable and English where already public (`owner`, `task`, `project`, etc.). Turkish presentation is first-class. The human owner may be presented as **`Padişah · Patron`**, but this is a UX label, not a new authority model.

---

## 0. EXECUTION MODE — READ THIS BEFORE TOUCHING CODE

You are not being asked to produce another proposal. You are being asked to **inspect → reconcile → plan → implement → verify → continue** until the locally achievable product outcome is complete or a genuinely non-resolvable owner decision blocks you.

### Owner authorization granted by this mandate

You may, without repeatedly asking the owner:

- inspect the repository, git history, local environment and installed agent CLIs;
- create local branches and isolated worktrees;
- edit code, tests, docs and repo-owned configuration within the mandate;
- run build, test, lint, typecheck, benchmark, browser, security and packaging commands;
- use installed Codex / Claude Code as bounded workers or independent reviewers when their real installed capabilities are verified first;
- create commits and draft/open PRs for completed, independently verified slices;
- rebase or reconstruct **your own** mandate branches when required by current `main`;
- update `.divan/progress.md`, BLUEPRINT/ADR material and evidence required by the repository contract.

You **must still ask the owner** before:

- publishing a release/tag or promoting to production;
- deleting or irreversibly transforming owner/customer data;
- spending money or changing a paid plan/quota;
- weakening a security/quality gate;
- accepting a large product-scope tradeoff with meaningful business consequences;
- changing credentials, global OS security settings or unrelated projects;
- force-pushing, bypassing branch protection or discarding user-authored work.

A failed tool, missing credential or provider quota is a runtime condition to classify and recover from where possible — not a reason to abandon the entire plan.

### Never do these

- Do not rewrite Divan from scratch.
- Do not create a second orchestration authority beside Divan Core.
- Do not replace working stdlib-only core behavior merely because an external framework looks fashionable.
- Do not install a large tool stack before proving the local gap it solves.
- Do not revive deprecated Company OS paths except for compatibility.
- Do not treat a model's self-report as evidence.
- Do not call compilation alone “done”.
- Do not mark `UNKNOWN`, `SKIPPED`, `NOT_INSTALLED` or timeout as PASS.
- Do not silently expand scope.
- Do not ask the owner routine framework/library/implementation questions that Divan can resolve through repository evidence and current official documentation.

---

# 1. CURRENT REALITY — PRESERVE THIS FOUNDATION

The repository is already far beyond a prompt collection. Before implementation, verify current `HEAD`; the reference state at the time this mandate was authored was `main` at `68e91fdf48dbcc385be567f4b525a682eeb9af05`. **If HEAD has moved, never reset to this SHA.** Reconcile the mandate with newer verified work.

Current proven concepts that must be preserved unless tests demonstrate a defect:

- one public product: **Divan**;
- owner-first authority chain and fail-closed mutation rules;
- `plugins/sadrazam/divan_runtime/` as the canonical modular core;
- current project contract, Ferman / Nizâm-ı Sefer concepts and bounded planning;
- `ExecutionRouter` and replaceable execution engines;
- worktree-oriented implementation isolation;
- independent Claude/Codex review requirement before guarded merge;
- evidence receipts, deterministic hashes and owner approval boundaries;
- verified Claude Code + Codex host installation paths;
- 42 skills and the current modular package model (`sadrazam`, `core-pack`, `ui-pack`, `react-pack`, `zanaat-pack`);
- current plugin/marketplace metadata and candidate-adoption discipline;
- Tauri 2 + React desktop application and self-contained `divan-core` sidecar;
- Windows NSIS build/release lanes and real-user acceptance contract;
- immutable release/checksum philosophy;
- `python scripts/verify.py` + `git diff --check` as canonical repo-wide local verification unless current `AGENTS.md` says otherwise;
- current public writing, security, licensing, benchmark and adoption rules.

The current Desktop already has a **Patron Masası** surface. Treat it as the seed of the new human-facing command center, not disposable prototype code.

---

# 2. PRODUCT DEFINITION — WHAT DIVAN MUST BECOME

## One sentence

**Divan is a local-first AI Software Agency OS where a human owner says what outcome is wanted, Divan researches and remembers, turns that outcome into a product and engineering plan, delegates bounded work to real coding agents, independently verifies the result, and brings only important decisions and evidence back to the human.**

## Product promise

> **Ne istediğini söyle. Divan gerisini yönetsin.**

The owner is a vibe coder / product owner, not a process supervisor. The product must reduce cognitive load rather than expose the complexity of agents, tool calls, retries and infrastructure.

### What the owner should normally do

1. Choose a project or start a new one.
2. Write a Ferman in ordinary language.
3. Review the high-level plan only when useful.
4. Answer only genuinely consequential decisions.
5. Receive a verified result, evidence summary and clear next action.

### What the owner should normally NOT need to do

- select a worker for each task;
- know MCP/ACP/JSON-RPC details;
- manage worktrees;
- watch terminals;
- retry stuck workers manually;
- choose basic implementation libraries without a product reason;
- remember old architectural decisions;
- repeatedly explain the repository to a new agent;
- manually collect test output and screenshots;
- interpret raw stack traces for ordinary failures.

---

# 3. HUMAN AUTHORITY MODEL — PADİŞAH IS A HUMAN

Keep technical machine IDs stable. Presentation hierarchy:

| Machine concept | Human-facing Turkish | Responsibility |
|---|---|---|
| `owner` | **👑 Padişah · Patron** | Goal, constraints, business decisions, final authority |
| mandate/goal | **📜 Ferman** | Desired outcome and acceptance boundary |
| agency core | **🏛 Divan** | End-to-end project authority and state |
| orchestrator | **Sadrazam** | Decompose, sequence, route, replan |
| intelligence | **🔎 İstihbarat** | Memory-first research and freshness checks |
| product | **Ürün Divanı** | User/problem/MVP/requirements |
| design | **🎨 Mühendishane** | UX, UI, design system, accessibility |
| architecture | **🏗 Mimarlık Divanı** | Stack/API/DB/security/deploy decisions |
| execution | **⚔ Ocak** | Codex, Claude Code and future workers |
| tools | **🧰 Cephanelik** | CLI, MCP, API, browser, scanners |
| skills/plugins | **🎓 Talimhane** | Skills, plugins, recipes, hooks, workflows |
| quality | **🕵 Teftiş Ocağı** | Tests, browser QA, security, independent review |
| delivery | **📦 Teslimat Divanı** | Installer, docs, release evidence, rollback |
| maintenance | **🏥 Bakım Ocağı** | Bugs, updates, monitoring, security maintenance |
| memory | **🧠 Arşiv** | Decisions, incidents, lessons, intelligence |
| budget | **💰 Defterdar** | Time, tokens, quota, cost/confidence |
| policy | **⚖ Kanun** | Permissions, scope, approvals, sandbox policy |

**Do not implement each role as a permanent model process.** Roles are domain responsibilities. A small number of real agents may perform multiple roles at different stages.

Default execution topology should remain small:

- one planner/architect where reasoning is needed;
- one builder per independent workstream;
- one independent reviewer that did not author the change;
- additional specialists only when evidence shows true parallel value.

More agents are not automatically better.

---

# 4. THE ROOT OBJECT IS PROJECT, NOT TASK

Tasks are implementation details. The owner experiences a **Project**.

Introduce or evolve canonical project-level lifecycle/state without breaking existing task/goal receipts:

```text
IDEA / INTAKE
→ INTELLIGENCE
→ PRODUCT_DEFINITION
→ UX_DESIGN
→ ARCHITECTURE
→ PLAN_REVIEW
→ READY_FOR_EXECUTION
→ IMPLEMENTATION
→ VERIFICATION
→ STAGING / ACCEPTANCE
→ DELIVERY_READY
→ RELEASED (only after owner/release authority)
→ MAINTENANCE
→ LEARNING
```

The migration may use additive schemas and compatibility projections. Do not rewrite old receipts in place.

Canonical project artifacts/concepts should converge on:

- `ProjectRecord`
- `Ferman` / mandate
- `ProjectContract`
- `ProductContract`
- `UXContract`
- architecture decisions / ADRs
- execution route / DAG
- `WorkPackage`
- `Attempt`
- `AgentRun`
- `PolicyDecision`
- `GateResult`
- `EvidenceManifest`
- `OwnerDecision`
- `Incident`
- `KnowledgeItem` / memory record
- release/delivery receipt

Do not create duplicate concepts where an existing Divan type already covers the same responsibility. Prefer migration/adapters over parallel models.

---

# 5. MEMORY-FIRST INTELLIGENCE — THE MOST IMPORTANT PRODUCT ADVANTAGE

Before new research, Divan must ask:

1. What do we already know about this project?
2. What decision was already made and why?
3. Have we seen this failure before?
4. Is the stored knowledge still fresh enough?
5. What is missing and therefore deserves new research/tool calls?

## Memory classes

At minimum distinguish:

- **Constitution memory** — stable Divan/repo rules;
- **Project memory** — stack, commands, architecture, critical paths, constraints;
- **Decision memory** — what was decided, alternatives, reason, scope and freshness;
- **Mistake/incident memory** — symptom, root cause, fix, regression evidence;
- **Intelligence memory** — researched frameworks/tools/licenses/providers + provenance + freshness;
- **Skill/recipe memory** — successful repeatable workflows;
- **Retrospective memory** — estimate vs actual, retries, reviewer catches, failure patterns.

## The most important learning rule

A repeated lesson should not remain only prose.

Prefer this promotion ladder:

```text
incident / lesson
→ structured memory
→ if deterministic: regression test
→ if permission/safety: policy gate
→ if reusable procedure: skill/recipe
→ if environment/tool event: hook/doctor check
```

The best memory is knowledge the model no longer needs to remember because the system now enforces it.

## Existing work to reuse

Do not build a second memory system blindly. Inspect and reconcile the existing draft work:

- PR **#121** — local-first Divan Knowledge Fabric v1;
- PR **#123** — project-aware Agency Memory read model.

These branches may be behind current `main`; rebase/reconstruct the smallest valid slices on top of current verified state. Preserve the stated design strengths: structured knowledge kinds, provenance, candidate/validated/deprecated lifecycle, SQLite local persistence, separate observations, explainable analytics and no silent auto-promotion.

### Semantic/vector retrieval

Do **not** add a vector database simply because it is fashionable. First benchmark the structured/lexical retrieval from Knowledge Fabric on realistic Divan project histories. Only if recall/token metrics justify it, evaluate an optional replaceable semantic-index adapter. The canonical source must remain inspectable and exportable; an index must be rebuildable.

---

# 6. CONTEXT AND TOKEN ECONOMY

The fastest agent is the one that does not reread the entire world.

Implement a `ContextCompiler` concept above providers. It should assemble the smallest task-specific context pack from:

- Ferman and acceptance criteria;
- project summary;
- relevant architecture decisions;
- relevant prior incident(s);
- related symbols/interfaces/tests;
- current diff and active failure;
- current official framework documentation only when needed;
- required quality/policy rules.

Use progressive disclosure. Never inject all skills, all history, all research and the full repository by default.

Track metrics such as:

- candidate context bytes/tokens;
- selected context bytes/tokens;
- reused memory count;
- external research calls avoided by fresh memory;
- duplicate context eliminated;
- tool-output bytes externalized/summarized;
- worker input/output token counts **only where the provider exposes reliable data**;
- confidence: `exact | estimated | unknown`.

Existing Divan planning context budgets must remain honest planning assumptions unless the installed host verifies a real limit.

Possible community tools such as semantic code retrieval or repo packing are **candidates**, not mandatory dependencies. Evaluate through Divan's existing candidate, license, benchmark and adoption process. Do not bypass `registry/candidates.json`, `UPSTREAM.md`, `THIRD_PARTY_LICENSES.md` and relevant eval rules.

---

# 7. INTELLIGENCE DEPARTMENT — RESEARCH MUST BE A GATE, NOT DECORATION

Before architecture or dependency adoption, create/update a `Project Intelligence Dossier` sufficient to answer:

## Product intelligence

- What problem is being solved?
- Who uses it?
- What is already standard in this product category?
- Which requested features are MVP vs later?
- What must explicitly stay out of scope?

## Repository intelligence

- current architecture and runtime paths;
- active framework/package/runtime versions;
- build/test/release commands;
- persistence and migration surfaces;
- auth/security boundaries;
- existing debt and known failures;
- current open branches/PRs that overlap the task.

## Technology intelligence

For each material dependency/tool:

- current installed/project version;
- official docs/API/CLI behavior;
- Windows compatibility where relevant;
- license and redistribution constraints;
- maintenance status and security risk;
- why existing Divan primitives are insufficient;
- `KEEP | ADD | ADAPT | LATER | REPLACE | REJECT` decision;
- exit/replacement strategy.

Research is allowed to produce `PLAN_BLOCKED` when a critical unknown would make implementation guesswork.

Do not research stable facts on every run. Use freshness timestamps and only refresh stale/critical knowledge.

---

# 8. PRODUCT + UX BEFORE DEEP IMPLEMENTATION

A Ferman should produce human/product contracts before a large code wave.

## Product Contract

Capture at least:

- problem statement;
- target user;
- jobs/outcomes;
- user journeys;
- functional requirements;
- non-functional requirements;
- MVP / later / out-of-scope;
- testable acceptance criteria;
- success metrics where meaningful;
- material product risks.

## UX Contract

For UI work, define testable experience constraints such as:

- primary task path;
- maximum complexity/steps where meaningful;
- responsive behavior;
- loading / empty / error states;
- keyboard and focus behavior;
- accessibility requirements;
- no raw stack traces or provider jargon in normal mode;
- human-readable recovery state;
- technical details available on demand rather than hidden forever.

Use the existing `ui-pack`, `product-design-audit`, browser testing and relevant React package instead of creating a second design system without need.

---

# 9. TWO-PASS PLANNING — SADRAZAM + MÜŞAVİR

The current deterministic Nizâm-ı Sefer planner is valuable and must remain a **validator/planning authority**, not be replaced by free-form model prose.

Evolve planning into two layers:

1. **Proposal layer** — a capable agent may synthesize product/architecture/task proposals from bounded context.
2. **Deterministic Divan validation/materialization** — schemas, dependencies, scope, authority, evidence and budget are checked by code before becoming executable work packages.

Then run an independent **Müşavir** review of the plan before execution for non-trivial projects.

Müşavir asks:

- Is a requirement missing?
- Is there a broken user journey?
- Is migration/rollback missing?
- Did the plan forget security/authz/negative tests?
- Did it confuse “code written” with “feature delivered”?
- Are browser/mobile/accessibility/error states covered where applicable?
- Are release/installer/docs/maintenance obligations present?
- Can tasks truly run in parallel without same-file conflict?
- Did the planner request a capability not proven on this machine?

Only after this challenge should the final route be locked/materialized.

---

# 10. IMMEDIATE OPEN-PR SEQUENCE — DO NOT DUPLICATE ACTIVE WORK

Before starting new implementation, inspect all current open PRs and branch relationships.

Highest-value current stack at mandate authoring time:

1. **#156** — `goal.preview` / explicit `goal.create` Nizâm-ı Sefer Desktop planning on current main;
2. **#157** — materialize route tasks into dependency-aware, receipt-bound work packages;
3. **#158** — connect Patron Masası to the real Ferman preview/save flow.

They are stacked. Do not flatten them blindly or create competing implementations. Verify required CI, diff and current base. If still valid, land/reconstruct them in dependency order. If `main` moved, preserve behavior through a fresh minimal port and rerun all required checks.

Also reconcile, later in the sequence:

- **#121 / #123** — Knowledge Fabric + project-aware Agency Memory;
- **#119** — fail-closed Plugin SDK / Plugin Trust Center.

Do not merge a stale draft merely because its design is desirable. Bring each valuable slice to current `main`, rerun current verification, and retire/supersede obsolete branches cleanly.

Dependabot PRs are maintenance work and must not be mixed into feature proof unless the dependency is required for that slice.

---

# 11. EXECUTION FABRIC — BUILD ON THE CURRENT CORE

Reuse and extend:

- `DivanOrchestrator`;
- `TaskStore`;
- `ExecutionRouter`;
- execution receipts;
- worktree creation;
- review snapshot;
- guarded fast-forward merge;
- evidence store;
- current engine/provider contracts.

Do not replace these with a third-party workflow engine unless a measured reliability gap survives a smaller internal fix.

## Agent adapters

Codex and Claude Code are first-class installed workers. Detect capability; do not guess it.

For each host, record a capability manifest with at least:

- executable/version;
- authentication state when safely observable;
- noninteractive/programmatic mode support;
- structured output/event support;
- resume/session support;
- approval/permission controls;
- MCP/skills/plugins support where proven;
- sandbox/worktree behavior;
- last verified time/source;
- supported Divan operations.

Before relying on a CLI flag or protocol, inspect the installed binary (`--version`, `--help`, documented protocol) and/or current official vendor documentation. Existing tests/registry claims are not permission to guess a future CLI.

If a richer native integration is supported by the installed host, implement it behind the existing adapter boundary. Keep a safe bounded CLI fallback where appropriate.

## Worker reliability additions

Add, incrementally and with deterministic tests:

- attempt identity separate from task identity;
- worker lease;
- heartbeat / liveness timestamp;
- stalled classification;
- checkpoint metadata;
- idempotent retry/backoff;
- interrupted/orphaned recovery;
- resume when safely supported;
- replacement worker selection when resume is impossible;
- provider/quota/auth failure classification;
- circuit breaker to stop expensive retry loops;
- explicit cancellation.

A process PID alone is not proof of healthy work.

Suggested recovery states (adapt to existing enums rather than creating duplicates):

```text
RUNNING
→ SUSPECTED_STALLED
→ ORPHANED / INTERRUPTED
→ RECOVERY_PENDING
→ RESUMED | REPLACED | RETRY | BLOCKED
```

Test this by **actually killing** a worker/process in a controlled fixture/acceptance run. Do not certify recovery from mocked state transitions alone.

---

# 12. POLICY, SCOPE AND SANDBOX

Prompts are not a sandbox.

Preserve current owner authority and worktree boundaries, then strengthen enforcement in layers:

- allowed/denied project paths;
- symlink/path traversal rejection;
- explicit mutation authority;
- per-task tool/capability allowlist;
- protected secrets/credentials;
- network policy where the runtime can truly enforce it;
- resource/time/tool-call ceilings that can actually be measured;
- post-run diff validation against the contract;
- no merge if the diff escaped scope.

Do not make WSL2 or Docker a mandatory dependency merely because stronger isolation is desirable. Divan is Windows-first and currently has a native working distribution. If stronger Linux isolation is added, make it a replaceable **optional execution profile** and prove the UX/install story first.

Do not give workers raw long-lived secrets when a narrower brokered action can solve the task.

---

# 13. TALİMHANE + CEPHANELİK — EXTENSIONS WITHOUT CHAOS

The repository already has package/marketplace concepts. Continue from them.

## Distinguish clearly

- **Skill**: procedural knowledge, progressively loaded;
- **Plugin/package**: versioned bundle of capabilities;
- **MCP/API/CLI**: live tool/action surface;
- **Agent adapter**: worker/session interface;
- **Quality adapter**: independent evidence producer.

Do not expose all extensions to every worker.

## Trust levels

Converge on a simple human-readable status model, reusing PR #119 where appropriate:

- `CORE_CERTIFIED`
- `CURATED`
- `EXPERIMENTAL`
- `BLOCKED`

Activation must be based on evidence, not popularity.

Before a community extension becomes activatable:

1. source + exact version/commit identity;
2. license;
3. permissions/capabilities;
4. scripts/hooks inspection;
5. secret/security scan where applicable;
6. isolated smoke test;
7. contract test;
8. removal/rollback path;
9. observed compatibility with current host;
10. trust decision recorded with evidence.

Reuse the existing candidate registry and Plugin SDK draft rather than inventing a parallel marketplace.

---

# 14. TEFTİŞ — AN AGENT MAY NOT MARK ITS OWN HOMEWORK COMPLETE

The worker's “done” message is not evidence.

Project-specific quality profiles should be selected from observable stack/risk. Do not run irrelevant tools for theater.

Potential gates, when applicable:

- project-native unit tests;
- integration tests;
- typecheck/lint;
- production build;
- migration validation;
- browser E2E;
- screenshots/trace where UI evidence matters;
- accessibility checks;
- secret scan;
- dependency/vulnerability scan;
- SAST where relevant;
- auth/authz negative tests;
- installer smoke;
- upgrade/rollback smoke;
- independent Codex/Claude review;
- evidence manifest validation.

Keep status semantics explicit:

```text
PASS | FAIL | BLOCKED | NOT_INSTALLED | UNKNOWN
```

Only PASS is PASS.

## Browser quality

Use the existing browser-testing capability. Prefer deterministic Playwright tests/CLI for repeatable product flows. Use agent-driven browser exploration only when discovery/debugging benefits from it. Capture artifacts only when they prove acceptance criteria; do not create screenshot noise.

## Security/tool candidates

External scanners (for example dependency/vulnerability, secret or SAST tools) are evidence producers, not Divan authority. Evaluate and adapt them through existing candidate/plugin governance. Do not couple Divan Core to a scanner.

---

# 15. EVIDENCE MANIFEST — THE DELIVERY RECEIPT

Build on the current evidence store and receipts. For a material work package/project delivery, be able to reconstruct:

- project / Ferman / work package / attempt IDs;
- base and result commit identity;
- branch/worktree identity;
- changed files and diff digest;
- commands run + exit status;
- required gate results;
- browser/security/build artifacts where applicable;
- reviewer identity and result;
- policy decisions/denials;
- worker/provider/session identity where safe;
- duration/retries;
- token/cost fields with `exact|estimated|unknown` confidence;
- owner approvals;
- timestamp and source versions.

Human UI shows a short summary; Technical mode can expose the full receipt.

---

# 16. PADİŞAH UX — HUMAN LANGUAGE IS A PRODUCT REQUIREMENT

The normal user must not experience Divan as an admin panel for processes.

## Three information depths

1. **👑 Padişah · Patron** — outcome, progress, problems, decisions, result.
2. **🏛 Divan** — project plan, departments, work packages, risks, evidence status.
3. **🛠 Teknik** — exact agent, command, worktree, trace, receipt, diff, raw logs.

Technical detail is **available**, not forced.

## Every important status should answer five things

1. Ne oluyor?
2. Ne durumda?
3. Sorun var mı?
4. Divan ne yapıyor?
5. Benden bir şey gerekiyor mu?

Bad:

```text
worker codex-7 exit=1 retry=2
```

Good:

```text
Backend çalışanı görevi bitiremedi.
Sebep: yeni değişiklik bir testi bozdu.
Divan yapılan işi kaydetti ve güvenli ikinci denemeyi başlattı.
Sizden şu anda işlem beklenmiyor.
```

The technical event remains available under “Teknik ayrıntılar”.

## Human notification compression

Thousands of technical events should collapse into something like:

```text
0 kritik sorun
1 karar sizi bekliyor
2 bilgi
```

Treat **owner attention as a limited resource**, like token budget.

## Ask the owner only when needed

Normally ask only for:

- irreversible production/data operation;
- material budget/quota increase;
- unavailable credential/login;
- ambiguous business outcome;
- security/quality exception;
- major scope/timeline tradeoff;
- release/promotion decision.

Do not ask “Postgres mi SQLite mı?” unless the answer materially changes product ownership and repository evidence cannot settle it.

## Completion language

Separate:

- **Yapıldı** — implementation exists;
- **Kontrol ediliyor** — independent verification running;
- **Hazır** — required independent gates/evidence passed.

Only the last one may be presented as ready to the owner.

---

# 17. PATRON MASASI → REAL AGENCY COMMAND CENTER

Evolve the current Patron Masası in vertical slices. Do not turn `PatronDesk.tsx` or `App.tsx` into a larger monolith; extract typed UI modules as the surface expands.

Target primary navigation:

- **Taht** — projects, overall health, decisions, ready deliveries;
- **Ferman** — natural-language intake;
- **Divan** — Intelligence → Product → UX → Architecture → Plan;
- **Ocak** — human-readable team/workstream status;
- **Teftiş** — quality/evidence summary;
- **Arşiv** — memory/decisions/incidents;
- **Talimhane & Cephanelik** — certified extension/tool inventory;
- **Defterdar** — usage/time/token/quota visibility;
- **Teslimat** — installer/release/rollback/evidence.

Do not make all screens before the underlying core state exists. Every visible worker, progress percentage and PASS must be backed by real Core data.

### Recommended autonomy settings

Expose simple user-facing modes but map them to deterministic authority policy:

- **Kontrollü** — more checkpoints;
- **Dengeli** — default; only material-risk decisions interrupt the owner;
- **Tam Divan** — reversible local technical decisions proceed automatically, while hard owner gates remain hard.

No UI mode may bypass release/data/security owner gates.

---

# 18. INSTALLATION / FIRST RUN — WINDOWS 11 MUST FEEL LIKE A PRODUCT

Do not invent a second installer. Extend the existing Tauri/NSIS Desktop release chain.

Existing product intent is correct: the end-user installer contains the Core sidecar and does not require a separate Python installation.

Target first-run UX:

```text
Divan hazırlanıyor…
✓ Git
✓ Divan Core
✓ Codex bulundu / giriş durumu
✓ Claude Code bulundu / giriş durumu
✓ proje çalışma alanı
✓ temel teftiş kabiliyetleri

[Codex'i bağla]   [Claude Code'u bağla]

Divan hazır.
[Proje ekle] [Yeni Ferman]
```

Never collect provider credentials into Divan UI if the official provider login can own them.

Build/maintain a user-friendly **Doctor** view/command that reports capability truth, not merely executable presence. It should distinguish:

- installed;
- authenticated/usable when safely detectable;
- verified capability;
- degraded;
- unavailable;
- incompatible.

Keep advanced CLI controls available for maintainers; ordinary daily usage should not require terminal commands.

---

# 19. MULTI-MACHINE IS AN EXTENSION OF THE SAME MODEL, NOT A SECOND PRODUCT

Do not prioritize distributed workers before single-machine recovery is proven.

After local reliability is strong, define a replaceable worker registration contract including:

- worker id;
- hostname/display name;
- OS/architecture;
- CPU/RAM/GPU capability;
- installed runtimes/tools/agent capabilities;
- labels;
- concurrency capacity;
- health/heartbeat;
- trust/enrollment identity.

The owner should see “Ofis PC — 2 çalışan müsait”, not transport-protocol details.

Only add a message bus/distributed workflow dependency when a real second-node test demonstrates the need. Keep remote-worker security stronger than local UI convenience.

---

# 20. BACKTEST / PALABENCH PRINCIPLE — MEASURE THE SYSTEM, NOT THE PROMPT

Use and extend the repository's existing `evals/` and benchmark rules rather than inventing marketing scores.

Create an Agency OS evaluation set only when implementation reaches the relevant features. Cover realistic classes such as:

- small bug fix;
- bounded feature;
- refactor with preserved behavior;
- large-repo context retrieval;
- stale-memory detection;
- repeated-known-error prevention;
- worker crash;
- provider unavailable/quota failure;
- scope/path violation;
- failing test / browser regression;
- merge conflict;
- restart/recovery;
- independent reviewer catching a planted defect;
- installer/first-run failure;
- plugin drift/permission rejection.

Track actual metrics such as:

- task success rate;
- first-pass success;
- human interventions;
- recovery success;
- scope violations blocked;
- escaped defects;
- reviewer catch rate;
- median completion time;
- retries;
- context bytes/tokens;
- memory hits/research avoided;
- exact/estimated/unknown usage cost.

Use predeclared acceptance thresholds and the existing repo benchmark discipline. If results are noisy or too expensive to repeat, say so; do not invent precision.

---

# 21. IMPLEMENTATION PASSES — ORDER IS BINDING UNLESS EVIDENCE CHANGES IT

## PASS 0 — Truth and branch reconciliation

**Goal:** one trustworthy current baseline.

- Read `CLAUDE.md`, `AGENTS.md`, `BLUEPRINT.md`, `.divan/progress.md`, current product docs, release/CI contracts and relevant tests.
- Run `python scripts/handoff.py --check` if current contract still requires it.
- Record current branch, status, tool versions and installed Codex/Claude capabilities.
- Inventory open PRs, especially #156/#157/#158/#121/#123/#119.
- Identify stale documentation that contradicts current code.
- Run the canonical baseline verification before modifying implementation.
- Do not “clean up” unrelated owner changes.

**Exit:** current truth recorded; exact next slice known; baseline reproducible.

## PASS 1 — Finish real Ferman planning flow

Bring #156 → #157 → #158 behavior onto current main in correct dependency order.

**Exit acceptance:**

- ordinary-language Ferman;
- read-only preview;
- explicit plan persistence;
- dependency-aware work packages;
- no execution authority granted by planning;
- Patron Masası shows real plan data;
- current CI green.

## PASS 2 — Project/Agency lifecycle contracts

Add the project-level Agency OS lifecycle and product/UX/intelligence artifacts additively around existing goal/task contracts.

**Exit acceptance:** one project can move from Ferman through planning with machine-readable project/product/UX/architecture state and clear owner-facing status without breaking v1 receipts.

## PASS 3 — Knowledge Fabric / Memory-first Intelligence

Rebase/adapt #121/#123 onto the now-current core.

Add freshness/recall behavior and project-open/task-close learning workflow. Make recurring deterministic lessons promotable to tests/policies/skills.

**Exit acceptance:** a second task can reuse a prior validated decision/lesson without rereading/researching the entire source, with provenance and no silent auto-authority.

## PASS 4 — Worker capability + resilient attempts

Improve real Codex/Claude worker capability discovery and execution attempt lifecycle. Add lease/heartbeat/checkpoint/stall/retry/replacement/cancel in minimal slices.

**Exit acceptance:** controlled worker kill/restart scenario produces truthful recovery evidence; provider unavailable state does not masquerade as success.

## PASS 5 — Plugin SDK / Cephanelik Trust

Rebase/adapt #119 and wire trust state into the human UI without granting plugin authority prematurely.

**Exit acceptance:** a plugin can be inspected, provenance-bound, permission-reviewed and smoke/contract tested before activation; drift invalidates approval.

## PASS 6 — Context Compiler + token/memory economy

Measure baseline context behavior first. Add retrieval/context compiler around existing project/memory/code sources. Evaluate external context tools only if they win the declared benchmark and license/safety gates.

**Exit acceptance:** representative tasks receive smaller relevant context with no correctness regression and measured before/after evidence.

## PASS 7 — Teftiş Factory

Make quality profiles first-class, connect relevant project-native + browser + security gates and improve EvidenceManifest.

**Exit acceptance:** deliberately planted UI/test/security defect is caught; unknown/missing tools fail closed for required gates.

## PASS 8 — Full human Padişah UX

Refactor expanding PatronDesk/App code into maintainable typed components/views. Implement the three information depths and decision compression.

**Exit acceptance:** a vibe coder can create a project/Ferman, understand progress, survive a worker failure, review a decision and inspect evidence without seeing terminal details unless requested.

## PASS 9 — Installer / onboarding / doctor

Use existing NSIS/Tauri release system. Improve first-run provider/capability discovery, official login guidance and recovery.

**Exit acceptance:** clean Windows user installs, opens app, attaches a repo, connects installed Codex/Claude, runs a real bounded task, restarts and retains state. Existing real-user acceptance lane must prove it.

## PASS 10 — Multi-machine (only after local reliability)

Add one remote worker profile behind a stable worker contract; avoid broad cluster complexity.

**Exit acceptance:** second trusted machine can execute an isolated work package and return evidence; disconnect/reconnect is handled truthfully.

## PASS 11 — Agency OS evaluation + release candidate

Run realistic fault-injection/eval suite, fix regressions, update docs and produce the release-ready evidence package.

**Exit:** all required gates pass, known limitations documented, owner receives a release decision. **Do not publish without explicit owner release authority.**

---

# 22. FIRST END-TO-END VERTICAL SLICE — DO THIS BEFORE BIG UI EXPANSION

Prove the whole loop with one small but real task, for example:

> “Bu projeye küçük bir kullanıcı-visible özellik/health davranışı ekle ve kanıtla.”

The exact task must be suitable for the chosen fixture/project.

Required chain:

```text
Padişah Ferman
→ memory/intelligence lookup
→ product/acceptance summary
→ plan proposal
→ deterministic plan validation
→ work package
→ isolated worktree
→ real Codex or Claude builder
→ project-native tests
→ independent other-agent review
→ evidence
→ owner-friendly result
→ guarded merge eligibility
→ memory/lesson capture
```

Do not build dozens of screens before this chain works on a real repository.

---

# 23. DEFINITION OF DONE FOR THE PRODUCT

Divan is not “Agency OS ready” because the UI looks complete. A release candidate must prove, at minimum:

1. clean Windows install with current installer;
2. startup/doctor identifies real tool state truthfully;
3. project registration;
4. ordinary-language Ferman;
5. memory-first intelligence;
6. product/UX/architecture/planning artifacts where required;
7. dependency-aware work packages;
8. real Codex and/or Claude bounded execution;
9. isolated concurrent writers where parallelism is used;
10. worker failure recovery;
11. scope violation rejection;
12. required tests/browser/security gates for the chosen profile;
13. independent review;
14. human-readable evidence summary;
15. no merge before required approval/gates;
16. controlled merge path;
17. restart persistence;
18. lesson/memory capture;
19. uninstall/update/recovery contracts remain healthy;
20. public docs match the real product;
21. signed/stable release chain only when its existing production prerequisites are truly satisfied.

If any required item is blocked by missing credentials/infrastructure, report it as BLOCKED with exact evidence and continue all independent achievable work.

---

# 24. STATUS REPORTING TO THE HUMAN

Do not dump a developer diary on the owner.

At meaningful checkpoints report in this format:

```text
Ne yaptım
- ...

Şu an durum
- Proje: %X (only if based on defined milestones, never invented)
- Çalışan: ...
- Teftiş: ...
- Kritik sorun: ...

Otomatik çözdüğüm
- ...

Sizden karar gerekiyor mu?
- Hayır
```

If owner input is required:

```text
Karar gerekiyor
Sorun: ...
Divan önerisi: ...
Alternatif: ...
Risk: ...
Ek süre/maliyet: ...
```

Do not ask a question without also giving the recommended decision.

---

# 25. CODING / QUALITY DISCIPLINE

- Prefer vertical slices over broad scaffolding.
- Preserve current behavior before refactoring.
- For large files (notably Desktop UI), baseline behavior/tests before extraction.
- One canonical source of state; UI projections must not become authority.
- Every new provider/tool behind an adapter/contract.
- Every critical adapter gets contract tests.
- Every recovery feature gets real kill/interruption tests.
- Every security boundary gets negative tests.
- Every persisted schema change gets compatibility/migration evidence.
- Every user-visible feature gets human-language states for success/loading/error/recovery.
- Every external candidate follows license/source/adoption rules.
- Keep dependencies minimal; “available OSS” is not a reason to add it.
- Keep secrets out of logs/evidence/public docs.
- Never fabricate token/cost/model capability.
- Never hide skipped quality gates.

---

# 26. START NOW — DO NOT STOP AFTER WRITING A PLAN

When this mandate is given to Claude Code Desktop:

1. Read the repository contracts and current git truth.
2. Verify that this mandate is still compatible with newer `main`; preserve newer valid work.
3. Run the baseline verification.
4. Inspect the current stacked planning PRs (#156/#157/#158) and all overlapping open work.
5. Produce a short current-state delta: **already done / partially done / missing / stale**.
6. Start PASS 1 immediately using the smallest safe branch/worktree strategy.
7. After each pass, run targeted tests then canonical verification, independent review and CI as applicable.
8. Update durable project state and evidence before moving to the next pass.
9. Continue automatically through locally achievable passes. Do not return merely because one implementation task finished.
10. Stop only for a real owner gate, missing external credential/infrastructure that cannot be bypassed safely, or a failure whose next safe action cannot be inferred from evidence.

The guiding standard is not “how much code did you write?”

It is:

> **Can a human say what they want, can Divan understand and remember it, can Divan safely organize real agents to produce it, can independent checks prove it, and can the human understand the result without becoming the system administrator?**

Until that answer is demonstrated with real evidence, the transformation is not complete.
