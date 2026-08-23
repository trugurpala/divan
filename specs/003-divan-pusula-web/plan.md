# Implementation Plan: Divan Pusula Web

**Feature**: `003-divan-pusula-web`  
**Constitution**: `2.0.0`  
**Locked index**: `.pusula/plan-lock.json`  
**Baseline**: `68e91fdf48dbcc385be567f4b525a682eeb9af05`

## Architecture Decision

Pusula is not a fork of a large developer platform. It is a thin first-party product and decision
layer composed over replaceable, independently maintained infrastructure.

```text
Human
  |
  v
React Pusula UI ---- Logto/OIDC
  |
  v
Django Control API -------- PostgreSQL (Mizan canonical state)
  |                             |
  |                             +-- Goal / Revision / Scope
  |                             +-- Fact / Evidence / Decision
  |                             +-- Cost / Audit / Deployment
  |
  +-- OPA (deterministic policy)
  +-- Hatchet OSS (durable orchestration)
  +-- ToolHive (MCP/tool runtime) ---- OpenBao (secrets)
  +-- Forgejo (canonical Git/PR/release/package)
          |
          +-- optional GitHub/GitLab mirrors
          |
          v
       Dagger (canonical CI logic)
          |
          v
   RunnerProvider (local container or disposable VM/microVM)
          |
          +-- OpenHands Agent Server / ACP
          |      +-- Codex lead
          |      +-- Claude independent reviewer
          |      +-- optional Gemini/local agent
          |
          +-- codebase-memory adapter
          +-- Trivy / SBOM / provenance
          |
          v
   DeploymentAdapter ---- Coolify default / Vercel optional / others
```

## Why These Boundaries

### Canonical Git: Forgejo

Forgejo gives Pusula owned repository, pull-request, issue, release, package and Actions-compatible
surfaces. GitHub remains a distribution/mirror/integration choice, never the only source of truth.

### Canonical pipeline: Dagger

Pipeline logic is code that runs locally and on CI providers. Forgejo Actions and GitHub Actions are
thin triggers. This prevents provider YAML from becoming the product's business logic and supports
local/offline verification.

### Canonical brain: PostgreSQL + Mizan

Queue state, agent memory and provider dashboards are not authoritative. Mizan stores append-only
events, projections, evidence, decisions, cost, audit and deployment history in PostgreSQL.

### Policy: OPA

Merge, deployment, budget, tool and evidence rules use deterministic policy-as-code. An agent can
prepare inputs and explanations but cannot create the final ALLOW result itself.

### Durable work: Hatchet OSS

Long-running work needs retry, wait, resume, cancellation, event triggers and crash recovery. The
first plan does not reimplement these primitives in Celery or a custom queue. Cloud Hatchet is an
optional operational purchase, not an architectural dependency.

### Tool surface: ToolHive + OpenBao

MCP/tool servers are registered, isolated and permissioned rather than linked directly into the
Mizan process. Secret values are resolved at execution time from secret references.

### Agent runtime: OpenHands + ACP

Pusula does not own subprocess/session transport for every coding agent. OpenHands Agent Server and
ACP provide the runtime boundary; Pusula owns provider selection, scope, budget, evidence and final
authority.

## Upstream Adoption Rules

| Capability | Default | Adoption form | Do not do |
|---|---|---|---|
| Agent process/stream | OpenHands OSS + ACP | pinned runtime/service | fork OpenHands product |
| Agent engineering method | ECC 2.0 | selected skills/rules, pinned ref | inject all 286 skills into every prompt |
| Spec workflow | GitHub Spec Kit 1.0 | project files + pinned CLI workflow | use spec files as runtime memory |
| UI reasoning | UI UX Pro Max | selected design reasoning + audit | buy Premium before a measured need |
| Git forge | Forgejo | self-host service/API | rewrite GitHub clone |
| CI logic | Dagger | first-party Dagger module | duplicate logic in provider YAML |
| Auth | Logto | self-host OIDC adapter | custom cryptography/session stack |
| Policy | OPA | Rego packages + tests | LLM final ALLOW/DENY |
| Workflow | Hatchet OSS | self-host service/SDK | custom retry/resume engine |
| MCP runtime | ToolHive | registry/gateway/runtime | run arbitrary MCP server in API process |
| Secrets | OpenBao | secret refs/dynamic credentials | raw secrets in prompts or DB |
| Research | Firecrawl | connector with provenance | private data by default |
| Model discovery | Hugging Face | metadata/benchmark connector | mandatory hosted embedding API |
| Deployment | Coolify | default adapter | hard-code one hosting vendor |
| Hosted sandbox | Vercel Sandbox | optional RunnerProvider candidate | make hosted Vercel mandatory |

## ECC Selective Profile for Pusula

Observed ECC 2.0 surface is large (68 agents, 286 skills, 94 command shims in the audited README), so
Pusula begins with a small profile instead of a full-context install:

- planning / architecture
- TDD and verification
- benchmark methodology
- security review / AgentShield concepts
- documentation lookup / research-first development
- context/session continuity
- code review / build repair

