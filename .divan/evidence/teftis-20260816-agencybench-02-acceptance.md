# Teftiş — AgencyBench-02 acceptance, measured rather than reported

Date: 2026-08-16
Project: a disposable local project outside the Divan repository
Application head at the time of these runs: `0c9852a`

Every verdict below comes from a request this harness sent, a row it read out
of the database, or a page a real browser rendered. No gate is satisfied by a
test file existing under a matching name.

## The correctness of the money

Sixteen checks against the running application and its database.

| Check | What was observed |
|---|---|
| Same input, same answer | 125.50 under the same rate gave 0.13 twice |
| Rounding at the edges | zero, small, boundary and a million all came back to two decimals |
| Negative amount refused | answered 400 |
| A retry has one economic effect | the same operation identity twice produced one calculation |
| A retry can read its own outcome | the second call answered 201 with the first result |
| Distinct events are not collapsed | two different identities on one case produced two calculations |
| Four simultaneous identical retries | one calculation, all four answered 201 |
| Identity enforced by the database | a duplicate operation identity was refused by the constraint |
| A correction does not rewrite history | 21 earlier ledger entries unchanged; the ledger grew |
| A correction carries what changed and why | prior value, new value, reason and actor all present |
| A correction is linked to a ledger entry | 1 of 1 |
| The corrected record keeps its original value | it still reads the original |
| Direct edit of a corrected record | answered 405 |
| A later rate change | left an already recorded commission untouched |
| The ledger is a linked chain | 22 entries, sequences unique, each linked to the one before |
| Sequence uniqueness enforced by the database | a duplicate sequence was refused |

### The one real defect, and how it was closed

The first run of these probes failed one check: the same commission event sent
twice produced two calculations and two ledger entries, both answering 201. A
client that retried after a timeout would have doubled the money.

That measurement became a task contract and went to a real Codex attempt.
`REPAIR-LEDGER-IDEMPOTENCY-A001`, 215 seconds, two files changed, committed as
`0c9852a`. The fix added an `operation_id` carried in the body or the
`Idempotency-Key` header, a `UNIQUE(tenant_id, operation_id)` constraint so two
concurrent retries cannot both win a read-then-write race, and a migration for
rows that predate it.

The probe was then extended rather than merely re-run: a retry now has to land
once, two genuinely different operations still have to stay two, four
simultaneous identical submissions have to produce exactly one, and the
database itself has to refuse a duplicate identity. All four hold.

## Backup and restore

Fourteen checks. A fixture was built across two tenants and four roles, then
the store was destroyed and brought back.

| Check | What was observed |
|---|---|
| The fixture covers every table | 2 tenants, 8 users, 5 cases, 5 attempts, 15 audit events, 29 ledger entries, 2 rates, 5 calculations, 2 corrections, 5 documents |
| The backup carries a checksum manifest | 6 files, each with a sha256 |
| The backup verifies its own integrity | the manifest matched every file |
| A tampered backup is refused | verification rejected an altered database file |
| The store was destroyed | the database file was gone |
| The application could not see the destroyed data | its case list came back empty |
| Restore returns every row | every table count identical |
| Restore returns the same business identities | 5 cases matched by tenant, title, status and owner |
| Restore returns the same ledger chain | 29 entries with identical hashes |
| Restore returns the same money | 5 calculations identical |
| The digest matches | `3a09ae2a3b58e379` before and after |
| The restored application serves the data | tenant one saw 3 cases and 17 ledger entries |
| The restored application keeps tenants apart | tenant two saw its own 2 cases and none of tenant one's |

Only the disposable benchmark store was destroyed.

## Browser and security, re-run on the repaired tree

Ten browser checks in a real Chromium, and eleven security checks. Both were
run again after the repair rather than carried forward from before it.

Browser: the sign-in form has accessible names, all four roles sign in, a
manager creates a case from the landing page and sees it listed, a worker
claims from the queue, a read-only role is offered no controls at all, the
reporting view offers nothing destructive, the CSV export answers as
`text/csv`, a 375 pixel viewport produces no sideways scroll, and the first
tab stop is the username field.

Security: unauthenticated access refused, a wrong password issues no session,
role boundaries hold when probed directly rather than through the page that
hides the button, a tenant's identifier space is not readable from outside it,
a recorded attempt cannot be changed, three path traversal shapes return
nothing, document download needs a session, the project declares no
dependencies, and no provider key or private key is committed.

### Two corrections to the harness, recorded because they were mine

The browser run first reported three failures. Before calling any of them a
defect, the routes were read: the application puts each role's controls on its
own landing page rather than at guessable URLs, and the CSV export belongs to
the operations manager rather than the auditor. All three were the harness
driving the application wrong. They were fixed in the harness.

The secret scanner first flagged a variable named `token` holding a freshly
generated session id, then flagged thirty-five lines of synthetic test
passwords. Looking at the actual matches showed three synthetic fixtures and
nothing else. The check now asks whether a real provider key or private key was
committed, and reports the synthetic values rather than failing on them.
