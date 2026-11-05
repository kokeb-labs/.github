# ADR-0007: Drivers pinned in kb-core to release tags; tested sets released as trains

- Status: Accepted
- Date: 2026-11-03, updated 2026-11-05

## Context

The stack is composed with Git submodules. Without tags, declared versions drift apart and a board cannot report
which versions it runs. The ESP-IDF component registry was considered: most drivers are not IDF components, the
HALs include kb-core through CMake, and the host and STM32 builds need a non-IDF path.

Independent driver versions also leave users asking which combination works. They need named, tested sets, and
the build needs to know which drivers work on which MCU.

## Decision

- kb-core includes each driver as a submodule in `drivers/driver-<chip>/`, pinned to a release tag commit
  (`vX.Y.Z`, or `vX.Y.Z-rc.N` during a wave). Board HALs and products pin kb-core and `kb-hal-common` the same
  way.
- Each driver has independent SemVer starting at `0.1.0`; kb-core has one version for all its parts.
- Each driver describes itself in `driver.yml` (bus, supported MCUs, peripheral, minimum kb-core). kb-core builds
  `catalog/compat.yml` from the pinned drivers' files; it is kb-core's bill of materials and generates the MCU gate
  table in `cmake/kb_build_settings.cmake`. A future `kb` command-line tool and a web configurator read it too.
- A tested set of one kb-core version and its pinned drivers is a release train, named `kb YYYY.N`.
- Board HALs and products carry `version_lock.txt` (`REF_<repo>=vX.Y.Z@<sha>`), checked in CI: a warning on PRs to
  `main`, a failure on `release/*` and tag pushes, plus a check that the tag is on `main`.
- Firmware reports the train and the tag and SHA of every submodule.
- Releases go bottom-up, each layer re-pinned to the tags below it.

## Consequences

- A product release names exactly what it contains, all the way down, and a user can pick a train instead of
  choosing driver versions one by one.
- Enabling a driver on an MCU it does not support fails at CMake configure time.
- Moving a driver forward is a pin PR in kb-core; a bump bot opens them.
- Private product repositories are not protected by tag rulesets on the free plan; the CI pin and ancestry checks
  are their only safeguard.
- The registry can be revisited for outside users once 0.x settles.
