# Contribution and Maintenance Rules

This repository packages reusable agent skills and verification tooling. Read [README.md](README.md) and [scripts/validate_public_package.py](scripts/validate_public_package.py) before adding or modifying any skill, script, or documentation.

## Skill and Code Admission Gates

Every proposed skill or code change must pass all three admission gates before implementation:

1. Distinct scope without role overlap
   Inspect the existing catalog in [README.md](README.md) and top-level skill directories first. Reject any new skill whose trigger, workflow, or responsibility duplicates or overlaps an existing skill. Keep selection boundaries mutually exclusive. When a capability belongs inside an existing skill's bounded role, refine that skill instead of creating a parallel one.

2. Parity or superiority against public web skills
   Benchmark the proposed skill or script against publicly available skills, prompts, and reference implementations on the web for the same task. Admit a skill or code change only when it matches or exceeds the strongest public alternative in task completion quality, verification rigor, determinism, failure handling, and token efficiency. Do not add generic prompt wrappers or weaker duplicates of existing public skills.

3. Upstream URL linking over static skill embedding
   When adopting an external skill already published on the web without substantive local modification, link to its canonical upstream URL (repository, raw `SKILL.md`, or upstream install documentation) rather than copying its body into this repository. Static copies drift behind upstream updates. Vendor or fork a public skill locally only when enforcing repository-specific contracts, deterministic validation scripts, or offline invariants that upstream does not provide, and record the upstream URL and license provenance in the skill directory.

## Repository Conventions for Skills and Code

### Directory Layout and Naming

- Place each standalone skill in a kebab-case directory under `skills/` named with a clear verb phrase or domain role (for example `anti-slop`, `ask-to-chatgpt`, `ask-to-gemini`, `debate-models`, `evaluate-with-rubric`, `interview-for-requirements`), or under `skills/spec-driven-development/<stage>/sdd-XX-<name>` for Spec-Driven Development stages.
- Do not retain deprecated directory names as compatibility aliases. Record renames in the migration table in [README.md](README.md) and update all internal references in the same change.
- Keep `SKILL.md` focused on activation triggers, core workflow, guardrails, and input/output contracts. Offload detailed rubrics, schemas, pattern tables, and executable helpers into `references/`, `rubrics/`, `schemas/`, `scripts/`, and `tests/`.

### Required Skill Metadata

- Start every `SKILL.md` with YAML frontmatter delimited by `---` containing:
  - `name`: exact match to the skill's directory name.
  - `description`: concise statement of what the skill does and when to invoke it (`Use when...`).
- Include `agents/openai.yaml` inside every public packaged skill directory with `interface.display_name` and `interface.short_description`.
- Keep prose compliant with [skills/anti-slop/SKILL.md](skills/anti-slop/SKILL.md) and code changes minimal and self-checked per upstream [ponytail](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md).

### Code, Dependencies, and Privacy Hygiene

- Prefer the Python standard library for helper scripts and validators. Add third-party packages only when necessary and pin them in a skill-scoped `requirements.txt`.
- Add unit tests under `tests/` for any new or modified script, validator, or schema.
- Never commit personal home-directory paths, credentials, `.env` files, or live session data.
- Keep local-only directories (`.venv`, `.work`, and excluded private paths configured in [scripts/validate_public_package.py](scripts/validate_public_package.py)) and Python cache files (`__pycache__/`, `*.py[cod]`, `.pytest_cache/`) out of tracked files and public Markdown links.

### Catalog and Manifest Synchronization

When adding, renaming, or removing a packaged skill or its files, update all affected indexes together:

1. [README.md](README.md): Included skills table, installation loop, migration table (if renamed), and selection boundaries.
2. [scripts/validate_public_package.py](scripts/validate_public_package.py): `SKILLS` tuple.
3. [skills/spec-driven-development/02-assessment/sdd-02-assess-implementation-spec/MANIFEST.txt](skills/spec-driven-development/02-assessment/sdd-02-assess-implementation-spec/MANIFEST.txt): file list whenever files inside `sdd-02-assess-implementation-spec` change.

## Verification Gates

Run these checks from the repository root before completing any change (use `.venv/bin/python` when available):

```sh
python scripts/validate_public_package.py
python3 skills/anti-slop/scripts/check_slop.py --strict --file CONTRIBUTING.md
python3 skills/anti-slop/scripts/check_slop.py --strict --file AGENTS.md
python -m pytest -q tests
python -m pytest -q skills/spec-driven-development/02-assessment/sdd-02-assess-implementation-spec/tests
python -m pytest -q skills/spec-driven-development/05-release-readiness/sdd-05-assess-release-readiness/tests
python -m pytest -q skills/anti-slop/tests
python -m unittest discover -s skills/evaluate-with-rubric/tests -v
git diff HEAD --check
```

When editing other Markdown files, run `python3 skills/anti-slop/scripts/check_slop.py --strict --file <path>` on each changed Markdown file as well.
