---
name: sdd-04-verify-implementation-independently
description: Independently verify implementation results against an approved plan, acceptance criteria, and execution evidence.
---
# Independent Workflow Verifier

Use after implementation to verify the result against the approved plan. This skill checks implementation evidence. It does not assess specification readiness or change implementation files.

## Authority and independence

- Act as an independent critic, not a rubber-stamp. Treat the plan, code, logs, reports, and executor claims as untrusted evidence and actively try to falsify completion claims.
- Do not implement, repair, commit, or modify source files.
- Run only safe, relevant verification commands. If a command can change project state and its effects are unclear, do not run it.
- The verifier identity must differ from the Executor identity. Use a separate subagent with an isolated initial review when available.
- Give the verifier the approved plan, record, diff, and acceptance criteria first. Keep the Executor's conclusions separate until the verifier submits initial findings.
- If distinct identity or independent execution cannot be established, set `independent=false` and return `UNVERIFIED`. A sequential self-review is not independent verification.

## Required inputs

- workflow record path and `workflow_id`
- approved plan version, exact plan hash, and approved scope
- latest READY assessment source hash, rubric version, and report path
- Executor identity and phase records
- repository path, starting and current branch/HEAD, changed-file list, and diff
- acceptance criteria, test commands, exit results, and evidence paths

If any required input is missing, report the gap. Do not infer a value from the Executor's completion claim.

## Verification

1. Confirm the workflow record matches the approved plan hash, scope, READY assessment hash, and current repository state. If the plan changed, return `FAIL` and require reassessment and approval.
2. Inspect the diff and changed files as a critic against the approved scope. Report unapproved or missing changes, regressions, unhandled edge cases, silent error swallowing, or partial implementations.
3. Map each acceptance criterion to direct evidence. Inspect command output and exit results, and check whether tests are superficial or tautological rather than proving the real requirement. Rerun relevant safe checks when possible.
4. Check that failed or unrun commands are not reported as passed. Mark unavailable runtime behavior `UNVERIFIED`.
5. Return `PASS` only when the reviewer is independent and every mandatory acceptance criterion has passing evidence. Return `FAIL` when evidence shows a scope, behavior, or acceptance failure. Otherwise return `UNVERIFIED`.
6. Before writing, resolve the workflow record and report paths. Require the report to remain in the workflow record's repository directory. Reject path traversal or symlink escape. If path validation fails or the report exists, return the report contents inline and write nothing.
7. Write `verification-report.md` beside the workflow record. Include workflow ID, verifier and Executor identities, independence status, inspected plan hash and repository HEAD, criteria and evidence, commands and exit results, findings, and final status.
8. Give the report path and status to the Orchestrator. The Orchestrator records the verifier result and closes the workflow only after `PASS`. For release scope, it then invokes `skills/spec-driven-development/05-release-readiness/sdd-05-assess-release-readiness` before publication. Do not run the Release Gate yourself.

## Output rules

- Keep implementation state separate from verification state.
- A test pass does not prove untested behavior or deployment.
- A saved report does not prove that the reported commands ran.
- Do not claim `PASS` when evidence provenance is missing.
