# v1.0.3 local release-candidate evidence

- Candidate branch: `codex/v110-friendly-control-plane`
- Reviewed head: `8665af84fdc8c2d1eda0def659851e59ac4a9af7`
- Base: `b242f0f`
- Evidence date: 2026-08-01

## Product outcome

The candidate separates one-time setup, plain-language daily use, and
maintenance. A healthy doctor no longer tells an installed user to reinstall;
human output ends with a single `READY` instruction. Machine output preserves
the public string contract with `next_command: ""` when no command is needed.

Host compatibility claims are now surface-scoped. Repository evidence verifies
the Codex CLI lifecycle only. Codex Desktop, IDE extension, and mobile remain
explicitly outside the verified Divan claim until separate canaries exist.

README, Turkish and English guides, and both Pages source mirrors now lead an
installed user to one copyable natural-language decree. The release bootstrap
remains the no-checkout first-install path; the immutable runner remains the
maintenance and recovery path.

## Independent code review

A read-only reviewer inspected base `b242f0f` through candidate head
`80d4699`. No Critical findings were reported. Four Important findings were
resolved before this evidence was recorded:

1. preserve the healthy `next_command` string type rather than making it
   nullable in a patch release;
2. narrow the verified Codex surface from Desktop plus CLI to CLI only;
3. reject list/object surface values without crashing the registry validator;
4. attach an exact recovery command when an invalid terminal journal changes a
   healthy diagnosis to attention.

Regression coverage was added for all four boundaries. The reviewer also
confirmed synchronized README/site mirrors, accessibility contracts, and the
absence of new PATH mutation, runtime dependency, or authority expansion.

## Local verification

The canonical command `python scripts/verify.py` completed successfully in
359.2 seconds on Windows 11:

- 715 tests passed;
- 14 platform-specific tests were skipped as expected;
- 5 packages and 41 skills validated;
- 241 release surfaces validated before adding this evidence surface;
- hygiene, catalog, handoff, v1, release, evaluation, clean-code, and final
  hygiene gates passed;
- `git diff --check` was clean.

The only validator notices were the existing advisory size warnings for
`writing-skills/SKILL.md` and `claude-api/SKILL.md`; they are not new failures
and remain candidates for reference-file extraction in a later bounded change.

Focused real-command readback also passed:

```text
python scripts/divan.py doctor --host codex --ref v1.0.2
codex: healthy
READY: Divan is installed and verified. Start a new agent session and describe your goal.
```

JSON readback returned `status: healthy`, an empty issue list, and
`next_command: ""`.

## Limits

This is local release-candidate evidence, not publication evidence. It does not
claim that v1.0.3 is tagged, released, installed from GitHub assets, live on
Pages/Wiki, or verified on Codex Desktop UI. Those claims require PR CI, merge,
immutable Release asset readback, and live URL verification.
