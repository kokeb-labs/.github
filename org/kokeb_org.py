#!/usr/bin/env python3
"""Keep the Kokeb Labs organizations and their repositories as declared here: organization profile and member
privileges, repository settings, security, Actions policy, rulesets and labels.

Desired state lives next to this file:
  policy.json      settings shared by every organization and repository, review mode, default required checks
  repos.json       one entry per organization (profile, extra Actions patterns) with one entry per repository:
                   kind, description, topics, homepage, overrides (`code_scanning: advanced` leaves CodeQL to the
                   repository's own workflow)
  labels.json      the label set
  rulesets/*.json  the rulesets (main-review.<mode>.json picks the review mode)
  actions-allowlist.json  both organizations' Actions policy: allowed third-party actions, SHA pinning

Default is a dry run over every organization in repos.json that prints what would change. --apply writes it.
--check exits 1 on any drift (for CI). --org limits the run to one organization (repeatable).
Re-running is safe: everything is compared first and only differences are written. Labels and rulesets that are
not declared here are reported, never deleted.

Requires gh, authenticated as an organization owner. Python 3.9+, standard library only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SECTIONS = ("settings", "security", "actions", "rulesets", "labels")


class Gh:
    """Thin wrapper over `gh api`. Writes are refused unless apply is set."""

    def __init__(self, apply: bool) -> None:
        self.apply = apply

    def call(self, path: str, method: str = "GET", body: Any = None, ok_missing: bool = False) -> Any:
        cmd = ["gh", "api", "-X", method, "-H", "Accept: application/vnd.github+json", path]
        if method == "GET" and "?" not in path:
            cmd.insert(2, "--paginate")
        data = None
        if body is not None:
            cmd += ["--input", "-"]
            data = json.dumps(body)
        res = subprocess.run(cmd, input=data, capture_output=True, text=True)
        if res.returncode != 0:
            if ok_missing and ("404" in res.stderr or "Not Found" in res.stderr or "HTTP 404" in res.stdout):
                return None
            raise RuntimeError(f"gh api {method} {path} failed: {res.stderr.strip() or res.stdout.strip()}")
        out = res.stdout.strip()
        if not out:
            return {}
        if method == "GET" and out.startswith("[") and "][" in out:  # --paginate concatenates arrays
            out = out.replace("][", ",")
        return json.loads(out)

    def write(self, path: str, method: str, body: Any = None) -> None:
        if not self.apply:
            return
        self.call(path, method, body)

    def write_retry(self, path: str, method: str, body: Any = None, tries: int = 4, wait: float = 5.0) -> None:
        """`write`, trying again after `wait` seconds while GitHub answers 422 (a change that has not propagated)."""
        for attempt in range(1, tries + 1):
            try:
                self.write(path, method, body)
                return
            except RuntimeError as err:
                if "HTTP 422" not in str(err) or attempt == tries:
                    raise
                time.sleep(wait)


def load(name: str) -> Any:
    return json.loads((HERE / name).read_text())


def subset_differs(want: Any, have: Any) -> bool:
    """True when `want` is not contained in `have` (dict keys compared recursively, lists element-wise)."""
    if isinstance(want, dict):
        if not isinstance(have, dict):
            return True
        return any(subset_differs(v, have.get(k)) for k, v in want.items())
    if isinstance(want, list):
        if not isinstance(have, list) or len(want) != len(have):
            return True
        return any(subset_differs(w, h) for w, h in zip(want, have))
    return want != have


class Run:
    def __init__(self, gh: Gh, org: str, plan: str = "") -> None:
        self.gh = gh
        self.org = org
        self.plan = plan
        self.drift = 0

    def change(self, repo: str, section: str, what: str) -> None:
        self.drift += 1
        print(f"  {section:<9} {'' if self.gh.apply else 'would '}{what}")

    # -- settings ----------------------------------------------------------------------------------------------
    def settings(self, repo: str, info: dict, entry: dict, policy: dict) -> None:
        want = dict(policy["repo_settings"])
        for key in ("description", "homepage"):
            if key in entry:
                want[key] = entry[key]
        if entry.get("discussions"):
            want["has_discussions"] = True
        if entry.get("kind") == "template":
            want["is_template"] = True
        want.update(entry.get("settings", {}))
        if info.get("visibility") != "public" and self.plan == "free" and want.pop("allow_auto_merge", None):
            print("  settings  note: auto-merge needs a paid plan on private repositories (applied once public)")
        diff = {k: v for k, v in want.items() if info.get(k) != v}
        if diff:
            self.change(repo, "settings", "set " + ", ".join(f"{k}={v!r}" for k, v in diff.items()))
            self.gh.write(f"repos/{self.org}/{repo}", "PATCH", diff)
        if "topics" in entry and sorted(info.get("topics", [])) != sorted(entry["topics"]):
            self.change(repo, "settings", f"set topics={entry['topics']}")
            self.gh.write(f"repos/{self.org}/{repo}/topics", "PUT", {"names": entry["topics"]})

    # -- security ----------------------------------------------------------------------------------------------
    def dependabot(self, repo: str) -> None:
        if self.gh.call(f"repos/{self.org}/{repo}/vulnerability-alerts", ok_missing=True) is None:
            self.change(repo, "security", "turn on Dependabot alerts")
            self.gh.write(f"repos/{self.org}/{repo}/vulnerability-alerts", "PUT")
        fixes = self.gh.call(f"repos/{self.org}/{repo}/automated-security-fixes", ok_missing=True) or {}
        if not fixes.get("enabled"):
            self.change(repo, "security", "turn on Dependabot security updates")
            self.gh.write(f"repos/{self.org}/{repo}/automated-security-fixes", "PUT")

    def security(self, repo: str, info: dict, entry: dict | None = None) -> None:
        if info.get("visibility") != "public":
            self.dependabot(repo)
            print("  security  private repository: Dependabot only (secret scanning, private vulnerability "
                  "reporting and code scanning need a paid plan there)")
            return
        saa = info.get("security_and_analysis") or {}
        want_saa = {}
        for feat in ("secret_scanning", "secret_scanning_push_protection"):
            if (saa.get(feat) or {}).get("status") != "enabled":
                want_saa[feat] = {"status": "enabled"}
        if want_saa:
            self.change(repo, "security", "turn on " + ", ".join(want_saa))
            self.gh.write(f"repos/{self.org}/{repo}", "PATCH", {"security_and_analysis": want_saa})
        self.dependabot(repo)
        pvr = self.gh.call(f"repos/{self.org}/{repo}/private-vulnerability-reporting", ok_missing=True) or {}
        if not pvr.get("enabled"):
            self.change(repo, "security", "turn on private vulnerability reporting")
            # Right after a repository goes public the endpoint can answer 422 for a few seconds.
            self.gh.write_retry(f"repos/{self.org}/{repo}/private-vulnerability-reporting", "PUT")
        cs = self.gh.call(f"repos/{self.org}/{repo}/code-scanning/default-setup", ok_missing=True) or {}
        # "code_scanning": "advanced" in the entry: the repository runs its own CodeQL workflow, and turning the
        # default setup on next to it would double the analysis and fight over the same results.
        if (entry or {}).get("code_scanning") == "advanced":
            return
        if cs and cs.get("state") != "configured":
            self.change(repo, "security", "turn on code scanning (default setup)")
            try:
                self.gh.write(f"repos/{self.org}/{repo}/code-scanning/default-setup", "PATCH",
                              {"state": "configured", "query_suite": "default"})
            except RuntimeError as err:  # no supported language yet (for example a docs-only repository)
                print(f"  security  code scanning not enabled: {err}")

    # -- organisation settings ---------------------------------------------------------------------------------
    def org_settings(self, info: dict, cfg: dict, policy: dict) -> None:
        """Profile fields from repos.json and member privileges from policy.json."""
        want = {**policy.get("org_settings", {}), **cfg.get("profile", {})}
        diff = {k: v for k, v in want.items() if info.get(k) != v}
        if diff:
            self.change(self.org, "settings", "set " + ", ".join(f"{k}={v!r}" for k, v in diff.items()))
            self.gh.write(f"orgs/{self.org}", "PATCH", diff)

    # -- organisation security ---------------------------------------------------------------------------------
    def org_security(self, policy: dict) -> None:
        """The code security configuration that new repositories get (GitHub recommended, public ones)."""
        want = policy.get("code_security_default")
        if not want:
            return
        confs = self.gh.call(f"orgs/{self.org}/code-security/configurations") or []
        conf = next((c for c in confs if c.get("name") == want["configuration"]), None)
        if conf is None:
            print(f"  security  note: no code security configuration named '{want['configuration']}'")
            return
        defaults = self.gh.call(f"orgs/{self.org}/code-security/configurations/defaults") or []
        have = next((d.get("default_for_new_repos") for d in defaults
                     if (d.get("configuration") or {}).get("id") == conf["id"]), None)
        if have != want["default_for_new_repos"]:
            self.change(self.org, "security",
                        f"make '{conf['name']}' the default for new {want['default_for_new_repos']} repositories")
            self.gh.write(f"orgs/{self.org}/code-security/configurations/{conf['id']}/defaults", "PUT",
                          {"default_for_new_repos": want["default_for_new_repos"]})

    # -- settings only the web interface can change ------------------------------------------------------------
    def manual_checks(self, info: dict) -> None:
        """Print the UI-only settings the API lets us read and that are not as required. Never counts as drift."""
        open_items = []
        if not info.get("two_factor_requirement_enabled"):
            open_items.append("Settings > Authentication security: require two-factor authentication")
        for item in open_items:
            print(f"  manual    [ ] {item}")
        if open_items:
            print("  manual    the other UI-only items are listed in org/ORG-SETTINGS.md")

    # -- organisation Actions policy ---------------------------------------------------------------------------
    def org_actions(self, allow: dict, extra_patterns: list[str], policy: dict) -> None:
        """The org-wide allow-list and SHA pinning, from actions-allowlist.json (patterns compared as a set), the
        default workflow token and the approval of fork pull request runs."""
        base = f"orgs/{self.org}/actions/permissions"
        want_perm = {"enabled_repositories": "all", "allowed_actions": "selected",
                     "sha_pinning_required": allow["sha_pinning_required"]}
        have_perm = self.gh.call(base) or {}
        if subset_differs(want_perm, have_perm):
            self.change(self.org, "actions", f"set {want_perm}")
            self.gh.write(base, "PUT", want_perm)
        third_party = [f"{a['action']}@*" for a in allow["actions"]]
        patterns = list(dict.fromkeys([f"{self.org}/*", *extra_patterns, *third_party]))
        want_sel = {"github_owned_allowed": allow["github_owned_allowed"], "verified_allowed": allow["verified_allowed"],
                    "patterns_allowed": sorted(patterns)}
        # The allow-list only exists once allowed_actions is "selected" (GitHub answers 409 before that).
        have_sel = (self.gh.call(f"{base}/selected-actions") if have_perm.get("allowed_actions") == "selected"
                    else None) or {}
        have_sel = {**have_sel, "patterns_allowed": sorted(have_sel.get("patterns_allowed", []))}
        if subset_differs(want_sel, have_sel):
            added = sorted(set(patterns) - set(have_sel["patterns_allowed"]))
            removed = sorted(set(have_sel["patterns_allowed"]) - set(patterns))
            self.change(self.org, "actions", f"set the allow-list (add {added or 'none'}, remove {removed or 'none'})")
            self.gh.write(f"{base}/selected-actions", "PUT", want_sel)
        want_wf = policy["actions_workflow_permissions"]
        if subset_differs(want_wf, self.gh.call(f"{base}/workflow") or {}):
            self.change(self.org, "actions", f"set workflow token to {want_wf}")
            self.gh.write(f"{base}/workflow", "PUT", want_wf)
        if policy.get("fork_pr_approval_policy"):
            have = self.gh.call(f"{base}/fork-pr-contributor-approval", ok_missing=True)
            if have is not None and have.get("approval_policy") != policy["fork_pr_approval_policy"]:
                self.change(self.org, "actions", f"set fork PR approval to {policy['fork_pr_approval_policy']}")
                self.gh.write(f"{base}/fork-pr-contributor-approval", "PUT",
                              {"approval_policy": policy["fork_pr_approval_policy"]})

    # -- actions -----------------------------------------------------------------------------------------------
    def actions(self, repo: str, info: dict, policy: dict) -> None:
        want = policy["actions_workflow_permissions"]
        have = self.gh.call(f"repos/{self.org}/{repo}/actions/permissions/workflow", ok_missing=True) or {}
        if subset_differs(want, have):
            self.change(repo, "actions", f"set workflow token to {want}")
            self.gh.write(f"repos/{self.org}/{repo}/actions/permissions/workflow", "PUT", want)
        if info.get("visibility") == "public" and policy.get("fork_pr_approval_policy"):
            path = f"repos/{self.org}/{repo}/actions/permissions/fork-pr-contributor-approval"
            have = self.gh.call(path, ok_missing=True)
            if have is not None and have.get("approval_policy") != policy["fork_pr_approval_policy"]:
                self.change(repo, "actions", f"set fork PR approval to {policy['fork_pr_approval_policy']}")
                self.gh.write(path, "PUT", {"approval_policy": policy["fork_pr_approval_policy"]})

    # -- rulesets ----------------------------------------------------------------------------------------------
    def wanted_rulesets(self, entry: dict, policy: dict) -> list[dict]:
        sets = []
        for name in ("main-integrity", f"main-review.{policy['review_mode']}", "release-tags", "major-tags"):
            sets.append(json.loads((HERE / "rulesets" / f"{name}.json").read_text()))
        checks = entry.get("required_checks", policy["default_required_checks"])
        if checks:
            text = (HERE / "rulesets" / "main-checks.json").read_text()
            ctx = [{"context": c, "integration_id": policy["github_actions_app_id"]} for c in checks]
            sets.append(json.loads(text.replace('"@REQUIRED_CHECKS@"', json.dumps(ctx))))
        return sets

    def rulesets(self, repo: str, info: dict, entry: dict, policy: dict) -> None:
        if info.get("visibility") != "public":
            print("  rulesets  skipped: GitHub Free enforces rulesets on public repositories only")
            return
        existing = {r["name"]: r["id"] for r in self.gh.call(f"repos/{self.org}/{repo}/rulesets") or []}
        wanted = self.wanted_rulesets(entry, policy)
        for rs in wanted:
            rid = existing.get(rs["name"])
            if rid is None:
                self.change(repo, "rulesets", f"create {rs['name']}")
                self.gh.write(f"repos/{self.org}/{repo}/rulesets", "POST", rs)
                continue
            have = self.gh.call(f"repos/{self.org}/{repo}/rulesets/{rid}")
            have_rules = sorted(have.get("rules", []), key=lambda r: r["type"])
            want_rules = sorted(rs["rules"], key=lambda r: r["type"])
            if (subset_differs(want_rules, have_rules) or have.get("enforcement") != rs["enforcement"]
                    or subset_differs(rs["conditions"], have.get("conditions"))
                    or len(rs["bypass_actors"]) != len(have.get("bypass_actors", []))):
                self.change(repo, "rulesets", f"update {rs['name']}")
                self.gh.write(f"repos/{self.org}/{repo}/rulesets/{rid}", "PUT", rs)
        for name in sorted(set(existing) - {r["name"] for r in wanted}):
            print(f"  rulesets  note: '{name}' is not declared here (left alone)")

    # -- labels ------------------------------------------------------------------------------------------------
    def labels(self, repo: str, labels: list[dict]) -> None:
        have = {l["name"].lower(): l for l in self.gh.call(f"repos/{self.org}/{repo}/labels?per_page=100") or []}
        for lab in labels:
            cur = have.get(lab["name"].lower())
            if cur is None:
                self.change(repo, "labels", f"create '{lab['name']}'")
                self.gh.write(f"repos/{self.org}/{repo}/labels", "POST", lab)
            elif cur["color"].lower() != lab["color"].lower() or (cur.get("description") or "") != lab["description"]:
                self.change(repo, "labels", f"update '{lab['name']}'")
                body = {"new_name": lab["name"], "color": lab["color"], "description": lab["description"]}
                self.gh.write(f"repos/{self.org}/{repo}/labels/{cur['name']}", "PATCH", body)
        extra = sorted(set(have) - {l["name"].lower() for l in labels})
        if extra:
            print(f"  labels    note: not declared here (left alone): {', '.join(extra)}")


def run_org(gh: Gh, org: str, cfg: dict, policy: dict, labels: list[dict], args: argparse.Namespace,
            sections: list[str], seen: set[str]) -> int:
    """Plan or apply one organization; returns its number of changes. Adds the --repo names it holds to `seen`."""
    info = gh.call(f"orgs/{org}")
    run = Run(gh, org, (info.get("plan") or {}).get("name", ""))
    repos = cfg.get("repos", {})
    live = {r["name"]: r for r in gh.call(f"orgs/{org}/repos?per_page=100&type=all") or [] if not r.get("archived")}
    targets = sorted(r for r in args.repo if r in live or r in repos) if args.repo else sorted(live)
    seen.update(targets)
    if args.repo and not targets:
        return 0
    for name in sorted(set(repos) - set(live)):
        if not args.repo or name in args.repo:
            print(f"declared but not on GitHub yet: {org}/{name}")
    print(f"{'Applying' if args.apply else 'Plan for'} {org}: review mode {policy['review_mode']}, "
          f"sections {', '.join(sections)}\n")

    if not args.repo:
        print(f"{org} (organisation, {info.get('plan', {}).get('name', 'unknown')} plan)")
        if "settings" in sections:
            run.org_settings(info, cfg, policy)
        if "security" in sections:
            run.org_security(policy)
        if "actions" in sections:
            run.org_actions(load("actions-allowlist.json"), cfg.get("actions_patterns", []), policy)
        run.manual_checks(info)
        if "rulesets" in sections and info.get("plan", {}).get("name") == "free":
            print("  rulesets  note: GitHub Free has no organization rulesets; each public repository gets a copy")

    for repo in targets:
        if repo not in live:
            print(f"{repo}: not found in {org}, skipped")
            continue
        entry = repos.get(repo)
        print(f"{repo} ({live[repo]['visibility']})")
        if entry is None:
            print("  note      not in repos.json: shared settings only; add an entry for description and topics")
            entry = {}
        repo_info = gh.call(f"repos/{org}/{repo}")
        if "settings" in sections:
            run.settings(repo, repo_info, entry, policy)
        if "security" in sections:
            run.security(repo, repo_info, entry)
        if "actions" in sections:
            run.actions(repo, repo_info, policy)
        if "rulesets" in sections:
            run.rulesets(repo, repo_info, entry, policy)
        if "labels" in sections:
            run.labels(repo, labels)
    print(f"\n{org}: {run.drift} change(s) {'applied' if args.apply else 'pending'}.\n")
    return run.drift


def main() -> int:
    orgs = load("repos.json")["orgs"]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="write the changes")
    mode.add_argument("--check", action="store_true", help="exit 1 if anything differs (writes nothing)")
    ap.add_argument("--org", action="append", choices=sorted(orgs), default=[],
                    help="only this organization (repeatable; default: every organization in repos.json)")
    ap.add_argument("--repo", action="append", default=[], help="only this repository (repeatable)")
    ap.add_argument("--section", action="append", choices=SECTIONS, default=[], help="only this section (repeatable)")
    args = ap.parse_args()

    policy, labels = load("policy.json"), load("labels.json")
    gh = Gh(apply=args.apply)
    sections = args.section or list(SECTIONS)
    drift, seen = 0, set()
    for org in args.org or list(orgs):
        drift += run_org(gh, org, orgs[org], policy, labels, args, sections, seen)
    for name in sorted(set(args.repo) - seen):
        print(f"{name}: not found in {', '.join(args.org or orgs)}, skipped")
    print(f"{drift} change(s) {'applied' if args.apply else 'pending'}.")
    return 1 if (args.check and drift) else 0


if __name__ == "__main__":
    sys.exit(main())
