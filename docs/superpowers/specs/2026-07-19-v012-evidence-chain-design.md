# v0.12 Evidence Chain Design

## Goal

Make the next real Divan evaluation and Codex installation evidence reproducible on
Windows without claiming that either remaining v1 external-evidence gate is closed.

## Decision

The v0.12 candidate will have two bounded components:

1. The Windows installer test will exercise `kur-codex.ps1` and
   `kaldir-codex.ps1` in isolated temporary directories. It must prove the same
   41-skill install, collision backup, manifest-driven uninstall, and restoration
   contract already checked by the POSIX shell test.
2. The eval runner will accept an optional, checked-in-safe provenance JSON file
   and retain it in the public result. The metadata identifies the real agent,
   independent judge, model/version, source commit, and redacted execution
   environment. Secrets, prompts containing private data, and API keys are out of
   scope and rejected by documentation rather than collected.

## Data flow

`metadata.json` is read only when `python evals/run.py --run` is requested. Its
validated object is copied to the public result as `provenance`; the blind mapping
continues to be written only to the separate key file. Without a judge the result
remains `review_required`; provenance does not turn a fixture or contract check
into product evidence.

## Required metadata

The JSON object must contain non-empty strings for `agent`, `agent_version`,
`judge`, `judge_version`, `source_commit`, and `environment`. Optional `notes`
is a non-empty string. Values must not contain an API-key-like `sk-` token. The
schema stays stdlib-only and provider-neutral.

## Non-goals

- Add a provider SDK, API key, or a fake agent/judge implementation.
- Change either pending v1 gate to passed or ready.
- Publish an evaluation result, tag, release, or create a PR before a real run.

## Acceptance criteria

- Windows runs the PowerShell installer lifecycle test instead of skipping it.
- Existing POSIX lifecycle coverage remains unchanged.
- Eval metadata is rejected when missing, malformed, or secret-like; valid
  metadata is retained in the public result and not the blind key.
- The Turkish and English evaluation documentation explains the metadata command
  and the fact that it is provenance, not proof of quality.
- The repository's full validation contract passes on Windows.
