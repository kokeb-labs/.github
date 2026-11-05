# AGENTS.md

`kokeb-labs/.github` holds the organization profile, the community files every repository inherits, the `org/`
settings-as-code, the brand files and the Kokeb Labs engineering standard in [`standards/`](standards/README.md).

Agents working here or in any Kokeb Labs repository follow [`standards/agents.md`](standards/agents.md). Read it
first.

## This repository

- `standards/`: the standard. A rule change comes with an ADR in `standards/adr/` and updates every page, checklist
  and config it touches.
- `org/`: settings, security, rulesets and labels as code. Agents may run `org/kokeb_org.py` without `--apply` to
  show the plan; only an organization owner runs it with `--apply`.
- `brand/`: the logo generator. Regenerate the assets with `python3 brand/generate.py`; never edit generated files
  by hand.
- `profile/README.md`: the organization page.

## Checks before pushing

- Markdown: markdownlint with line length 120 (tables and code blocks exempt).
- Python: `python3 -m py_compile org/kokeb_org.py brand/generate.py`.
- JSON and YAML: `python3 -m json.tool` on `org/*.json` and `org/rulesets/*.json`; yamllint on `.github/`.
- Commits are signed off (`git commit -s`).
