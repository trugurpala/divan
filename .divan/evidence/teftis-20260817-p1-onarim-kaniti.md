# Teftiş — dört P1 onarımı, RED ve GREEN kanıtıyla

Date: 2026-08-17
Benchmark head before: `9fc2d67` · after: `ce4a4da`
Suite: 79 tests, green, worktree clean

Each repair was driven through Divan's own path: a task contract carrying the
defect and its root cause, compiled context, a real Codex attempt, then the
project's whole suite. Nothing was hand-written.

A passing test proves nothing by itself, so each fix was reverted while its
tests were kept, the suite was run, and the tests that went red were recorded.
Only the source file was reverted; the tests are the instrument doing the
measuring.

## P1-A — ordinary recovery raised a false tamper alarm

**Cause.** `audit_ledger` entries recomputed their payload hash by looking the
payload up again with tenant, event, actor and timestamp. Those four are not
unique. Two leases expiring in one recovery pass wrote two events with the same
four values, both entries resolved to the first row via `LIMIT 1`, and the
second entry's recomputed hash disagreed with its stored one. The ledger
reported tampering where none had happened.

**Fix.** Entries now carry `source_type` and `source_id`, the identity of the
row whose payload they hash, written at append time and read at verification.
Existing databases migrate, with `payload_reference_status` recording honestly
where a legacy reference could not be determined. The verifier was not
loosened: it still recomputes and still refuses.

**RED without the fix.** 13 tests fail, among them `two leases expiring in one
recovery pass leave the ledger valid`, `business-row tampering after collision
recovery names the first bad ledger entry`, and `ledger truncation after
collision recovery is reported against the head anchor`. The last two matter as
much as the first: they show the verifier did not go blind to earn the pass.

## P1-B — an expired lease still carried authority

**Cause.** Ownership was checked route by route, and the checks looked at owner
and tenant but never at `lease_expires_at`. This class of defect had been fixed
four separate times in this project, each time in one route.

**Fix.** One `authorizeCase(user, caseId, action)` decides every owner-scoped
operation, checking tenant, role, ownership and lease validity together, and
expiring a lapsed claim into the queue with its ledger event before answering.
Fourteen call sites route through it. A regression matrix test enumerates every
owner-scoped route and asserts refusal for a non-owner, an expired owner and a
foreign tenant, so the next route added cannot quietly forget the rule.

**RED without the fix.** 10 tests fail, including `every owner-scoped route
applies the same non-owner, expired-owner, and tenant boundary` and `an expired
owner is refused and ordinary claim-next immediately reclaims the recovered
case`.

## P1-C — attempts and documents were not retry-safe

**Cause.** Commission carried an operation identity bound to case and content.
Attempt creation and document upload did not, so one business action retried
after a lost response became two rows and two ledger entries.

**Fix.** The same contract now covers both, with uniqueness enforced at the
database rather than in the handler, so two concurrent identical retries cannot
both win. Same identity with a changed payload or a different case answers 409;
a missing identity answers 400. The HTML form routes carry it too.

**RED without the fix.** 7 tests fail, including the identical-retry cases for
both attempts and documents, both conflict cases, and `attempt and document
mutations require an operation identity in JSON and HTML forms`.

## P1-D — restore left a manifest that no longer described the store

**Cause.** The staged copy was verified against the backup manifest, then
document paths were rewritten inside it, and it was never verified again. The
manifest shipped beside a database that had moved. The destination was also
removed before the copy, so a failure mid-restore left neither the old store
nor a whole new one.

**Fix.** Restore stages beside the destination, relocates inside staging,
generates and verifies a final manifest against the staged result, then
promotes by rename with the previous directory kept until the swap succeeds and
restored if it does not. Identical source and destination are refused outright.
`createBackup` publishes the same way, so a failed backup no longer destroys
the previous good one.

**RED without the fix.** 1 test fails: `backup verification rejects a document
removed together with its manifest entry`.

That is a thinner proof than the other three, so the invariant this repair
exists for was measured directly rather than trusted to the suite: a restore
was run, `verifyBackupIntegrity` was called on the restored directory, and then
a second restore was run over that same live store and verified again.

```
restore directory exists   : true
manifest after restore     : VALID
manifest after re-restore  : VALID
```

Both hold. The manifest describes the store it ships with, and restoring over
an existing store does not leave a half-written one.

## Reading

| Repair | RED without fix | GREEN with fix |
|---|---|---|
| P1-A false tamper alarm | 13 tests | 79 pass |
| P1-B central authorisation | 10 tests | 79 pass |
| P1-C mutation idempotency | 7 tests | 79 pass |
| P1-D two-phase restore | 1 test, plus a direct probe | 79 pass |

Four of four are load-bearing. The suite is green at `ce4a4da` with a clean
worktree, and it was green before the experiment began, so the reds above are
the experiment rather than noise.
