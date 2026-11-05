# ADR-0012: Drivers carry no brand

- Status: Accepted
- Date: 2026-11-05

## Context

A chip driver is the part of the stack most likely to be used alone: in another framework, on another MCU, or in
a fork. An org prefix in its repository name, namespace, CMake target, macros or Kconfig symbols (`xx_<chip>`,
`xx::<chip>`, `XX_<CHIP>_*`) ties it to the org for no technical reason. A fork either keeps a brand it has no
right to, or renames every symbol and breaks its users. Two drivers for the same chip from different sources
would also collide on the chip name only, which is the collision that matters.

## Decision

- A driver repository is `driver-<chip>` (`driver-pcal95555`).
- Its namespace is `<chip>::` only; its class is `<chip>::<CHIP>`; its umbrella header is `inc/<chip>.hpp`.
- CMake: `find_package(<chip>)`, target `<chip>::<chip>`, build settings in `cmake/<chip>_build_settings.cmake`,
  options and macros `<CHIP>_*`. Kconfig: `CONFIG_<CHIP>_*`.
- A driver contains no `kb_`, `kb::`, `KB_`, or any other org prefix, and depends on nothing in kb-core. The one
  mention of kb-core is `kb_core_min` in `driver.yml`, which is metadata.
- The `kb` prefix belongs to kb-core and `kb-hal-common` only.

## Consequences

- A driver is usable and forkable on its own; a fork inherits no brand and needs no renames.
- The trademark policy is easy to follow: the code carries no name to remove.
- kb-core's handlers refer to drivers by chip name (`pcal95555::PCAL95555`, `pcal95555::pcal95555`), which reads
  the same in every project.
- Two packages for the same chip cannot be installed side by side under the same prefix; that is accepted, since a
  project uses one driver per chip.
