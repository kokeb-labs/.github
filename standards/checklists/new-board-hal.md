# Checklist: new board HAL

Copy this list into the tracking issue for a new board HAL. Board HALs live in the product's organization or
repository. [hal.md](../hal.md) is the contract.

```markdown
### Repository
- [ ] Created from `kokeb-labs/board-hal-template` when it exists, else from the example in `kb-hal-common`; named for the board in the product's organization; settings and rulesets applied there
- [ ] Submodules `lib/core` (kb-core) and `lib/common` (kb-hal-common), both pinned to release tags; `version_lock.txt` checked in CI
- [ ] Board pin table in `board/<board>/`, written with the generic `pincfg` framework
- [ ] `CODEOWNERS`, `AGENTS.md`, `CLAUDE.md`, `.claude/skills/verify/` and `bump-pin/`; licence chosen by the product owner; org clang configs
- [ ] [Root layout](../repo-governance.md#repository-root): tool configuration (`mkdocs.yml` with `docs_dir: ../docs`, `Doxyfile`, clang configs) in `_config/`, no symlinks; at the root only what a tool needs there (`CMakePresets.json`, `version_lock.txt`) besides the usual files

### Structure
- [ ] `board/<board>/`: bus table, chip list, pin table, product choices passed to kb-core (masks, profile tables); data only
- [ ] `bsp_bind/<family>/` implements the `kb::hal::bind` interface for the MCU with kb-core's `mcu/<family>/` classes; `bsp_bind/host/` with fakes and a settable clock
- [ ] The bind stores every object statically, sized by `kMax*` constants; `Create*` / `Destroy*` by slot
- [ ] Common managers come from `kb-hal-common`; only board-specific managers live here, each deriving from `ManagerBase`
- [ ] Managers reach chips only through handler APIs or `VisitDriver()`; no driver includes
- [ ] Every fallible manager method returns `kb::Status`; `GetLastError()`; no local error enum
- [ ] Facade `<board>::Hal` derives from `FacadeBase`; start-up order fixed and documented; fail-closed; safety-relevant managers not optional
- [ ] The facade gives the kb-core logger its sink
- [ ] No ESP-IDF, FreeRTOS or `mcu/<family>/` includes outside `bsp_bind/`; `kb::rtos` for locks and delays; `kb::MonotonicUs()` for time
- [ ] No allocation after start-up; start-up allocations allowlisted

### CI, tests and docs
- [ ] The `kb-hal-common` lints (boundary, driver access, allocation, lock) run and pass
- [ ] Host build with the host bind; tests for start-up order, fail-closed with a failure injected into each manager, diagnostics
- [ ] `examples/esp32` (or the board's family) builds for the board's MCU with `CONFIG_FREERTOS_HZ=1000`
- [ ] HAL page set with the board card, pin table, manager table, start-up order and `docs/contract.md`
- [ ] Bench list for first bring-up written in the tracking issue
```
