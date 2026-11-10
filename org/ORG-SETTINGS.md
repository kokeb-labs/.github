# Organization settings

These apply to both organizations, `kokeb-labs` and `kokeb-labs-drivers`, at
`https://github.com/organizations/<org>/settings`. They protect each organization as a whole. `kokeb_org.py` sets
what the API allows: the profile fields, base permission, repository and Pages creation, forking, web sign-off, the
default code security configuration and the Actions policy. The rest is done once by an owner in the UI and is
marked **UI** below. Recheck this list once a year, and whenever an owner or maintainer joins or leaves.

## The owner account first

The organization is only as safe as its owner accounts.

- [ ] Two-factor authentication with a **passkey or hardware security key**, plus an authenticator app as backup.
      Avoid SMS.
- [ ] Recovery codes saved offline, somewhere other than the laptop. GitHub support can't restore an organization
      whose only owner is locked out.
- [ ] An SSH or GPG **signing key** added to the account and `git config commit.gpgsign true`, so your local
      commits show as Verified.
- [ ] No classic personal access tokens. Where a token is needed, use a fine-grained one limited to the
      repositories and permissions it needs, with an expiry date.
- [ ] A **second owner** as soon as there is someone you trust, so the organization survives a lost account.
      Until then, the recovery codes are the backup.
- [ ] Notifications for security alerts go to an address you read.

## Profile

- [ ] Name, one-line description and website: from `repos.json` (**Kokeb Labs**, **Kokeb Labs Drivers**). A
      public contact email on the domain (for example `hello@`) once it is live.
- [ ] **UI:** avatar `brand/mark/avatar-500.png`, for both organizations.
- [ ] **UI:** **Verified domain** (Settings > Verified and approved domains) once the domain is bought, for both
      organizations. It puts a Verified badge on the organization page and stops look-alike organizations from
      claiming it.

## Authentication security

- [ ] **UI:** **Require two-factor authentication** for everyone in the organization.

## Member privileges

| Setting | Value | Why |
| --- | --- | --- |
| Base permissions | Read | Members see everything; write comes from teams |
| Repository creation | Owners only (members: none, public or private) | Every new repository goes through `repos.json` |
| Repository forking | Don't allow forks of private repositories | Unreleased work stays inside |
| Pages creation | Public allowed, private off | Docs sites are public |
| Admin repository permissions (**UI**) | Owners only can change visibility, delete or transfer repositories | These are hard to undo |
| Delete or transfer issues (**UI**) | Owners only | |
| Team creation (**UI**) | Owners only | |
| Allow members to create discussions in the organization (**UI**) | Yes | |

The rows without **UI** come from `policy.json` (`org_settings`).

## Actions

| Setting | Value |
| --- | --- |
| Policies | Allow `kokeb-labs` actions and reusable workflows (and in `kokeb-labs-drivers` its own), GitHub-owned actions, and the third-party actions in [`actions-allowlist.json`](actions-allowlist.json). `kokeb_org.py --section actions --apply` sets it |
| Require actions to be pinned to a full commit SHA | On (also set from `actions-allowlist.json`) |
| Fork pull request workflows from outside collaborators | Require approval for all outside collaborators (set by the script) |
| Workflow permissions | Read repository contents only; don't allow GitHub Actions to create or approve pull requests (set by the script) |
| Runners | GitHub-hosted only; no self-hosted runners on public repositories |

## Code security

- [ ] **Code security > Configurations:** **GitHub recommended** is the default for new public repositories
      (`kokeb_org.py` sets it). That turns on Dependabot, secret scanning with push protection and code scanning
      default setup as repositories are created. Existing repositories get the same features from the script's
      `security` section.
- [ ] **Private vulnerability reporting:** on, for all new public repositories.

## Third-party access

- [ ] **OAuth app policy:** access restricted (the default for new organizations). Approve only what you use, for
      example the GitHub CLI.
- [ ] **Personal access tokens:** allow fine-grained tokens with approval required; block classic tokens.
- [ ] **GitHub Apps:** install only on the repositories that need them, never on all.

## Discussions and community

- [ ] **UI:** **Discussions:** enable organization discussions with `.github` as the source repository
      (Settings > Discussions; the API can't). `kokeb_org.py` turns Discussions on in each `.github` repository,
      which gives the categories Announcements (maintainers only), General, Ideas, Polls, Q&A and Show and tell.
      `kokeb-labs-drivers/.github` has a form for each in `.github/DISCUSSION_TEMPLATE/`.
- [ ] **Sponsors:** later, once there's something to fund.

## Scaling up

- **Teams:** `maintainers` (Maintain on every repository, the code owners in team mode). Add `driver-maintainers`
  or per-area teams only when different people own different areas.
- **Paid plan (Team):** organization-wide rulesets, rulesets on private repositories, required reviewers on
  environments for private repositories. Not needed while everything is public.
- **Releases to registries** (ESP-IDF registry, PlatformIO): publish from a `release` environment that requires an
  owner's approval, with OIDC or a scoped token stored only in that environment.
