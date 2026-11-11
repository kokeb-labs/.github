# Checklist: new repository

The life of a repository from creation to its first release, in the order that works. A driver also follows
[new-driver.md](new-driver.md) and the template's `release` skill; the reasons for the order are in the template's
`docs/repo-setup.md`, section 6.

```markdown
### 1. Create and declare
- [ ] Created from the template (`driver-template`, `board-template`) in the right organization, **private**
- [ ] Entry in `org/repos.json` by pull request (description, topics, homepage; `"required_checks": []` until its gate
      exists; `"code_scanning": "advanced"` if it runs its own CodeQL); merged
- [ ] `python3 org/kokeb_org.py --org <org> --repo <name> --apply`

### 2. Build it
- [ ] Scaffolded, filled in and reviewed per the template's `new-driver-from-template` skill
- [ ] `tools/preflight.sh` ends with `0 failure(s)` before every push; every change is a pull request, squash-merged
- [ ] No personal email or attribution anywhere: commits use the noreply address, no co-author lines, no tool names

### 3. Green `main`
- [ ] `CI` on `main` is green, including `CI gate / gate` (a red check is read before it is re-run; infrastructure
      failures only are re-run, see the `release` skill, section 5)
- [ ] Independent review done before the first release (drivers: the `safety-reviewer` agent, by a different author)

### 4. First release candidate
- [ ] `vX.Y.Z-rc.1` tagged on that commit; its CI is green and the pre-release exists with firmware, SBOM, checksums
- [ ] The release notes say the bench status: the board and tests, or **CI-only, not verified on hardware**

### 5. Public
- [ ] `gh repo edit <org>/<name> --visibility public --accept-visibility-change-consequences`
- [ ] `python3 org/kokeb_org.py --org <org> --repo <name> --apply`: rulesets, secret scanning, push protection,
      CodeQL, private vulnerability reporting (run again after a few seconds if it answers 422)
- [ ] Pages enabled from `gh-pages`, root; `https://<org>.github.io/<name>/` loads
- [ ] `python3 org/kokeb_org.py --org <org> --repo <name> --check` ends with `0 change(s) pending`

### 6. Final release
- [ ] Benched, or approved to go straight to the final release (a driver no board uses); the same commit is tagged
      `vX.Y.Z`; docs published and `latest` moved
- [ ] Pin-bump pull requests opened in the repositories that consume it
```
