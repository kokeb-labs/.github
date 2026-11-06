# Settings as code

Every repository in `kokeb-labs` gets the same settings, security features, Actions policy, rulesets and labels.
They are declared here and applied by one script, so a new repository is set up the same way as the first one and
drift shows up in a dry run.

| File | Declares |
| --- | --- |
| [`policy.json`](policy.json) | Settings shared by every repository, the review mode, the default required check, the Actions token policy |
| [`repos.json`](repos.json) | One entry per repository: kind, description, topics, homepage, per-repository overrides |
| [`labels.json`](labels.json) | The label set |
| [`rulesets/`](rulesets) | Branch and tag rulesets |
| [`actions-allowlist.json`](actions-allowlist.json) | The organisation's Actions policy: which third-party actions may run, and SHA pinning |
| [`ORG-SETTINGS.md`](ORG-SETTINGS.md) | Organization-level settings, set once by an owner in the GitHub UI |

## Running it

Requires `gh` authenticated as an organization owner, and Python 3.9 or newer.

```bash
python3 org/kokeb_org.py                       # plan: what would change (writes nothing)
python3 org/kokeb_org.py --apply               # write the changes
python3 org/kokeb_org.py --repo driver-tmp117  # one repository (repeatable)
python3 org/kokeb_org.py --section rulesets    # one section: settings, security, actions, rulesets, labels
python3 org/kokeb_org.py --section actions     # also the organisation's allow-list (when no --repo is given)
python3 org/kokeb_org.py --check               # exit 1 on any drift, for a scheduled CI job
```

It compares before it writes, so re-running is safe. Labels and rulesets that aren't declared here are reported and
left alone.

## Adding a repository

1. Create it (from `driver-template` for a driver or library).
2. Add its entry to `repos.json` in a pull request. A repository whose CI gate doesn't exist yet gets
   `"required_checks": []` until it does.
3. After the merge, an owner runs `python3 org/kokeb_org.py --repo <name> --apply`.

## Trying out a new action

Actions in `kokeb-labs` may only come from GitHub, from `kokeb-labs` itself, or from the third-party actions in
[`actions-allowlist.json`](actions-allowlist.json), and every one must be pinned to a full commit SHA. That stops a
compromised or retagged action from running with our tokens. It doesn't stop you from building CI:

| You want to | Do this |
| --- | --- |
| Write a new action or reusable workflow | Put it in a `kokeb-labs` repository; it is allowed at once. In the same repository call it as `uses: ./path/to/action`; from another repository pin a commit, `uses: kokeb-labs/<repo>/<path>@<full SHA>` |
| Try a change to a `ci-tools` reusable workflow | Call it from a branch while you test: `uses: kokeb-labs/ci-tools/.github/workflows/<file>.yml@<your-branch>`, then go back to `@v1` once it is released. SHA pinning applies to actions, not to reusable workflows |
| Try a third-party action | Try it first in a repository under your own account, where the organisation's policy doesn't apply. Then open a pull request here that adds it to `actions-allowlist.json` |
| Run a tool that has no action you trust | Install it in a `run:` step from its own release and check a pinned SHA-256, as `ru-docs-publish` does for Doxygen |

A pull request that adds an action answers, in the entry's fields and the description:

1. **Who maintains it?** An organisation or a well-known maintainer, with recent commits and releases.
2. **Is the SHA a real release?** The commit must be on a release tag of that repository, not a commit that exists
   only in a fork (a fork's commit can be reached by the same name and SHA).
3. **What does it run?** Read `action.yml`. A composite action can call other actions: each of them needs an entry
   too. Prefer a `run:` step when the action is only a thin wrapper.
4. **What can it touch?** The permissions of the job that uses it, and any secret passed to it. Write access needs
   a reason.
5. **Who keeps it current?** Dependabot updates the SHA and its `# vX.Y.Z` comment weekly in `ci-tools`.

After the merge an owner runs `python3 org/kokeb_org.py --section actions --apply`.

## What every repository gets

| Section | Setting |
| --- | --- |
| Merging | Squash only; the PR title and body become the commit; head branches deleted on merge; auto-merge allowed; "update branch" offered |
| Web edits | Sign-off required, so commits made in the browser pass the DCO check |
| Features | Issues on; wiki and classic projects off; Discussions only on `.github`, which hosts the organization's |
| Security (public repositories) | Secret scanning, push protection, Dependabot alerts, Dependabot security updates, private vulnerability reporting, CodeQL default setup |
| Actions | Workflow token read-only by default; workflows can't approve pull requests; runs from first-time and outside contributors' forks wait for approval |

## Rulesets

| Ruleset | Applies to | Rules | Bypass |
| --- | --- | --- | --- |
| `main-integrity` | default branch | no deletion, no force-push, linear history, signed commits | none |
| `main-review` | default branch | changes only through a pull request, conversations resolved, squash only; reviews per the review mode below | none in solo mode; owners through a pull request in team mode |
| `main-checks` | default branch | the required checks pass (default `CI gate / gate`), reported by GitHub Actions only | none |
| `release-tags` | `v*.*.*` tags | only a release workflow (or an owner) creates them; once created, nobody moves or deletes them | owners, to fix a mistake; GitHub Actions, to create the release tag |
| `major-tags` | `v1`, `v2`, … `v99` | only a release workflow (or an owner) moves the major tag every caller pins to; nobody deletes it | owners; GitHub Actions, to move the tag after a release |

Notes:

- **Signed commits** cost nothing extra here: GitHub signs every squash merge. Only pushes straight to `main` would
  need your own signing key, and those are blocked anyway.
- **Required checks are pinned to GitHub Actions** (app ID 15368), so no other app or token can report a fake
  green `CI gate / gate`.
- **Creating** a `v*.*.*` tag needs write access, which today means owners and release workflows (`ci-tools` cuts
  its own patch releases). GitHub doesn't let GitHub Actions bypass a ruleset, so creation isn't restricted
  further. Workflows from forks get a read-only token and can't create tags.
- **Moving major tags** such as `v1` in `ci-tools` don't match `v*.*.*`, so its release workflow can still move them.
- **GitHub Free** enforces rulesets on public repositories only, and has no organization-wide rulesets. The script
  applies a copy to each public repository and says which private ones it can't protect. On a paid plan these
  become one organization ruleset.

## Review mode

Both review modes turn off GitHub's *extra approval for unattributed changes*. In solo mode nobody else could
give that approval, and in team mode the code-owner review already covers it.

`policy.json` has `"review_mode": "solo"` while one person maintains the organization. A pull request is still
required, so CI runs and history stays clean, but no approval is needed, since GitHub doesn't let you approve your
own pull request.

When a second maintainer joins:

1. An owner creates the `maintainers` team (UI: **Teams** > **New team**) and gives it the **Maintain** role on
   every repository.
2. Change every `.github/CODEOWNERS` to `* @kokeb-labs/maintainers` (one pull request per repository).
3. Set `"review_mode": "team"` and run `--apply`. Pull requests then need one approving review from a code owner,
   after the last push. Owners can still merge their own pull requests through the pull request page.
