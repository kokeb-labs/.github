# ADR-0014: Chip-, MCU- and product-specific code each have one place

- Status: Accepted
- Date: 2026-11-05

## Context

"Platform-specific" was used for three different things: code that knows one chip, code that knows one MCU, and
code that knows one product. Treating them alike let MCU calls and `#ifdef ESP_PLATFORM` blocks spread into shared
code, and let one product's needs (its pins, its channels, its limits) end up in drivers and the core, where every
other product then carried them.

## Decision

| Kind | Where it lives | Rule |
| --- | --- | --- |
| Chip-specific | Its own driver and its handler | Fine there |
| MCU-specific | Only `interfaces/mcu/<family>/` in kb-core (above core: a board HAL's bind, a product's `platform/`) | The build selects the family and compiles only that folder; each header there `#error`s in any other build |
| Product-specific | The product's board HAL or repository | Never in kb-core or a driver |

- `KB_MCU` selects the family. Drivers that need one MCU's peripheral are listed in an MCU gate table in
  `cmake/kb_build_settings.cmake` (`"WS2812:ESP32:RMT"`), so enabling them on another MCU stops CMake.
- Differences between chip variants of one family use the vendor's capability macros, only inside
  `mcu/<family>/`.
- Shared code never tests `ESP_PLATFORM` or a similar platform macro.
- Product needs become generic extension points: config masks, profile tables passed in, backend interfaces,
  injected loggers.
- The test for a change to kb-core or a driver: could a second, made-up product with a different board use it
  without editing core?

## Consequences

- Shared code compiles for every family and on the host, and a lint can check it by searching for platform macros.
- A wrong MCU for a driver is a configure error, not a link error or a bench surprise.
- Some product requests take longer, because the generic extension point has to be designed first.
- A peripheral only one family has gets a `Base*` interface and one implementation, which is more code than a
  direct call but keeps the call sites portable.
