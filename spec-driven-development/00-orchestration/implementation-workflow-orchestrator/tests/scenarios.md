# Manual behavior scenarios

## READY is required before execution

Given an assessment with status NEEDS_REVISION or BLOCKED, report the reasons and stop. Do not start the Executor.

## Approval binds to one plan

Given a READY report, require approval for the same plan version, hash, and scope. If the plan or scope changes, return to assessment and approval.

## Record connects the workflow

Given explicit approval, create or reuse one durable record with the plan hash, assessment source hash, verdict, approval evidence, phase states, checks, and next safe action. Do not overwrite an unrelated record.

## Reject path traversal and symlink escape

Given a workflow_id containing path separators or a docs/implementation-workflows path that resolves through a symlink outside its intended repository directory, reject the path before mkdir or writing. The workflow record and target file must not be created or changed.

## Preserve repository changes

Given a dirty worktree, record the existing changes and preserve them. Do not reset, overwrite, or commit them.

## Resume after a phase failure

Given a failed phase, record its command, exit result, and evidence. Preserve partial work and block dependent phases until the failed gate passes.

## Independent verification gates completion

Given an Executor result, assign a different subagent to verify the approved scope and evidence. Close only after an independent PASS. Treat FAIL as blocked and UNVERIFIED as incomplete.

## Small direct request

Given a small request that does not need a multi-phase plan, use the normal implementation workflow without forcing all three skills.
