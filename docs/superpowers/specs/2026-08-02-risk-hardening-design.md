# Divan Risk Hardening Design

**Goal:** Close the actionable security, documentation, dependency-observation,
and CI-duration risks proven by the 2026-08-02 read-only audit without mixing in
an unrelated runtime rewrite.

## Decision

Divan will use a risk-first, three-part change:

1. Remove unsafe interpretation and incomplete escaping from distributed skill
   code. The brainstorming companion will no longer reflect a session key into
   executable HTML. Vercel Optimize claim patterns will be literal strings,
   Markdown table values will escape backslashes before pipes, package export
   stars will be replaced consistently, and the p5.js template will pin the
   downloaded script with Subresource Integrity.
2. Repair public instructions and durable project state. Every active audit
   example will use the real `--json` interface. BLUEPRINT and the current host
   guide will describe published v1.3.3 rather than an older release target.
3. Keep one canonical test execution in CI. `scripts/verify.py --coverage` will
   replace its unittest child with coverage execution and reporting, so the
   quality workflow does not run the full suite twice. Dependabot will also
   observe the repository's pip development dependencies.

## Boundaries

- No external runtime dependency is added.
- No release tag, GitHub Release, ruleset, account setting, or existing security
  alert is mutated by this change.
- The large `project_os.py`, `engine.py`, and `providers.py` modules are not split
  here. That work needs a separate behavior-preserving design and review cycle.
- Scorecard findings that require independent reviewers, repository age, or a
  repository-security setting remain explicit governance work rather than being
  hidden by a code change.
- Existing public v1.3.3 assets remain immutable.

## Interfaces

- `python scripts/verify.py` keeps its current local behavior.
- `python scripts/verify.py --coverage` runs the same verification sequence but
  substitutes one coverage-instrumented unittest run and a coverage report with
  the repository floor.
- Claim patterns accepted by Vercel Optimize are literal text. A value that looks
  like `/pattern/flags` is no longer executed as a regular expression.
- The Divan impact graph classifies nested skill implementation files and
  `.github/dependabot.yml`; changed paths must not remain unclassified.

## Error and security behavior

- Untrusted token text never enters an inline script.
- Untrusted claim text cannot construct a regular expression.
- Markdown table cells preserve literal backslashes and cannot use an existing
  backslash to neutralize Divan's pipe escaping.
- The remote p5.js resource is accepted only when its SHA-384 digest matches the
  pinned integrity value.
- Coverage mode fails with the existing child exit code and timeout rules; it
  does not introduce a second test process.

## Verification

The work is accepted only when:

- regression tests fail against the original implementation and pass after the
  minimal fixes;
- JavaScript behavior is exercised through Node, not source assertions alone;
- README aliases, Turkish/English contract pages, Wiki inputs, and release
  surfaces remain synchronized;
- Divan impact reports no unclassified changed path;
- `python scripts/verify.py`, `python scripts/verify.py --coverage`, and
  `git diff --check` pass from the isolated branch;
- the pull request's required GitHub checks are green.
