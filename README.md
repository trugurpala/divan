# Divan

![audit](https://github.com/trugurpala/divan/actions/workflows/quality-gate.yml/badge.svg)
![version](https://img.shields.io/badge/version-0.18.1-1f6feb)
![license](https://img.shields.io/badge/license-MIT-2ea44f)

[Türkçe](README.tr.md) · **English** · [Wiki](https://github.com/trugurpala/divan/wiki) · [Changelog](CHANGELOG.md) · [Roadmap](BLUEPRINT.md)

<img src="docs/assets/muhurdar-idle.png" alt="Mühürdar, Divan's verification mascot" width="128" align="right">

**You are Hükümdar, the owner. Divan is one product around your coding agent:
41 skills, five focused packs, persistent project memory, and independent
verification.**

You issue the decree. Divan clarifies it, plans the work, builds with tests,
verifies the result, records the decisions, and presents a finished delivery.
It runs as a native plugin in Claude Code/Desktop Code and Codex; its Agent
Skills remain portable to Cursor and other compatible hosts.

Host support is evidence-graded rather than advertised as a single yes/no
claim. Claude Code and Codex are verified today; every other host keeps an
explicit current tier, target tier, capability map, and official source in the
[host compatibility registry](registry/host-compatibility.json).

**Current source:** v0.18.1 · **Latest published:** v0.18.1 · **Releases:** https://github.com/trugurpala/divan/releases · **Website:** https://trugurpala.github.io/divan/ · **Live Wiki:** https://github.com/trugurpala/divan/wiki · **Catalog:** [docs/skill-catalog.md](docs/skill-catalog.md) · **Host compatibility:** [docs/Host-Uyumlulugu.md](docs/Host-Uyumlulugu.md) · **v1 scorecard:** [docs/V1-Hazirlik.md](docs/V1-Hazirlik.md)

Divan Engine is the product's built-in, stdlib-only execution core. The Divan
Governance Model (Divan Nizamı) defines its owner-first authority order; it is
not a second product. The core remains in this repository and has no external
agent-runtime or external-repository dependency.
Divan Nizamı is local workflow governance, not identity authentication; the
host operating-system account and repository permissions remain the security
boundary.

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
| A connected tool silently expands the job | Divan Nizamı: only Hükümdar can expand scope; every delegated layer is narrower |
| The technical work is hard to follow in chat | Plain-language progress contract: report what is happening, why it matters, and what comes next |

Divan is not a model or a separate third-party agent runtime. It is an
auditable Agent Skills distribution with its own modular execution core,
adding **delivery discipline, specialist procedures, and project memory** to
the coding agent you already use.

## Divan Engine

Describe the outcome; do not memorize internal skill names. Sadrazam safely
inspects the project, detects its framework, selects the smallest qualified
team, and expands changed paths through an impact graph. Core Pack supplies
engineering discipline, UI Pack handles interfaces, React Pack activates only
for detected React projects, and Zanaat Pack joins creative or integration
work. See [Divan Engine](docs/Divan-Engine.md).

Nizam-i Sefer adds the missing execution judgment. A plan now explains the
structural risk, host certainty, conservative context budget, required model
class, number of sefers, task dependencies, handoff point, evidence, and a
maximum of three parallel workstreams. It does not call a model or claim that a
candidate model is available:

```powershell
python scripts/divan.py plan --project . --intent "Secure, test and release the API" --host-profile auto --json
python scripts/divan.py plan --project . --intent "Secure, test and release the API" --host-profile codex --context-window 1050000 --target released --json
```

Hükümdar is the final authority. A Ferman delegates bounded work through
Sadrazam and Divan to specialists and providers. Tool availability never grants
authority, and only Hükümdar may expand scope. Inspect the nine-module contract
or validate it without changing the project:

```powershell
python scripts/divan.py architecture --json
python scripts/divan.py validate
```

Expert shortcuts remain available when explicit control is useful:
`/divan`, `/ferman`, `/sefer`, `/teftis`, `/defter`, and `/vezir`. The former
`/company` and `company-validate` names remain bounded compatibility aliases
through v1.

Install the same contract into a project with a no-write preview first:

```powershell
python scripts/divan.py init --project . --profile standard --locale auto
python scripts/divan.py init --project . --profile standard --locale auto --execute
python scripts/divan.py audit --project . --format json
```

The Divan repository follows `DCS-*`; the installed project follows only the
applicable `DPS-*` rules and records evidence in `.divan/`. See the
[Divan Project Contract](docs/Project-Contract.md).

After initialization, inspect ownership and drift without writing, then preview
any repair or project-schema update before execution:

```powershell
python scripts/divan.py project status --project . --json
python scripts/divan.py project update --project .
python scripts/divan.py project update --project . --execute
python scripts/divan.py project repair --project .
python scripts/divan.py project repair --project . --execute
```

Host `update` replaces Divan packages in Claude/Codex. Project `update` migrates
only Divan-owned Project Contract surfaces in a target repository. `audit`
evaluates DPS quality evidence; `project status` compares ownership
fingerprints and drift. Verified
goals can be archived, and a privacy-bounded adoption receipt can be exported
without exposing usernames, absolute paths, remotes, secrets, or unrelated
plugins. Owner-canary evidence never closes the independent-adoption gate.

## Follow progress locally

Seyir turns Divan's existing goal, task, Git, check, and receipt evidence into a
calm local page. It is read-only, uses no cloud service or API key, and binds
only to `127.0.0.1`. Start it from the project you want to follow:

```powershell
python scripts/divan.py status --project . --open --lang auto
```

Divan selects a free port, prints the exact working address, and opens the same
address when `--open` is present. The address is temporary; stop it with
`Ctrl+C`. Do not reuse an example port from documentation.

## Install

The commands below pin Current source. If Current source differs from Latest
published, substitute Latest published in every `--ref` command. Only install a
ref whose immutable tag and GitHub Release exist. Preview the no-write plan,
then install the same pinned release into both hosts:

```powershell
python scripts/divan.py install --host both --ref v0.18.1
python scripts/divan.py install --host both --ref v0.18.1 --execute
```

For Codex Desktop, one explicit auto-profile command diagnoses the local CLI
and chooses the strongest route it can prove:

```powershell
python scripts/divan.py install --host codex --profile auto --ref v0.18.1
python scripts/divan.py install --host codex --profile auto --ref v0.18.1 --execute
```

A healthy Codex CLI keeps the full native plugin path. A missing,
non-executable, or OS-denied CLI selects the checksum-backed 41-skill
fallback. The fallback includes skills and instructions, but it does not claim
native commands, agents, hooks, MCP configuration, or native lifecycle
support. Invalid host JSON blocks instead of hiding a compatibility problem.

For safety, the installer never overwrites an existing `divan` marketplace or
`@divan` plugin whose source/ref cannot be proven; it leaves the entry untouched
and fails with an actionable error.

The installer delegates to the official Claude and Codex plugin CLIs, records
pre-state, and never removes unrelated plugins. See
[installation options](docs/Kurulum.md) for single-host, manual, legacy
migration, and removal paths.

The five-minute safe lifecycle continues with:

```powershell
python scripts/divan.py doctor --host both --ref v0.18.1
python scripts/divan.py update --host both --ref v0.18.1
python scripts/divan.py update --host both --ref v0.18.1 --execute
python scripts/divan.py recover "C:\Users\you\.divan\transactions\upgrade-20260721-120000.json"
python scripts/divan.py recover "C:\Users\you\.divan\transactions\install-20260721-120000.json"
```

Replace the example journal with doctor's exact `recovery_command`. Rolling
back the `install-...json` journal uninstalls only Divan entries created by that
transaction. See [docs/Kaldirma.md](docs/Kaldirma.md) for host-aware manual
removal and ownership boundaries.

## Clean development

```powershell
python scripts/verify.py
python scripts/hygiene.py --check
python scripts/hygiene.py --clean
```

`verify.py` is the shared local/CI verification path. It disables Python
bytecode, redirects tool caches outside the repository, runs the core gates,
and finishes with a second hygiene check. `--check` rejects invalid UTF-8,
BOM/mojibake, locale-dependent text
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
published; independent user evidence remains the external gate. v0.17.0
publishes Divan Engine and Divan Nizamı while preserving old paths. PR #49,
all required CI, immutable tag/Release, five checksummed and attested assets,
Pages, and Wiki are verified in the publication evidence. See the
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
