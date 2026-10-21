# Choose the implementation layer

Start with the user's complete workflow and the existing project's maturity,
constraints, and accepted quality bar. Small implementation slices are a delivery
method, not permission to replace a real workflow with a demo or fake integration.

## Put each capability in the right place

| Need | First candidate | Evidence before choosing |
| --- | --- | --- |
| Repeatable reasoning or engineering method | A relevant existing skill or concise project instructions | Read its actual instructions and check that its tools are available. |
| Read or change data in an external application | An authorized existing plugin, MCP tool, API, or CLI | Required operation, account/resource identity, permissions, and result. |
| Standard functionality inside application code | Existing framework primitives, then a maintained library | Version compatibility, license, data model fit, integration tests. |
| Forms, CRUD, admin workflows, or internal dashboards | Existing low-code/admin framework or configured service | Real authorization, validation, error states, data ownership, export/migrations, customization, and testability. |
| Persistent shared capability | A matching existing service; self-hosted when required | Deployment identity, current health, capacity, backup/upgrade responsibility, and operational cost. |
| Distinctive behavior that existing options cannot support well | A focused custom implementation | Concrete mismatch and lower total maintenance cost, not preference for rewriting. |

An agent-side tool is not automatically an application's runtime dependency.
Reading an API through MCP does not implement the product's API integration.
A plugin label does not prove a backend exists, and a clickable UI with fixtures
does not prove a real data workflow.

## Compare only serious options

Use the repository first, then current official documentation and a short shortlist,
normally two or three options. An available SAK or equivalent reuse/scouting skill
can support this judgment; it is not a required Divan dependency.

For each serious option, record the source/version, license and attribution,
maintenance evidence, stack compatibility, integration and testing effort,
operating cost, data portability, and one material risk. Include the existing or
custom approach when plausible. Popularity helps discovery; it does not establish
fitness. Respect the user's local hosting policy and existing architecture.

Make a compact decision: **outcome; existing assets; selected approach and why;
material tradeoff; acceptance check; next action**. A small task needs a paragraph,
not another planning document. Ask only about a missing product choice or setup
authorization that changes the result. Use the capability reference for new installs.

If compatibility is uncertain, run a bounded, reversible trial with representative
data in the authorized environment. Check the actual user action, failure behavior,
and persistence where relevant. Label temporary fixtures and discard them from the
shipped path. A promising trial is not a production-readiness claim.

After selection, carry the decision into implementation and current verification.
Reuse the existing project decision/operations document when the choice matters to
future work. Do not keep researching options after the requirement is met unless
new evidence invalidates the decision.
