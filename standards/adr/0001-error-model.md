# ADR-0001: Drivers keep their own error type; handlers map to `kb::Status`

- Status: Accepted
- Date: 2026-11-03

## Context

The review this standard grew from found five error models across the drivers (success spelt `Success`, `None`,
`Ok` and `OK`; one driver `bool`-only; bitmask flags in another), about 30 more error types above them, and two
incompatible `ManagerError` enums in the HALs that no product read. Bus errors were lost in several places: `void`
UART writes, `void` GPIO hooks, a getter returning a stale angle after a failed read.

Two shapes were considered: one shared `kb::Result` used everywhere including drivers, or a small per-driver
`Result<T>` and `Error` mapped to a shared status at the handler. A shared type inside drivers would make every
driver depend on kb-core, and the drivers are meant to be usable on any MCU without the rest of the stack.

## Decision

- Each driver declares `enum class <chip>::Error : uint8_t` with a fixed base set (`Ok`, `NotInitialized`,
  `InvalidArgument`, `Bus`, `Timeout`, `DeviceIdMismatch`, `Crc`, `Busy`, `DeviceFault`, `Unsupported`, values 0
  to 9), chip-specific values from 16, and `<chip>::Result<T>` with `ok()` and `[[nodiscard]]`.
- Above the drivers there is one status, `kb::Status` (12 codes), and one result, `kb::Result<T>`, carrying the
  original code as `detail`. They live in a dependency-free header in kb-core's `utils` (`kb/utils/Status.h`).
- Each boundary maps once: handlers map driver errors, the interfaces map `kb_*_err_t` with `ToStatus()`, the
  facade adds the failing manager, the product maps to its fault catalogue.

## Consequences

- Drivers stay standalone and keep precise, chip-level errors.
- One mapping table serves every handler because the base set has fixed values.
- Every driver whose API returns `bool` or flags changes its public API once, before v0.1.
- `ManagerError` enums and per-layer error types do not exist.
- `detail` keeps the original code for diagnostics, but code above the handler cannot branch on it.
