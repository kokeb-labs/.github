# Checklist: release one repository

Copy this list into the `Release vX.Y.Z` PR. [release.md](../release.md) is the rule; the wave order is on that
page.

```markdown
### Before
- [ ] Every repository this one pins is released, and the pins point at those tags; `version_lock.txt` or `catalog/compat.yml` updated
- [ ] CI green on `main` with the pinned ESP-IDF; no open `safety` issues against this version
- [ ] `## [Unreleased]` complete: every breaking change under `### Breaking` with what callers change; headings normalised
- [ ] Version chosen: breaking → next minor (0.y+1.0), otherwise next patch; `-rc.N` while benching

### Prepare (prepare-release workflow, or by hand)
- [ ] `## [Unreleased]` rolled into `## [X.Y.Z] - YYYY-MM-DD`, empty `## [Unreleased]` left above it
- [ ] Version bumped in the build settings (`cmake/<chip>_build_settings.cmake` or `cmake/kb_build_settings.cmake`), `driver.yml`, `PROJECT_NUMBER` in `_config/Doxyfile` and any hand-written header; the version test passes
- [ ] Builds with `add_subdirectory()` and with `find_package()` (`<chip>::<chip>`, or each `kb::<part>`) in the install-consumer test
- [ ] kb-core: `catalog/compat.yml` regenerated, MCU gate table agrees, train name `kb YYYY.N` set
- [ ] PR titled `Release vX.Y.Z`, every commit signed off, CI gate green, squash-merged

### Tag
- [ ] Tag `vX.Y.Z` (or `vX.Y.Z-rc.N`) on the merge commit on `main`; pushed with the App token so workflows run
- [ ] Release workflow passed: tag matches the declared version, commit is on `main`, body is the changelog section
- [ ] Release notes state the bench status: MCU, board and test list, or **CI-only**; kb-core notes list every pinned driver and the train
- [ ] Products: `.bin`, `.elf`, `sha256` and `sdkconfig` attached; NVS or partition changes carry the erase or migration step
- [ ] Docs published for the tag; an `-rc` did not move `latest`

### After
- [ ] Consumers' pin-bump PRs opened (bump bot or by hand), linking this release
- [ ] For an rc that passed the bench: the same commit tagged `vX.Y.Z`
```
