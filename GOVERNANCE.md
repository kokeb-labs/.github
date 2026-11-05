# Governance

## Roles

| Role | Who | Can |
| --- | --- | --- |
| Owner | Organization owners | Everything, including settings, rulesets, releases and the name and logo |
| Maintainer | Members of the `maintainers` team | Review and merge pull requests, triage issues, cut releases of the repositories they maintain |
| Contributor | Anyone | Open issues, discussions and pull requests |

Today one owner maintains every repository. The rules below already work for more people; adding a maintainer is a
team change, not a rewrite.

## How decisions are made

- **Day to day:** in pull requests. A maintainer merges when CI passes and the change follows the
  [engineering standard](standards/README.md).
- **Rules and architecture:** an ADR in [`standards/adr/`](standards/adr), proposed in a pull request to this
  repository and open for comment for at least seven days unless it fixes a defect.
- **Disagreements:** discussed in the pull request or ADR. If maintainers still disagree, the owners decide and
  record why.

## Becoming a maintainer

After a record of good pull requests and reviews in a repository, a maintainer or owner can propose you. Owners add
you to the `maintainers` team. When the second maintainer joins, the review rule changes from "pull request
required" to "one approving review from a code owner" (see [`org/README.md`](org/README.md#review-mode)).

## Contributions and licence

Contributions are accepted under the repository's licence (MIT) with a Developer Certificate of Origin sign-off on
every commit; see [CONTRIBUTING.md](CONTRIBUTING.md#sign-off-dco). There is no contributor licence agreement.
