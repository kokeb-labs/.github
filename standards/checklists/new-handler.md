# Checklist: new handler

Copy this list into the PR that adds `kb-core/handlers/<chip>/`. [handler.md](../handler.md) is the contract. The
driver is released and pinned in kb-core first.

```markdown
### Files and build
- [ ] Driver submodule at `drivers/driver-<chip>/`, pinned to a release tag; entry in `catalog/compat.yml` from its `driver.yml`
- [ ] `handlers/<chip>/<Chip>Handler.h/.cpp` with class `kb::<Chip>Handler`
- [ ] Adapter `Hal<Bus><Chip>Comm` deriving from the driver's port base, using the shared adapter base from `handlers/common/`
- [ ] `KB_ENABLE_<CHIP>` compiles the handler and links `<chip>::<chip>`; listed on the Build options page
- [ ] MCU-bound driver: row in the MCU gate table in `cmake/kb_build_settings.cmake`, matching `catalog/compat.yml`
- [ ] Includes only the driver, `kb/interfaces/Base*.h`, `kb/rtos/`, `kb/utils/` and `kb/handlers/common/`; no `#ifdef` for an MCU or product

### Shape
- [ ] Constructor stores references only: no I/O, no driver creation, no allocation; not copyable or movable
- [ ] Driver stored in place (`std::optional<Driver>`); no `make_unique`, `new` or `shared_ptr`
- [ ] `EnsureInitialized()` returns `kb::Result<void>`, retries cleanly after a failure
- [ ] `Deinitialize()` and `IsInitialized()`
- [ ] Own `RtosMutex` taken by every public method; optional bus mutex, taken after the handler mutex
- [ ] Typed methods return `kb::Result<T>`; no driver result types, `esp_err_t` or `bool` for fallible calls
- [ ] `ToStatus(<chip>::Error)` in the adapter header: every enumerator listed, no `default:`
- [ ] `VisitDriver(fn)` returns `kb::Status`, refuses before init; no public `GetDriver()` or driver pointer
- [ ] `GetDiagnostics()` returns a struct starting with `kb::DiagnosticsHeader`, updated on every call
- [ ] Wrappers (if any) owned in fixed storage, created by `EnsureInitialized()`
- [ ] Product choices come in through the handler config or a table passed in

### Tests and docs
- [ ] Host test over fake `Base*` objects and the driver's mock, with `KB_RTOS=NONE` and `KB_MCU=HOST`: no I/O in the constructor, retry after failed init, bus failure maps to `Status::Bus`, `VisitDriver()` before init, diagnostics counts
- [ ] Handler page in `kb-core/docs/handlers/`: API, chip-specific `Error` mapping, locking, diagnostics fields
- [ ] kb-core `CHANGELOG.md` entry under `## [Unreleased]`
```
