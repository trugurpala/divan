# Teftiş — istiflenmiş PR birleştirme planı

Date: 2026-08-16
Measured against: `origin/main` at `68e91fd`, PR #165 at `7f7d436`

Plan only. Nothing here was merged, and nothing here authorises a merge.

## What was measured

For each open stacked PR, three counts from git rather than from memory: how
many commits it carries beyond `main`, how many of those are absent from #165
by identity, and how many are absent from #165 by content (`git cherry`, which
catches a rebased or squashed equivalent).

| PR | Branch | Commits past main | Absent from #165 by id | Absent by content |
|---|---|---|---|---|
| #158 | `feat/patron-goal-plan-flow` | 11 | 0 | 0 |
| #160 | `feat/agency-project-lifecycle-v1` | 23 | 0 | 0 |
| #162 | `feat/spec-compiler-v1` | 26 | 0 | 0 |
| #163 | `feat/agency-memory-current` | 6 | 0 | 0 |
| #164 | `feat/plugin-sdk-current` | 4 | 0 | 0 |
| #165 | `feat/agency-os-turnkey-v1` | 66 | — | — |

## Reading

Every one of the five is fully subsumed by #165. None carries a unique commit
and none carries unique content. #165 is a strict superset of the whole stack.

The stack's shape is a chain plus two side branches: #158 → #160 → #162 → #165
by base, and #163 and #164 based directly on `main` but already folded into
#165's history.

## Safe integration order

Because #165 contains everything, there is exactly one integration to perform
and it is #165 itself. Merging the intermediate PRs first would land the same
commits twice and give `main` a history with five interior merge points that
mean nothing.

Recommended:

1. Retarget #165's base from `feat/spec-compiler-v1` to `main`, so its diff is
   the whole delivery against the real target and CI evaluates it as such.
2. Confirm exact-head CI green on that retargeted head.
3. Merge #165 alone, as a merge commit rather than a squash so the 66 commits
   with their evidence trail survive on `main`.
4. Close #158, #160, #162, #163 and #164 with a note pointing at the merged
   #165 commit. They need no merge; their content is already on `main` at that
   point.

## Rollback point

`origin/main` at `68e91fd`. A revert of the single #165 merge commit returns
`main` to it exactly, which is the property a merge commit buys over a squash
here: one revert, one delivery.

## What is not decided here

Whether to merge at all. That is the owner's call and a hard gate in this
campaign. This document only removes the guesswork from how.
