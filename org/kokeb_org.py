#!/usr/bin/env python3
"""Keep every kokeb-labs repository's settings, security, Actions policy, rulesets and labels as declared here.

Desired state lives next to this file:
  policy.json      settings shared by every repository, review mode, default required checks
  repos.json       one entry per repository: kind, description, topics, homepage, overrides
  labels.json      the label set
  rulesets/*.json  the rulesets (main-review.<mode>.json picks the review mode)
  actions-allowlist.json  the organisation's Actions policy: allowed third-party actions, SHA pinning

Default is a dry run that prints what would change. --apply writes it. --check exits 1 on any drift (for CI).
Re-running is safe: everything is compared first and only differences are written. Labels and rulesets that are
not declared here are reported, never deleted.

Requires gh, authenticated as an organization owner. Python 3.9+, standard library only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
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
    def __init__(self, gh: Gh, org: str) -> None:
        self.gh = gh
        self.org = org
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
        diff = {k: v for k, v in want.items() if info.get(k) != v}
        if diff:
            self.change(repo, "settings", "set " + ", ".join(f"{k}={v!r}" for k, v in diff.items()))
            self.gh.write(f"repos/{self.org}/{repo}", "PATCH", diff)
        if "topics" in entry and sorted(info.get("topics", [])) != sorted(entry["topics"]):
            self.change(repo, "settings", f"set topics={entry['topics']}")
            self.gh.write(f"repos/{self.org}/{repo}/topics", "PUT", {"names": entry["topics"]})

    # -- security ----------------------------------------------------------------------------------------------
    def security(self, repo: str, info: dict) -> None:
        if info.get("visibility") != "public":
            print("  security  skipped: private repository (these features need Advanced Security there)")
            return
        saa = info.get("security_and_analysis") or {}
        want_saa = {}
        for feat in ("secret_scanning", "secret_scanning_push_protection"):
            if (saa.get(feat) or {}).get("status") != "enabled":
                want_saa[feat] = {"status": "enabled"}
        if want_saa:
            self.change(repo, "security", "turn on " + ", ".join(want_saa))
            self.gh.write(f"repos/{self.org}/{repo}", "PATCH", {"security_and_analysis": want_saa})
        if self.gh.call(f"repos/{self.org}/{repo}/vulnerability-alerts", ok_missing=True) is None:
            self.change(repo, "security", "turn on Dependabot alerts")
            self.gh.write(f"repos/{self.org}/{repo}/vulnerability-alerts", "PUT")
        fixes = self.gh.call(f"repos/{self.org}/{repo}/automated-security-fixes", ok_missing=True) or {}
        if not fixes.get("enabled"):
            self.change(repo, "security", "turn on Dependabot security updates")
            self.gh.write(f"repos/{self.org}/{repo}/automated-security-fixes", "PUT")
        pvr = self.gh.call(f"repos/{self.org}/{repo}/private-vulnerability-reporting", ok_missing=True) or {}
        if not pvr.get("enabled"):
            self.change(repo, "security", "turn on private vulnerability reporting")
            self.gh.write(f"repos/{self.org}/{repo}/private-vulnerability-reporting", "PUT")
        cs = self.gh.call(f"repos/{self.org}/{repo}/code-scanning/default-setup", ok_missing=True) or {}
        if cs and cs.get("state") != "configured":
            self.change(repo, "security", "turn on code scanning (default setup)")
            try:
                self.gh.write(f"repos/{self.org}/{repo}/code-scanning/default-setup", "PATCH",
                              {"state": "configured", "query_suite": "default"})
            except RuntimeError as err:  # no supported language yet (for example a docs-only repository)
                print(f"  security  code scanning not enabled: {err}")

    # -- organisation Actions policy ---------------------------------------------------------------------------
    def org_actions(self, allow: dict) -> None:
        """The org-wide allow-list and SHA pinning, from actions-allowlist.json (patterns compared as a set)."""
        base = f"orgs/{self.org}/actions/permissions"
        want_perm = {"enabled_repositories": "all", "allowed_actions": "selected",
                     "sha_pinning_required": allow["sha_pinning_required"]}
        have_perm = self.gh.call(base) or {}
        if subset_differs(want_perm, have_perm):
            self.change(self.org, "actions", f"set {want_perm}")
            self.gh.write(base, "PUT", want_perm)
        patterns = [allow["own_org"]] + [f"{a['action']}@*" for a in allow["actions"]]
        want_sel = {"github_owned_allowed": allow["github_owned_allowed"], "verified_allowed": allow["verified_allowed"],
                    "patterns_allowed": sorted(patterns)}
        have_sel = self.gh.call(f"{base}/selected-actions") or {}
        have_sel = {**have_sel, "patterns_allowed": sorted(have_sel.get("patterns_allowed", []))}
        if subset_differs(want_sel, have_sel):
            added = sorted(set(patterns) - set(have_sel["patterns_allowed"]))
            removed = sorted(set(have_sel["patterns_allowed"]) - set(patterns))
            self.change(self.org, "actions", f"set the allow-list (add {added or 'none'}, remove {removed or 'none'})")
            self.gh.write(f"{base}/selected-actions", "PUT", want_sel)

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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="write the changes")
    mode.add_argument("--check", action="store_true", help="exit 1 if anything differs (writes nothing)")
    ap.add_argument("--repo", action="append", default=[], help="only this repository (repeatable)")
    ap.add_argument("--section", action="append", choices=SECTIONS, default=[], help="only this section (repeatable)")
    args = ap.parse_args()

    policy, repos, labels = load("policy.json"), load("repos.json")["repos"], load("labels.json")
    org = policy["org"]
    gh = Gh(apply=args.apply)
    run = Run(gh, org)
    sections = args.section or list(SECTIONS)

    live = {r["name"]: r for r in gh.call(f"orgs/{org}/repos?per_page=100&type=all") or [] if not r.get("archived")}
    targets = args.repo or sorted(live)
    for name in sorted(set(repos) - set(live)):
        print(f"declared but not on GitHub yet: {name}")
    print(f"{'Applying' if args.apply else 'Plan for'} {org}: review mode {policy['review_mode']}, "
          f"sections {', '.join(sections)}\n")

    if "actions" in sections and not args.repo:
        print(f"{org} (organisation)")
        run.org_actions(load("actions-allowlist.json"))

    for repo in targets:
        if repo not in live:
            print(f"{repo}: not found in {org}, skipped")
            continue
        entry = repos.get(repo)
        print(f"{repo} ({live[repo]['visibility']})")
        if entry is None:
            print("  note      not in repos.json: shared settings only; add an entry for description and topics")
            entry = {}
        info = gh.call(f"repos/{org}/{repo}")
        if "settings" in sections:
            run.settings(repo, info, entry, policy)
        if "security" in sections:
            run.security(repo, info)
        if "actions" in sections:
            run.actions(repo, info, policy)
        if "rulesets" in sections:
            run.rulesets(repo, info, entry, policy)
        if "labels" in sections:
            run.labels(repo, labels)

    print(f"\n{run.drift} change(s) {'applied' if args.apply else 'pending'}.")
    return 1 if (args.check and run.drift) else 0


if __name__ == "__main__":
    sys.exit(main())
