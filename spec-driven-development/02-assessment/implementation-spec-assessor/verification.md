# Verification evidence

Checks ran in an isolated Python 3.11.15 environment. The commands below ran
from the repository root unless the command says otherwise.

## Passed checks

- `env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_public_package.py` — exit 0; checked 57 files across 3 skills.
- `env PYTHONDONTWRITEBYTECODE=1 ../../../.venv/bin/python -m pytest -p no:cacheprovider -q` from `spec-driven-development/02-assessment/implementation-spec-assessor/` — exit 0; 63 tests passed.
- The host skill creator validator reported `Skill is valid!` through all three global Codex symlinks.
- Assessment CLI checks for the excellent fixture, end-to-end example, improved example, and contradictory fixture — each exited 0 with schema, arithmetic, gates, references, capabilities, and caps passed.
- The poor fixture exited 0. Its source provenance is unverified because the source was not supplied.
- The invalid-ready fixture exited 1 with the expected `status mismatch` failure.

Exact command output is recorded in [verification-results.json](verification-results.json).

## Limits

- The manual behavior scenarios are documented but were not executed in a live agent runtime.
- Independent review and repeated model-scoring experiments were not run.
- The deterministic validator does not prove complete semantic extraction, scoring repeatability, or correctness of a program described by an assessed specification.
