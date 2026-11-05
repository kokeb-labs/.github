# ADR-0005: A shared `kb-hal-common` repository

- Status: Accepted
- Date: 2026-11-03

## Context

Board HALs that start as copies of each other drift: in the review, six managers were near-copies, the facades
were near-clones, the platform binds used different shapes and verbs, each HAL's lint missed the other's rules,
and their `ManagerError` enums differed in values, width and namespace. Keeping copies aligned by hand was the
alternative; the drift shows it does not hold.

Board HALs are also product code: their pin tables, chip lists and board-specific managers belong to one product.

## Decision

- `kb-hal-common` in `kokeb-labs` (namespace `kb::hal`) holds `ManagerBase`, `FacadeBase` with ordered,
  fail-closed start-up and one `CollectDiagnostics()`, the six common managers (NVS, LED, GPIO, ADC, temperature,
  comms), one `PlatformBind` interface, the lints, and an example board HAL.
- Board HALs live in the product's organization or repository. A board HAL keeps only its board config, its pin
  table (written with the generic `pincfg` framework), its bind and its board-specific managers.
- `kb-hal-common` is a submodule of each board HAL, pinned to a release tag.
- `kokeb-labs/board-hal-template` will carry the board HAL shell; until it exists, new board HALs start from the
  example in `kb-hal-common`.

## Consequences

- A fix to a common manager lands once.
- A new board starts from `kb-hal-common` and the new-board checklist instead of a copy.
- One more repository to release, between kb-core and the board HALs in the release order.
- The common managers take everything board-specific as configuration and never name a board.
