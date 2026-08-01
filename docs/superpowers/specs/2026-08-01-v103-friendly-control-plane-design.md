# Divan v1.0.3 Friendly Control Plane Design

**Target:** v1.0.3  
**Status:** Approved by the owner's autonomous implementation mandate  
**Theme:** One-time setup, natural-language daily use, truthful maintenance

## Purpose

Divan v1.0.2 is published and its v1 readiness score is 8/8. The next release
must not grow the framework merely by adding more skills. It must remove the
real friction observed while using the released product:

1. a healthy `doctor` currently recommends installation again;
2. the website's first command assumes a repository checkout;
3. installation, daily use, and maintenance are presented as one flow;
4. host compatibility is stated at product level even when support differs by
   surface, such as Codex Desktop/CLI versus the IDE extension;
5. a vibe coder sees infrastructure terms before seeing the next human action.

The release therefore introduces a small, truthful control-plane improvement.
It changes no existing package count, skill payload, release checksum policy,
or host permissions.

## Product Goal

> A new user installs Divan once from an immutable release, opens a fresh agent
> session, describes the desired outcome in natural language, and receives a
> truthful next action whenever maintenance is required.

The experience has three explicit moments:

| Moment | User-facing action | Divan responsibility |
|---|---|---|
| First setup | Run the verified release bootstrap | Preview, verify, install, and preserve recovery evidence |
| Daily use | Tell Codex or Claude what outcome is wanted | Route the smallest capable team and report progress plainly |
| Maintenance | Run the retained bootstrap's doctor/update command | Diagnose without mutation and print only a real next action |

## Non-negotiable Decisions

### 1. Natural language is the daily interface

After installation, a user should not need a repository-relative command to
start work. A fresh Codex or Claude session plus a plain-language ferman is the
golden path. Shell commands remain the maintenance boundary.

### 2. No hidden PATH or shell-profile mutation

Divan will not install a global wrapper in v1.0.3. Modifying PATH, PowerShell
profiles, or POSIX shell files creates cross-platform ownership and recovery
risks while duplicating the host plugin's real daily interface. The verified
`divan.pyz` bootstrap remains portable when invoked by `python` or `py` and can
be retained in a user-chosen tools directory.

### 3. Tight where damage is possible, light where it is not

The release keeps:

- immutable release refs and SHA-256 verification;
- dry-run before writes;
- explicit `--execute` for state changes;
- transaction journals and ownership-aware recovery;
- evidence before completion claims;
- verification gates for release and public surfaces.

It removes:

- repeated installation advice after a healthy diagnosis;
- repository-relative commands from the no-clone onboarding path;
- claims that silently span unsupported host surfaces;
- infrastructure-first wording in the primary user journey.

This is risk-based strictness, not relaxed integrity.

## Doctor Contract

The doctor remains read-only.

### Healthy

Machine output:

```json
{
  "status": "healthy",
  "next_command": null
}
```

Human output ends with a readiness message, not an install command:

```text
READY: Divan is installed and verified. Start a new agent session and describe your goal.
```

### Attention, unavailable, or unfinished transaction

`next_command` remains a copyable exact command. Recovery keeps priority over
installation. Invalid host JSON remains blocked rather than hidden by a
fallback.

This is a backward-compatible structural record except that healthy
`next_command` becomes nullable. Consumers must already inspect `status`; a
command is meaningful only when action is required.

## Host-Surface Truth

Each compatibility row gains:

- `surfaces`: the exact product surfaces to which the row applies;
- `excluded_surfaces`: known surfaces intentionally outside the claim.

For example, the verified Codex plugin claim applies to Desktop and CLI. It
does not imply plugin availability in the IDE extension or mobile clients.
The registry validator rejects empty, duplicate, malformed, or overlapping
surface declarations.

Compatibility tiers remain evidence-based:

- `verified`: exercised by repository evidence;
- `native`: the host supports the distribution model, without Divan canary
  proof yet;
- `skill-compatible`: portable skill/instruction support only;
- `experimental`: documented target with incomplete adapter proof.

## Modular Boundary

```text
Hükümdarın fermanı
        |
        v
Host plugin / skill layer      <- daily natural-language interface
        |
        v
Divan Engine + Divan Nizamı    <- plan, risk, routing, evidence
        |
        v
Project state + Seyir          <- durable work and readable progress

Separate maintenance lane:

immutable divan.pyz
  -> doctor / install / update / recover
  -> host adapters
  -> transaction + provenance evidence
```

React and Zanaat packs remain optional. They are selected only when project
evidence requires React-family expertise, MCP/API integration, or creative
production. Installing or loading them into every task would increase context,
latency, and ambiguity without improving correctness.

## Ecosystem Review

The following current projects were reviewed as references, not vendoring
targets. Divan remains one repository and imports no foreign runtime merely for
feature parity.

| Project | Useful idea | Divan decision |
|---|---|---|
| `obra/superpowers` | enforced planning, TDD, review | Keep as workflow reference through licensed skills |
| `github/spec-kit` | spec-to-plan-to-task flow | Adapt terminology-neutral task decomposition |
| `anthropics/skills` | progressive skill disclosure | Keep smallest-capable-team loading |
| `github/awesome-copilot` | host-specific discovery | Reference; do not copy catalog wholesale |
| `ComposioHQ/awesome-claude-skills` | broad skill discovery | Candidate source only, with license/provenance review |
| `composiohq/awesome-codex-skills` | Codex-oriented discovery | Candidate source only |
| `VoltAgent/awesome-agent-skills` | cross-host skill inventory | Candidate source only |
| `vercel-labs/skills` | multi-agent installation patterns | Adapt host capability boundaries, not installer code |
| `modelcontextprotocol/servers` | standard tool transport | Use host-provided MCP selectively; no automatic bulk install |
| `microsoft/playwright-mcp` | structured browser evidence | Prefer real browser verification for UI tasks |
| `OpenHands/OpenHands` | end-to-end execution runtime | Reference executor ideas; do not add runtime dependency |
| `langchain-ai/langgraph` | durable state and resume | Keep Divan's stdlib state model independent |
| `vercel-labs/agent-browser` | agent-oriented browser tests | Reference for optional UI verification |
| `agentskills.io` | portable skill contract | Preserve standards-compatible skill fallback |

The research changes Divan through selection rules and contracts, not by
forking ten repositories into one codebase.

## User-Facing Copy Contract

Primary surfaces must answer these questions in order:

1. What does Divan do for me?
2. Is this my first setup or is Divan already installed?
3. What is the one next action?
4. What proof will I receive?
5. Where do I go for advanced maintenance?

Turkish and English sources must remain semantically equivalent. Site and docs
mirrors must remain byte-identical where the release contract requires it.

## Verification

The release is acceptable only when:

1. a healthy doctor returns `next_command: null`;
2. human doctor output prints `READY` and no `NEXT` line when healthy;
3. attention and recovery diagnoses still print an exact command;
4. host-surface declarations validate and Codex excludes unsupported plugin
   surfaces explicitly;
5. README and website separate first setup, daily use, and maintenance;
6. no-clone instructions use the release bootstrap, never
   `scripts/divan.py`;
7. focused host, documentation, site, release, and full repository checks pass;
8. PR CI, merged `main`, Pages, Wiki, and release assets agree before the
   release is called published.

## Deliberate Non-goals

- No new model runtime or agent framework dependency.
- No automatic Gmail, Slack, Figma, or MCP authorization.
- No global PATH or shell-profile edits.
- No forced React/Zanaat loading in non-React, non-integration work.
- No change to the immutable v1.0.2 tag or assets.
- No claim that every host surface has equivalent plugin capabilities.
