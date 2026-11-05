# ADR-0002: One lifecycle for drivers and handlers

- Status: Accepted
- Date: 2026-11-03

## Context

The review found six start-up styles. Some drivers had no initialisation at all, one reset the chip the first time
any setter ran, some constructors did I/O, and handlers either built their driver with `make_unique` in an
`Initialize()` or exposed only `EnsureInitialized()`. A caller could not tell when the bus was first touched or
whether a failed start-up could be retried.

## Decision

- Constructors are `noexcept`, do no I/O and cannot fail.
- Drivers have `Initialize(const Config& = {})`: port up, reset, chip-ID check, apply config; then
  `EnsureInitialized()`, `IsInitialized()` and `Deinitialize()`. Every I/O call returns `NotInitialized` before
  initialisation; nothing initialises as a side effect.
- Handlers have `EnsureInitialized()` returning `kb::Result<void>`, which emplaces the driver in place and runs its
  initialisation, and leaves nothing cached on failure so the next call retries.
- HAL managers have `Initialize()` / `Deinitialize()`; the facade starts them in a fixed order and fails closed.

## Consequences

- Construction order no longer matters: objects can be static, and the bus is first touched at a known point.
- A missing chip is a `DeviceIdMismatch` / `NotFound` at start-up instead of garbage later.
- Drivers without initialisation gain one; drivers that reset on first use stop doing so.
