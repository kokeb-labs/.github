# Checklist: new organization

Run these in order for a new organization, and again as an audit of an existing one. The reasons are in
[`org/ORG-SETTINGS.md`](../../org/ORG-SETTINGS.md); the script is `org/kokeb_org.py`. Items marked **UI** can only be
done in the GitHub web interface; everything else is a command or a pull request.

```markdown
### 0. The owner account (once per owner)
- [ ] **UI** Settings > Emails: *Keep my email addresses private* on, and *Block command line pushes that expose my
      email* on. Check: `gh api user --jq .email` prints `null`
- [ ] `git config --global user.email "<id>+<login>@users.noreply.github.com"` (the id is `gh api user --jq .id`)
- [ ] Two-factor with a passkey or security key, recovery codes stored offline, a signing key on the account
- [ ] No classic tokens; `gh` is the only OAuth app

### 1. Create it
- [ ] **UI** Create the organization on the Free plan, named `kokeb-labs-<area>`; the owner account is its owner
- [ ] **UI** Settings > Authentication security: *Require two-factor authentication*
- [ ] **UI** Avatar: `brand/mark/avatar-500.png`
- [ ] Contact and billing email are the organization's role address (`kokeblabs@gmail.com`), never a personal one;
      `repos.json` declares both, the script sets them

### 2. Declare it (one pull request to `kokeb-labs/.github`)
- [ ] `org/repos.json`: a new entry under `orgs` with `profile` (name, description, `blog`, `email`,
      `billing_email`), `actions_patterns` and `repos`
- [ ] `org/actions-allowlist.json`: the organization's Actions policy
- [ ] The organization's own `.github` repository in `repos` with `"discussions": true`, `"kind": "meta"`
- [ ] Merge helper and templates know the organization (`merge_when_green.sh`, `driver-template` default org)

### 3. Its `.github` repository (public, from the existing ones)
- [ ] `profile/README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, issue forms,
      `DISCUSSION_TEMPLATE/`, pull request template
- [ ] Every contact in those files is the role address; no personal email, no tool or author attribution
- [ ] `python3 org/kokeb_org.py --org <org> --repo .github --apply`

### 4. Apply
- [ ] Plan: `python3 org/kokeb_org.py --org <org>` and read every line
- [ ] Apply: `python3 org/kokeb_org.py --org <org> --apply`
- [ ] Check: `python3 org/kokeb_org.py --org <org> --check` ends with `0 change(s) pending`

### 5. UI-only items (the script prints the ones it can read as `manual`)
- [ ] **UI** Member privileges rows marked UI in ORG-SETTINGS.md: admin repository permissions, issue transfer,
      team creation, members may create discussions
- [ ] **UI** Discussions: organization discussions on, source repository `.github`
- [ ] **UI** OAuth app policy restricted; fine-grained tokens with approval, classic blocked; Apps only on chosen
      repositories
- [ ] **UI** Verified domain, once a domain is owned

### 6. Verify
- [ ] `gh api orgs/<org> --jq '{two_factor_requirement_enabled, email, billing_email, default_repository_permission}'`
- [ ] A repository created in it by the [new repository checklist](new-repository.md) gets every setting without a
      manual step
- [ ] Date and reviewer recorded in the pull request; repeat this list once a year and when an owner joins or leaves
```
