# Layers

The Kokeb Labs stack, what each layer promises to the one above, what it may depend on, and which includes are
allowed. The per-layer pages give the detail; this page is the contract between them.

## The stack

```text
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │ Product app            product repository, product org namespace <board>::app│
 │   uses the HAL facade and managers, kb::rtos, the kb-core logger             │
 ├──────────────────────────────────────────────────────────────────────────────┤
 │ Board HAL              board HAL repository, product org  namespace <board>  │
 │   board config, pin table, board managers, on kb-hal-common (kb::hal)        │
 │  ┌────────────────────────────────────────────────────────────────────────┐  │
 │  │ Platform bind      bsp_bind/<family>   creates the MCU family's objects│  │
 │  └────────────────────────────────────────────────────────────────────────┘  │
 ├──────────────────────────────────────────────────────────────────────────────┤
 │ kb-core handlers       kb-core/handlers/<chip>, handlers/common  namespace kb│
 │   one handler per chip: lock, lifecycle, error mapping, VisitDriver          │
 ├──────────────────────────────────────────────────────────────────────────────┤
 │ kb-core interfaces     kb-core/interfaces: base/ (Base*), mcu/<family>/      │
 ├──────────────────────────────────────────────────────────────────────────────┤
 │ kb-core rtos           kb-core/rtos: the only RTOS access                    │
 ├──────────────────────────────────────────────────────────────────────────────┤
 │ kb-core utils          kb-core/utils/general, utils/canopen                  │
 ├──────────────────────────────────────────────────────────────────────────────┤
 │ Chip drivers           driver-<chip>, in kb-core/drivers/ as submodules      │
 │   platform-free C++20 templates on a CRTP port            namespace <chip>   │
 └──────────────────────────────────────────────────────────────────────────────┘
```

Dependencies point down only. A layer MUST NOT include, link or call anything above it, and the submodule graph
MUST stay acyclic: product → board HAL → kb-hal-common and kb-core → drivers.

