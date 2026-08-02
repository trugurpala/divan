# Site Release CTA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the published Divan release a visible, direct and accessible first action on the public site.

**Architecture:** Keep `docs/index.html` and `site/index.html` byte-identical because both are canonical Pages sources. Add one ordinary anchor in the existing first-installation card; it points to GitHub's moving `releases/latest` endpoint, so the installed release stays the authority without duplicating version data. Lock the public contract in the existing static-markup test.

**Tech Stack:** Static HTML/CSS, Python `unittest`, existing Pages deployment.

## Global Constraints

- No runtime dependency, tracking script or new host integration.
- The call to action must use plain Turkish, work with keyboard navigation and remain usable at 390 px width.
- The link must target `https://github.com/trugurpala/divan/releases/latest`, not a mutable branch or a hard-coded old tag.
- `docs/index.html` and `site/index.html` must stay byte-identical.
- Public copy follows `docs/Yazim-ve-Uslup.md`; no unsupported adoption or quality claim.

---

### Task 1: Lock the public Release route

**Files:**

- Modify: `tests/test_site_markup.py`
- Test: `tests/test_site_markup.py`, `tests/site_testi.py`

**Produces:** A regression contract requiring an accessible direct Release link in both Pages sources.

- [x] **Step 1: Add a failing assertion**

Add a test that reads both HTML sources, isolates the hero, and requires:

```python
release_url = "https://github.com/trugurpala/divan/releases/latest"
self.assertIn(release_url, hero)
self.assertIn("GitHub Release’ini aç", hero)
```

- [x] **Step 2: Run the focused test and confirm the expected failure**

Run: `python -B -m unittest tests.test_site_markup -v`

Expected: failure because the hero has no direct GitHub Release URL.

### Task 2: Add the first-installation call to action

**Files:**

- Modify: `docs/index.html`
- Modify: `site/index.html`
- Test: `tests/test_site_markup.py`

**Consumes:** The release URL and label from Task 1.

**Produces:** A visible anchor beneath the first-installation explanation, styled as a real touch target and mirrored in both Pages sources.

- [x] **Step 1: Add the minimal semantic HTML**

Inside the `İlk kez kuruyorum` card, add:

```html
<a class="release-cta" href="https://github.com/trugurpala/divan/releases/latest">GitHub Release’ini aç</a>
```

- [x] **Step 2: Add the minimal shared CSS**

Add `.release-cta` styling that preserves the existing palette, has a 44 px minimum hit area, a visible focus state through the existing global focus rule, and no forced new window.

- [x] **Step 3: Keep the two sources identical**

Copy the completed `site/index.html` content to `docs/index.html` through a patch, then check equality in the existing test suite.

- [x] **Step 4: Run focused static tests**

Run: `python -B -m unittest tests.test_site_markup -v`

Expected: all tests pass.

- [x] **Step 5: Cover the visible browser route**

Require the same named direct Release link in `tests/site_testi.py` and run the
existing test against a temporary local Pages server.

### Task 3: Verify the public-site change

**Files:**

- Verify only: `site/index.html`, `docs/index.html`, `tests/test_site_markup.py`

- [x] **Step 1: Run text and release contracts**

Run:

```powershell
python -B scripts/prose.py --check --json
python -B scripts/release.py --check
git diff --check
```

- [x] **Step 2: Run the repository's canonical verification**

Run: `python -B scripts/verify.py`

Expected: the existing quality sequence passes from a clean worktree.

- [x] **Step 3: Inspect the final diff**

Confirm that the only product change is the direct Release CTA, its supporting style and its regression test; the plan is the only additional project record.

## Self-review

- The plan adds a visible first-installation action, not another installation path.
- It uses GitHub's latest-release endpoint, avoiding a stale hard-coded tag.
- It covers static behavior, source parity, public prose and the canonical verifier.
- It introduces no external dependency, new tracking, new runtime or unsupported host claim.
