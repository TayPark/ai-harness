---
name: sdd-05-assess-release-readiness
description: Assess a pre-publication release using evidence for SLO disposition, security, rollback, and operations.
---
# Release Readiness Assessor

Assess release readiness as a strict critic from evidence. Actively challenge weak finding dispositions, untested recovery assumptions, and superficial operational checks; do not rubber-stamp release approval. Do not publish, merge, push, create tags, or change remotes.

## Preconditions

1. Read the current workflow record, frozen candidate manifest and hashes, approved scope, and Independent Verification report.
2. Require Independent Verification `PASS` for the exact same frozen candidate hash. If Independent Verification is missing, `FAIL`, `BLOCKED`, `UNVERIFIED`, not independent, or bound to a different hash, set Release Readiness to `BLOCKED`.
3. Run this gate before publication. Do not use a merge, tag, push, or release result as evidence for this gate.
4. Confirm `release_in_scope` is `true` before producing `PASS`. `NOT_REQUIRED` is allowed only when `release_in_scope` is `false`.

## Required evidence

Assess each row independently. Record source paths relative to the repository, source and artifact hashes, check versions, times, exit results, and finding dispositions. Do not invent thresholds or claim checks that did not run.

### SLO

- If repository documentation or configuration defines a service SLO, record its exact target and measurement evidence. Pass only when the evidence meets that target.
- Use `N_A_WITH_RATIONALE` for the SLO row only when source-backed inspection shows that no service SLO is defined. Attach the inspected source evidence and explain the absence.
- If the applicable SLO or measurement cannot be established, mark the evidence `UNVERIFIED` and set the gate to `BLOCKED`. Do not create a numeric target.

### Security

Run the applicable documented static, privacy, and secret checks. For each check, record its name, version, scope, policy source path and hash, command, time, exit result, output hash, and findings. Record a disposition and supporting evidence for every finding. Missing policy, unavailable checks, failed checks, or unresolved findings block `PASS`.

### Rollback

Provide an evidence-backed procedure that identifies the target project's last known good baseline and reverses the candidate changes using a project-appropriate recovery method. State the expected restored state and the check that confirms it. Do not move or delete tags, rewrite history, or force-push.

- Mark a rollback procedure as `untested` (evidence result `UNVERIFIED`) unless it was actually exercised.
- An unexercised (`UNVERIFIED`) rollback cannot satisfy `ROLLBACK: PASS`; set the `ROLLBACK` row to `BLOCKED` and the gate to `BLOCKED` until a non-destructive rollback rehearsal or clean-room baseline restoration test passes and produces `PASS` evidence.

### Operations

Provide evidence for installation, update, and recovery. Each procedure must state the responsible role, ordered steps, and observable success condition. Cover partial installation or update recovery. Use the target project's documented deployment or installation method.

## Decision and handoff

- Set `PASS` only when `release_in_scope` is `true`, Independent Verification is `PASS` for the same candidate hash, and every required row has passing evidence (`PASS`, or source-backed `N_A_WITH_RATIONALE` for `SLO` only).
- Set `FAIL` when evidence shows a required condition failed. Set `BLOCKED` when required policy or evidence is missing or `UNVERIFIED`.
- Write a typed report conforming to `skills/spec-driven-development/02-assessment/sdd-02-assess-implementation-spec/schemas/gate-report.schema.json` with `gate_name: RELEASE_READINESS`, bound to `workflow_id` and the frozen candidate hash (`input_hash`). List every evidence item and finding disposition.
- Validate the typed report against the workflow record before returning it to the Orchestrator. Publication can start only after this gate returns `PASS` and passes local validation.

## Sample typed report and validation

Minimal valid structure (compute `report_hash` with `canonical_report_hash(report)` before saving):

```json
{
  "schema_version": "1.0",
  "workflow_id": "d53e1c45-7793-4b58-94e6-9687519303dd",
  "report_id": "release-readiness-001",
  "gate_name": "RELEASE_READINESS",
  "input_hash": "<64-hex-frozen-candidate-sha256>",
  "report_hash": "<64-hex-canonical-report-sha256>",
  "hash_method": "stdlib-json-v1-no-report_hash",
  "assessor_version": "1.0.0",
  "status": "PASS",
  "attempt": 1,
  "generated_at": "2026-11-23T09:00:00Z",
  "requirement_links": [
    {"requirement_id": "R-01", "acceptance_ids": ["AC-01"], "task_ids": ["T-01"], "verification_ids": ["V-01"]}
  ],
  "checklist": [
    {"check_id": "SLO", "requirement_ids": ["R-01"], "criterion": "Use existing SLO or source-backed absence.", "status": "N_A_WITH_RATIONALE", "evidence_ids": ["E-SLO"], "rationale": "Inspected docs define no service SLO."},
    {"check_id": "SECURITY", "requirement_ids": ["R-01"], "criterion": "Applicable static/privacy/secret checks pass.", "status": "PASS", "evidence_ids": ["E-SEC"], "rationale": null},
    {"check_id": "ROLLBACK", "requirement_ids": ["R-01"], "criterion": "Baseline restoration procedure verified.", "status": "PASS", "evidence_ids": ["E-RBK"], "rationale": null},
    {"check_id": "OPERATIONS", "requirement_ids": ["R-01"], "criterion": "Install, update, and recovery steps verified.", "status": "PASS", "evidence_ids": ["E-OPS"], "rationale": null}
  ],
  "evidence": [
    {"evidence_id": "E-SLO", "kind": "REPORT", "relative_path": "README.md", "sha256": "<64-hex>", "result": "PASS", "captured_at": "2026-11-23T09:00:00Z"},
    {"evidence_id": "E-SEC", "kind": "SCAN", "relative_path": "scripts/validate_public_package.py", "sha256": "<64-hex>", "result": "PASS", "captured_at": "2026-11-23T09:00:00Z"},
    {"evidence_id": "E-RBK", "kind": "TEST", "relative_path": ".sdd-local/runs/d53e1c45-7793-4b58-94e6-9687519303dd/rollback-check.log", "sha256": "<64-hex>", "result": "PASS", "captured_at": "2026-11-23T09:00:00Z"},
    {"evidence_id": "E-OPS", "kind": "TEST", "relative_path": ".sdd-local/runs/d53e1c45-7793-4b58-94e6-9687519303dd/ops-check.log", "sha256": "<64-hex>", "result": "PASS", "captured_at": "2026-11-23T09:00:00Z"}
  ],
  "findings": [],
  "errors": []
}
```

Validate the saved gate report against the workflow record from the repository root:

```sh
.venv/bin/python -c '
import json, sys
from pathlib import Path
sys.path.insert(0, "skills/spec-driven-development/02-assessment/sdd-02-assess-implementation-spec")
from scripts.validate_assessment import validate_gate_report
report = json.loads(Path("release-report.json").read_text(encoding="utf-8"))
workflow = json.loads(Path("workflow-record.json").read_text(encoding="utf-8"))
errors = validate_gate_report(report, workflow)
print("PASS" if not errors else errors)
sys.exit(1 if errors else 0)
'
```
