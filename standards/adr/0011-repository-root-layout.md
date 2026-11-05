# ADR-0011: Repository root layout

- Status: Accepted
- Date: 2026-11-03

## Context

A driver template whose root held about twenty entries (`Doxyfile`, `mkdocs.yml`, `Kconfig`, `idf_component.yml`,
`.clang-format` and `.clang-tidy` as symlinks into `_config/`, `CONTRIBUTING.md`, `SECURITY.md` and `TEMPLATE.md`
next to the README) did not let a reader see at a glance what a repository is, and the symlinks hid where the real
configuration lived: two names for one file, broken on Windows checkouts, and easy to edit in the wrong place. Tool
configuration was split between the root and `_config/` with no rule for which went where.

ESP-IDF support was a wrapper component under `examples/esp32/components/` that sourced the root `Kconfig` and the
build settings, plus a root `idf_component.yml` that no release used: the component manager does not need a
manifest for a git dependency, and the stack does not publish to the ESP Component Registry. The layout also read
as if the drivers were ESP32 drivers, though their code is MCU-agnostic and ESP32 is only the first example
platform.

## Decision

1. **The root holds only (a) files GitHub or a tool requires at the root, and (b) the files a reader looks for
   first.** For a driver or standalone library repository that is:
   - Files: `README.md`, `LICENSE`, `CHANGELOG.md`, `CMakeLists.txt`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`,
     `.gitmodules`, and `driver.yml` in a driver (its metadata, read by kb-core's catalog).
   - Folders: `.github/`, `.claude/`, `_config/`, `cmake/`, `docs/`, `examples/`, `inc/`, `src/`, `tests/`,
     `tools/`.

   Other kinds keep their own source folders (kb-core: `utils/`, `rtos/`, `interfaces/`, `handlers/`, `drivers/`,
   `catalog/`; `kb-hal-common`: `include/`, `lib/`, `templates/`) and add only what a tool requires at the root,
   named in their `AGENTS.md` (for example `CMakePresets.json`, which CMake reads only from the source root).
2. **One location for tool configuration: `_config/`.** clang-format, clang-tidy, `Doxyfile`, `mkdocs.yml`
   (`docs_dir: ../docs`), `Kconfig`, markdownlint, yamllint and lychee live there. Every command and workflow names
   the path (`--style=file:_config/.clang-format`, `--config-file=_config/.clang-tidy`,
   `mkdocs build -f _config/mkdocs.yml`, `mkdocs_config` / `doxygen_config` in the docs workflow). Doxygen runs
   from the root, so paths inside `_config/Doxyfile` stay relative to the root.
3. **No symlinks.** Editors that find `.clang-format` / `.clang-tidy` only by name use a local copy that
   `.gitignore` lists; nothing at the root is a link.
4. **`CONTRIBUTING.md` and `SECURITY.md` live in `.github/`**, where GitHub reads them as well.
5. **One root `CMakeLists.txt` serves every build.** Under `ESP_PLATFORM` it is the ESP-IDF component
   (`idf_component_register()` from `cmake/<chip>_build_settings.cmake`, `KCONFIG _config/Kconfig`); otherwise it
   is the CMake library with the `<chip>::<chip>` alias and install/export. An ESP-IDF project uses the repository
   directly: `EXTRA_COMPONENT_DIRS`, a checkout under `components/`, or a component-manager git dependency. There
   is no root `idf_component.yml` and no example wrapper component. A manifest is added only if registry
   publishing is chosen. This `ESP_PLATFORM` branch is build glue; source files never test `ESP_PLATFORM`
   ([ADR-0014](0014-three-kinds-of-specific.md)).
6. **Drivers and libraries are MCU-agnostic.** Platform code lives only in `examples/<platform>/`, one
   self-contained folder per platform carrying its own port, built by CI. Every repository ships `examples/host/`,
   which runs on any PC and is built and run in the host tests. Plain CMake covers STM32, RP2040, nRF and host
   builds; Zephyr, Arduino or PlatformIO manifests are added only when a user needs them, without a second copy
   of the sources. kb-core's `interfaces/mcu/<family>/` and board HALs, which are MCU-specific by design through
   their binds, are the documented exceptions.

## Consequences

- A reader sees the README, the licence, the changelog and the build entry point, and every configuration is in
  one obvious place. The template's setup self-test fails when a generated root holds anything else.
- Tools are called with a path. The lint workflow takes `clang_format_config` / `clang_tidy_config`; the docs
  tooling (`kokeb-docs`) takes the folder that holds `docs_dir` as the repository root, finds `_config/mkdocs.yml`
  on its own and accepts `kokeb-docs -f`.
- ESP-IDF names a component after its folder, so a project that uses `EXTRA_COMPONENT_DIRS` on a checkout requires
  the checkout folder's name; a submodule under `components/<chip>` or a component-manager key gives a stable name.
- Room for more platforms without touching the root: a new `examples/<platform>/` with its CI job, and a manifest
  only when a build system cannot use the root `CMakeLists.txt`.
