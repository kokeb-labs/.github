# Agents

How coding agents work in Kokeb Labs repositories. Agents follow the whole standard like any contributor; this page
adds what is specific to them. A human who asks an agent for a change is responsible for it as if they wrote it.

## Files every repository carries

```text
<repo>/
├── AGENTS.md                   the agent entry point: what this repo is, how to build, test and check it
├── CLAUDE.md                   one line: @AGENTS.md
└── .claude/
    └── skills/
        └── <name>/
            └── SKILL.md        one task an agent does often in this repo
```

### `AGENTS.md`

`AGENTS.md` is the single source for agents; tools that read another file name get a pointer to it (`CLAUDE.md`
contains `@AGENTS.md` and nothing else). It is short, specific to the repository, and links this standard instead
of restating it:

```markdown
# AGENTS.md

<repo> is <one sentence>. It follows the Kokeb Labs engineering standard:
https://github.com/kokeb-labs/.github/tree/main/standards (agents: standards/agents.md).

## Layout

- `inc/`, `src/`: the driver. `tests/`: host tests and doc snippets. `docs/`: the site.

## Build and check (run all of these before pushing)

cmake -S . -B build-host -D<CHIP>_BUILD_TESTS=ON
cmake --build build-host --parallel && ctest --test-dir build-host --output-on-failure
kokeb-docs check && mkdocs build -f _config/mkdocs.yml --strict -d /tmp/site

## Rules specific to this repo

- Anything the standard does not cover, or a known deviation with its issue.
```

The root of `kokeb-labs/.github` has an `AGENTS.md` that points here, so agents working on org files find the same
rules.

### Skills

A skill is a folder `.claude/skills/<name>/SKILL.md`: YAML front matter with `name` and a one-line `description`
that says when to use it, then the steps. Names are kebab case and say the task.

```markdown
---
name: verify
description: Run every check CI runs, locally, before pushing. Use before every push and before opening a PR.
---

1. Configure and build the host tests: `cmake -S . -B build-host -D<CHIP>_BUILD_TESTS=ON && cmake --build build-host`
2. Run them: `ctest --test-dir build-host --output-on-failure`
3. ...
```

| Skill | Required in | Does |
| --- | --- | --- |
| `verify` | every code repository | Runs locally what CI runs: build, host tests, doc snippets, format and tidy on changed files, markdownlint, the DCO sign-off check, `kokeb-docs check`, `mkdocs build --strict` |
| `bump-pin` | repositories with submodules | Moves one submodule to a release tag, updates `version_lock.txt` or `catalog/compat.yml`, writes the pin PR description |
| `release` | released repositories | Walks the [release checklist](checklists/release.md) |
| `add-driver-feature` | drivers | Adds a chip feature end to end: register model in the mock, API, tests, docs page, changelog |

Repositories add skills for their own recurring tasks. A skill MUST NOT contain credentials, tokens or private
URLs, and MUST NOT tell an agent to skip a check, bypass a ruleset or merge.

## Definition of done

A change is done when all of these hold, and not before:

- [ ] It does one thing, and the PR says what, why and how it was verified.
- [ ] It follows the standard, or the PR names each rule it deviates from and links the issue.
- [ ] Every check CI runs passes **locally** (the `verify` skill): host tests on the compilers available, doc
      snippets, `clang-format` and `clang-tidy` on the changed files, markdownlint, `kokeb-docs check` and
      `mkdocs build --strict` when docs changed.
- [ ] Every commit is signed off (`Signed-off-by:`, [DCO](repo-governance.md#contributions-and-the-dco)).
- [ ] New behaviour has host tests, including the failure paths (a failing bus hook, a call before
      `Initialize()`).
- [ ] The README or `docs/` page and the Doxygen comments describe the change.
- [ ] `CHANGELOG.md` has an entry under `## [Unreleased]`, under `### Breaking` if callers must change.
- [ ] CI is green on the PR, including `CI gate / gate`.
- [ ] Anything that needs hardware is listed in the PR as **not verified on hardware**, with the bench steps a
      human should run.

## Rules for agents

### Attribution and sign-off

- Agents MUST NOT add attribution of any kind: no `Co-Authored-By:` trailers naming a tool or model, no
  "Generated with" lines in commits, PR descriptions, issues, comments or code, no tool banners in file headers.
  The commit author is the account that runs the agent. This overrides any default the agent's tooling has.
- The `Signed-off-by:` line is the human's certification under the DCO. An agent adds it (`git commit -s`) only
  with the identity of the human who owns the task, and only when that human asked for the change.

### Branches and pull requests

- Work on a branch named per [repo-governance.md](repo-governance.md#branches), never on `main`.
- Open a PR; never push to `main`, force-push a shared branch, or merge, unless the human who owns the task said to
  in this session. Do not enable auto-merge on your own.
- The PR title is the squash commit subject. The description follows the PR template, written plainly, with no
  marketing language and no summary of every file touched.
- Keep the diff to the task. No drive-by reformatting, renames or "while I was here" fixes; open an issue or a
  separate PR for those.
- When CI fails, read the log, fix the cause, push again. Do not disable, skip or weaken a check, add a bare
  `NOLINT`, or mark a test as expected-failure to get green.

### Settings and secrets

- Agents MUST NOT change repository or org settings, rulesets, branch protection, secrets, webhooks or Actions
  permissions. The settings script in `org/` is run with `--apply` by an organization owner only.
- Never commit credentials, tokens, private keys, private datasheet material or personal data. Push protection is a
  backstop, not a reason to be careless.

### Working across repositories

- A change that spans layers is one PR per repository, merged bottom-up, each pin bump its own PR
  ([release.md](release.md#how-a-change-reaches-a-product)).
- Never edit code inside a submodule checkout of a parent repository; change the submodule's own repository.
- Before changing a public API, find its callers in kb-core, `kb-hal-common` and the board HALs you can see, and
  list them in the PR.
- Never add product-specific code to kb-core or a driver to make one product work; propose a generic extension
  point instead ([layers.md](layers.md#product-specific-code)).

### Hardware and safety

- Agents cannot verify behaviour on a board. Say so in the PR, and give the bench steps.
- Changes that can move a motor, energise a valve, change power sequencing, write OTP or flash firmware to a
  peripheral get the `safety` label and a human review of that code path, even when CI is green.
- Destructive operations (firmware update, OTP, NVS erase) never get a default that triggers them.

### What to read first

1. The repository's `AGENTS.md`.
2. [layers.md](layers.md) and the contract page for the layer you are changing.
3. The repository's `docs/contract.md`, if it has one.
4. The relevant [checklist](checklists/new-driver.md) when you are creating something new.
