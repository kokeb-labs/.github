# Board HAL contract

What a board HAL provides, what lives in the shared `kb-hal-common`, and the shape of the platform bind
(`bsp_bind/<family>`). Decision: [ADR-0005](adr/0005-kb-hal-common.md).

## What lives where

| Repository / folder | Where | Contains | Namespace |
| --- | --- | --- | --- |
| `kb-hal-common` | `kokeb-labs` | `ManagerBase`, `FacadeBase`, `ManagerId`, the `PlatformBind` interface, the six common managers (NVS, LED, GPIO, ADC, temperature, comms), the diagnostics collector, the boundary lints and a board HAL example | `kb::hal` |
| A board HAL | The product's organization or repository | The board config (bus table, chip list), the board's pin table, the bind for its MCU family, the board-specific managers (for example motor, IMU or valves), the board facade, its examples | `<board>` |
| `bsp_bind/<family>/` in the HAL | The board HAL | The code that creates the MCU family's `Esp*` / `Stm*` / `Host*` objects from the board config | `<board>::bsp` |

Board HALs are product code: they live with the product, not in `kokeb-labs`. New board HALs start from
`kokeb-labs/board-hal-template` once it exists, and from the example in `kb-hal-common` until then.

A board HAL MUST NOT carry its own copy of anything in `kb-hal-common`. A manager that two boards need, written
without anything product-specific, moves to `kb-hal-common`; a manager only one board needs stays in that HAL.

A board HAL consumes `kb-hal-common` (`lib/common`) and `kb-core` (`lib/core`) as submodules pinned to release
tags.

## Managers

```cpp
namespace kb::hal {

enum class ManagerId : uint8_t {
  Nvs, Led, Gpio, Adc, Temperature, Comms,  // common managers
  Board = 32,                               // board-specific managers number from here
};

class ManagerBase {
public:
  virtual ~ManagerBase() = default;
  [[nodiscard]] virtual ManagerId Id() const noexcept = 0;
  [[nodiscard]] virtual const char* Name() const noexcept = 0;

  virtual kb::Status Initialize() noexcept = 0;    // idempotent
  virtual kb::Status Deinitialize() noexcept = 0;  // to the safe state
  [[nodiscard]] bool IsInitialized() const noexcept;

  [[nodiscard]] kb::Status GetLastError() const noexcept;
  void ClearLastError() noexcept;

  virtual void CollectDiagnostics(DiagnosticsSink& sink) const noexcept = 0;
};

} // namespace kb::hal
```

Rules:

- One manager per board function. A manager owns the handlers for its function and the `Base*` objects the bind
  created for them.
- Managers reach chips only through their handlers' typed API or `VisitDriver()`. A manager MUST NOT include a
  driver header or hold a driver pointer.
