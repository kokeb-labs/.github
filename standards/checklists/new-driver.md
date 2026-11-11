# Checklist: new driver

Copy this list into the tracking issue or the first PR of a new `driver-<chip>`. Each item links the rule it
checks; [driver.md](../driver.md) is the contract.

```markdown
### Repository
- [ ] Created from `kokeb-labs/driver-template` in `kokeb-labs-drivers` with `tools/setup.py --kind driver`, private until its first release candidate, named `driver-<chip>`; follow the [new repository checklist](new-repository.md)
- [ ] Metadata added in `org/` of `kokeb-labs/.github`; merge settings, security, rulesets and labels applied by an owner
- [ ] `CODEOWNERS`, `AGENTS.md`, `CLAUDE.md` (`@AGENTS.md`), `.claude/skills/verify/SKILL.md`
- [ ] `LICENSE` is MIT; `_config/.clang-format` and `_config/.clang-tidy` copied unchanged from the standard
- [ ] Root holds only the [allowed entries](../repo-governance.md#repository-root); `Doxyfile`, `mkdocs.yml` (`docs_dir: ../docs`) and `Kconfig` in `_config/`; `CONTRIBUTING.md`, `SECURITY.md` in `.github/`; no symlinks
- [ ] No org prefix anywhere: no `kb_`, `kb::`, `KB_` or other brand in names, macros, targets, files or options

### Code
- [ ] Everything in `namespace <chip>`; class `<chip>::<CHIP>`; umbrella header `inc/<chip>.hpp`, implementation `src/<chip>.ipp`
- [ ] Port base `<chip>::<Bus>Interface<Derived>` and concept `<chip>::<Bus>Port`; required hooks not declared in the base
- [ ] Hooks PascalCase, `noexcept`, `bool`, raw bytes only; the driver never configures the bus
- [ ] Optional hooks detected with `requires` in one helper; a missing delay hook fails to compile
- [ ] `enum class Error : uint8_t` with the base set at values 0 to 9, chip-specific values from 16, each one returned somewhere; `ToString()`
- [ ] `Result<T>` / `Result<void>` with `ok()` and `[[nodiscard]]` on every fallible call
- [ ] Every port failure propagates; no getter returns a stale or zero value after a failed read
- [ ] `noexcept` constructor with no I/O; `Initialize(const Config& = {})` resets, checks the chip ID, applies config
- [ ] `EnsureInitialized()`, `IsInitialized()`, `Deinitialize()`; every I/O call returns `NotInitialized` before init
- [ ] `Config` struct with unit-suffixed fields and datasheet defaults; Kconfig only through `inc/<chip>_kconfig.hpp`
- [ ] Product choices (channels, features, profiles) are `Config` fields, not compile-time switches
- [ ] No heap, exceptions, RTTI, `std::function`, `std::string`, `printf`, static mutable state; no locking, no RTOS
- [ ] Destructive operations take explicit data or confirmation; no default triggers them
- [ ] Names and units per the naming standard; `clang-tidy` clean on `inc/` and `src/`

### Build
- [ ] C++20; version only in `cmake/<chip>_build_settings.cmake` (`<CHIP>_VERSION_*`); generated `<chip>_version.h`
- [ ] `EXPORT_NAME <chip>` and alias `<chip>::<chip>`; `find_package(<chip>)`; install rules for every header, the `.ipp` and the package config
- [ ] Options `<CHIP>_BUILD_TESTS` and `<CHIP>_ENABLE_WARNINGS`
- [ ] Root `CMakeLists.txt` is also the ESP-IDF component (`ESP_PLATFORM`, `KCONFIG _config/Kconfig`); no `idf_component.yml`, no wrapper component
- [ ] No SDK, RTOS or vendor header in `inc/` or `src/`, and no `ESP_PLATFORM` test there; platform code only in `examples/<platform>/`, each with its own port
- [ ] `examples/host/` built and run by the host tests; `examples/esp32` with `EXTRA_COMPONENT_DIRS` at the root and `CONFIG_FREERTOS_HZ=1000` in `sdkconfig.defaults`
- [ ] `driver.yml` with `bus`, `mcus`, `peripheral` (if MCU-bound) and `kb_core_min`; checked against the build settings in CI
- [ ] CI from `kokeb-labs/ci-tools` at `@v1`, ending in the `CI gate` job with the DCO check in its `needs`; `CI gate / gate` required once it has run

### Tests
- [ ] `tests/mock_<chip>.hpp` register model
- [ ] Host suite on gcc and clang with `-Werror -fno-exceptions -fno-rtti`: not-initialised, ID mismatch, bus failure on every path, argument checks, register traffic
- [ ] `tests/docs/` compiles every snippet on the site
- [ ] `tests/install_consumer/` builds against `find_package(<chip>)` and `<chip>::<chip>`
- [ ] Version agreement test (CMake, Doxyfile, `driver.yml`, `GetDriverVersion()`)

### Docs
- [ ] The driver page set, including `docs/contract.md` and `docs/platforms.md`; site config `_config/mkdocs.yml`
- [ ] Doxygen clean with `EXTRACT_ALL = NO` and warnings as errors on `inc/`
- [ ] Quickstart checks every return value; Porting shows a complete, compiled port
- [ ] README sections per the README standard; datasheet in `docs/datasheet/` where its licence allows
- [ ] `CHANGELOG.md` with `## [Unreleased]`

### kb-core (separate PRs, after the first release)
- [ ] Submodule `drivers/driver-<chip>/` in kb-core pinned to the release tag; `catalog/compat.yml` entry
- [ ] Handler per the [new handler checklist](new-handler.md)

### Exceptions (only if they apply)
- [ ] MCU-bound: README, Contract page and `driver.yml` say so; the peripheral backend lives in kb-core `interfaces/mcu/<family>/`; MCU gate row added
- [ ] Protocol client: remote identity check replaces the chip-ID check
```
