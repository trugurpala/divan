# Nizâm-ı Sefer Planning Intelligence Design

## Product decision

Divan remains an auditable Agent Skills distribution and Project OS. The new
planning intelligence belongs inside Sadrazam's portable control plane rather
than in a desktop UI, daemon or separate orchestration framework.

## Inputs

- natural-language intent;
- existing Company OS route;
- bounded project inspection;
- target state: verified, previewed, released or observed;
- optional exact host-reported context window;
- conservative host planning profile when exact capacity is unavailable.

## Outputs

- schema-3 route with deterministic complexity and estimated working set;
- context reserve, handoff point and usable session budget;
- recommended sessions and bounded parallel lane;
- English-canonical campaigns and tasks with Ottoman display labels;
- functional command hierarchy, memory contract and publication obligations;
- SHA-bound `.divan/routes/<goal-id>.json` for durable restart.

## Identity model

Goal identity uses project, intent, target and host-neutral Company OS facts.
Host profile, context size, campaigns and other execution-plan fields do not
change `goal_id`. This permits Claude/Codex handoff without creating two goals.

## Compatibility model

DPS-005 continues to bind exactly `spec.md`, `plan.md`, and `tasks.md`.
`route.json` is stored outside that exact artifact set and its digest is
recorded in `spec.md`. Existing receipt validators and projects remain valid.

## Safety model

- fallbacks are labelled and never claimed as model limits;
- route overwrite is fail-closed;
- parallelism is bounded;
- unknown capacity reduces autonomy;
- all new paths are impact-classified;
- public docs and release manifest move with the code.
