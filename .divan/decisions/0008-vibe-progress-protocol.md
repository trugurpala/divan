# ADR 0008: Calm, evidence-bound progress for vibe coders

## Status

Accepted for v0.17.1 implementation on 2026-07-29.

## Context

Divan can coordinate a large amount of engineering work, but raw command names,
file paths, subagent activity, hashes, and test logs make the conversation feel
like a terminal. The primary user needs a calm view of what is happening, why
it matters, and what comes next without losing the evidence boundary between
planned, implemented, verified, merged, published, and live-verified states.

Codex, Claude Code, and other hosts own their chat user interface. Divan can
govern the language its skills and commands use, but it cannot directly add
native progress widgets to a host application.

## Decision

1. `plugins/sadrazam/skills/sadrazam/references/vibe-progress.md` is the single
   source for substantial user-facing progress communication.
2. The stable semantic states are received, inspecting, implementing,
   verifying, publishing, completed, and blocked. The contract provides
   English and Turkish labels and uses the user's language without mixing them.
   Blocked is reserved for a real need for user action, new authority, or an
   external-state change.
3. Progress is reported before tool use and at meaningful phase changes,
   important decisions, real blockers, or after 45–60 seconds of otherwise
   silent work when new information exists. Commands, retries, files, and
   subagents are not narrated one by one.
4. A structured update may use at most three semantic parts—current, learned,
   and next—with English (`Current`, `What I learned`, `Next`) or Turkish
   (`Şu anda`, `Ne öğrendim`, `Sırada`) labels matching the user's language. A
   natural single sentence remains preferred.
5. Code-ready, tested, GitHub-sent, main-merged, published, live-verified, and
   not-verified are separate semantic evidence claims with English and Turkish
   labels. They follow the user's language, and a later claim is forbidden
   until its evidence exists.
6. Status never depends only on color, emoji, metaphor, or an invented
   percentage. Secrets, hidden reasoning, raw logs, and private scratch work
   remain outside the user-facing progress stream.
7. Sadrazam and the public `/divan`, `/ferman`, `/sefer`, `/teftis`, `/yayin`,
   `/defter`, and `/vezir` entry commands link to the same contract instead of
   copying it. Every command resolves the contract from the loaded-plugin root,
   never the user-controlled working directory.
8. This change adds no runtime module, daemon, hosted control plane, MCP server,
   external repository, or third-party dependency.

## Consequences

- The contract directs the loaded host agent to show the outcome and next
  meaningful state while keeping detailed engineering work in the background.
- Technical evidence remains available in the final handoff or a focused
  blocker explanation without dominating routine progress.
- Hosts that load the updated Sadrazam package receive one consistent
  communication contract; Divan does not claim control over native host UI.
- Contract and public-surface tests prevent mechanical drift. This release does
  not claim a new real-agent A/B result; a later behavioral eval may add
  redacted real-host transcripts without turning private reasoning into an
  artifact.
