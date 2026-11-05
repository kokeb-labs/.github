# ADR-0008: One naming scheme, enforced by `clang-tidy`

- Status: Accepted
- Date: 2026-11-03

## Context

The review found methods in PascalCase, camelCase and snake_case; units written `_mA`, `_ma`, `Ma`, `Mv`, `Ua`
or as a `Unit` enum; symbols declared at global scope; driver classes named `Device` or `Driver`; and diverging
`.clang-format` files (column limit 100 in most, 120 in some) and `.clang-tidy` files with no naming rules.

## Decision

- Namespaces: `<chip>` for drivers, `kb` for kb-core, `kb::hal` for the shared HAL, `<board>` for board code,
  `<board>::app` for products. Drivers carry no org prefix ([ADR-0012](0012-unbranded-drivers.md)).
- Types, functions and public methods PascalCase; private methods camelBack; variables and parameters snake_case;
  private members `snake_case_`; constants `kPascalCase`; macros `UPPER_CASE`; units as suffixes; `Read*` for calls
  that touch the bus. Datasheet names may stay `UPPER_CASE`.
- One include root per repository or kb-core part (`kb/interfaces/BaseSpi.h`).
- One org `.clang-format` (LLVM base, 100 columns) and one `.clang-tidy` with `readability-identifier-naming`, kept
  in `kokeb-labs/.github/standards/config/` and copied unchanged into each repository's `_config/`.

## Consequences

- Names are predictable across the stack, and a reviewer no longer argues style.
- Private helpers stay camelBack, which register-level drivers already use, so they pass with few findings.
- Code brought in at 120 columns reformats once, in a PR that changes nothing else.
- Public API renames (camelCase methods, unit spellings) are breaking changes and land with the v0.1 API work.
