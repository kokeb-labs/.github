# Naming and style

How Kokeb Labs code is named, laid out and formatted. The naming rules are enforced by
`readability-identifier-naming` in the org [`.clang-tidy`](config/.clang-tidy), and formatting by the org
[`.clang-format`](config/.clang-format). Decisions: [ADR-0008](adr/0008-naming.md) and, for drivers,
[ADR-0012](adr/0012-unbranded-drivers.md).

## Prefixes

| Code | Namespace | Macros | Includes | CMake |
| --- | --- | --- | --- | --- |
| A chip driver (`driver-<chip>`) | `<chip>` | `<CHIP>_*`, Kconfig `CONFIG_<CHIP>_*` | `"<chip>.hpp"` | `find_package(<chip>)`, `<chip>::<chip>`, options `<CHIP>_*` |
| kb-core | `kb` | `KB_*`, Kconfig `CONFIG_KB_*` | `"kb/..."` | `kb::utils`, `kb::rtos`, `kb::interfaces`, `kb::handlers`; options `KB_*` |
| `kb-hal-common` | `kb::hal` | `KB_HAL_*` | `"kb/hal/..."` | `kb::hal` |

A driver never carries the `kb` prefix or any other org prefix; the prefix belongs to kb-core and the shared HAL
only.

## Namespaces

| Code | Namespace |
| --- | --- |
| A chip driver | `<chip>` (`pca9685`, `tmc9660`); internals in `<chip>::detail` |
| kb-core | `kb`, or `kb::<area>` (`kb::can`) |
| `kb-hal-common` | `kb::hal` |
| A board HAL | `<board>`; the bind in `<board>::bsp` |
| A product | `<board>::app` |

Namespaces are lower case. `using namespace` is not allowed in headers. Anonymous namespaces are for `.cpp`-local
helpers only.

## Identifiers

| Kind | Style | Examples |
| --- | --- | --- |
| Classes, structs, enums, unions, type aliases, concepts | `PascalCase` | `Zp100Handler`, `Config`, `I2cPort` |
| A chip driver class | the part number | `PCA9685`, `TMC9660` |
| Template parameters | `PascalCase` | `Port`, `Derived`, `SpiType` |
| Functions and public / protected methods | `PascalCase` | `Initialize()`, `ReadPressurePa()`, `SetDuty()` |
| Private methods | `camelBack` | `writeReg()`, `selectBank()` |
| Parameters and local variables | `snake_case` | `channel`, `timeout_ms` |
| Public data members (struct fields) | `snake_case` | `config.ready_timeout_ms` |
| Private and protected data members | `snake_case_` | `initialized_`, `bus_mutex_` |
| Constants (`constexpr`, `static const`, global `const`) | `kPascalCase` | `kNumChannels`, `kDefaultAddress` |
| Enumerators | `PascalCase` | `Error::NotInitialized`, `Oversampling::X8` |
| Macros | `UPPER_CASE`, prefixed with the repository or part | `PCA9685_VERSION_MAJOR`, `CONFIG_ZP100_ODR_HZ`, `KB_ENABLE_PCA9685` |
| Files | as the main type: `PascalCase` in kb-core and HALs (`Zp100Handler.h`); `<chip>_<part>.hpp` in drivers | `pca9685_i2c_interface.hpp` |

Allowed exceptions, also allowed by the tidy config:

- **Datasheet names** in `UPPER_CASE` for register addresses, bit fields and enumerators that mirror the datasheet
  (`MODE1`, `PRE_SCALE`, `GEN_CFG1`), and for `GpioSignal::ACTIVE` / `INACTIVE`.
- **Vocabulary-type members** `ok()`, `begin()`, `end()`, `size()`, `data()`, `empty()`, so `Result<T>` and
  containers read like the standard library.
- **C-style APIs** kb-core keeps: the `os_*` functions in `kb::rtos` and the `kb_*_t` types in `kb::interfaces`.
  New code does not add to them.
- **Host test cases** named `test_<what>` in `tests/`.

## Verbs and units

