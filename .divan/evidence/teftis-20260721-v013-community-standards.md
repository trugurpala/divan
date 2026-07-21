# v0.13.0 local release-candidate evidence

Date: 2026-07-21

## Scope and truth boundary

This record covers local preparation on branch `codex/community-standards-v013`.
The starting feature commit was `1f27cf5856b77c93d94abd7ffa3e39d8e08264ca`;
the merge base was `origin/main` at
`1b277d107cbd18bbce0cc1565c962998bbdd842b`.

No push, pull request, merge, repository setting, ruleset, tag, GitHub Release,
attestation, Pages/Wiki publication, or global host mutation was performed by
this preparation task. Those delivery states remain pending and must be
recorded only after readback evidence exists.

## Baseline integration before version preparation

- `python -m unittest discover -s tests -v`: 212 passed, 2 skipped. The skips
  were the Windows symlink privilege fixture and the POSIX-only shell installer.
- `ruff check .`: passed.
- `mypy scripts evals`: passed; 29 source files checked.
- `python scripts/clean_code.py --check`: passed.
- `.superpowers/sdd/actionlint-1.7.10/actionlint.exe`: passed with no findings.
- `agentskills --version`: 0.1.1; all 41 `plugins/*/skills/*` directories passed.
- `npx --yes @anthropic-ai/claude-code@2.1.212 plugin validate ... --strict`:
  the root marketplace and all five package manifests passed.

An initial focused command named a nonexistent `tests.test_site` module and
therefore produced one unittest loader error after 136 valid tests passed. The
correct modules are `tests.test_site_markup` and `tests/site_testi.py`; the
subsequent discovery run above included the real markup suite and passed. This
was a command-name error, not a product failure.

## Release preparation

- `python scripts/yayin.py --prepare 0.13.0`: succeeded from v0.12.2.
- `VERSION`, both native marketplaces, README files, fallback installers, Wiki
  sources, Pages/site sources, and other manifest-selected version surfaces
  now identify v0.13.0.
- `registry/v1-gates.json` was not changed. `python scripts/v1.py --check`
  continues to report target v1.0.0 with 7/8 evidence gates passed.

## Social preview

- Path: `docs/assets/divan-social-preview.png`
- PNG signature: `89-50-4E-47-0D-0A-1A-0A`
- IHDR: 1280x640, bit depth 8, color type 2 (RGB)
- Size: 908422 bytes (under the 1000000-byte contract)
- SHA-256: `58e93e2be0ca37f9e4f78e51a78a2247a895221ec9e640f2003e6597ccf3b8e0`

The release controller now validates the binary PNG contract directly from
the stdlib; no image runtime dependency was added.

## Final local verification

- `python scripts/hijyen.py --check`: passed after allowlisted generated caches
  were removed with `python scripts/hijyen.py --clean`.
- `python scripts/validate.py`: passed; 5 packages and 41 skills. The two
  existing over-500-line third-party skill-body recommendations remained
  warnings, not failures.
- `python scripts/devral.py --check`, `python scripts/katalog.py --check`,
  `python scripts/v1.py --check`, `python scripts/yayin.py --check`, and
  `python evals/run.py --check`: passed. Publication reports 58 surfaces; eval
  discovery reports 4 skills and 13 cases.
- `python scripts/wiki.py --check`, `python scripts/meclis.py --check`, and
  `python scripts/standartlar.py --check`: passed; Wiki reports 18 pages and
  Meclis reports 1 candidate.
- `ruff check .`, `python scripts/clean_code.py --check`, and
  `mypy scripts evals`: passed.
- `coverage run -m unittest discover -s tests` followed by
  `coverage report --fail-under=60`: 212 passed, 2 skipped, 72% branch coverage.
  This is above both the 60% configured floor and the recorded 64% baseline.
- Local `tests/site_testi.py` against a temporary server for `docs/`: HTTP 200,
  v0.13.0 visible, 5 intents, interactions, 5 packages, 6 phases, mobile layout,
  and zero console errors. Running it against the default live Pages URL first
  correctly found v0.13.0 absent because publication has not happened yet.
- actionlint 1.7.10, skills-ref 0.1.1 over all 41 skills, and Claude Code
  2.1.212 strict validation over the marketplace plus five packages passed
  again after version preparation.
- `git diff --check`: passed.

The version bump exposed two stale test assumptions. The SBOM CLI fixture was
still comparing against hardcoded v0.12.2, and the browser check expected an
old visible repository string removed by the new lifecycle layout. Each failure
was reproduced before its smallest test-only correction: SBOM now reads
`VERSION`, while the browser verifies the visible canonical repository link.

## Pending external delivery

1. Independent whole-branch review with no Critical or Important findings.
2. Ready PR and all green workflow checks.
3. Merge to `main`, then read back exact successful check names.
4. Apply/read back the `main` ruleset with administrator recovery bypass.
5. Verify homepage/social preview, Pages, Wiki, immutable tag, Release assets,
   checksums, SPDX SBOM, and attestations.
6. Run read-only doctor, pinned v0.13.0 dual-host upgrade, rollback verification,
   and confirm all unrelated extensions remain unchanged.

Independent non-owner adoption evidence is still absent, so v1 remains 7/8.
