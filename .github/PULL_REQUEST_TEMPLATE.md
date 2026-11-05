## Summary

<!-- What changes, in one or two sentences. -->

## Why

<!-- The problem this solves. Link the issue or discussion. -->

## How verified

- [ ] CI green, including `CI gate / gate`
- [ ] Ran locally: <!-- host tests, lint, docs build; or "n/a" -->
- [ ] On hardware: <!-- MCU, board, what was run and observed; or "not verified on hardware" plus the steps to run -->

## Checklist

- [ ] Every commit is signed off (`git commit -s`)
- [ ] The title is an imperative commit subject (it becomes the squash commit)
- [ ] One logical change; no unrelated edits
- [ ] README, `docs/` and Doxygen updated for any behaviour or API change
- [ ] `CHANGELOG.md` entry under `## [Unreleased]`; breaking changes under `### Breaking`
- [ ] Tests added or updated, including failure paths
- [ ] Follows the [engineering standard](https://github.com/kokeb-labs/.github/blob/main/standards/README.md),
      or each deviation is listed here
- [ ] No secrets, credentials or vendor datasheet files
