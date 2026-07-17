# Divan

![audit](https://github.com/trugurpala/divan/actions/workflows/teftis.yml/badge.svg)
![version](https://img.shields.io/badge/version-0.9.0-1f6feb)
![license](https://img.shields.io/badge/license-MIT-2ea44f)

[Türkçe](README.md) · **English** · [Changelog](CHANGELOG.md) · [Roadmap](BLUEPRINT.md)

<img src="docs/assets/muhurdar-idle.png" alt="Mühürdar, Divan's verification mascot" width="128" align="right">

**You are the sovereign. Divan is the council around your coding agent: 41
skills, five focused packs, persistent project memory, and independent
verification.**

You issue the decree. Divan clarifies it, plans the work, builds with tests,
verifies the result, records the decisions, and presents a finished delivery.
It runs natively in Claude Code and its Agent Skills remain portable to Codex,
Cursor, and other compatible hosts.

**Current release:** v0.9.0 · **Website:** https://trugurpala.github.io/divan/ · **Catalog:** [docs/Vezir-Katalogu.md](docs/Vezir-Katalogu.md)

## Why Divan?

A collection of clever prompts is not a delivery system. Real work needs the
right capability at the right time, durable decisions, evidence, and a public
surface that stays in sync with the implementation.

| Failure mode | Divan's answer |
|---|---|
| The agent starts coding without a plan | Sadrazam: brief → counsel → plan → execution → inspection → delivery |
| Every new session forgets the project | Defterdar: AGENTS.md, BLUEPRINT, and `.divan/` records |
| “It works” has no evidence | Tests, official validators, and an independent inspector |
| Huge skill dumps consume context and trust | Curation, license/provenance gates, and progressive disclosure |
| External swarm harnesses add cost and complexity | One native session first; bounded subagents/worktrees only when justified |
| A PR is ready but the public product is still stale | Publication Law: docs + changelog + merge + live verification |

Divan is not a model and not another agent runtime. It is an auditable Agent
Skills distribution that adds **delivery discipline, specialist procedures,
and project memory** to the coding agent you already use.

## Install

Claude Code:

```text
/plugin marketplace add trugurpala/divan
/plugin install sadrazam@divan
/plugin install core-pack@divan
/plugin install ui-pack@divan
/plugin install react-pack@divan
/plugin install zanaat-pack@divan
```

Codex on Windows:

```powershell
irm https://raw.githubusercontent.com/trugurpala/divan/main/scripts/kur-codex.ps1 | iex
```

See [installation options](docs/Kurulum.md) for macOS/Linux and removal.

## How it improves itself

Divan does not equate improvement with installing more repositories:

1. Resolve the real source and canonical repository.
2. Audit license, provenance, hooks, scripts, tools, and permissions.
3. Measure the actual gap and overlap with the existing council.
4. Create the smallest useful adaptation and add behavioral eval cases.
5. Pass local tests plus the official Agent Skills and Claude Code validators.
6. Update README, catalog, changelog, and roadmap in the same change.
7. When publication is requested, treat a PR as an intermediate state; do not
   claim delivery until the default branch and live surface are verified.

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
structural validation and selected original skills include eval contracts.
An automated skill-vs-baseline behavior runner, independent adoption evidence,
and reproducible productivity benchmarks remain v1.0 gates. Until those exist,
the project does not claim a speed multiplier, revenue increase, or “best in
the world” status.

## Contributing and security

- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [License and third-party notices](THIRD_PARTY_LICENSES.md)

Divan is not affiliated with or endorsed by Anthropic, Claude, OpenAI, or
Vercel. Product and compatibility names are descriptive only.
