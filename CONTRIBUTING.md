# Contributing to Kokeb Labs

This applies to every repository in the `kokeb-labs` organization unless the repository has its own
`CONTRIBUTING.md`. The full rules are in the [engineering standard](standards/README.md); this page is the short
version for a first pull request. Where they differ, the standard wins.

## Before you start

- For anything larger than a small fix, open an issue or a discussion first so we can agree on the approach.
- New chip driver? Start from [`driver-template`](https://github.com/kokeb-labs/driver-template) and run
  `python3 tools/setup.py`; it produces a complete, tested repository for your chip.

## Branches and pull requests

- `main` is the only long-lived branch and only changes through pull requests.
- Branch from `main` as `feat/<topic>`, `fix/<topic>`, `docs/<topic>`, `ci/<topic>` or `chore/<topic>`.
- One change per pull request; prefer under about 400 changed lines and split larger work into a series.
- Fill in the pull request template: what changed, why, how you verified it.
- Pull requests are squash-merged. The title becomes the commit subject on `main`, so write it as one.
- Add an entry under `## [Unreleased]` in `CHANGELOG.md` for anything a user would notice; under `### Breaking`
  if they must change their code.

## Commit messages

- Subject in the imperative mood, under about 72 characters, no trailing period: `Add FIFO read`, not `Added fifo`.
- An optional body after a blank line says why, not what.
- No attribution trailers other than the sign-off below.

## Sign-off (DCO)

Every commit carries a `Signed-off-by:` line certifying the
[Developer Certificate of Origin](https://developercertificate.org/): that you wrote the change or have the right to
submit it under the repository's licence. Add it with `git commit -s`. The name and email must match the commit
author. CI checks it; a pull request with an unsigned commit can't merge. Edits made in the GitHub web editor are
signed off automatically.

To fix a missing sign-off on your branch: `git rebase --signoff main`, then force-push your branch.

## The CI gate

Every pull request must pass its repository's CI. The one required check is `CI gate / gate`. Depending on the
repository it runs host tests, C++ lint and static analysis, example builds for ESP32 and other targets, Markdown
and YAML lint, the docs build and a link check. Don't merge on red; fix the cause, or fix the check and say why.

If a change affects behaviour on hardware, say in the pull request which MCU and board you ran it on and what you
observed, or write "not verified on hardware" with the steps someone should run.

## Timing

Every FreeRTOS project in the organization runs the tick at 1000 Hz (`CONFIG_FREERTOS_HZ=1000` in
`sdkconfig.defaults`, and in `sdkconfig` if one is committed). Delays round up and wait at least the requested time.
Convert milliseconds with the kb-core helpers, never with a raw tick count. Details:
[threading and timing](standards/threading-and-timing.md).

## How a change reaches a product

Drivers are separate repositories; kb-core includes each one as a Git submodule pinned to a release tag.

1. Change the driver (for example `driver-pcal95555`), merge, and tag a release if consumers need it.
2. In `kb-core`, bump that driver's submodule to the new tag in its own pull request, and update the handler if
   the API changed.
3. Board HALs and products bump their `kb-core` pin the same way.

Never point a submodule at an unmerged branch, and never edit code inside a submodule checkout; change the
submodule's own repository first.

## Documentation

Update the README and `docs/` in the same pull request as the code they describe. Public headers carry Doxygen
comments. See [documentation](standards/docs.md).

## Conduct and security

By taking part you agree to the [code of conduct](CODE_OF_CONDUCT.md). Report vulnerabilities privately as
[SECURITY.md](SECURITY.md) describes, never in an issue.
