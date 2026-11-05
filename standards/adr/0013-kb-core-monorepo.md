# ADR-0013: kb-core is one monorepo with four targets and one version

- Status: Accepted
- Date: 2026-11-05

## Context

The code the standard was built from split the core into many repositories: separate utilities, an RTOS wrapper,
an MCU interface wrapper, a pin-config library, aggregator repositories that only collected submodules, and the
core with the handlers. Every change to a low layer took a chain of pin bumps through the aggregators; versions
had to be kept compatible by hand; and headers with the same name in two repositories collided.

The parts are tightly coupled and always released together. Users still need to take only part of it, for example
the utilities on their own.

## Decision

- kb-core is one repository holding `utils/` (`general`, `canopen`), `rtos/`, `interfaces/` (`base/` and
  `mcu/esp32`, `mcu/stm32`, `mcu/host`), `handlers/` (`common`, one folder per chip), and `drivers/driver-<chip>/`
  as git submodules pinned to driver release tags, with `cmake/kb_build_settings.cmake` and `catalog/compat.yml`.
- It exports four CMake targets that are consumable separately: `kb::utils`, `kb::rtos`, `kb::interfaces`,
  `kb::handlers`. Each is also installable as its own package.
- The dependency direction is fixed: `utils` ← `rtos` ← `interfaces` ← `handlers`. Drivers depend on nothing in
  kb-core.
- kb-core has one version number for all of its parts.
- Prefix: namespace `kb::`, macros `KB_`, includes `"kb/..."`, options `KB_MCU=ESP32|STM32|HOST|NONE`,
  `KB_RTOS=FREERTOS|THREADX|NONE`, `KB_ENABLE_<CHIP>`.
- Drivers stay separate repositories ([ADR-0012](0012-unbranded-drivers.md)). Board HALs stay with their products
  ([ADR-0005](0005-kb-hal-common.md)).

## Consequences

- A change across utils, rtos, interfaces and handlers is one PR, tested together.
- No aggregator repositories and no pin chains inside the core; a driver update is one pin PR in kb-core.
- Upward includes fail to link because each part is its own target.
- A user who needs only `kb::utils` still clones kb-core (or installs the `kb_utils` package); that is accepted.
- The rtos layer supports FreeRTOS, ThreadX and none; other RTOS backends need a new ADR.
