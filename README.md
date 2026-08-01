# Divan

![audit](https://github.com/trugurpala/divan/actions/workflows/quality-gate.yml/badge.svg)
![version](https://img.shields.io/badge/version-1.0.2-1f6feb)
![license](https://img.shields.io/badge/license-MIT-2ea44f)

[Türkçe](README.tr.md) · **English** · [Wiki](https://github.com/trugurpala/divan/wiki) · [Changelog](CHANGELOG.md) · [Roadmap](BLUEPRINT.md)

<img src="docs/assets/muhurdar-idle.png" alt="Mühürdar, Divan's verification mascot" width="128" align="right">

**You are Hükümdar, the owner. Divan turns the coding agent you already use
into a modular delivery system: one repository, five focused packs, 41 skills,
persistent project memory, local progress, and independent verification.**

You write the decree in plain language. Divan narrows the scope, selects the
smallest qualified team, plans the work, builds with tests, verifies the
result, records the decisions, and presents a finished delivery. It runs as a
native plugin in Claude Code and in Codex Desktop/CLI; its Agent Skills remain
portable to Cursor and other compatible hosts.

## Host compatibility

Host support is evidence-graded rather than advertised as a single yes/no
claim. Claude Code and Codex are verified today; every other host keeps an
explicit current tier, target tier, capability map, and official source in the
[host compatibility registry](registry/host-compatibility.json).
Every claim is surface-scoped. In particular, verified Codex plugin support
means Desktop and CLI; it does not claim plugin availability in the Codex IDE
extension or mobile clients.

**Current source:** v1.0.2 · **Latest published:** v1.0.2 · **Releases:** https://github.com/trugurpala/divan/releases · **Website:** https://trugurpala.github.io/divan/ · **Live Wiki:** https://github.com/trugurpala/divan/wiki · **Catalog:** [docs/skill-catalog.md](docs/skill-catalog.md) · **Host compatibility:** [English guide](#host-compatibility) · **Local progress:** [Seyir](#follow-progress-locally) · **v1 scorecard:** [docs/V1-Hazirlik.md](docs/V1-Hazirlik.md)

## Already installed? Start here

Open a fresh Codex or Claude Code session in your project and describe the
outcome. You do not need to remember a skill name or a repository command:

> **Divan, take ownership of this task. Verify the current state, write the
> plan, implement it with tests, and deliver the evidence: [your goal].**

Divan selects the smallest capable pack. React Pack joins only a detected
React-family project; Zanaat Pack joins only creative or integration work.
Connected GitHub, Figma, Gmail, Slack, or MCP tools do not gain permission by
being available—the requested task remains the authority boundary.

### First setup

Use the [verified no-checkout install](#fastest-first-install-one-verified-file-no-repository-checkout)
once, then start a new agent session so the host loads the installed plugin.
Keep the downloaded `divan.pyz` and checksum together for later diagnosis and
recovery. Divan does not silently edit PATH or a shell profile.

### Maintenance

Use the retained bootstrap only when you need doctor, update, or recovery.
A healthy doctor ends with `READY` and does not tell you to install again. A
real problem prints one exact copyable command.

Divan Engine is the product's built-in, stdlib-only execution core. The Divan
Governance Model (Divan Nizamı) defines its owner-first authority order; it is
not a second product. The core remains modular inside this repository and has
no external agent-runtime or external-repository dependency.
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

Project inspection keeps the user-facing plan focused on the real project. It
does not turn Divan-owned scratch worktrees, dependency/build caches, fixture
projects, or skill-internal helper folders into extra workspaces unless one of
those folders is the explicit project root.

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
goals can be archived. The primary v1 evidence path now proves a real task in a
project distinct from Divan, runs bounded test/regression checks once, observes
the host version directly, and seals a privacy-bounded schema-2 receipt:

```powershell
python divan-project.pyz goal advance --project . --goal <goal-id> --to verified --evidence <implementation-file> <test-or-verification-file>
python divan-project.pyz goal advance --project . --goal <goal-id> --to verified --evidence <implementation-file> <test-or-verification-file> --execute
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex --execute
python divan-project.pyz adoption verify .divan/adoption/<proof-id>/adoption-receipt.json
```

The VERIFIED transition hashes the named project-relative files into the goal
receipt atomically; plan-only evidence is rejected. Preview writes nothing and
starts no subprocess. Operator identity does not
change eligibility: maintainer and external users pass the same technical
gate. Only `valid-clean-room-adoption` can qualify; historical schema-1 export
receipts remain verifiable but are never v1 evidence. Keep the downloaded
`divan-project.pyz` and `divan-project.pyz.sha256` together; proof execution
also requires a Git repository so tracked-source drift can fail closed.

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

When verification takes time, Seyir now shows why the page can look quiet, the
current evidence-backed normal wait window, and when the run deserves attention.
That keeps the front of the product calm for vibe coders while the back keeps
running measured checks.

## Install

The commands below pin Current source. If Current source differs from Latest
published, substitute Latest published in every `--ref` command. Only install a
ref whose immutable tag and GitHub Release exist. v1.0.2 is now the latest
published release and can be used for release-pinned installs.

### Fastest first install: one verified file, no repository checkout

After the matching GitHub Release exists, download its standalone bootstrap and
checksum, verify them locally, inspect the no-write plan, then execute:

```powershell
$tag = "v1.0.2"
Invoke-WebRequest "https://github.com/trugurpala/divan/releases/download/$tag/divan.pyz" -OutFile divan.pyz
Invoke-WebRequest "https://github.com/trugurpala/divan/releases/download/$tag/divan.pyz.sha256" -OutFile divan.pyz.sha256
$expected = ((Get-Content .\divan.pyz.sha256 -Raw).Trim() -split "\s+")[0].ToLowerInvariant()
$actual = (Get-FileHash .\divan.pyz -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw "Divan bootstrap SHA-256 mismatch" }
python .\divan.pyz doctor --host codex --json
python .\divan.pyz install --host codex --profile auto
python .\divan.pyz install --host codex --profile auto --execute
```

The file contains the exact five-package, 41-skill catalog and immutable source
commit for that release. It rejects another source or ref. Keep `divan.pyz`;
doctor uses it to print the exact recovery command if an interrupted operation
needs attention.

From a repository checkout, preview the no-write plan and install the same
pinned release into both hosts:

```powershell
python scripts/divan.py install --host both --ref v1.0.2
python scripts/divan.py install --host both --ref v1.0.2 --execute
```

For Codex Desktop, one explicit auto-profile command diagnoses the local CLI
and chooses the strongest route it can prove:

```powershell
python scripts/divan.py install --host codex --profile auto --ref v1.0.2
python scripts/divan.py install --host codex --profile auto --ref v1.0.2 --execute
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
pre-state, and never removes unrelated plugins. Run
`python scripts/divan.py install --help` for the English host and profile
options. The complete Turkish reference remains available in
[docs/Kurulum.md](docs/Kurulum.md).

The five-minute safe lifecycle continues with:

```powershell
python scripts/divan.py doctor --host both --ref v1.0.2
python scripts/divan.py update --host both --ref v1.0.2
python scripts/divan.py update --host both --ref v1.0.2 --execute
python scripts/divan.py recover "C:\Users\you\.divan\transactions\upgrade-20260721-120000.json"
python scripts/divan.py recover "C:\Users\you\.divan\transactions\install-20260721-120000.json"
```

The standalone `divan.pyz` uses its embedded immutable release identity during
an update; it does not treat the extracted bundle as a Git checkout.

Replace the example journal with doctor's exact `recovery_command`. Rolling
back the `install-...json` journal uninstalls only Divan entries created by that
transaction; it does not remove unrelated host entries. The manual,
host-aware Turkish reference is [docs/Kaldirma.md](docs/Kaldirma.md).

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

Divan v1.0.2 is published after all eight machine-backed readiness gates passed.
All 41 skills receive structural validation; four original skills provide 13
behavioral cases and a provider-neutral A/B runner. The stable contract keeps
one repository, five modular packages, the stdlib-only Divan Engine,
owner-first Divan Nizamı governance, the installed Divan Project Contract, and
Claude Code/Codex lifecycle support. v1.0.2 adds quieter project discovery so
Divan-owned worktrees, fixture trees, caches, and skill-internal helper folders
do not appear as duplicate user workspaces. The immutable tag, seven
checksummed and attested assets, SBOM, Pages, Wiki, clean-host matrix, and
release readbacks are recorded in the
[v1.0.2 publication evidence](.divan/evidence/teftis-20260731-v102-release.md).
The clean-room result proves a bounded technical workflow; it does not claim an
independent-user count, endorsement, market adoption, speed gain, revenue
increase, quality win, or “best in the world” status.

## Contributing and security

- [Contributing in English](CONTRIBUTING.en.md) · [Türkçe](CONTRIBUTING.tr.md)
- [Support and request routing](SUPPORT.md)
- [DCS-001–DCS-011 community standards](docs/Topluluk-Standartlari.md)
- [Security policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [License and third-party notices](THIRD_PARTY_LICENSES.md)

Divan is not affiliated with or endorsed by Anthropic, Claude, OpenAI, or
Vercel. Product and compatibility names are descriptive only.

The v1 readiness scorecard is now **8/8**: immutable v0.18.5 produced one
machine-verifiable clean-room adoption on Windows 11, Codex, and a real external
project; the privacy-reviewed receipt was committed and re-verified offline.
This is bounded technical evidence, not an independent-user count, endorsement,
market-adoption claim, speed gain, or quality win. The checksum sidecar protects
the download; the v1 gate separately pins and matches the reviewed release
runner digest in `registry/v1-gates.json`.
