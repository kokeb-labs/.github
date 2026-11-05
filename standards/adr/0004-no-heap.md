# ADR-0004: No heap in drivers, none after start-up anywhere

- Status: Accepted
- Date: 2026-11-03

## Context

Embedded targets run for months; heap fragmentation and allocation failure after start-up are hard to test and
hard to recover from. The review found a driver documented as heap-free that allocated, `std::function` in two
drivers, a static report buffer in another, handlers allocating with `make_unique` and `nothrow new`, and wrappers
returned as `std::shared_ptr`.

## Decision

- Drivers use no heap, exceptions, RTTI, `std::function`, `std::string`, `printf` or static mutable state.
  Callbacks are a function pointer plus `void*`.
- Handlers store their driver in place (`std::optional`) and their wrappers in fixed arrays.
- HALs and products allocate only during start-up, for objects that live until reset, and the HAL allocation lint
  lists them. Nothing allocates after start-up.
- Every repository builds with `-fno-exceptions -fno-rtti`.

## Consequences

- Memory use is visible at link time and does not change at run time.
- APIs that returned owning pointers or `shared_ptr` change to references into fixed storage.
- Capacity limits become `constexpr` constants that a board can size, and "pool full" is `Status::NoMemory`.
