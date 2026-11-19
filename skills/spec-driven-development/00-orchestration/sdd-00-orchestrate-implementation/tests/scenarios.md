# Manual behavior scenarios

## READY is required before execution

Given an assessment with status NEEDS_REVISION or BLOCKED, report the reasons and stop. Do not start the Executor.

## Approval binds to one plan

Given a READY report, require approval for the same plan version, hash, and scope. If the plan or scope changes, return to assessment and approval.

## Record connects the workflow

Given explicit approval, create or reuse one durable record with the plan hash, assessment source hash, verdict, approval evidence, phase states, checks, and next safe action. Do not overwrite an unrelated record.

## Reject path traversal and symlink escape

Given a workflow_id containing path separators or a `.sdd-local/runs/<workflow_id>` path that resolves through a symlink outside the repository, reject the path before writing. If the run root is absent, validate its existing parent before creating it; then resolve and recheck it. Do not create the workflow directory or target file after a failed check.

## Preserve repository changes

Given a dirty worktree, record the existing changes and preserve them. Do not reset, overwrite, or commit them.

## Resume after a phase failure

Given a failed phase, record its command, exit result, and evidence. Preserve partial work and block dependent phases until the failed gate passes.

## Independent verification gates completion

Given an Executor result, assign a different subagent to verify the approved scope and evidence. Close only after an independent PASS. Treat FAIL as blocked and UNVERIFIED as incomplete.

## Small direct request

Given a small request that does not need a multi-phase plan, use the normal implementation workflow without forcing all three skills.

## Validate record transitions

Given a gate transition, write a new gate report artifact, update the matching `gate_state_map` entry, and validate the entire record against `skills/spec-driven-development/02-assessment/sdd-02-assess-implementation-spec/schemas/workflow-record.schema.json` before atomic replacement. Preserve the previous valid record on validation failure.

## Verify sandbox probes

Given a sandbox candidate, require the out-of-scope write probe to be blocked and the scoped output probe to succeed. Record paths, exit codes, expected and observed results, and evidence IDs. Set `VERIFIED` only when both match.

## Examples are illustrative

Given the example exchange in `SKILL.md`, treat placeholder IDs and hashes as explanatory only. Do not claim execution or copy placeholders into a workflow record.
