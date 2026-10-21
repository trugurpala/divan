# Testing and Verification

- Test behavior and contracts rather than internal implementation details.
- For a bug fix, prefer a regression test that fails before the correction and passes after it.
- Keep unit, integration, and end-to-end tests aligned with the risk being proved.
- Do not use snapshots as a default substitute for behavioral assertions.
- Treat flaky tests as unresolved evidence, not a green signal.
- `lint`, `typecheck`, `test`, and `build` are distinct claims; run the applicable real gates before completion.
