# Errors

One error model for the whole stack: drivers keep their own small `Error` enum, every layer above a driver speaks
`kb::Status`, and the original code travels along as `detail`. Decision: [ADR-0001](adr/0001-error-model.md).

## `kb::Status`

```cpp
namespace kb {

enum class Status : uint8_t {
  Ok = 0,
  NotInitialized = 1,      // the object has not been (successfully) initialised
  InvalidArgument = 2,     // a parameter is out of range; nothing was done
  Busy = 3,                // the resource is in use; retrying later can succeed
  Timeout = 4,             // a wait expired
  Bus = 5,                 // a transfer failed: NACK, CRC, framing, arbitration, transport error
  NotFound = 6,            // the device or resource is absent or answered with the wrong identity
  Fault = 7,               // the device reported a fault, or a check of its state failed
  Unsupported = 8,         // the operation is not available on this chip, board or build
  DependencyNotReady = 9,  // something this call needs (a bus, a manager, a handler) failed to start
  NoMemory = 10,           // a fixed-capacity pool or table is full
  Unknown = 11,            // anything that maps to none of the above
};

[[nodiscard]] constexpr const char* ToString(Status status) noexcept;

template <typename T>
struct [[nodiscard]] Result {
  T value{};
  Status status{Status::Ok};
  uint16_t detail{0};  // the originating layer's own code (driver Error, kb_*_err_t, manager code); 0 if none
  [[nodiscard]] constexpr bool ok() const noexcept { return status == Status::Ok; }
  constexpr explicit operator bool() const noexcept { return ok(); }
};

template <>
struct [[nodiscard]] Result<void> {
  Status status{Status::Ok};
  uint16_t detail{0};
  [[nodiscard]] constexpr bool ok() const noexcept { return status == Status::Ok; }
  constexpr explicit operator bool() const noexcept { return ok(); }
};

} // namespace kb
```

`kb::Status` and `kb::Result<T>` live in `kb/utils/Status.h` in kb-core's `utils/general`, a header with no
dependencies, because `utils` is the lowest part of kb-core and every other part already depends on it. Drivers
do not include it.

Rules:

- New codes are added only by changing this page and the header together. Values are never renumbered.
- `detail` is diagnostic. Code MUST NOT branch on `detail`; it branches on `status`.
- A `Result` that is ignored is a compiler warning (`[[nodiscard]]`), which CI turns into an error.
- `ToString()` returns a static string for every value.

## Which layer returns what

| Layer | Returns | Maps from | Where the mapping lives |
| --- | --- | --- | --- |
| Driver | `<chip>::Result<T>` with `<chip>::Error` | port hook `bool` results | the driver |
| interfaces `Base*` | `kb_<periph>_err_t` (kept) | the vendor SDK's codes | each `mcu/<family>/` class |
| interfaces | `kb::Status ToStatus(kb_<periph>_err_t) noexcept`, one per error type | `kb_<periph>_err_t` | next to the error list in `base/Base<Periph>.h` |
| Handler | `kb::Result<T>` | `<chip>::Error` | one `ToStatus(<chip>::Error)` per handler, in its adapter header |
| Manager (HAL) | `kb::Status`; `GetLastError()` returns the last one | handler `kb::Result<T>` | the manager |
| Facade (HAL) | `kb::Status` plus the `ManagerId` that failed | manager `kb::Status` | `FacadeBase` |
| Product | its own fault catalogue (CANopen EMCY codes, fault IDs) | `kb::Status` plus `ManagerId` | one table in the product |

Each mapping happens once, at the boundary. A layer MUST NOT re-map a `Status` it received from below; it passes
it up, possibly with its own `detail`.

## Driver `Error` to `kb::Status`

