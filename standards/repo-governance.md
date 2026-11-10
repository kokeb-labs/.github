# Repository governance

How every Kokeb Labs repository is set up and how changes reach `main`. The org has one maintainer today and is
open to contributors; the rules already work for more people, and the one rule that changes when a second
maintainer joins is called out below. Decision: [ADR-0015](adr/0015-solo-maintainer-governance.md).

Settings are kept as code in this repository's `org/` folder (`org/kokeb_org.py`), for both organizations,
`kokeb-labs` and `kokeb-labs-drivers`. It shows the plan without `--apply`; only an organization owner runs it with
`--apply`.

## Branches

- `main` is the only long-lived branch. Nobody pushes to it; every change is a pull request, including the
  maintainer's own.
- Work branches are named by kind, then a short topic in kebab case:

  | Prefix | For |
  | --- | --- |
  | `feat/<topic>` | New behaviour or API |
  | `fix/<topic>` | A bug fix |
  | `docs/<topic>` | Documentation only |
  | `ci/<topic>` | Workflows, lint and build configuration |
  | `chore/<topic>` | Pin bumps, version bumps, renames, housekeeping |
  | `release/x.y` | A maintenance line for an older minor (`release/0.1`), created from its tag by a maintainer, changed only by PR |

- Branches are deleted automatically when their PR merges (see [Merge settings](#merge-settings)).
- A submodule never points at an unmerged branch.

## Pull requests

- **Squash merge only**, and the PR title becomes the commit subject on `main`. Write the title as a commit
  subject: imperative, under about 72 characters, no trailing period (`Add ZP100 FIFO read`).
- **One logical change** per PR, ideally under about 400 lines of diff. Larger work is a series of PRs, each green.
- **The PR template** (`.github/PULL_REQUEST_TEMPLATE.md` in `kokeb-labs/.github`, inherited by every repository
  without its own) is filled in: summary, why, how it was verified (CI, host tests, which MCU and board), the
  checklist.
- **Docs and changelog in the same PR** as the code: the README or `docs/` page for any behaviour or API change, and
  an entry under `## [Unreleased]` in `CHANGELOG.md` ([release.md](release.md#changelog)).
- **A deviation from the standard** is named in the PR description with the rule and the tracking issue.
- **A pin bump** is its own PR that links the PR or release it pulls in and notes API or build-setting changes.
- **No attribution lines** in commits, PR descriptions, issues or comments other than the DCO sign-off: no
  `Co-Authored-By:` trailers for tools, no "Generated with" footers. Authorship is the account that opened the PR.
- **Review**: every conversation resolved before merge. While the org has one maintainer, no approving review is
  required and the maintainer merges their own PRs, always through a PR. When a second maintainer joins, every PR
  needs one approving review from a code owner ([Review mode](#review-mode)).

## Contributions and the DCO

- Contributions are accepted under the repository's licence (MIT; CERN-OHL-P-2.0 for hardware designs,
  [ADR-0009](adr/0009-licensing.md)). There is no contributor licence agreement.
- Every commit carries a `Signed-off-by:` line certifying the
  [Developer Certificate of Origin](https://developercertificate.org/): `git commit -s`. The name and email match
  the commit author.
- CI checks every commit of a PR for the sign-off. The DCO job is one of the jobs the `CI gate` needs, so a PR with
  an unsigned commit cannot merge.
- A missing sign-off is fixed on the branch with `git rebase --signoff main` and a force-push of that branch (never
  of `main`).

## Issues and labels

Issues use the org forms: **Bug report**, **Driver request** and **Feature request**. Blank issues are off;
questions go to the org discussions (<https://github.com/orgs/kokeb-labs/discussions>), and vulnerabilities to a
private security advisory ([Security](#security)).

Every repository uses this label set:

| Label | Meaning |
| --- | --- |
| `bug` | Something behaves wrong (set by the bug form) |
| `enhancement` | New capability or API change (set by the feature form) |
| `driver-request` | A new chip driver (set by the driver request form) |
| `safety` | Can damage hardware or cause unsafe motion, heat or pressure; fixed before anything else |
| `breaking` | Changes a public API, a config layout or NVS; needs `### Breaking` in the changelog |
| `standard` | Brings the repository in line with this standard |
| `documentation` | Docs only |
| `ci` | Workflows and tooling |
| `dependencies` | Dependency and action updates (set by Dependabot) |
| `good first issue` | Small and well described |

The settings script creates the labels.

## CODEOWNERS

GitHub has no org-wide CODEOWNERS, so each repository carries `.github/CODEOWNERS`:

```text
# Default reviewers for every path in this repository.
* @N3b3x
```

When the `maintainers` team exists, the line becomes `* @kokeb-labs/maintainers`. A repository started from a
template already has the file.

## Rulesets

The rulesets apply to every public repository:

| Ruleset | Applies to | Rules | Bypass |
| --- | --- | --- | --- |
| `main-integrity` | default branch | no deletion, no force push, linear history, signed commits | nobody |
| `main-review` | default branch | changes through a PR, squash only, resolved conversations, required check `CI gate / gate`; 0 approvals while solo | nobody |
| `release-tags` | `v*` tags | no deletion, no moving | org owners, to fix a tag pushed by mistake before its release is published |

Signed commits on `main` cost a contributor nothing: GitHub signs the squash commit it creates when a PR merges.
Commits on work branches need not be signed.

### Review mode

| Maintainers | `main-review` requires |
| --- | --- |
| One | A PR, resolved conversations and a green `CI gate / gate`; 0 approvals |
| Two or more | The same, plus one approving review from a code owner; stale approvals dismissed on push |

The switch is one change to the ruleset, made by an owner when the second maintainer joins, together with the
CODEOWNERS change above.

### The required check

Every repository's CI ends in one gate job from the reusable `ru-ci-gate.yml`
(`kokeb-labs/ci-tools/.github/workflows/ru-ci-gate.yml@v1`), named `CI gate`, so the single required status check
is always:

```text
CI gate / gate
```

The gate is required only once the repository has the job, because a required check that never runs blocks every
PR. A repository created from a template has it from the first commit.

The gate MUST list every other job in `needs`, including the DCO check, and use `if: always()`; with
`verify_needs: true` (the default) the gate checks this itself.

## Security

Every public repository has secret scanning, push protection, Dependabot alerts, Dependabot security updates, and
**private vulnerability reporting**. Vulnerabilities are reported through a private security advisory on the
repository, never in an issue; the org `SECURITY.md` says how.

Workflows follow least privilege: `permissions: contents: read` at the top, wider permissions only on the job that
needs them, and no secrets in workflows triggered by forks.

## Dependabot

Every repository with workflows has `.github/dependabot.yml` for GitHub Actions; repositories with Python tooling
add `pip`:

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    labels: [dependencies]
    commit-message:
      prefix: "ci"
```

Dependabot does not manage submodules: it tracks branches, and kb-core pins release tags. Submodule pins move
through the bump bot and pin-bump PRs ([release.md](release.md#pins-and-the-manifest)). Reusable workflows are
pinned to the major tag (`@v1`), which Dependabot leaves alone.

## Merge settings

Every repository, public and private, has **Automatically delete head branches** on and allows squash merging only,
with the PR title as the default commit title. The `main-review` ruleset enforces squash on public repositories; on
private repositories it is the repository setting alone.

## Licence and trademarks

- Firmware, libraries, drivers and tooling are MIT. Hardware designs are CERN-OHL-P-2.0
  ([ADR-0009](adr/0009-licensing.md)). Each repository carries its own `LICENSE`.
- The MIT licence covers the code, not the **Kokeb Labs** name or logos. Their use is governed by the
  [trademark policy](../TRADEMARKS.md). A fork distributed as its own project uses its own name; drivers make that
  easy because they carry no brand ([ADR-0012](adr/0012-unbranded-drivers.md)).

## Metadata

Every repository's description, homepage and topics are kept with the org settings in `org/`, and the portal's
catalogue reads them. Change them by PR, then an owner applies them.

## Repository root

The root holds only what GitHub or a tool requires at the root and what a reader looks for first
([ADR-0011](adr/0011-repository-root-layout.md)). For a driver or standalone library: `README.md`, `LICENSE`,
`CHANGELOG.md`, `CMakeLists.txt`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`, `.gitmodules`, `driver.yml` (drivers),
and the folders `.github/`, `.claude/`, `_config/`, `cmake/`, `docs/`, `examples/`, `inc/`, `src/`, `tests/`,
`tools/`. Other kinds keep their own source folders (kb-core: `utils/`, `rtos/`, `interfaces/`, `handlers/`,
`drivers/`, `catalog/`) and list any other root file a tool requires (such as `CMakePresets.json`) in their
`AGENTS.md`.

- Tool configuration lives in `_config/` and nowhere else; no symlinks anywhere in the repository.
- `CONTRIBUTING.md` and `SECURITY.md` live in `.github/` (or are inherited from `kokeb-labs/.github`).
- A reviewer refuses a PR that adds anything else to the root without a reason a tool imposes.

## Creating a repository

1. **Create it from the template** for its kind, in the `kokeb-labs` org, public:

   ```bash
   gh repo create kokeb-labs/driver-<chip> --public --template kokeb-labs/driver-template
   gh repo clone kokeb-labs/driver-<chip> && cd driver-<chip>
   python3 tools/setup.py --kind driver --name <chip> --bus spi|i2c|uart|adc --description "..."
   ```

   The template carries the shell: CMake layout, CI workflows with the gate and the DCO check, `_config/` with every
   tool configuration, docs page set, `driver.yml`, `CODEOWNERS`, `.github/CONTRIBUTING.md`, `.github/SECURITY.md`,
   `AGENTS.md`, `CLAUDE.md` and `.claude/skills/`, in the [root layout](#repository-root) of ADR-0011.
   `--platforms host,esp32` picks the example platforms (`host` always). The templates by kind:

   | Kind | Template | How |
   | --- | --- | --- |
   | Chip driver | [`driver-template`](https://github.com/kokeb-labs/driver-template) | `tools/setup.py --kind driver` |
   | Standalone library | [`driver-template`](https://github.com/kokeb-labs/driver-template) | `tools/setup.py --kind library` |
   | kb-core handler | `templates/handler/` in kb-core | its scaffold script, see kb-core `AGENTS.md` |
   | Board HAL | `board-hal-template` (planned); until then the example in `kb-hal-common` | in the product's organization |

2. **Add the metadata** in `org/` by PR to `kokeb-labs/.github`; an owner applies it with the settings script.
3. **Apply the settings**: merge settings, security, rulesets and labels, by the settings script.
4. **Require the gate** once the first CI run has produced `CI gate / gate` ([The required check](#the-required-check)).
5. **Wire it in**: for a driver, add it to kb-core as `drivers/driver-<chip>/`, pinned to its first release tag,
   with its handler and its `catalog/compat.yml` entry ([handler checklist](checklists/new-handler.md)).

Then follow the checklist for its kind in [`checklists/`](checklists/new-driver.md).

## Archiving

A repository that is superseded gets the `legacy` topic and a `[Legacy] ... superseded by <repo>.` description in
the metadata, a README note pointing to its successor, and is archived. Archived repositories are skipped by the
settings script.
