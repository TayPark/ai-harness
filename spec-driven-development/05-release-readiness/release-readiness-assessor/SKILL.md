---
name: release-readiness-assessor
description: Assess a pre-publication release using evidence for SLO disposition, security, rollback, and operations.
---
# Release Readiness Assessor

Assess release readiness from evidence. Do not publish, merge, push, create tags, or change remotes.

## Preconditions

1. Read the current workflow record, frozen candidate manifest and hashes, approved scope, and Independent Verification report.
2. Require Independent Verification `PASS` for the same candidate hash. If its result is missing, not independent, or bound to a different hash, set Release Readiness to `BLOCKED`.
3. Run this gate before publication. Do not use a merge, tag, push, or release result as evidence for this gate.
4. Confirm release is in scope. `NOT_REQUIRED` is allowed only when `release_in_scope` is false.

## Required evidence

Assess each row independently. Record source paths relative to the repository, source and artifact hashes, check versions, times, exit results, and finding dispositions. Do not invent thresholds or claim checks that did not run.

### SLO

- If repository documentation or configuration defines a service SLO, record its exact target and measurement evidence. Pass only when the evidence meets that target.
- Use `N_A_WITH_RATIONALE` for the SLO row only when source-backed inspection shows that no service SLO is defined. Attach the inspected source evidence and explain the absence.
- If the applicable SLO or measurement cannot be established, mark the evidence `UNVERIFIED` and set the gate to `BLOCKED`. Do not create a numeric target.

### Security

Run the applicable documented static, privacy, and secret checks. For each check, record its name, version, scope, policy source path and hash, command, time, exit result, output hash, and findings. Record a disposition and supporting evidence for every finding. Missing policy, unavailable checks, failed checks, or unresolved findings block `PASS`.

### Rollback

Provide an evidence-backed procedure that identifies the `v0.1b` baseline and restores the `v0.2` changes with a new revert commit. State the expected restored state and the check that confirms it. Do not move or delete tags, rewrite history, or force-push. Mark a rollback as untested unless it was actually exercised.

### Operations

Provide evidence for installation, update, and recovery. Each procedure must state the responsible role, ordered steps, and observable success condition. Cover partial installation or update recovery. Use the six public skill folders and the documented local installation method.

## Decision and handoff

- Set `PASS` only when the Independent Verification prerequisite passes and every required row has passing evidence. The SLO row may use evidence-backed `N_A_WITH_RATIONALE`.
- Set `FAIL` when evidence shows a required condition failed. Set `BLOCKED` when required policy or evidence is missing. Mark a required check that could not be confirmed as `UNVERIFIED` evidence and set the gate to `BLOCKED`.
- Write a typed report with `gate_name: RELEASE_READINESS`, bound to the workflow ID and frozen candidate hash. List each evidence item and finding disposition.
- Return the report and status to the Orchestrator. Publication can start only after this gate returns `PASS`.
