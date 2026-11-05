# Product contract

What a product repository provides: the application firmware for one board, built on that board's HAL. Products
and their board HALs live in the product's own organization or repository, not in `kokeb-labs`. This page is the
contract they follow when they build on the stack.

## Layout

```text
<product>/
├── main/ or app/        the application: tasks, protocols, state machines, faults     namespace <board>::app
├── platform/            the only folder that may use ESP-IDF directly
├── hal/                 the board HAL: a folder, or a submodule pinned to a release tag
├── version_lock.txt     the pin manifest (release.md)
├── sdkconfig.defaults   CONFIG_FREERTOS_HZ=1000 and the product's settings
├── partitions.csv
├── docs/, CHANGELOG.md, LICENSE, README.md
└── _config/
```

## Rules

### What the application uses

- The application MUST use only: the HAL facade and its managers' public API, `kb::rtos`, and the kb-core logger.
- It MUST NOT include handlers, drivers, `Base*` headers, `mcu/<family>/` classes or raw FreeRTOS outside
  `platform/` ([layers.md](layers.md#includes)). The HAL boundary lint runs over the product too.
- Board functions the facade does not offer yet (for example CAN) are added to the HAL first, then used.
- Product-specific code stays in the product or its board HAL. A need that kb-core or a driver cannot meet is
  raised as an issue for a generic extension point, not patched into core
  ([layers.md](layers.md#product-specific-code)).

### `platform/`

- Holds `app_main()`, partition and OTA handling, the console, and other start-up code that needs ESP-IDF.
- `app_main()` creates the facade, calls `Initialize()`, reports a failed start-up through the fault catalogue,
  and starts the application tasks. It contains no application logic.

### Faults

- The product has one fault catalogue: every fault it can report, with its ID, its protocol code (for example a
  CANopen EMCY code), its severity and the reaction (stop, derate, warn).
- `kb::Status` plus `ManagerId` map onto the catalogue in one table ([errors.md](errors.md#products)). The
  catalogue is documented on the product's Operation page.
- A failed start-up MUST leave every actuator in its safe state, which the facade's fail-closed start-up
  guarantees; the product then reports the fault and does not start the control tasks.

### Tasks and timing

- Tasks, stack sizes, priorities and core affinity are named in one header (`<board>::app::kTaskConfig`) and
  created through `kb::rtos` ([threading-and-timing.md](threading-and-timing.md#tasks)).
- The product runs FreeRTOS at 1 kHz.

### Configuration

- `sdkconfig.defaults` only; no committed full `sdkconfig`.
- Product settings that change per unit (calibration, node ID) live in NVS through the HAL's NVS manager, with a
  documented layout and version. A change that moves or reformats NVS is listed under `### Breaking` in the
  changelog with the erase or migration step.

### Releases

- A product release is a firmware release: the tag builds the firmware and attaches `.bin`, `.elf`, `sha256` and
  the effective `sdkconfig`; a missing artifact fails the release ([release.md](release.md)).
- The firmware reports its own version, the release train it is built on, and the tag and SHA of every pinned
  submodule (the provenance header).
- `version_lock.txt` lists `REF_<repo>=vX.Y.Z@<sha>` for every submodule, and CI checks it against the pins.

### Tests and docs

- Application logic that does not need hardware (state machines, fault mapping, protocol encoding) has host
  tests, built against the HAL's host bind.
- The product page set in [docs.md](docs.md); decisions specific to the product are ADRs in its own
  `docs/adr/`.
