# Divan Company OS

Divan turns a natural-language request into a small, evidence-led software
company around the coding agent. It does not simulate dozens of personas or
add a second agent runtime. It selects only the roles, packs, framework rules,
and verification gates justified by the project and requested outcome.

## How it works

1. **Inspect** reads bounded project manifests without executing project code.
2. **Plan** classifies the work, detects frameworks, selects a workflow, and
   names the smallest qualified team.
3. **Nizâm-ı Sefer** estimates the working set, resolves declared or
   conservative host capacity, chooses a safe orchestration lane, and splits
   the work into evidence-gated sessions without pretending to know an
   unreported model limit.
4. **Deliver** uses Core Pack for engineering discipline, UI Pack for product
   interfaces, React Pack only for detected React/Next.js work, and Zanaat Pack
   only for creative or integration work.
5. **Impact** expands intended and actual changed paths through the dependency
   graph so catalog, documentation, Wiki, site, evaluation, and release checks
   cannot be missed.
6. **Verify** requires fresh tests, durable receipts, and independent review
   before completion.

Ordinary users write their intent naturally. Maintainers and integrations can
use the same portable contracts directly:

```powershell
python scripts/divan.py inspect --project .
python scripts/divan.py plan --project . --intent "Improve the onboarding UI"
python scripts/divan.py plan --project . --intent "Ship the release" --target released --host-profile codex --context-window 128000 --json
python scripts/divan.py impact README.md plugins/sadrazam/skills/sadrazam/SKILL.md
python scripts/divan.py company-validate
```

`--context-window` is an exact value declared by the host or operator. When it
is absent, `host-profiles.json` supplies a conservative planning fallback. The
fallback is not a product, subscription, or model-capability claim; the plan
returns its source and warning explicitly.

## Nizâm-ı Sefer contract

The enriched route is schema 3 and adds:

- a deterministic complexity score and estimated working-set size;
- usable context budget, reserve, and handoff threshold;
- recommended session count and bounded parallel-workstream limit;
- `tek-sefer`, `ardisik-sefer`, or `sinirli-ordu` orchestration;
- stage tasks with dependencies, responsible functional roles, and required
  evidence;
- the Padişah → Sadrazam → vezir → paşa command structure;
- durable memory and public-surface obligations.

Starting a goal keeps the long-standing human contract under
`.divan/specs/<goal-id>/{spec.md,plan.md,tasks.md}` and writes the machine route
to `.divan/routes/<goal-id>.json`. The route SHA-256 is recorded in `spec.md`.
This preserves existing Project OS receipts while giving every new session an
exact restart contract.

```powershell
python scripts/divan.py goal start --project . --intent "Harden and publish the API" --target released --host-profile auto --json
python scripts/divan.py goal start --project . --intent "Harden and publish the API" --target released --host-profile auto --execute --json
```

Every sefer must finish with a checkpoint, decision/progress updates, evidence,
and one exact next action. Parallel work is allowed only up to the route's
`safe_parallel_workstreams`; unknown context capacity lowers autonomy rather
than increasing it.

## Surface obligations

Planning intelligence does not rewrite arbitrary prose blindly. It makes the
obligation machine-readable and fail-closed:

1. calculate impact before editing;
2. recalculate impact from actual changed paths;
3. reject unclassified paths at completion;
4. update the canonical source and derived README/Wiki/site/release surfaces in
   the same change;
5. require remote readback for released or observed targets.

The impact graph classifies changes to the planning engine, profiles, goal
runtime, CLI, and focused tests as Company OS, documentation, and release
work. A PR that changes the brain but leaves its public explanation stale must
therefore fail the required checks.

Project OS makes this selection durable in the installed project:

```powershell
python scripts/divan.py init --project . --profile standard --locale auto
python scripts/divan.py audit --project . --format json
```

Repository-level `DCS-*` rules remain Divan's maintenance contract. Applicable
installed-project `DPS-*` rules and evidence are explained in
[Project OS](../docs/Project-OS.md).

The installed plugin carries the stdlib-only implementation under
`plugins/sadrazam/company/`; it does not send project data anywhere.

| Pack | Selected for | Excluded from |
|---|---|---|
| Core Pack | planning, tests, debugging, review, verification | never skipped for product changes |
| UI Pack | interface, UX, accessibility, browser validation | backend-only work |
| React Pack | detected React, Next.js, or React Native projects | unrelated frameworks |
| Zanaat Pack | MCP/API integrations and original creative assets | ordinary feature development |

The core contracts are `roles.json`, `workflows.json`, `frameworks.json`,
`impact-graph.json`, and `host-profiles.json`; `planning.py` derives the
Nizâm-ı Sefer route. English is canonical for technical identifiers; Turkish
remains a supported user locale. See [Türkçe](Company-OS.tr.md).
