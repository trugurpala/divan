# Musavir Capability Audit Design

**Date:** 2026-08-01
**Status:** Approved by bounded implementation pre-authorization

## Objective

Extend `musavir` so an agent can inspect the capabilities actually available in
the current session and project, measure task-specific coverage, research
unstable technology claims from primary sources, make explicit adoption
decisions, and apply only bounded, reversible local changes when authorized.

The result is a project-readiness audit. It is not a score for model
intelligence, general software quality, or future success.

## Non-goals

- Do not install every recommended package or connector.
- Do not create a new MCP server, daemon, hosted service, or package runtime.
- Do not infer capabilities from marketing copy or stale startup context.
- Do not modify accounts, billing, secrets, access control, security posture,
  external messages, releases, or remote repositories without separate
  authorization.
- Do not claim a behavioral improvement percentage without provider eval
  evidence.

## Considered approaches

### 1. Prompt-only audit

Add instructions to `SKILL.md` and let the model calculate percentages. This is
small, but arithmetic and category handling can drift between runs. Rejected as
the only mechanism.

### 2. Deterministic scorer plus skill workflow

Keep the reasoning workflow in `musavir`, but calculate coverage with a
stdlib-only Python script. Add a current toolkit decision reference and contract
evals. This is the selected approach because it is inspectable, portable, and
fits Divan's existing skill architecture.

### 3. New updater MCP or autonomous installer

Create a service that discovers and installs tools automatically. This adds a
large trust boundary, credential and supply-chain risk, and operating cost.
Rejected for this change.

## Capability model

Every audit begins with an explicit list of requirements for one concrete task.
Each requirement has a unique `id`, one status, and optional evidence strings:

- `verified`: capability exists and was observed working; weight `1.0`.
- `partial`: capability exists but does not fully meet the requirement; weight
  `0.5`.
- `missing`: capability is absent; weight `0.0`.
- `unknown`: available evidence is insufficient; weight `0.0` and confidence is
  reduced.

The scorer reports:

```text
coverage_percent = 100 * (verified + 0.5 * partial) / requirement_count
gap_percent = 100 - coverage_percent
confidence_percent = 100 * (requirement_count - unknown) / requirement_count
```

Percentages use one decimal place. An empty requirement list, duplicate ID,
unknown field status, malformed input, or non-string evidence is an error. The
same input must always produce the same ordered JSON output.

## Audit workflow

1. Read repository rules, architecture, dependencies, and current task scope.
2. Inventory tools, skills, connectors, local commands, and project facilities
   that can be directly verified in the current host.
3. Define the minimum requirement set before assigning statuses.
4. Record evidence and run the deterministic scorer.
5. Verify unstable claims such as versions, deprecations, pricing, security,
   compatibility, and maintenance state using official primary sources.
6. Classify each candidate as `KEEP`, `ADD`, `LATER`, `REPLACE`, or `REJECT`.
7. When explicitly authorized to decide and apply, change only bounded,
   reversible local files. Stop at an approval boundary for paid services,
   secrets, accounts, broad permissions, external communication, releases, or
   destructive actions.
8. Report implemented, tested, committed, pushed, published, and live states
   separately.

## Technology adoption rules

Recommendations must identify their delivery model: runtime dependency,
development dependency, source-owned component, external CI service, separate
package, or reference only. Existing architecture wins unless a replacement has
a concrete requirement, migration path, and documented benefit.

Conflicting parallel foundations are rejected by default. Examples include two
design systems, Express beside Nest/Fastify, MongoDB beside an established
PostgreSQL/RLS financial core, browser-managed JWT beside an OIDC/BFF session,
and Axios beside a generated Fetch client without a distinct need.

## Files and boundaries

- `plugins/sadrazam/skills/musavir/scripts/score_capabilities.py` owns only
  deterministic validation and scoring.
- `plugins/sadrazam/skills/musavir/references/capability-audit.md` owns the audit
  workflow and autonomy boundaries.
- `plugins/sadrazam/skills/musavir/references/toolkit-2026.md` owns the current
  application-tool decision matrix and primary references.
- `plugins/sadrazam/skills/musavir/evals/evals.json` owns behavioral contract
  examples; it does not prove a win rate by itself.
- `plugins/sadrazam/skills/musavir/SKILL.md` routes relevant user requests to
  those focused resources.

## Verification

Unit tests cover valid scoring and every input rejection rule. Eval contract
validation checks the three representative prompts. Repository validation,
catalog regeneration, canonical verification, and `git diff --check` must pass
before completion is claimed.

