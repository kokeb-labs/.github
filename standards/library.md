# Library contract

What the libraries between the drivers and the board HALs provide: the `utils`, `rtos` and `interfaces` parts of
kb-core, how kb-core builds them with its handlers and drivers, and the rules for standalone libraries such as
`pincfg`. Decision: [ADR-0013](adr/0013-kb-core-monorepo.md).

## kb-core layout

```text
kb-core/
├── utils/
│   ├── general/                  include/kb/utils/: Status.h, SoftwareVersion, ring buffers, ...
│   └── canopen/                  include/kb/canopen/: frame builders, CiA 402 helpers
├── rtos/                         include/kb/rtos/; backends in freertos/, threadx/, none/
├── interfaces/
│   ├── base/                     include/kb/interfaces/: Base* classes, Time.h, error lists
│   └── mcu/
│       ├── esp32/                include/kb/interfaces/esp32/: Esp* on ESP-IDF
│       ├── stm32/                include/kb/interfaces/stm32/: Stm* on the STM32 HAL
│       └── host/                 include/kb/interfaces/host/: Host* for host builds and tests
├── handlers/
│   ├── common/                   include/kb/handlers/common/: adapter bases, Delay.h, Logger.h, diagnostics
│   └── <chip>/                   one folder per handler (handler.md)
├── drivers/
│   └── driver-<chip>/            git submodules, each pinned to a driver release tag
├── catalog/compat.yml            built from each driver's driver.yml (release.md)
├── cmake/kb_build_settings.cmake version, options, targets, MCU gate table
├── tests/, examples/, docs/, _config/, .github/, .claude/
└── CMakeLists.txt, README.md, LICENSE (MIT), CHANGELOG.md, AGENTS.md, CLAUDE.md, .gitignore, .gitmodules
```

## Every part of kb-core

- **One CMake target per part**, each with one include root:

  | Part | Target | Include root | Depends on |
  | --- | --- | --- | --- |
  | `utils/general`, `utils/canopen` | `kb::utils` | `kb/utils/`, `kb/canopen/` | The C++ standard library |
  | `rtos/` | `kb::rtos` | `kb/rtos/` | `kb::utils`, the selected RTOS |
  | `interfaces/` | `kb::interfaces` | `kb/interfaces/` | `kb::rtos`, `kb::utils`, the selected family's SDK |
  | `handlers/` | `kb::handlers` | `kb/handlers/` | `kb::interfaces`, `kb::rtos`, `kb::utils`, each enabled driver's `<chip>::<chip>` |

- **Separately consumable**: each target works after `add_subdirectory()` of kb-core and is also installable as
  its own package (`find_package(kb_utils)` → `kb::utils`, and the same for `kb_rtos`, `kb_interfaces`,
  `kb_handlers`). A project that needs only `kb::utils` gets nothing else.
- **One version** for all of kb-core, in `cmake/kb_build_settings.cmake`; every package carries it.
- **One include root per part**: every public header is reached as `#include "kb/<root>/<Header>.h"`. Two parts
  MUST NOT ship headers that resolve to the same include path.
- **No macros that leak**: no `MIN`, `MAX`, `ARRAY_SIZE` or similar in public headers. Use `std::min`,
  `std::size` or a `constexpr` function in the library's namespace. Public macros carry the `KB_` prefix.
- **Namespace** `kb` (or `kb::<area>`). The C-style APIs kept from the code kb-core was built from (`os_*` in
  rtos, the `kb_*_t` types in interfaces) keep their names; new API is C++ in `kb`.
