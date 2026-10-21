# Changelog

## Unreleased

- Make the order-race grader catch the same unsafe read-modify-write pattern
  through `read_text`, `read_bytes`, and built-in `open`; test red and green controls.
- Add a reproducible order-concurrency task and independent grader; publish the
  measured parity with a no-skill control and the automatic-activation limit.
- Reject malformed SemVer manifest versions, including leading-zero numeric
  identifiers, empty dot-separated labels, and non-ASCII digits.
- Declare the local executor required by the Codex skills-only workflow and
  validate it in the package contract. Clarify that installation cannot grant
  project file or command permissions.
- Explain how to verify first-use skill activation and record the current
  execution-policy blocker separately from model task success.

## 2.0.0-alpha.5 — 2026-10-22

- A public task-report form collects sanitized real-world outcomes and checks.
- Editable Turkish overview and first-use cards with a launch kit provide accurate, reusable promotion assets.
- The launch kit installation link targets the actual README heading; the remote portable-skill installation path has a fresh-project check.
- The GitHub Pages project site explains both installation routes. Listing metadata now links to the live site, support, and the published data-handling notice.

## 2.0.0-alpha.4 — 2026-10-22

- First-use guidance identifies the project chat, offers a concrete starting
  request, and directs authorized development requests from plan to implementation
  and current checks. Model behavior still needs a real task trial.
- The source repository includes an optimized GitHub social preview image.

## 2.0.0-alpha.3

- One Codex plugin with seven focused skills for understanding a repository,
  implementing changes, debugging, reviewing, verifying, and continuing work.
- Natural-language guidance handles mixed technical terms, meaningful progress
  updates, status interruptions, and questions that change the result or scope.
- Bilingual getting-started instructions cover installation, first tasks, updates,
  and troubleshooting without making users select internal skills.
- The same seven Agent Skills can be installed in compatible coding agents through
  a pinned optional installer. Host-neutral instructions, relative companion links,
  and per-skill MIT notices keep the portable source usable outside Codex.
- A compatibility guide distinguishes installation checks, host discovery, and
  real task execution rather than claiming universal model or editor support.
- Capability discovery distinguishes installed skills, configured connections,
  callable tools, live services, and candidates. Existing integrations and low-code
  options are evaluated by project fit and ongoing maintenance cost.
- Concise project records and an on-demand 50-point reference library support
  continuation and source-based decisions.
- Standard-library validation and deterministic packaging check file boundaries,
  supported local Markdown links, required notices, and unexpected package content.
- A repeatable isolated check verifies an exact Git tree in a temporary workspace,
  reporting source identity, test output, and package hashes.
- Linux and Windows CI cover the full mechanical test suite.

The package is a maintained development prerelease. Mechanical checks and bounded
task trials are reported separately; they do not establish comparative model quality,
equal performance in every language, or an OS/network sandbox for untrusted code.
