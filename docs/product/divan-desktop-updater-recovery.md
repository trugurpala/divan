# Divan Desktop Signed Updater Recovery

This document defines the recovery and rollback policy for the first stable Windows updater.

## Non-negotiable rules

- Tauri updater signature verification is mandatory and is never disabled for recovery.
- Stable updater metadata and artifact URLs are HTTPS-only.
- A failed signature, malformed feed, source-mismatched promotion manifest or unavailable update fails closed; the currently installed version remains authoritative.
- Stable clients keep Tauri's monotonic version behavior. An older signed version is not silently offered as a downgrade.
- Production private signing material is never used by PR updater tests. CI uses an ephemeral updater key and a localhost-only test configuration.

## Normal upgrade

1. Keep the currently installed version running.
2. Publish the next version's signed NSIS updater artifact and exact Tauri `.sig`.
3. Generate `latest.json` and the promotion manifest from that exact installer/signature pair.
4. Publish the feed and artifact over production-controlled HTTPS.
5. The client checks the feed only on explicit operator action and installs only after a second explicit confirmation.
6. Signature verification must succeed before the updater installation is accepted.

## Failed or tampered update

If signature verification or updater installation fails:

1. Do not modify updater trust settings.
2. Do not replace the feed with an unsigned artifact.
3. Keep the last installed version in service.
4. Remove or replace the bad feed entry.
5. Rebuild or recover the intended release, sign the replacement artifact with the protected updater key and publish a corrected feed.
6. Retry the normal signed update flow.

The Windows updater E2E gate proves this behavior by offering a tampered N+2 signature to N+1, requiring rejection, verifying N+1 remains installed, then recovering only with the valid signed N+2 artifact.

## Rollback policy: roll forward, never bypass signatures

Divan does not use updater downgrade mode as an emergency escape hatch. If a released version must be functionally rolled back:

1. Check out the last known-good source state or create the required revert commit.
2. Assign a version greater than the currently deployed version.
3. Run the full acceptance and stable release gates on that reverted source state.
4. Produce a new Authenticode-signed NSIS artifact and mandatory Tauri updater signature.
5. Generate a new source-bound updater feed and promotion manifest.
6. Publish it as a normal higher-version signed update.

Example: if `1.3.10` is bad and `1.3.9` contained the desired behavior, the recovery release is not a downgrade to `1.3.9`; the known-good code is promoted as a new higher version such as `1.3.11` after all release gates pass.

The updater E2E gate additionally serves the older valid N artifact to installed N+2 and requires the updater to report no update. This protects the monotonic stable policy.

## CI evidence

`scripts/windows_desktop_updater_e2e.ps1` uses an ephemeral Tauri updater key and a temporary localhost feed to prove the real updater runtime without production secrets. The temporary configuration alone enables Tauri's insecure-transport test option; committed production configuration does not.

The evidence JSON must be bound to the exact Git source commit/tree and report PASS for:

- valid signed N -> N+1 upgrade,
- tampered N+2 signature rejection,
- unchanged N+1 after the rejected update,
- valid signed forward recovery to N+2,
- older N not offered as a downgrade,
- mandatory signatures,
- production transport policy remaining HTTPS-only.

A stable candidate may not proceed until this updater E2E gate passes.