- Every fallible method returns `kb::Status` ([errors.md](errors.md#managers-and-the-facade)). There is no
  `ManagerError` enum.
- Managers are created by the facade in static storage. No heap after start-up; allocation during `Initialize()`
  is allowed only for objects that live until reset, and the HAL's allocation lint lists them.
- Managers are thread-safe: each public method takes the manager's `RtosMutex` or delegates to a thread-safe
  handler.
- `CollectDiagnostics()` writes the manager's state and the `DiagnosticsHeader` of each handler it owns into the
  sink; it does not log.
- The common managers in `kb-hal-common` take everything board-specific as configuration (which channels, which
  LEDs, which NVS namespaces); they never name a board.

## Facade and start-up

```cpp
namespace kb::hal {

struct StartupResult {
  kb::Status status = kb::Status::Ok;
  ManagerId manager = ManagerId::Nvs;  // the first manager that failed; meaningless when status is Ok
};

class FacadeBase {
public:
  StartupResult Initialize() noexcept;   // ordered, fail-closed
  void Deinitialize() noexcept;          // reverse order
  void CollectDiagnostics(DiagnosticsSink& sink) const noexcept;

protected:
  explicit FacadeBase(std::span<ManagerBase* const> start_order) noexcept;
};

} // namespace kb::hal
```

- The board facade (`<board>::Hal`) derives from `FacadeBase` and passes its managers in start-up order. The order
  is fixed at compile time and documented on the HAL's Architecture page.
- **Fail-closed**: `Initialize()` starts managers in order and stops at the first failure. It then deinitialises
  the managers already started, in reverse, so every output is back in its safe state, and returns the failing
  manager and its status.
- A manager the board can run without is marked optional in the start order; its failure is recorded in the
  diagnostics and start-up continues. Safety-relevant managers (motor, valves, power) are never optional.
- The facade is the product's only entry point. It exposes the managers by reference and nothing below them.
- `CollectDiagnostics()` visits every manager. It is the one diagnostics call a product makes.
- The facade passes the kb-core logger its sink during start-up ([library.md](library.md#handlers)).

## The platform bind

The bind turns the board config into `Base*` objects. It is the only code in a board HAL that names the MCU
family. There is one interface, declared in `kb-hal-common`:

```cpp
namespace kb::hal::bind {

// Peripherals, created and destroyed by slot. Specs carry raw pins resolved from the board's pin table.
BaseGpio* CreateGpio(size_t slot, const GpioSpec& spec) noexcept;
void DestroyGpio(size_t slot) noexcept;
bool CreateSpiBus(size_t bus, const SpiBusSpec& spec) noexcept;
BaseSpi* CreateSpiDevice(size_t bus, const SpiDeviceSpec& spec) noexcept;
void DestroySpiBus(size_t bus) noexcept;
BaseI2c* CreateI2cDevice(size_t bus, const I2cDeviceSpec& spec) noexcept;
BaseUart* CreateUart(const UartSpec& spec) noexcept;
BaseCan* CreateCan(const CanSpec& spec) noexcept;
BaseAdc* CreateInternalAdc(uint8_t unit, uint32_t channel_mask) noexcept;
BaseTemperature* CreateDieTemperature() noexcept;
BaseNvs& NvsRegion(size_t slot, const char* name_space) noexcept;

// LED strip
bool LedStripBegin(const LedStripSpec& spec) noexcept;
void LedStripSetPixel(uint16_t index, uint32_t rgb) noexcept;
bool LedStripShow() noexcept;
void LedStripEnd() noexcept;

// System
uint64_t MonotonicMicros() noexcept;
uint32_t LastResetReason() noexcept;
[[noreturn]] void SystemRestart() noexcept;
uint32_t FreeHeapBytes() noexcept;
uint32_t LargestFreeHeapBlock() noexcept;

} // namespace kb::hal::bind
```

Rules:

- Verbs are `Create*` / `Destroy*` (and `Acquire*` for singletons the SDK owns). Each `Create*` returns `nullptr`
  or `false` on failure and is idempotent per slot.
- Buses are slots (`bus`, `slot` indices below `kMax*` constants), so a board with two SPI controllers and four
  devices each needs no new API.
- The bind stores every object it creates in static storage sized by the `kMax*` constants. It does not allocate
  after start-up.
- The bind creates the `Esp*` / `Stm*` / `Host*` objects that kb-core's `interfaces/mcu/<family>/` provides. It
  does not reimplement a peripheral; a peripheral kb-core lacks is added to kb-core first.
- Every family the board runs on has a bind: `esp32c6/`, `esp32s3/`, `stm32h7/` as boards need them, and `host/`,
  which backs the host tests with fakes and a settable clock.
- The bind's interface header includes only `Base*` headers and standard headers, so the HAL above it compiles
  for every family.

## Board config

- One `board/<board>/` folder holds the bus table, the chip list and the board's pin table, written with the
  generic `pincfg` framework ([library.md](library.md#pincfg)). It contains data, not logic.
- Raw pin numbers appear only in the pin table and the bind; managers use functional pin names.
- Product choices that reach kb-core (channel masks, profile tables, limits) are declared here and passed in
  through configuration.

## Lints

`kb-hal-common` ships the lints, run in every board HAL's CI:

| Lint | Fails on |
| --- | --- |
| Boundary | an ESP-IDF, FreeRTOS, `mcu/<family>/` or driver include outside `bsp_bind/` |
| Driver access | `GetDriver()`, a driver pointer, or a driver call outside `VisitDriver()` |
| Allocation | `new`, `malloc`, `make_unique`, `make_shared`, `std::vector` growth outside the allowlisted start-up code |
| Lock | a raw RTOS lock, or a manager holding its lock across a call into another manager |

An exception goes in the lint's allowlist file in the HAL, with a comment naming the issue that removes it.

## Tests and docs

- The HAL builds on the host with the `host/` bind, and `tests/host/` covers start-up order, fail-closed
  behaviour (inject a failure into each manager in turn), and `CollectDiagnostics()`.
- Examples in `examples/esp32/` (or the board's family) build in CI for the board's MCU.
- The HAL page set in [docs.md](docs.md), with the start-up order and the manager table on the Architecture page.
