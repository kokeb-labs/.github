# Release

How Kokeb Labs repositories are versioned, tagged and released, how tested sets become release trains, and the
order a release wave follows. Decisions: [ADR-0007](adr/0007-submodule-pinning-and-tags.md) and
[ADR-0013](adr/0013-kb-core-monorepo.md).

## Versions

- **Independent SemVer per repository**, starting at `0.1.0`. Drivers change at different rates, so a lockstep
  version would force empty releases. The combinations that are tested together are named by release trains
  instead ([Release trains](#release-trains)).
- **One version for all of kb-core.** `kb::utils`, `kb::rtos`, `kb::interfaces` and `kb::handlers` are released
  together under kb-core's version, even when they are installed as separate packages.
- **0.x makes no API stability promise.** A breaking change bumps the minor (`0.1.0` → `0.2.0`); a fix or an
  addition bumps the patch (`0.1.0` → `0.1.1`). `1.0.0` is declared per repository, by ADR, when its API is meant
  to hold.
- **`ci-tools` is the exception**: it is at `1.x` with a moving major tag (`v1`) that callers pin, and follows its
  own versioning page.
- **One version source** per repository: `cmake/<chip>_build_settings.cmake` in a driver,
  `cmake/kb_build_settings.cmake` in kb-core. The generated version header, `driver.yml`, an `idf_component.yml`
  where one exists, and any hand-written copy are derived from it or checked against it.

## Licence in a release

Every firmware and tooling release is MIT; a release of a hardware design is CERN-OHL-P-2.0
([ADR-0009](adr/0009-licensing.md)). Release notes do not grant use of the Kokeb Labs name or logos
([trademark policy](../TRADEMARKS.md)).

## Tags and release candidates

- Tags are `vX.Y.Z` on a commit that is on `main` (or on `release/x.y` for a maintenance release). Release
  candidates are `vX.Y.Z-rc.N`. The `release-tags` ruleset protects every `v*` tag on public repositories.
- **A release is a named, immutable snapshot** that meets all of:
  - CI was green on that commit with the pinned ESP-IDF;
  - the changelog section for the version is complete;
  - it builds with `add_subdirectory()` and with `find_package()` (`<chip>::<chip>` for a driver, `kb::<part>` for
    kb-core);
  - the release notes state its bench status: the MCU, board and test list it ran on, or **CI-only**.
- A repository that no board has run yet can only be released as CI-only, and MAY skip the release candidate.
- A release candidate is promoted by tagging **the same commit** `vX.Y.Z`. If anything changed, the next candidate
  is `-rc.N+1`.

## Changelog

Every repository has a `CHANGELOG.md` in [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) form:

```markdown
# Changelog

## [Unreleased]

### Breaking

- `Initialize()` now returns `Result<void>` instead of `bool`.

### Added

- `ReadFifoLevel()`.

### Fixed

- Bus errors during `ReadPressurePa()` were reported as `Ok` with a stale value.

## [0.1.0] - 2026-11-17
```

- `## [Unreleased]` is always the first section, and every PR that changes behaviour adds to it.
- Section headings are exactly `### Breaking`, `### Added`, `### Changed`, `### Deprecated`, `### Removed`,
  `### Fixed`, `### Security`, in that order, each only when it has entries.
- **Any breaking change is listed under `### Breaking`**, with what a caller has to change. A PR labelled
  `breaking` without a `### Breaking` entry is not merged.
- Released sections are `## [X.Y.Z] - YYYY-MM-DD` and are not edited afterwards except to fix links.
- Entries describe the effect for a user of the repository, not the commits.
- The release body is the changelog section, not generated notes.

## Release automation

These workflows come from `ci-tools` (`kokeb-labs/ci-tools/.github/workflows/<name>.yml@v1`). Until a repository
has them, a maintainer does each step by hand and checks the same conditions.

| Workflow | Does |
| --- | --- |
| `prepare-release` (manual, input `version`) | Normalises changelog headings, rolls `## [Unreleased]` into `## [X.Y.Z] - <date>`, bumps every version declaration (build settings, `driver.yml`, hand-written headers), and opens a `Release vX.Y.Z` PR. Merging it tags the merge commit. |
| `release.yml` (on a `v*` tag) | Fails if the tag does not match the declared version or the commit is not on `main` / `release/*`; creates the GitHub Release with the changelog section as the body; for products, attaches `.bin`, `.elf`, `sha256` and `sdkconfig` and fails if any is missing. |
| Docs publish (on a `v*` tag) | Publishes the versioned docs with `kokeb-docs`. A `-rc` tag publishes without moving the `latest` alias. |
| Pin check | Checks each submodule against a release tag and the manifest or `catalog/compat.yml`: warns on PRs to `main`, fails on `release/*` and tag pushes, and checks the tagged commit is on `main`. |
| Bump bot | Opens a pin-bump PR in kb-core when a pinned driver tags a release. |

Tags that trigger other workflows are pushed with a GitHub App token, not the workflow token. Release workflows
call reusable workflows at `@v1`, never `@main`.

## Pins and the manifest

- kb-core includes each driver as a submodule in `drivers/driver-<chip>/`, pinned to a **release tag commit**. The
  ESP-IDF component registry is not used for the stack (most drivers are not IDF components, and the host and
  STM32 builds need a non-IDF path). Decision: [ADR-0007](adr/0007-submodule-pinning-and-tags.md).
- kb-core is the bill of materials for the drivers: `catalog/compat.yml` lists the version of every driver it pins,
  and its release notes repeat it.
- Board HALs and products pin kb-core and `kb-hal-common` the same way, and carry a `version_lock.txt` manifest,
  one line per submodule:

  ```text
  REF_kb-core=v0.1.0@3f2a9c1e5b7d...
  REF_kb-hal-common=v0.1.0@9be0d4c7a1f2...
  ```

- The firmware reports the tag and SHA of every submodule it was built from, and the release train.

## Release trains

A release train is a tested set of one kb-core version and the driver versions it pins, named `kb YYYY.N`
(`kb 2026.1`, then `kb 2026.2`). A user who picks a train gets a combination that was built and tested together.

- A train is cut from a kb-core release: the train's content is that release's `catalog/compat.yml`.
- `catalog/compat.yml` is built from each pinned driver's `driver.yml` ([driver.md](driver.md#metadata-driveryml)):

  ```yaml
  train: kb 2026.1
  kb_core: 0.3.0
  drivers:
    zp100:
      version: 0.2.0
      bus: [i2c]
      mcus: [any]
      kb_core_min: 0.1.0
    ws2812:
      version: 0.1.1
      bus: [pio]
      mcus: [esp32]
      peripheral: RMT
      kb_core_min: 0.2.0
  ```

- The file drives three things: the MCU gate table in `cmake/kb_build_settings.cmake` (generated from the
  `mcus` and `peripheral` fields, [layers.md](layers.md#mcu-specific-code)), the planned `kb` command-line tool,
  and the planned web configurator. CI fails when the gate table and the file disagree, or when a pinned driver's
  `kb_core_min` is newer than kb-core.
- A train is announced in kb-core's release notes and on the docs site with its bench status, like any release.
- Trains are not patched. A fix produces a new kb-core release and a new train.

## How a change reaches a product

A change to a lower layer reaches a product in steps, one PR per repository, each merged before the next is
opened:

1. Change the driver (for example `driver-pcal95555`) and merge. Tag a release if the change is meant for
   consumers.
2. In kb-core, bump the driver's submodule to that tag, update `catalog/compat.yml`, and update the handler if the
   API changed.
3. Release kb-core; the release names the new train.
4. In the board HAL, bump `lib/core` (and `lib/common` if `kb-hal-common` changed).
5. In the product, bump the HAL.

Never point a submodule at an unmerged branch, and never edit code inside a submodule checkout of a parent
repository; make the change in the submodule's own repository first.

## Release order

A release wave goes bottom-up. Each layer is re-pinned to the tags under it before it is tagged.

| Step | Repositories | Notes |
| --- | --- | --- |
| 0 | `ci-tools` | The release automation above, released first |
| 1 | Every driver and standalone library (`pincfg`), in parallel | Drivers a board uses go through an rc; CI-only drivers MAY go straight to the release |
| 2 | kb-core | Release notes list each pinned driver version; names the train |
| 3 | `kb-hal-common` | |
| 4 | Board HALs, in their product organizations | After their bench lists pass |
| 5 | Products | Firmware releases with binaries; NVS or partition changes carry the erase or migration step |

## The stabilisation gate for a wave

1. **Hygiene PRs**: versions, changelog headings, install and export gaps, automation gaps, `driver.yml`.
2. **Tag `-rc.1` bottom-up** in the order above.
3. **Bench** on real boards: the bench lists from the merged PRs, on the boards named in the train's test list.
4. **Promote** the same commits to `vX.Y.Z` if nothing failed, or cut `-rc.2` with the fixes.

The per-repository steps are in the [release checklist](checklists/release.md).