The base set has fixed values ([driver.md](driver.md#errors-and-resultt)), so every handler starts from the same
table:

| `<chip>::Error` | `kb::Status` |
| --- | --- |
| `Ok` | `Ok` |
| `NotInitialized` | `NotInitialized` |
| `InvalidArgument` | `InvalidArgument` |
| `Bus` | `Bus` |
| `Timeout` | `Timeout` |
| `DeviceIdMismatch` | `NotFound` |
| `Crc` | `Bus` |
| `Busy` | `Busy` |
| `DeviceFault` | `Fault` |
| `Unsupported` | `Unsupported` |
| chip-specific | chosen per value by the handler, documented in the handler's page |

```cpp
// handlers/zp100/HalI2cZp100Comm.h
namespace kb {

[[nodiscard]] constexpr Status ToStatus(zp100::Error error) noexcept {
  switch (error) {
  case zp100::Error::Ok:               return Status::Ok;
  case zp100::Error::NotInitialized:   return Status::NotInitialized;
  case zp100::Error::InvalidArgument:  return Status::InvalidArgument;
  case zp100::Error::Bus:              return Status::Bus;
  case zp100::Error::Timeout:          return Status::Timeout;
  case zp100::Error::DeviceIdMismatch: return Status::NotFound;
  case zp100::Error::Crc:              return Status::Bus;
  case zp100::Error::Busy:             return Status::Busy;
  case zp100::Error::DeviceFault:      return Status::Fault;
  case zp100::Error::Unsupported:      return Status::Unsupported;
  case zp100::Error::FifoOverflow:     return Status::Fault;
  }
  return Status::Unknown;
}

template <typename T>
[[nodiscard]] constexpr Result<T> ToResult(const zp100::Result<T>& r) noexcept {
  return {r.value, ToStatus(r.error), static_cast<uint16_t>(r.error)};
}

} // namespace kb
```

The switch MUST list every enumerator and have no `default:`, so `-Wswitch` flags a new driver value that the
handler does not map yet.

## Interfaces codes to `kb::Status`

The interfaces keep their per-peripheral codes (they carry more detail than a handler needs) and add one
`ToStatus()` per type. The rules, applied by name:

| `kb_*_err_t` value names | `kb::Status` |
| --- | --- |
| `*_SUCCESS` | `Ok` |
| `*_NOT_INITIALIZED` | `NotInitialized` |
| `*_INVALID_PARAMETER`, `*_NULL_POINTER`, `*_INVALID_CONFIGURATION`, `*_INVALID_*` | `InvalidArgument` |
| `*_BUSY`, `*_ALREADY_INITIALIZED` when it means "in use" | `Busy` |
| `*_TIMEOUT` | `Timeout` |
| `*_BUS_ERROR`, `*_TRANSFER_FAILED`, `*_COMMUNICATION_FAILURE`, `*_NACK`, `*_ARBITRATION_LOST`, `*_CRC*`, `*_CS_CONTROL_FAILED` | `Bus` |
| `*_DEVICE_NOT_FOUND`, `*_DEVICE_NOT_RESPONDING`, `*_NOT_AVAILABLE` | `NotFound` |
| `*_HARDWARE_FAULT`, `*_VOLTAGE_OUT_OF_RANGE`, `*_CLOCK_ERROR` | `Fault` |
| `*_UNSUPPORTED_OPERATION`, `*_NOT_SUPPORTED` | `Unsupported` |
| `*_OUT_OF_MEMORY` | `NoMemory` |
| `*_FAILURE`, `*_SYSTEM_ERROR`, `*_UNKNOWN`, anything else | `Unknown` |

`ALREADY_INITIALIZED` returned from an idempotent `Initialize()` is success, not an error; the `Base*` class
handles that before mapping.

## Managers and the facade

- Every manager method that can fail returns `kb::Status`, and the manager records it: `GetLastError()` returns
  the last non-`Ok` status since `ClearLastError()`.
- A manager whose dependency (a handler, a bus from the bind) failed to start returns `DependencyNotReady` from
  every call, not the dependency's own status. The dependency's status is in its own diagnostics.
- The facade's start-up result is `{kb::Status status; kb::hal::ManagerId manager;}`: the first manager that failed
  and why. See [hal.md](hal.md#facade-and-start-up).

## Products

A product translates `kb::Status` plus `ManagerId` into its own fault catalogue in one table (for example to a
CANopen EMCY code and a fault ID). Product code MUST NOT inspect `detail`, driver `Error` values or `kb_*_err_t`
values. Fault catalogues are product-specific and never live in kb-core.

## What is not allowed

- Returning `bool` from a call that can fail for more than one reason.
- Logging an error and returning `Ok`.
- `esp_err_t`, `HAL_StatusTypeDef` or any vendor type above `bsp_bind`.
- A second error enum for a layer that already has one (`ManagerError`, `HalError`, `CommError`).
- Exceptions. Every repository builds with `-fno-exceptions`.
