---
name: root-cause-debug
description: Diagnose a bug, regression, failing test, build failure, or incorrect behavior. Use before changing code when the cause has not been demonstrated.
---

# Root-Cause Debugging

1. Reproduce the failure with the smallest credible command or scenario.
2. Capture the observed error and distinguish it from pre-existing noise.
3. Trace the failing path to the owning boundary.
4. Form explicit hypotheses and test the cheapest discriminating hypothesis first.
5. Change code only after evidence supports a cause.
6. Add or strengthen a regression test when practical.
7. Re-run the reproducer, targeted tests, and relevant broader gates.

Do not shotgun-edit multiple suspected causes.
Do not claim a root cause that was not demonstrated.
