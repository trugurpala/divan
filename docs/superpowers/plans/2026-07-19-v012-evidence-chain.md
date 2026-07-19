# v0.12 Evidence Chain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Windows installer lifecycle coverage and safe provenance to real evaluation records.

**Architecture:** Keep all installer behavior in the existing PowerShell scripts and test it through their public environment-variable contract. Keep evaluation provenance in the stdlib-only runner, validate it at the CLI boundary, and copy only sanitized metadata into the public result.

**Tech Stack:** Python 3 stdlib, Windows PowerShell, unittest, JSON.

## Global Constraints

- Preserve the 41-skill contract and existing POSIX installer coverage.
- Do not add dependencies, credentials, providers, or a real/fake performance claim.
- Keep the blind A/B mapping in `latest.key.json`; public provenance may not reveal it.
- Do not change pending v1 gates without externally supplied, reproducible evidence.

---

### Task 1: Exercise the native Windows installer lifecycle

**Files:**
- Modify: `tests/test_validate.py`

**Interfaces:**
- Consumes: `DIVAN_SOURCE_DIR`, `CODEX_SKILLS_DIR`, and `DIVAN_STATE_DIR` accepted by `scripts/kur-codex.ps1`.
- Produces: a Windows-only unittest that verifies installation, collision backup, uninstall, and restoration.

- [x] **Step 1: Replace the Windows skip with a failing lifecycle test**

Add a `test_powershell_installer_backs_up_collisions` method that builds this
command and expects the native scripts to restore a marker after uninstall:

```python
command = [
    "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
    str(ROOT / "scripts" / "kur-codex.ps1"),
]
```

The test sets `DIVAN_SOURCE_DIR`, `CODEX_SKILLS_DIR`, and `DIVAN_STATE_DIR` to a
`TemporaryDirectory`, asserts 41 `*/SKILL.md` files, creates
`sadrazam/kullanici-dosyasi.txt`, installs a second time, then runs
`kaldir-codex.ps1` and asserts the marker is restored.

- [x] **Step 2: Run the test before implementation**

Run: `python -m unittest tests.test_validate.RepositoryTests.test_powershell_installer_backs_up_collisions -v`

Expected: FAIL because the test does not yet exist.

- [x] **Step 3: Implement the smallest cross-platform test dispatch**

On Windows call the PowerShell test. On non-Windows keep the existing bash test.
Use `subprocess.run(..., check=True, env=env, capture_output=True, text=True)`
for both branches and assert the same marker/backup contract.

- [x] **Step 4: Verify the lifecycle test**

Run: `python -m unittest discover -s tests -v`

Expected: 30 tests pass with no skipped installer lifecycle test on Windows.

### Task 2: Add validated evaluation provenance

**Files:**
- Modify: `evals/run.py`
- Modify: `tests/test_eval_runner.py`

**Interfaces:**
- Produces: `_read_provenance(path: pathlib.Path) -> dict[str, str]`.
- Consumes: optional CLI `--provenance PATH` supplied with `--run`.
- Produces: public result field `provenance` when a valid file is supplied.

- [x] **Step 1: Write failing provenance tests**

Add tests that create `provenance.json` with all six required fields and assert
`result["provenance"] == metadata`, plus a test that omits `judge_version` and
expects `EvalError` mentioning that field.

- [x] **Step 2: Run the focused tests before implementation**

Run: `python -m unittest tests.test_eval_runner -v`

Expected: FAIL because `_read_provenance` and `provenance` are missing.

- [x] **Step 3: Implement strict JSON provenance parsing**

Read UTF-8 JSON using the existing error style. Reject non-object values, missing
or blank required strings, non-string optional notes, and values containing
`sk-`. Add `--provenance` to argparse; reject it without `--run`; pass the
validated object to `run_evaluations`; include it only in the public result.

- [x] **Step 4: Verify runner behavior**

Run: `python -m unittest tests.test_eval_runner -v`

Expected: all eval tests pass, including valid metadata retention and invalid
metadata rejection.

### Task 3: Document an honest reproducible evidence recipe

**Files:**
- Modify: `evals/README.md`
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/OpenAI-ve-Codex-Uyumlulugu.md`

**Interfaces:**
- Consumes: `--provenance` documented CLI contract.
- Produces: a redacted metadata example and an explicit statement that metadata
  cannot close a v1 gate by itself.

- [x] **Step 1: Add a redacted metadata example**

Document this safe shape and command, without an API key:

```json
{
  "agent": "Declared runner",
  "agent_version": "1.2.3",
  "judge": "Independent judge",
  "judge_version": "4.5.6",
  "source_commit": "0123456789abcdef",
  "environment": "Windows 11; redacted local environment"
}
```

```bash
python evals/run.py --run --skill kaynak-kuratori \
  --adapter "python adapter.py" --judge "python judge.py" \
  --provenance provenance.json
```

- [x] **Step 2: State non-claims in every affected public surface**

Say that provenance identifies a real run but does not establish universal
quality or change pending v1 gates; an independent, reproducible result remains
required.

- [x] **Step 3: Run generated-document and full repository checks**

Run: `python scripts/validate.py && python scripts/katalog.py --check && python scripts/v1.py --check && python evals/run.py --check && python -m unittest discover -s tests -v && git diff --check`

Expected: all commands exit 0; v1 external gates remain `pending`.
