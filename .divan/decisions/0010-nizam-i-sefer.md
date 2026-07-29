# ADR 0010: Nizam-i Sefer is planning intelligence inside Divan

Date: 2026-07-29

## Decision

Divan keeps one product, one repository, and the canonical nine-module runtime.
Nizam-i Sefer is a stdlib-only `planning.py` component with a focused
`planning_policy.py`, both owned by the existing `council` module. It enriches
the schema-2 intent route; it is not a tenth module, model runtime, daemon,
external swarm, or separate repository.

The planner derives a deterministic structural complexity score, a conservative
context budget, bounded workstreams, stage tasks, sefer boundaries, handoff
rules, evidence duties, and a portable model capability class. It never runs
target project commands, calls a model API, installs a dependency, or treats an
available tool as authority.

## Model and capacity boundary

Exact context supplied with `--context-window` is an owner declaration, not a
vendor-verified product limit. Without it, the numeric budget is labeled a
planning assumption and `verified_product_limit` remains false.

Model routing is risk-based: economy, balanced, or frontier. On Codex,
GPT-5.6 Luna, Terra, and Sol may appear only as host-confirmed candidates based
on current official OpenAI model guidance. Divan does not claim account
availability and does not silently downgrade a frontier requirement.
Security, production, release, credential, package-manager-conflict, financial,
and destructive/production-data signals impose explicit risk floors.

## Parallelism boundary

The planner never recommends more than three parallel workstreams. Workstreams
are explicit dependency-graph lanes, while sefers remain sequential context and
handoff windows; the lanes join at integrated verification. Conflicting host
hints become `ambiguous`. Host hint values are never persisted. External agent
harnesses remain unnecessary; parallel writes still require explicit isolation
and ownership under Ordu Nizami.

## Consequences

- Existing route fields and schema version remain stable.
- Every workflow that declares `independent-reviewer` contains an explicit
  independent-review gate.
- New goals persist `route.json` beside spec, plan, and tasks and bind its hash
  into the receipt.
- Legacy programmatic goal calls keep their stable identity behavior.
- Public plan and goal commands accept host profile and context-window inputs.
- Planning changes force focused tests and documentation/Wiki/site/release
  impact through the canonical graph.
