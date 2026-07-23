# Divan Project OS

[Türkçe](Project-OS.tr.md)

Divan Project OS is the supervised, portable contract installed into a target
project. It turns an authorized intent into a specification, plan, task list,
implementation evidence, preview, release, and live readback. It is invoked by
a user or coding-agent session; it is not a daemon, hosted control plane, model,
or independent agent runtime.

## Two standards layers

- **DCS-*** governs the Divan repository distribution: provenance, maintenance,
  documentation, host compatibility, and public release surfaces.
- **DPS-*** governs the installed project: intent, architecture, maintainability,
  tests, security, UX, contracts, reliability, documentation, recovery, SEO,
  and release evidence.

Only applicable DPS rules run. `DPS-011` SEO applies to a `public-web` project,
not to a Python library. Waivers require an owner, rationale, affected standard,
and an expiry of no more than 180 days.

## Initialize a project

Every mutating command is a dry run until `--execute` is present:

```powershell
python scripts/divan.py init --project . --profile standard --locale auto
python scripts/divan.py init --project . --profile standard --locale auto --execute
python scripts/divan.py audit --project . --format json
```

Initialization owns only `.divan/` and marked blocks in `AGENTS.md` or
`CLAUDE.md`. Existing text is preserved; malformed markers stop the operation.
A second identical initialization produces no diff.

## Goal and evidence lifecycle

```text
DISCOVERED → SPECIFIED → PLANNED → IMPLEMENTING
→ VERIFIED → PREVIEWED → RELEASED → OBSERVED
```

`BLOCKED` and `FAILED` are explicit outcomes. A receipt stores hashes, selected
workflows, changed relative paths, checks, provider evidence, and timestamps.
It never stores secrets, hidden reasoning, personal absolute paths, or unrelated
plugin inventory.

For public web projects, the read-only static audit is:

```powershell
python scripts/seo.py audit --project . --profile standard --json
```

The audit checks metadata, canonical and language links, social cards,
structured data, robots, sitemap, and local links against one configured
deployment origin. Static checks never complete the gate by themselves.
Initialized public-web projects receive bounded `.divan/lighthouse.json`,
`.divan/seo-tools.json`, and `.github/workflows/divan-seo.yml` contracts.
The pinned workflow pulls Lighthouse CI through its reviewed Linux/AMD64 OCI
digest and downloads Lychee through its reviewed release archive SHA256. It
accepts only the exact 13-member Lychee archive contract, rejects links and
path traversal, executes the nested verified binary, emits native JSON, and
uploads one GitHub artifact. The managed command plan is the workflow's command
authority: its acquisition argv, execution argv, outputs, and digest are
rendered from the same registry object. Local audit never downloads, executes,
or grants provider authority.

Runtime-rendered web projects must supply their deployment URL during init:

```powershell
python scripts/divan.py init --project . --profile standard --locale auto --expected-url https://app.example.com/
```

Without it, init is `BLOCKED`, emits no runnable SEO workflow, and returns the
safe continuation command.

Local native artifacts are at most `OBSERVED_UNVERIFIED`; caller-authored JSON
can never produce `PASS`. Authoritative verification is explicit:

```powershell
python scripts/seo.py verify-github --project . --repository owner/repo --run-id 123 --run-attempt 1 --workflow-commit <sha> --json
```

The repository is derived from the clean local Git HEAD and normalized
`github.com` origin; a CLI repository value can only confirm that identity.
Authenticated, fixed `gh api` readbacks bind the exact run attempt, commit and
tree, canonical workflow bytes/digest, artifact association/digest, and native
JSON archive. Missing GitHub capability or any mismatch remains
`BLOCKED`/error.

Search Console is disabled by default. An opt-in configuration must name an
account, property, and provider-managed authentication. Configuration alone is
`CONFIGURED_UNVERIFIED`, never ready. Readiness requires ProviderCapabilityV1
and provider readback evidence; until that adapter exists the audit remains
fail-closed. It never submits URLs or mutates Search Console.

See [Company OS](Company-OS.md) for routing and pack selection, and
[Community Standards](Topluluk-Standartlari.md) for the Divan distribution
contract.
