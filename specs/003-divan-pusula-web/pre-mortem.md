# Divan Pusula Pre-Mortem Contradiction Register

**Feature**: `003-divan-pusula-web`  
**Plan**: `2026-08-23.1`  
**Rule**: This register does not amend `.pusula/plan-lock.json`. A locked architecture choice changes only after the plan's acceptance-test contradiction rule is satisfied.

## Status vocabulary

- `NOT_APPLICABLE`: the locked plan does not make the challenged assumption.
- `CONSTRAINT`: the finding is valid and becomes an implementation rule without changing the locked architecture.
- `PENDING_TEST`: the claim may require a future architecture amendment, but only a representative acceptance test can authorize that amendment.
- `BLOCKED`: implementation must not cross the affected task until the named proof exists.

## Register

| ID | Claim | Status | Pusula decision | Required proof |
|---|---|---|---|---|
| PM-001 | Every runner must support identical public-Fulcio keyless trust | NOT_APPLICABLE | Pusula 1.0 does not mandate Fulcio or identical trust level. Provenance adapters must declare a trust tier and issuer/key method rather than pretending all runners have equal trust. | Before any Fulcio adoption, prove each target runner's issuer/key flow and record the trust tier. |
| PM-002 | Ephemeral CI loses Dagger cache | CONSTRAINT | Dagger cache is acceleration only. Pipeline correctness MUST hold with an empty cache. Hosted CI may use cold cache, persistent self-hosted engine storage, or Dagger Cloud after cost/latency evidence. | Run the same gate set cold and warm; results must be equivalent. Measure cache hit and wall time separately. |
| PM-003 | Long-lived services cannot live in GitHub-hosted Actions | CONSTRAINT | GitHub/Forgejo workflow YAML is a thin trigger. Mizan/PostgreSQL/Hatchet/OpenHands control services must live on persistent service infrastructure. CI jobs are disposable execution only. | Architecture/E2E test must prove control services survive runner teardown and that a hosted-runner job is never the service authority. |
| PM-004 | Hatchet workers used as CI runners create dual orchestration | CONSTRAINT | Forbidden topology. Hatchet owns durable workflow state; RunnerProvider owns disposable code execution. A Hatchet worker may dispatch a RunnerProvider job but must not be the disposable repository runner itself. | Integration test: killing a RunnerProvider job must not kill Hatchet orchestration state; retry creates a fresh runner attempt. |
| PM-005 | ACP is agent-to-agent orchestration | CONSTRAINT | Pusula MUST NOT assign agent-to-agent semantics to ACP. Pusula/OpenHands acts as the client/control surface and talks to an ACP coding-agent process such as Codex or Claude. Multi-agent coordination remains Mizan/Hatchet responsibility. | ACP contract test must launch one supported ACP agent through the client boundary and show that no peer-agent routing assumption is required. |
| PM-006 | Bit-for-bit reproducibility is fragile | PENDING_TEST | Reproducibility is evidence, not a slogan. If a release profile claims bit-for-bit output, base images/toolchains/timestamps must be pinned and a repeated clean-build digest test must pass. | Two clean builds from the same source identity must produce the claimed equal digest before the claim can enter policy. |
| PM-007 | pgmq and Hatchet create two queue authorities | NOT_APPLICABLE | pgmq/Supabase Queues are not part of the locked canonical stack. Do not add a second durable-work queue without a GoalRevision and ownership ADR. | If introduced later, prove every message class has exactly one queue owner. |
| PM-008 | AI speed or LOC is being treated as completion | CONSTRAINT | LOC is diagnostic only. Completion is acceptance evidence. Task 39 measures 12 representative tasks × 3 runs and records VERIFIED/PARTIAL/FAILED/UNKNOWN, cost, elapsed time, and human intervention. | Benchmark protocol plus per-run cost/latency/intervention telemetry. |
| PM-009 | Hatchet hard sticky/affinity can strand work | PENDING_TEST | Pusula 1.0 must not require hard sticky assignment for correctness. Prefer replayable/stateless work; any affinity feature remains an optimization until proven stable with fallback. | Worker-loss test must show recovery on another compatible worker or explicit BLOCKED state within a bounded timeout. |

## Locked topology guardrails

1. **One canonical durable brain:** PostgreSQL/Mizan owns product facts, decisions, audit and deployment history.
2. **One durable workflow owner:** Hatchet may own retry/wait/resume state; CI providers do not.
3. **One disposable execution boundary:** RunnerProvider executes untrusted repository work in disposable isolation.
4. **One pipeline definition:** Dagger defines checks; provider YAML only triggers them.
5. **ACP is a client-agent transport:** never use the phrase `ACP agent-to-agent` as an architecture guarantee.
6. **Cache is never evidence:** a warm cache may improve speed but cannot change pass/fail meaning.
7. **Provenance is tiered:** evidence must record how it was signed/attested and by which trust root; no fake equivalence across environments.
8. **No second queue by accident:** adding pgmq, Celery, RabbitMQ, NATS or another queue requires an explicit ownership decision.
9. **No long-lived authority in hosted Actions:** hosted CI may run jobs, not own Mizan/Hatchet/OpenHands service state.

## External evidence observed on 2026-08-23

- GitHub documentation: GitHub-hosted job execution limit is six hours; self-hosted limits differ.
- Dagger documentation: CI runners are commonly ephemeral; cold cache is valid, persistent cache is optional acceleration, and correctness must not depend on a warm cache.
- Agent Client Protocol documentation: ACP standardizes client/editor-to-coding-agent communication.
- OpenHands Agent Canvas documentation: Agent Server can spawn Claude Code, Codex and Gemini ACP processes and relay turns over ACP.
- Hatchet documentation: durable tasks checkpoint waits/child execution and can resume after worker interruption.

These observations are research evidence only. They do not substitute for Pusula's own acceptance tests when the locked-plan change rule requires test proof.