- `Read*` touches the bus; `Get*` returns cached state and never does I/O; `Set*` / `Write*` change the chip;
  `Is*` / `Has*` return `bool` and do no I/O.
- Quantities carry their unit as a suffix, in the identifier's own case:

  | Unit | In `PascalCase` | In `snake_case` |
  | --- | --- | --- |
  | milliseconds, microseconds, seconds | `Ms`, `Us`, `S` | `_ms`, `_us`, `_s` |
  | hertz, kilohertz | `Hz`, `Khz` | `_hz`, `_khz` |
  | millivolts, volts | `Mv`, `V` | `_mv`, `_v` |
  | milliamps, microamps, amps | `Ma`, `Ua`, `A` | `_ma`, `_ua`, `_a` |
  | pascals, degrees Celsius | `Pa`, `C` | `_pa`, `_c` |
  | revolutions per minute, degrees | `Rpm`, `Deg` | `_rpm`, `_deg` |
  | percent, raw counts | `Pct`, `Counts` | `_pct`, `_counts` |

  `SetHitCurrentMa(uint16_t current_ma)`, `ReadTemperatureC()`, `timeout_ms`. Not `_mA`, `MilliAmps` or a `Unit`
  enum parameter.
- SI base units and integers are preferred. A `float` in a public API states its unit like any other value.

## Include roots and headers

- One include root per kb-core part: `#include "kb/interfaces/BaseSpi.h"`, `#include "kb/rtos/RtosMutex.h"`,
  `#include "kb/utils/Status.h"`. Drivers use their flat `inc/`: `#include "pca9685.hpp"`. Relative paths that
  climb out of a repository or part (`"../../drivers/..."`) are not allowed.
- Every header starts with `#pragma once`.
- Include order: the file's own header, then standard headers, then other repositories, then this repository;
  one blank line between groups. `clang-format` sorts within a group.
- A header includes what it uses and compiles on its own.

## Formatting

[`config/.clang-format`](config/.clang-format): LLVM base, 2-space indent, 100-column limit, pointer and
reference attached to the type (`uint8_t* data`), attached braces, short functions only when empty, template
declarations on their own line.

The column limit is 100 everywhere.

Markdown wraps at 120 columns (markdownlint `MD013`, tables and code blocks exempt).

## Static analysis

[`config/.clang-tidy`](config/.clang-tidy) enables `bugprone-*`, `cert-*`, `clang-analyzer-*`,
`cppcoreguidelines-*`, `modernize-*`, `performance-*`, `portability-*` and `readability-*`, turns off the checks
that fight register-level code (each with its reason in the file), and sets the naming rules above.

## Using the configs in a repository

1. Copy both files into the repository's `_config/` unchanged. Do not add root copies or symlinks
   ([ADR-0011](adr/0011-repository-root-layout.md)); every tool is given the path:
   `clang-format --style=file:_config/.clang-format`, `clang-tidy --config-file=_config/.clang-tidy`. Editors that
   find the files only by name (clangd, CLion) use a local copy listed in `.gitignore`.
2. Point the lint workflow at them:

   ```yaml
   uses: kokeb-labs/ci-tools/.github/workflows/ru-cpp-lint.yml@v1
   with:
     clang_version: "20"
     clang_format_config: "_config/.clang-format"
     clang_tidy_config: "_config/.clang-tidy"
   ```

   The shared workflow links the files into its own checkout; the repository carries no link.
3. Fix findings in new and changed code. Existing findings are fixed in their own PRs, not mixed into features.
4. Suppress a finding only with `// NOLINT(<check>): <reason>` or `// NOLINTNEXTLINE(<check>): <reason>`. A bare
   `NOLINT` is not allowed.

A rule that is wrong for every repository is changed here, in both configs and on this page together.

## Comments

- Public API is documented with Doxygen (`///` or `/** */`): what it does, parameters with units, the `Error` or
  `Status` values it returns, and whether it does I/O. See [docs.md](docs.md#doxygen).
- Comments say why. Datasheet references name the section or table (`SBASB22 Table 7-12`).
- No commented-out code, no `TODO` without an issue link, no author or date banners, no tool attribution lines.