Additional ECC skills are discovered by catalog and loaded only when the Goal requires them.

## Spec Kit Use

Pusula follows the current Spec Kit sequence:

`constitution -> specify -> plan -> tasks -> implement -> converge`

`converge` is a real gate: implementation repeats until spec, plan, tasks and observed code agree or
the work is explicitly BLOCKED.

## UI/UX 20-Repository Audit Pool

GitHub discovery uses adoption only as a signal. The current candidate pool is intentionally mixed
between styled systems, headless primitives and dashboard-specific kits:

1. `nextlevelbuilder/ui-ux-pro-max-skill` — design reasoning layer; observed 120,032 stars.
2. `mui/material-ui`
3. `ant-design/ant-design`
4. `saadeghi/daisyui`
5. `chakra-ui/chakra-ui`
6. `mantinedev/mantine`
7. `radix-ui/primitives`
8. `tailwindlabs/headlessui`
9. `heroui-inc/heroui`
10. `adobe/react-spectrum`
11. `microsoft/fluentui`
12. `mui/base-ui`
13. `carbon-design-system/carbon`
14. `primer/react`
15. `themesberg/flowbite`
16. `react-bootstrap/react-bootstrap`
17. `tremorlabs/tremor-npm`
18. `uber/baseweb`
19. `rsuite/rsuite`
20. `DavidHDev/react-bits`

Before product UI adoption, Mizan Radar refreshes exact stars, latest release/commit, license,
maintenance activity, React 19 compatibility, accessibility evidence, bundle impact, SSR/RSC behavior,
agent-friendly docs/MCP/skills and styling ownership. Archived projects fail the maintenance gate even
if they have high stars.

### UI selection test

The first dashboard prototype implements the same representative screen with the top three qualified
approaches. The candidates receive the same content and test matrix:

- keyboard and screen-reader semantics
- WCAG contrast/focus/reflow
- 320/375/768/1024/1440 responsive behavior
- bundle delta and build time
- React 19 warnings/errors
- implementation LOC and modification friction
- agent implementation accuracy from a fixed prompt/spec

The winner is the lowest-maintenance option that clears all quality gates; stars do not add points
after discovery.

## Vercel Posture

Current Vercel documentation exposes isolated Sandbox execution, AI Gateway/coding-agent routing and
Agent Runs observability. These are useful optional adapters/benchmarks. Pusula does not make Vercel
the canonical runner because local/self-host operation and provider portability are product
requirements. A Vercel RunnerProvider can be accepted later if cost, isolation, latency and evidence
contracts beat the self-host baseline.

## Search / Embeddings

PostgreSQL FTS/trigram is the required baseline. The first semantic candidates are local pinned
multilingual models such as `intfloat/multilingual-e5-small`; larger multilingual options such as
BGE-M3 are benchmark candidates. No semantic model is enabled unless it improves the agreed retrieval
metric enough to justify latency, memory and maintenance cost.

## Cost Envelope

The plan separates software license cost, infrastructure cost and AI development cost.

- Default OSS software license cost: `$0` for the selected self-host core.
- Initial production infrastructure planning envelope: `EUR 40-100/month`, not a vendor quote.
- One-time AI-assisted build API-equivalent planning reserve: `$1,250-$2,500` hard ceiling.
- A Goal has its own soft/hard model budget and cannot exceed hard budget by automatic retry.
- Every paid tier is evaluated against twelve-month total cost including migration and maintenance.

The hard AI ceiling is intentionally higher than the expected spend. Hitting the ceiling without a
working product is treated as a workflow/architecture failure, not permission to buy more tokens.

## First-Party Code Budget

Target planning range for new Pusula-maintained code and tests: approximately `35k-60k LOC`. This is
not a completion metric. Third-party upstream source is not vendored merely to reduce first-party LOC.
Actual LOC, test count and complexity are measured after every 25% checkpoint.

## Four Execution Quarters

### 0-25% — Foundation

Tasks 1-12. Governance, identity/product spine, Forgejo, Dagger and runner contract. Exit requires a
human login path plus provider-independent canonical source/pipeline proof.

### 25-50% — Brain and tools

Tasks 13-24. Mizan, OPA, Hatchet, connectors, secrets, agent runtime, cost routing and code
intelligence. Exit requires a Goal to reach an isolated reviewed run without granting agents canonical
authority.

### 50-75% — Evidence and delivery

Tasks 25-32. Supply-chain evidence, security, PR authority, observability, deployment, rollback and
restore. Exit requires a deliberately bad candidate to be blocked or rolled back automatically.

### 75-100% — Human product and release

Tasks 33-40. Dashboard/workbench, Radar, collaboration, localization/accessibility, adversarial tests,
36-run agent evaluation and real production pilot. Exit is the Definition of Done in `spec.md`.

## Checkpoint Rule

Before crossing 25/50/75/100, create and validate a continuity capsule with
`scripts/pusula_checkpoint.py`. The capsule is the compact session restart authority; it never replaces
canonical evidence or historical records.
