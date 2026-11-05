# ADR-0006: FreeRTOS runs at 1 kHz everywhere

- Status: Accepted
- Date: 2026-11-03

## Context

ESP-IDF defaults to a 100 Hz tick. A millisecond delay rounds up to whole ticks, so at 100 Hz a 1 ms wait becomes
10 ms or more, which breaks datasheet timing in drivers and any 1 kHz control or CANopen loop. Some projects had
set 1000 Hz and some had not.

## Decision

- Every FreeRTOS project (products, board HALs, kb-core, every driver's `examples/esp32`) sets
  `CONFIG_FREERTOS_HZ=1000` in `sdkconfig.defaults` (and in a committed `sdkconfig`, while any remain).
- Milliseconds are converted with `pdMS_TO_TICKS()` or the `kb::rtos` helpers, never as raw tick counts; tick
  deadlines are compared by signed subtraction.
- A delay waits at least the requested time: the conversion rounds up and adds one tick.
- ThreadX builds use a 1 kHz kernel tick as well.

## Consequences

- One millisecond means one millisecond, give or take one tick, on every board and example.
- Ten times as many tick interrupts as the ESP-IDF default, a small and fixed CPU cost.
- `pdMS_TO_TICKS()` overflows above about 71 minutes and the tick counter wraps after about 49.7 days; code that
  waits that long uses `kb::MonotonicUs()` instead.
- The templates set the tick for every new project.
