# Manual behavior scenarios

## Independent reviewer required

Given an Executor identity and an available subagent, assign verification to a different subagent. If the identity cannot be distinguished, return `UNVERIFIED` with `independent=false`.

## Approved scope and hash

Given a plan hash or approved scope that differs from the workflow record, return `FAIL`. Do not approve the changed work.

## Evidence-backed acceptance

Given a mandatory criterion with a failing command or no evidence, return `FAIL` or `UNVERIFIED`. Do not infer success from the Executor's summary.

## Read-only verification

Given a source change is needed to make a check pass, record the finding and stop. Do not modify implementation files.

## Existing report

Given `verification-report.md` already exists, do not overwrite it. Return a path conflict and report inline.

## Unsafe report path

Given a workflow record or report path that escapes the repository directory through traversal or a symlink, reject it before writing. Do not create or change a file outside the workflow directory.
