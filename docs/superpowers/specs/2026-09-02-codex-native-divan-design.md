# Codex-native Divan V2 Design

## Goal

Rebuild Divan as a small Codex-first engineering plugin while preserving the existing repository history and the strongest legacy product principles: bounded scope, evidence before completion, user-change preservation, and simple natural-language UX.

## Product boundary

Divan is not a model, IDE, agent runtime, hosted service, or replacement linter. It is a plugin-delivered engineering workflow for Codex.

V2 alpha is intentionally skills-only:

- one plugin package at `plugins/divan`;
- seven high-signal skills;
- detailed engineering knowledge in progressive-disclosure references;
- no MCP server;
- no UI;
- no lifecycle hooks in the published alpha;
- no custom agent runtime or installer.

## User experience

The user should be able to say:

`Divan, bu projeyi incele ve bu özelliği doğru şekilde bitir.`

Internal routing stays hidden unless it matters to a user decision. The final response reports what changed, what was verified, what could not be verified, and the remaining material risk.

## Core skills

1. `divan`: natural-language coordinator and router.
2. `repo-audit`: establish repository facts and baseline.
3. `implementation-plan`: bound non-trivial change work.
4. `root-cause-debug`: reproduce and isolate failures before editing.
5. `quality-review`: review material engineering quality.
6. `completion-proof`: connect done claims to observed evidence.
7. `project-contract`: create concise durable project instructions.

## Engineering-taste knowledge

`quality-review/references/` stores specialized lenses for naming, types/contracts, architecture, database integrity, reliability, security, testing, and frontend/product quality. The review skill loads only the relevant references.

## Mechanical policy

The repository validator fails on:

- malformed plugin metadata;
- non-kebab plugin or skill names;
- skill folder/name mismatch;
- duplicate skill names;
- missing skill bodies;
- final-directory metadata limits used by Divan;
- MCP/app fields in the skills-only package;
- invalid repo marketplace wiring;
- Divan discovery metadata over a conservative 6,000-character soft budget.

The 6,000-character value is a Divan safety margin, not an OpenAI platform hard limit.

## Migration

The rewrite branch is created from the existing `main` commit, so legacy commits remain ancestors. The alpha package is added alongside the legacy implementation first. Legacy runtime removal happens only after the new package passes local validation, repository tests, and real Codex acceptance.

No orphan branch, history rewrite, force-push, or release deletion is part of this migration.

## Acceptance

The first alpha is acceptable when:

- all seven skills validate;
- routing eval contract has at least five positive and three negative cases;
- validator unit tests pass;
- plugin package validates from a clean checkout;
- GitHub Actions run the same checks;
- a later real Codex install test confirms the plugin can be discovered and invoked.

Mechanical tests are not evidence of model-quality improvement.
