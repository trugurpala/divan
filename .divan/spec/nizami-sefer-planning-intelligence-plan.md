# Nizâm-ı Sefer Planning Intelligence Plan

## Ferman

Make Sadrazam plan substantial software work with explicit awareness of project
shape, estimated working-set size, host/context capacity, safe session count,
bounded parallelism, durable handoff, and public-surface obligations while
preserving the Padişah → Sadrazam → vezir → paşa operating order.

## Problem statement

Company OS already detects frameworks, ranks workflows, selects roles and
skills, calculates transitive impact, and requires evidence. It does not yet
make the following decisions machine-readable:

- whether the work safely fits one session;
- how many sessions should be planned;
- when the host must checkpoint before context compaction;
- how much parallel work is safe;
- which functional role owns each executable stage;
- which evidence closes each task and campaign;
- which canonical and derived surfaces must move with the implementation.

## Boundaries

- Python standard library only.
- No daemon, model API, desktop application, hidden network service, or external
  agent runtime.
- No hard claim about Claude, Codex, ChatGPT, subscription, or model limits.
- Existing `spec.md`, `plan.md`, `tasks.md`, receipt and DPS boundaries remain
  backward compatible.
- Technical identifiers stay English-canonical; Ottoman terms remain product
  and display language.
- State-changing goal creation remains dry-run-first.

## Design

1. Add `host-profiles.json` with conservative, explicitly labelled planning
   fallbacks and an exact `--context-window` override.
2. Add `planning.py` to calculate complexity, usable session capacity,
   recommended session count, orchestration lane, campaigns, tasks, command
   hierarchy, memory contract, and publication obligations.
3. Keep `goal_id` host-neutral so Claude and Codex identify the same project
   goal even when their context plans differ.
4. Persist machine planning to `.divan/routes/<goal-id>.json`; bind its SHA-256
   from `spec.md` without adding it to the legacy DPS-005 receipt artifact set.
5. Extend the portable CLI and package the new contracts in
   `divan-project.pyz`.
6. Extend impact classification so planning changes force Company OS,
   documentation, release, and focused test gates.
7. Update Sadrazam law plus English/Turkish Company OS documentation in the
   same change.
8. Track every new contract in `release-manifest.json`.

## Acceptance criteria

- `plan` returns schema 3 with deterministic complexity and context metadata.
- Fallback capacity always carries a warning and never claims verified limits.
- Small work may select `single-expedition`; large compound work can select
  `sequential-expeditions` or `bounded-army` within a maximum parallel limit.
- Every task has one owner, dependencies, required evidence and an explicit
  completion rule.
- Same project/intent/target produces the same `goal_id` across Claude and Codex
  host profiles.
- Goal creation writes the three legacy human artifacts plus one SHA-bound
  machine route and a valid existing receipt.
- New planning files are included in the deterministic Project OS runner.
- Changed planning paths are fully classified by the impact graph.
- Focused tests, complete repository verification and required GitHub checks
  pass before the PR becomes ready.

## Verification plan

```powershell
python -m unittest tests.test_planning_intelligence -v
python -m unittest tests.test_company_engine tests.test_project_os tests.test_yayin -v
python scripts/divan.py company-validate
python scripts/divan.py impact plugins/sadrazam/company/planning.py plugins/sadrazam/company/goals.py docs/Company-OS.md --json
python scripts/release.py --check
python scripts/verify.py
```

## Publication boundary

This branch is an implementation candidate only. It does not change VERSION,
create a tag, publish a Release, merge itself, or claim live availability.
