# ADR-0009: MIT for firmware and tooling; CERN-OHL-P-2.0 for hardware designs

- Status: Accepted
- Date: 2026-11-03, updated 2026-11-05

## Context

Kokeb Labs publishes drivers, libraries, tooling and, later, hardware designs as open source, and wants them used
in products, including closed ones, without a licence question. Mixed licences complicate kb-core and firmware
images, which combine many drivers into one binary. Hardware designs need a licence written for hardware.

## Decision

- Every firmware, library, driver and tooling repository is MIT, with the MIT text in `LICENSE` and `MIT` in the
  README and any package metadata.
- Hardware designs (schematics, layouts, mechanical files) are CERN-OHL-P-2.0, the permissive variant, with the
  licence text in that repository's `LICENSE`.
- Contributions come in under the repository's licence with a DCO sign-off; there is no CLA
  ([ADR-0015](0015-solo-maintainer-governance.md)).
- The licences cover the work, not the Kokeb Labs name or logos; those are covered by the
  [trademark policy](../../TRADEMARKS.md).

## Consequences

- One licence for all code and every firmware image; products can use it without releasing their own code.
- Code copied in from elsewhere must be MIT compatible; third-party code keeps its own licence in `third_party/`
  with its notice.
- A fork may use the code freely but not the name; unbranded drivers make that easy.