- **Host tests** in `tests/host/` on gcc and clang, and compiled doc snippets in `tests/docs/`.
- **A Contract page** in the docs ([docs.md](docs.md#the-contract-page)), with a section per part.
- C++20, MIT, the org clang configs, no exceptions, no RTTI.
- **Platform-free outside `interfaces/mcu/` and the rtos backends** ([layers.md](layers.md#three-kinds-of-specific)):
  no other file tests `ESP_PLATFORM` or an MCU macro. The `mcu/` implementations and the RTOS backends are
  platform code by purpose; their portable parts (`base/`, the rtos API) still follow the rule.

## utils

### utils/general

Platform-free helpers (`SoftwareVersion`, `VariableMonitor`, `TimestampedVariable`, ring buffers and the like) and
`kb::Status` / `kb::Result<T>` ([errors.md](errors.md)).

- Headers and `.cpp` files; no RTOS, no vendor SDK, no global mutable state.
- A helper that needs a lock or a clock takes it as a parameter or template argument; it does not include
  `kb/rtos/`.
- One guide page per helper: purpose, a compiled example, complexity and memory.

### utils/canopen

CANopen frame builders and CiA 402 helpers over a self-contained `CanFrame`.

- No dependency on interfaces or a CAN driver; the caller sends the frame.
- No allocation; frames are values.

## rtos

The only RTOS access above the bind ([threading-and-timing.md](threading-and-timing.md)).

| Provides | Types |
| --- | --- |
| Locking | `RtosMutex`, `MutexLockGuard`, `CriticalGuard` |
| Delay and time in ticks | `os_delay_msec()`, `OsUtility` helpers |
| Tasks | `BaseThread`, `BaseThreadsManager` |
| Communication | `OsQueue`, `OsEventFlags`, `SignalSemaphore`, `SeqlockSnapshot` |
| Timers | `PeriodicTimer` |

Rules:

- One backend per build: `KB_RTOS=FREERTOS|THREADX|NONE`, which defines exactly one of `KB_RTOS_FREERTOS`,
  `KB_RTOS_THREADX` or `KB_RTOS_NONE`. Only the selected backend folder is compiled. The public API is the same on
  all three; the host tests run the FreeRTOS shim and none.
- Objects are statically allocated (FreeRTOS static API, ThreadX).
- No dependency other than `kb::utils` and the selected RTOS.

## interfaces

The MCU interfaces: abstract `Base*` peripheral classes and their implementations per MCU family.

| Part | Contains | May include |
| --- | --- | --- |
| `base/` | `BaseGpio`, `BaseAdc`, `BaseI2c`, `BaseSpi`, `BaseUart`, `BaseCan`, `BasePwm`, `BaseNvs`, `BasePeriodicTimer`, `BaseTemperature`, `BaseLogger`, `BasePio`, `BaseUsbSerialJtag`, `BaseWifi`, `BaseBluetooth`; `HardwareTypes.h`; `Time.h` (`kb::MonotonicUs()`, declared only) | Standard headers, `kb/utils/`, `kb/rtos/` |
| `mcu/esp32/` | `Esp*` implementations on ESP-IDF, and the ESP32 definition of `kb::MonotonicUs()` | ESP-IDF |
| `mcu/stm32/` | `Stm*` implementations on the STM32 HAL, and the STM32 definition of `kb::MonotonicUs()` | STM32Cube HAL |
| `mcu/host/` | `Host*` implementations for host builds and tests (`HostNvs`, a settable clock) | Standard headers |

A header in `base/` declares; the selected family's `mcu/<family>/` folder defines. The family is chosen by the
build, which compiles only that folder, so no header in `base/` tests a family macro.

Rules:

- `Base*` classes are the one place above the bind with virtual functions: the bind creates the concrete object,
  and everything above holds a `Base*&`. This is the run-time boundary between portable code and the MCU.
- Each `Base*` keeps its `kb_<periph>_err_t` X-macro list and adds `kb::Status ToStatus(kb_<periph>_err_t)`
  following [errors.md](errors.md#interfaces-codes-to-kbstatus).
- `Initialize()` is idempotent and `EnsureInitialized()` lazy; neither allocates after start-up.
- Exactly one family is compiled, chosen by `KB_MCU=ESP32|STM32|HOST|NONE`. `NONE` builds `base/` only, for
  consumers that bring their own implementation or fakes. Every family's sources MUST compile in CI, including
  STM32 (with stub SDK headers if needed).
- Every header in `mcu/<family>/` `#error`s when its family is not the one selected
  ([layers.md](layers.md#mcu-specific-code)).
- A header in `base/` MUST NOT include a file that does not exist on every family.
- Variant differences inside a family use the vendor's capability macros, only in that family's folder.
- A peripheral that only one family has (the ESP32 RMT) gets a `Base*` interface in `base/` and an implementation
  in that family's folder only; the drivers that need it are rows in the MCU gate table.

## handlers

One handler per chip, plus `handlers/common/`: the adapter bases, `kb::DelayUs()` / `kb::DelayMs()`, the
diagnostics header and the logger. The contract is in [handler.md](handler.md).

The logger (`kb/handlers/common/Logger.h`) is the one logging API above the bind. It formats; drivers do not. Its
sink is injected by the board HAL, so kb-core prints nothing on its own and carries no product's log format.

## kb-core build

- kb-core links each enabled driver's `<chip>::<chip>` target from its submodule in `drivers/driver-<chip>/`. It
  does not copy file lists out of a driver.
- `cmake/kb_build_settings.cmake` holds the version, the options, the targets and the MCU gate table; it holds no
  sources of a driver.
- The options:

  | Option | Values | Effect |
  | --- | --- | --- |
  | `KB_MCU` | `ESP32`, `STM32`, `HOST`, `NONE` | Compiles `interfaces/mcu/<family>/` for that family only |
  | `KB_RTOS` | `FREERTOS`, `THREADX`, `NONE` | Compiles that rtos backend only |
  | `KB_ENABLE_<CHIP>` | `ON`, `OFF` | Compiles the handler and links its driver; nothing else turns a handler on |
  | `KB_ENABLE_<FEATURE>` | `ON`, `OFF` | Compiles an optional part (`KB_ENABLE_CANOPEN`) |
  | `KB_BUILD_TESTS` | `ON`, `OFF` | Host tests and doc snippets |

- **The MCU gate**: configure fails when an enabled chip's row in the gate table names another MCU than `KB_MCU`
  ([layers.md](layers.md#mcu-specific-code)). The table is generated from `catalog/compat.yml`, and CI checks the
  two agree.
- Under ESP-IDF the root `CMakeLists.txt` is also the component; Kconfig options are `CONFIG_KB_*` and map onto
  the CMake options in one place.
- FreeRTOS builds run at 1000 Hz ([threading-and-timing.md](threading-and-timing.md#the-1-khz-tick)).

## Standalone libraries

A library that is not part of kb-core (for example `pincfg`, or a utility used outside the stack) lives in its own
repository, is created from `kokeb-labs/driver-template` (`python3 tools/setup.py --kind library`), and follows
the driver root layout ([driver.md](driver.md#repository-layout), [ADR-0011](adr/0011-repository-root-layout.md)):
tool configuration in `_config/`, one root `CMakeLists.txt`, platform code only in `examples/<platform>/`, and an `examples/host/`
program built and run by the host tests. A library meant for ESP-IDF adds the `ESP_PLATFORM` branch of the root
`CMakeLists.txt` (and `_config/Kconfig` if it has options) and an `examples/esp32/`; one that is not has neither.

It is versioned and released like a driver, with one target and one include root.

### pincfg

`pincfg` is a generic, header-only C++20 framework for pin tables: X-macro rows that name the function, the chip
and the drive mode.

- The framework holds no board's pins. Each board HAL carries its own pin table built with it ([hal.md](hal.md#board-config)).
- MCU pin numbers appear only in a board HAL's pin table and its bind.
- A host build with an empty table compiles for tests.