Inside kb-core the direction is fixed: `utils` ← `rtos` ← `interfaces` ← `handlers`. Each part MAY depend on the
parts to its left and MUST NOT depend on the parts to its right. The four parts are separate CMake targets
(`kb::utils`, `kb::rtos`, `kb::interfaces`, `kb::handlers`), so a wrong include fails to link
([library.md](library.md#kb-core-build)).

Drivers depend on nothing in kb-core, and kb-core's `utils`, `rtos` and `interfaces` do not depend on drivers.
They meet in the handler, where an adapter implements a driver's port with `Base*` calls.

## What each layer promises and depends on

| Layer | Promises to the layer above | Depends on | Page |
| --- | --- | --- | --- |
| Chip driver | The chip's full feature set as typed calls returning `Result<T>`; no I/O before `Initialize()`; no heap, no platform code | The C++ standard library (freestanding subset) and its own port | [driver.md](driver.md) |
| utils | Platform-free helpers, `kb::Status`, and CANopen frame builders | The C++ standard library | [library.md](library.md) |
| rtos | The only mutex, delay, thread, queue and timer types; the same API on FreeRTOS, ThreadX and none | utils; the selected RTOS, only inside its backend folder | [library.md](library.md) |
| interfaces | `Base*` peripheral classes with the same behaviour on every MCU family; `ToStatus()` for every error type; the monotonic clock | utils, rtos; the vendor SDK, only inside `mcu/<family>/` | [library.md](library.md) |
| Handler | A thread-safe, typed API per chip returning `kb::Result<T>`; `VisitDriver()` for the rest; diagnostics | Drivers, `Base*`, rtos, utils | [handler.md](handler.md) |
| Platform bind | `Base*` objects for the board's buses and pins, created and destroyed by slot; reset reason, restart, heap figures, LED strip | The MCU family's `Esp*` / `Stm*` / `Host*` classes and SDK | [hal.md](hal.md) |
| Board HAL | One facade with ordered, fail-closed start-up, one manager per board function, `kb::Status` everywhere, one `CollectDiagnostics()` | `kb-hal-common`, handlers, `Base*`, rtos, `pincfg`, its bind | [hal.md](hal.md) |
| Product | The board's behaviour: tasks, protocols, faults | The HAL facade and managers, rtos, the kb-core logger | [product.md](product.md) |

## Three kinds of "specific"

Code is specific to a chip, to an MCU, or to a product. Each kind has one place, and the rules differ:

| Kind | Example | Where it lives | Rule |
| --- | --- | --- | --- |
| Chip-specific | The register map and start-up sequence of a fictional ZP100 pressure sensor | Its own driver (`driver-zp100`) and its handler (`handlers/zp100/`) | Fine there. Nothing outside the driver and its handler knows the chip's registers. |
| MCU-specific | ESP-IDF I2C master calls, the STM32 HAL, the ESP32 RMT peripheral | Only `interfaces/mcu/<family>/` in kb-core (and, above core, a board HAL's `bsp_bind/<family>/` and a product's `platform/`) | The build selects one family and compiles only that folder. Each header there `#error`s in any other build. |
| Product-specific | A board's pin numbers, a product's fault codes, its motor limits, which channels it uses | The product's board HAL or the product repository | Never in kb-core or a driver. A product need becomes a generic extension point there. |

### MCU-specific code

- `KB_MCU=ESP32|STM32|HOST|NONE` selects the family ([library.md](library.md#interfaces)). Only
  `interfaces/mcu/<family>/` for that family is compiled; the other family folders are not on the include path.
- Every header in `interfaces/mcu/<family>/` stops a build for any other family:

  ```cpp
  // interfaces/mcu/esp32/include/kb/interfaces/esp32/EspI2c.h
  #pragma once
  #if !defined(KB_MCU_ESP32)
  #error "EspI2c.h is ESP32 code; this build selects another KB_MCU"
  #endif
  ```

- A driver that needs one MCU's peripheral (WS2812 timing on the ESP32 RMT) is listed in the MCU gate table in
  `cmake/kb_build_settings.cmake`. Enabling it for another MCU stops CMake at configure time instead of failing
  later at link time or on the bench:

  ```cmake
  # <CHIP>:<MCU>:<peripheral>, generated from catalog/compat.yml (release.md)
  set(KB_MCU_GATES
    "WS2812:ESP32:RMT"
  )
  ```

  With `KB_ENABLE_WS2812=ON` and `KB_MCU=STM32`, configure fails with a message naming the gate.
- Differences between variants of one family (ESP32-C6 and ESP32-S3, two STM32 lines) use the vendor's capability
  macros (`SOC_*_SUPPORTED`, the STM32 `HAL_*_MODULE_ENABLED` and peripheral defines) and only inside
  `mcu/<family>/`.

### Product-specific code

Product needs reach kb-core and drivers only as generic extension points:

| Instead of | Use |
| --- | --- |
| `#ifdef MY_PRODUCT` around a channel or a feature | A config mask in the handler or driver `Config` (`channel_mask`, `features`) |
| A hard-coded table of motor or sensor profiles | A profile table the board HAL passes in (`std::span<const Profile>`) |
| A product's own transport or storage in core | A backend interface in `interfaces/base/` that the board HAL implements |
| A product's log format or sink in core | An injected logger: the kb-core logger takes a sink from the HAL |

### The test

Shared code (drivers, kb-core outside `interfaces/mcu/`, `kb-hal-common`) MUST NOT test `ESP_PLATFORM`,
`STM32*`, `__ZEPHYR__`, a board or a product macro, or any similar platform switch.

For any change to kb-core or a driver, ask: **could a second, made-up product with a different board use it
without editing core?** If not, the change is product-specific and belongs in that product's board HAL or
repository, or it needs a generic extension point first.

## Includes

Paths below use the one-root-per-part layout from [naming-and-style.md](naming-and-style.md#include-roots-and-headers)
(`kb/interfaces/...`, `kb/rtos/...`).

| Code in | MAY include | MUST NOT include |
| --- | --- | --- |
| Driver (`inc/`, `src/`) | `<cstdint>`, `<cstddef>`, `<array>`, `<algorithm>`, `<type_traits>`, `<concepts>`, `<limits>`, `<cmath>`, `<cstring>`, `<span>`, `<utility>`, `<optional>`, `<bit>`; its own headers | Anything from kb-core or another Kokeb Labs repository; any vendor SDK, RTOS or `esp_*` header; `<iostream>`, `<cstdio>`, `<string>`, `<functional>`, `<memory>`, `<vector>`, `<map>`, `<thread>`, `<mutex>` |
| `utils/general`, `utils/canopen` | Standard headers; other `kb/utils/` headers | rtos, interfaces, handlers; any RTOS or vendor SDK header |
| `rtos/` | Standard headers; `kb/utils/`; the selected RTOS, only in its backend folder and the `.cpp` files | interfaces; handlers; any HAL or driver |
| `interfaces/base/` | Standard headers; `kb/utils/`; `kb/rtos/`; other `base/` headers | Any `mcu/<family>/` header; any vendor SDK or RTOS header |
| `interfaces/mcu/<family>/` | Its family's SDK; `base/`; `kb/utils/`; `kb/rtos/` | Another family's headers; rtos backend internals |
| Handler (`handlers/`) | Its driver's umbrella header; `kb/interfaces/Base*.h`; `kb/rtos/`; `kb/utils/`; `kb/handlers/common/` | `mcu/<family>/` headers; vendor SDK or RTOS headers; HAL or product headers |
| Platform bind (`bsp_bind/<family>/`) | Everything below it, including `Esp*` / `Stm*` / `Host*` and the SDK | Product headers; another family's bind |
| HAL outside `bsp_bind/` | `kb-hal-common`; handlers; `kb/interfaces/Base*.h`; `kb/rtos/`; `pincfg`; the bind's interface header | Vendor SDK, `esp_*`, FreeRTOS headers; `mcu/<family>/`; driver headers (drivers are reached through `VisitDriver()`) |
| Product outside `platform/` | The HAL's public API headers (facade and managers); `kb/rtos/`; the kb-core logger | Handlers; drivers; `Base*`; `mcu/<family>/`; vendor SDK or raw FreeRTOS |
| Product `platform/` | The vendor SDK, for start-up, partitions, OTA and the console | Handlers and drivers |

Tests and `examples/` may include whatever they exercise; the rules apply to library code.

### How the rules are enforced

- **Drivers**: the host test build compiles every header with `-fno-exceptions -fno-rtti` and no platform include
  paths, so a forbidden include fails to compile.
- **kb-core**: each part is its own target and links only the parts to its left, so an upward include fails. CI
  builds every target with `KB_MCU=NONE` and `KB_MCU=HOST`, and a lint rejects platform macros (`ESP_PLATFORM`,
  `STM32*`, `__ZEPHYR__`) outside `interfaces/mcu/`.
- **HALs**: the boundary lint in `kb-hal-common` rejects SDK, RTOS and driver includes outside `bsp_bind/`, and
  calls that reach a driver without `VisitDriver()`.
- **Products**: the same lint, run over everything outside `platform/`.
- **Everyone**: reviewers check the tables above; a new exception is a change to this page.

## Layer skips are defects

Code that reaches past the layer below it is a defect even when it works, because the skipped layer's lock,
lifecycle or error mapping no longer applies. Fix it by adding the missing call to the layer that was skipped.
Typical cases:

- A manager calling a driver through a handler's `GetDriver()`, which bypasses the handler lock.
- An application calling an `Esp*` class or raw FreeRTOS instead of the facade and `kb::rtos`.
- Middleware including a handler header.
