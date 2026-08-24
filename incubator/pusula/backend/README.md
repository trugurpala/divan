# Pusula Backend Incubator

This directory is the isolated application-spine incubation area for Divan Pusula. It is not part of the Divan Engine runtime.

Locked boundaries:

- Identity: Logto/OIDC. The backend never invents passwords, login codes, or token cryptography.
- Authorization: Pusula Team/Membership rules remain first-party and server-side.
- Canonical state: PostgreSQL via Django models.
- Canonical mutations: domain event + projection + outbox are committed atomically.
- External I/O: never happens inside the canonical database transaction.
- Customer repositories: never execute on the control-plane host.

The target repository remains `trugurpala/divan-pusula`; this incubator exists only until the product repository is bootstrapped with equivalent verified history.
