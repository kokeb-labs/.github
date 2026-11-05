# Threading and timing

One lock, one clock and one delay above the platform bind, and one tick rate everywhere. Decision for the tick:
[ADR-0006](adr/0006-freertos-1khz-tick.md).

## Who may call the RTOS

| Code | RTOS access |
| --- | --- |
| Drivers | None. Drivers do not lock, sleep or create tasks; they wait only through the port's delay hooks. |
| kb-core `utils`, `pincfg` | None. |
| kb-core `interfaces/base/` | None directly; MAY use `kb::rtos` types. `mcu/<family>/` classes MAY use the SDK's own primitives internally. |
| kb-core `rtos/` | The only code that includes RTOS headers, and only in the selected backend (`freertos/`, `threadx/`, `none/`). |
| Handlers, HALs, products | `kb::rtos` only. |
| `bsp_bind/<family>/`, product `platform/` | MAY use the SDK and RTOS directly for start-up and family-specific work. |

Raw `xTaskCreate`, `xSemaphoreTake`, `vTaskDelay`, `std::mutex` or `std::thread` above the bind is a defect.

`KB_RTOS=FREERTOS|THREADX|NONE` selects the backend and defines exactly one of `KB_RTOS_FREERTOS`,
`KB_RTOS_THREADX` or `KB_RTOS_NONE` (host tests and bare-metal). Code above `kb::rtos` MUST work on all three;
anything backend-specific stays inside the backend folder.

## One lock

- The only mutex above the bind is `RtosMutex`, taken with `MutexLockGuard` (`RtosUniqueLock<RtosMutex>`):

  ```cpp
  #include "kb/rtos/RtosMutex.h"

  kb::Result<float> Zp100Handler::ReadPressurePa() noexcept {
    MutexLockGuard lock(mutex_);
    // ...
  }
  ```

- No other mutex family exists above the bind: no per-HAL mutex wrappers, no private lock inside a protocol
  stack. A component that needs a lock takes an `RtosMutex`.
- Locks are held for the duration of one call. No lock is held across a `DelayMs()` longer than the operation
  requires, across a callback into other code, or across a call into another handler.
- Lock order: handler mutex, then bus mutex. Managers call handlers without holding their own lock when they can;
  when they cannot, the order is manager, handler, bus.
- ISRs never take a mutex. They set an `OsEventFlags` bit or give a `SignalSemaphore` and return.

## One clock

- The only time source above the bind is `kb::MonotonicUs()` (`kb/interfaces/Time.h`): microseconds since boot,
  64-bit, monotonic, safe from any task and from ISRs. `base/` declares it; the selected family's
  `mcu/<family>/` folder defines it.
- `esp_timer_get_time()`, `xTaskGetTickCount()`, `HAL_GetTick()` and `std::chrono::steady_clock` are not used above
  the bind. The bind's `MonotonicMicros()` returns the same counter and exists so the host bind can drive a fake
  clock in tests.
- Durations are `uint32_t` or `uint64_t` with a unit suffix (`timeout_ms`, `period_us`). Deadlines are compared
  by subtraction, never with `>`:

  ```cpp
  const uint64_t deadline_us = kb::MonotonicUs() + timeout_us;
  while (static_cast<int64_t>(kb::MonotonicUs() - deadline_us) < 0) { /* poll */ }
  ```

## Delays

A delay waits **at least** the requested time, never less.

| Delay | Call | Behaviour |
| --- | --- | --- |
| 1 ms and longer | `os_delay_msec(ms)` (`kb::rtos`) | Blocks the task. Converts to ticks rounding up, then adds one tick, because the first tick can arrive at once; at 1 kHz a 1 ms delay waits between 1 and 2 ms |
| Under 1 ms | `kb::DelayUs(us)` (`kb/handlers/common/Delay.h`) | Busy-waits on `kb::MonotonicUs()` until at least `us` have passed; no RTOS call |
| In a driver | the port's `DelayUs()` / `DelayMs()` hooks | Implemented by the adapter with the two rows above |

- `kb::DelayUs()` with 1000 µs or more rounds up to whole milliseconds and calls `os_delay_msec()`, so a datasheet
  minimum of 2.5 ms never becomes 2 ms.
- A delay of 0 returns at once (or yields, on an RTOS backend); it does not wait a tick.
- Busy-waits longer than 100 µs SHOULD be avoided in tasks above idle priority; restructure as a poll with a
  millisecond delay.
- `kb::DelayUs()` and `kb::DelayMs()` MUST NOT test `ESP_PLATFORM` or any MCU macro; the MCU-specific part is in
  `kb::MonotonicUs()` and the rtos backend.

## The 1 kHz tick

Every FreeRTOS project runs at 1000 Hz: products, board HALs, kb-core and every driver's `examples/esp32` project.
ESP-IDF's default of 100 Hz turns a 1 ms wait into 10 to 20 ms, and the millisecond helpers in `kb::rtos` assume
1 kHz.

- Set `CONFIG_FREERTOS_HZ=1000` in `sdkconfig.defaults`. A project that still commits a full `sdkconfig` sets it
  there too, because a committed `sdkconfig` overrides the defaults files.
- Convert milliseconds with `pdMS_TO_TICKS()` (inside the rtos backend) or the `kb::rtos` helpers. Never pass a
  raw tick count that assumes a rate.
- At 1 kHz, `pdMS_TO_TICKS()` overflows its 32-bit arithmetic above about 71 minutes, and the tick counter wraps
  after about 49.7 days: compare tick deadlines with `(int32_t)(now - deadline) > 0`.
- The driver and board HAL templates write the setting into new projects. CI SHOULD fail a build whose effective
  `CONFIG_FREERTOS_HZ` is not 1000.
- ThreadX builds SHOULD use a 1 kHz kernel tick as well, so timing behaves the same on STM32.

## Tasks

- Tasks are created through `kb::rtos` (`BaseThread`, `BaseThreadsManager`) by the product or a HAL manager, never
  by a handler or a driver.
- Stack sizes and priorities are named constants in one header per product (`<board>::app::kTaskConfig`), not
  literals at the call site.
- Core affinity is a product decision, in that header. HAL code does not assume a dual-core MCU.
- Work that must happen at a fixed rate uses `PeriodicTimer` or a task loop on `os_delay_msec()` with drift
  correction, not a chain of delays.

## What crosses tasks

- Data shared between tasks is either protected by one `RtosMutex`, passed through an `OsQueue`, or published with
  `SeqlockSnapshot` for one writer and many readers.
- Callbacks from handlers into the product run in the caller's task. A callback that must reach another task posts
  to a queue.
