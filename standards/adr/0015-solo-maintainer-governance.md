# ADR-0015: Governance for one maintainer, open to contributors

- Status: Accepted
- Date: 2026-11-05

## Context

Kokeb Labs has one maintainer and wants outside contributions. Rules written for a team (one approving review on
every PR) block a single maintainer from merging their own work, and the usual workaround, a bypass, removes the
checks along with the review. Without a review, the remaining safeguards have to come from the rulesets and CI.
Contributors also need to know under what terms their code comes in, without the friction of a CLA.

## Decision

- `main` changes only through PRs, squash-merged, with linear history and signed commits; GitHub signs the squash
  commit it creates.
- The required check is `CI gate / gate`. Conversations must be resolved before merge.
- `main` cannot be force-pushed or deleted; `v*` tags are protected.
- While there is one maintainer, PRs need 0 approvals and the owner merges their own PRs through a PR. When a
  second maintainer joins, PRs need one approving review from a code owner, and CODEOWNERS moves to the
  `maintainers` team.
- Contributions are accepted under the repository's licence with a DCO `Signed-off-by:` on every commit, checked
  by CI as part of the gate. There is no CLA.
- Vulnerabilities are reported privately through GitHub private vulnerability reporting.
- The code is MIT, but the Kokeb Labs name and logos are not licensed by it; a trademark policy covers them.

## Consequences

- The maintainer works under the same rules as contributors; nothing needs a bypass.
- Every change on `main` is a signed, single, revertable commit with a green gate.
- Without a second reviewer, CI and the checklists carry more of the review; safety-relevant changes get the
  `safety` label and a careful self-review.
- Adding a maintainer is a ruleset and CODEOWNERS change, not a new process.
