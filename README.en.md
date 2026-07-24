# Divan

![audit](https://github.com/trugurpala/divan/actions/workflows/quality-gate.yml/badge.svg)
![version](https://img.shields.io/badge/version-0.15.0-1f6feb)
![license](https://img.shields.io/badge/license-MIT-2ea44f)

[Türkçe](README.tr.md) · **English** · [Wiki](https://github.com/trugurpala/divan/wiki) · [Changelog](CHANGELOG.md) · [Roadmap](BLUEPRINT.md)

<img src="docs/assets/muhurdar-idle.png" alt="Mühürdar, Divan's verification mascot" width="128" align="right">

**You are the sovereign. Divan is the council around your coding agent: 41
skills, five focused packs, persistent project memory, and independent
verification.**

You issue the decree. Divan clarifies it, plans the work, builds with tests,
verifies the result, records the decisions, and presents a finished delivery.
It runs as a native plugin in Claude Code/Desktop Code and Codex; its Agent
Skills remain portable to Cursor and other compatible hosts.

**Current release:** v0.15.0 · **Releases:** https://github.com/trugurpala/divan/releases · **Website:** https://trugurpala.github.io/divan/ · **Live Wiki:** https://github.com/trugurpala/divan/wiki · **Catalog:** [docs/Vezir-Katalogu.md](docs/Vezir-Katalogu.md) · **v1 scorecard:** [docs/V1-Hazirlik.md](docs/V1-Hazirlik.md)

## Why Divan?

A collection of clever prompts is not a delivery system. Real work needs the
right capability at the right time, durable decisions, evidence, and a public
surface that stays in sync with the implementation.

| Failure mode | Divan's answer |
|---|---|
| The agent starts coding without a plan | Sadrazam: brief → counsel → plan → execution → inspection → delivery |
| Every new session forgets the project | Claude Code-native `CLAUDE.md` plus AGENTS, BLUEPRINT, and `.divan/` records |
| “It works” has no evidence | Tests, official validators, and an independent inspector |
| Huge skill dumps consume context and trust | Curation, license/provenance gates, and progressive disclosure |
| External swarm harnesses add cost and complexity | One native session first; bounded subagents/worktrees only when justified |
| A PR is ready but the public product is still stale | Publication Law: docs + wiki + changelog + merge + live verification |

Divan is not a model and not another agent runtime. It is an auditable Agent
Skills distribution that adds **delivery discipline, specialist procedures,
and project memory** to the coding agent you already use.

## Company OS

Describe the outcome; do not memorize internal skill names. Sadrazam safely
inspects the project, detects its framework, selects the smallest qualified
team, and expands changed paths through an impact graph. Core Pack supplies
engineering discipline, UI Pack handles interfaces, React Pack activates only
for detected React projects, and Zanaat Pack joins creative or integration
work. See [Company OS](docs/Company-OS.md).

Expert shortcuts remain available when explicit control is useful:
`/ferman`, `/sefer`, `/teftis`, `/defter`, `/vezir`, and `/company`.

## Install

Preview the no-write plan, then install the same pinned release into both hosts:

```powershell
python scripts/divan.py install --host both --ref v0.15.0
python scripts/divan.py install --host both --ref v0.15.0 --execute
```

For safety, the installer never overwrites an existing `divan` marketplace or
`@divan` plugin whose source/ref cannot be proven; it leaves the entry untouched
and fails with an actionable error.

The installer delegates to the official Claude and Codex plugin CLIs, records
pre-state, and never removes unrelated plugins. See
[installation options](docs/Kurulum.md) for single-host, manual, legacy
migration, and removal paths.

The five-minute safe lifecycle continues with:

```powershell
python scripts/divan.py doctor --host both --ref v0.15.0
python scripts/divan.py update --host both --ref v0.15.0
python scripts/divan.py update --host both --ref v0.15.0 --execute
python scripts/divan.py recover "C:\Users\you\.divan\transactions\upgrade-20260721-120000.json"
python scripts/divan.py recover "C:\Users\you\.divan\transactions\install-20260721-120000.json"
```

Replace the example journal with doctor's exact `recovery_command`. Rolling
back the `install-...json` journal uninstalls only Divan entries created by that
transaction. See [docs/Kaldirma.md](docs/Kaldirma.md) for host-aware manual
removal and ownership boundaries.

## Clean development

```powershell
python scripts/hygiene.py --check
python scripts/hygiene.py --clean
```

`--check` rejects invalid UTF-8, BOM/mojibake, locale-dependent text
subprocesses, and repository caches. `--clean` permanently removes only a fixed
allowlist of reproducible caches; it never touches `.divan/evidence`, eval
results, manifests, worktrees, or user/rollback backups. CI pins repository text
to UTF-8/LF and core Python complexity to McCabe 25.

## Start from intent

You do not need to memorize skill names. Use the
[live decree selector](https://trugurpala.github.io/divan/#basla) to choose what
you want to accomplish; it returns the smallest pack, a copyable request, and
the delivery path.

| Intent | Pack | First path |
|---|---|---|
| Ship a feature | `sadrazam` + `core-pack` | Brief → plan → TDD → inspection → publication |
| Fix a bug | `core-pack` | Symptom → root cause → regression test |
| Design a UI | `ui-pack` + `react-pack` | Aesthetic direction → system → browser verification |
| Learn a codebase | `sadrazam` + `core-pack` | Evidence search → architecture/risk map → durable record |
| Prove and publish | `sadrazam` + `core-pack` | A/B eval → blind judge → CI → live verification |

## Behavioral evals

Structural validity is not evidence that a skill improves behavior. The v0.10 series
ships a provider-neutral runner that executes the same case with and without a
skill, blinds the outputs as A/B, and optionally applies a judge and release
threshold:

```bash
python evals/run.py --check
python evals/run.py --run --skill kaynak-kuratori \
  --adapter "python /trusted/path/agent_adapter.py" \
  --judge "python /trusted/path/judge_adapter.py" \
  --provenance provenance.json
```

Without a real adapter or judge it records `review_required` instead of
inventing a win rate. Provenance identifies the agent, judge, and execution
environment of a real run; it is not a quality claim by itself. The first
v0.12.0 Claude→Codex blinded run recorded zero skill wins, one baseline win,
and two ties. No threshold was predeclared and the skill condition did not win,
so this is auditable execution evidence, not a quality-improvement claim. See the
[public result](evals/results/claude-codex-baglam-muhafizi-v012.json) and the
[adapter protocol](evals/README.md).

## How it improves itself

Divan does not equate improvement with installing more repositories:

1. Resolve the real source and canonical repository.
2. Audit license, provenance, hooks, scripts, tools, and permissions.
3. Measure the actual gap and overlap with the existing council.
4. Use a weekly read-only discovery and structured community intake to propose
   candidates without installing them.
5. Record an evidence-backed ADOPT, ADAPT, REFERENCE, or REJECT decision in the
   [candidate council](docs/Aday-Meclisi.md).
6. Create the smallest useful adaptation and add behavioral eval cases.
7. Pass local tests plus the official Agent Skills and Claude Code validators.
8. Use the publication manifest and `/yayin` path to fail CI when README, Wiki,
   site, changelog, marketplace, and version records drift.
9. Treat a PR as intermediate; after `main`, wait for Pages and Wiki to expose
   the same version, then generate the tag and GitHub Release from the changelog.

The latest example is the [40-repository source curation audit](reports/2026-07-18-claude-repo-kurasyonu.md).

## Packs

| Pack | Purpose |
|---|---|
| `sadrazam` | End-to-end delivery, persistent memory, stack counsel, skill creation, native orchestration |
| `core-pack` | Planning, TDD, debugging, verification, source curation, code search, context discipline |
| `ui-pack` | Distinctive frontend design, UI/UX intelligence, browser testing |
| `react-pack` | React/Next.js/React Native practices, composition, deployment, optimization |
| `zanaat-pack` | Algorithmic/static art, themes, MCP building, web artifacts, Slack GIFs, Claude API |

## Honest status

Divan follows the open Agent Skills specification and ships the standard GitHub
community and security files, but it is not v1.0 yet. All 41 skills receive
structural validation; four original skills provide 13 behavioral cases and a
provider-neutral A/B runner. v0.11 automates publication surfaces and clean-host
compatibility checks. The first declared real-agent/judge comparison is now
published; independent user evidence remains the external gate. See the
[machine-backed v1 scorecard](docs/V1-Hazirlik.md). Until that evidence exists,
the project does not claim a speed multiplier, revenue
increase, or “best in the world” status.

## Contributing and security

- [Contributing in English](CONTRIBUTING.en.md) · [Türkçe](CONTRIBUTING.tr.md)
- [Support and request routing](SUPPORT.md)
- [DCS-001–DCS-011 community standards](docs/Topluluk-Standartlari.md)
- [Security policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [License and third-party notices](THIRD_PARTY_LICENSES.md)

Divan is not affiliated with or endorsed by Anthropic, Claude, OpenAI, or
Vercel. Product and compatibility names are descriptive only.

The v1 scorecard remains **7/8**: independent-user evidence is still pending.
