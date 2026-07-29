# Divan Engine and Governance Model

[Türkçe](Divan-Engine.tr.md)

Divan is one product in one repository: a local-first, supervised software
delivery framework that turns an owner's mandate into bounded specialist work
and a verified release. Divan Engine is its stdlib-only execution core. The
Divan Governance Model defines how authority moves through that core; it is
not a second product or repository.

## Authority starts with the owner

| Rank | Machine id | English | Turkish |
|---:|---|---|---|
| 0 | `owner` | Owner | Hükümdar |
| 1 | `mandate` | Mandate | Ferman |
| 2 | `orchestrator` | Orchestrator | Sadrazam |
| 3 | `council` | Council | Divan |
| 4 | `specialist` | Specialist | Uzman |
| 5 | `provider` | Provider | Sağlayıcı |

Only `owner` may expand scope. Every lower layer receives narrower authority
from the layer above it. A provider can perform only the operation already
authorized by the mandate; tool availability never grants authority by itself.
Mutations require explicit authority and completion requires evidence.

This is enforceable local workflow governance, not user authentication. The
host operating-system account and repository permissions remain the identity
and access boundary. The public CLI binds each mutation's exact arguments to a
deterministic mandate id, treats `--execute` as explicit local owner authority,
and rejects a delegated `--actor` attempting mutation. Direct internal Python
APIs remain trusted implementation surfaces, not a separate security sandbox.

## Nine runtime modules

The canonical package is `plugins/sadrazam/divan_runtime/`.

| Module | Responsibility |
|---|---|
| `kernel` | validate the module graph and stable architecture |
| `governance` | validate delegation and authorize public CLI mutation |
| `council` | inspect projects, route intent, calculate impact |
| `evidence` | produce and verify redacted evidence receipts |
| `project` | initialize, own, audit, update, and verify project contracts |
| `records` | goals, archive, adoption |
| `providers` | bounded local, GitHub, Context7, and Vercel capabilities |
| `release` | source-bound release evidence and live readback |
| `api` | stable CLI, redacted JSON output, and pre-v0.17 aliases |

`modules.json` owns the dependency graph; `governance.json` owns the bilingual
authority contract. `python scripts/divan.py architecture --json` validates
and displays both. Dependencies must be acyclic. The core has no external
runtime or external-repository dependency.

## Nizam-i Sefer

`council` owns `planning.py` plus a small `planning_policy.py` policy component.
Both remain inside the existing council boundary. The schema-2 route is
enriched with `execution_plan`; no tenth runtime module is created.

The plan contains:

- explicit, environment-hint, ambiguous, or unknown host resolution without
  persisting environment values;
- a context budget whose fallback is always labeled a planning assumption;
- structural complexity and an economy/balanced/frontier model class, with
  mandatory high-risk floors for security, production, release, credentials,
  package-manager conflicts, and destructive or production-data signals;
- deterministic workflow-stage tasks, dependencies, evidence, sefer
  boundaries, explicit independent-review gates, and at most three parallel
  workstreams that join at integrated verification;
- shell-free argv for project-native commands and `auto_execute: false`;
- canonical-source, documentation, public-surface, provider, and handoff
  obligations.

On Codex, current official OpenAI guidance maps economy to `gpt-5.6-luna`,
balanced to `gpt-5.6-terra`, and frontier to `gpt-5.6-sol`. These are candidates,
not availability claims. The host must confirm the model. Exact
`--context-window` input is owner-declared and is still not described as a
verified vendor limit.

## Use it

Ordinary users state the desired result. The CLI is an expert and integration
surface:

```powershell
python scripts/divan.py architecture --json
python scripts/divan.py inspect --project .
python scripts/divan.py plan --project . --intent "Improve the onboarding UI"
python scripts/divan.py plan --project . --intent "Secure and release the API" --host-profile codex --context-window 1050000 --target released --json
python scripts/divan.py impact README.md plugins/sadrazam/skills/sadrazam/SKILL.md
python scripts/divan.py validate
python scripts/divan.py init --project . --profile standard
python scripts/divan.py init --project . --profile standard --actor owner --execute
python scripts/divan.py audit --project .
```

The engine selects the smallest justified team and pack set. Core Pack carries
engineering discipline; UI and React packs require matching project evidence;
Zanaat Pack requires a relevant creative or integration workflow.

The former `Company OS` name and `plugins/sadrazam/company/` path are
compatibility surfaces through v1 and will not be removed before v2. The old
`company-validate` alias returns the same contract as canonical `validate`.
Existing `.divan/` data, DCS/DPS identifiers, receipts, hashes, and generic CLI
commands do not change.

See [Divan Project Contract](Project-Contract.md) for the supervised contract
installed into a target repository.
