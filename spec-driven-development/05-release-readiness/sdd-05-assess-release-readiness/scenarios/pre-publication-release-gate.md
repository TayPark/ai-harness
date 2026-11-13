# Pre-publication Release Gate scenario

Manual scenario. This file records the procedure only.

Status: `NOT RUN`

## Preconditions

- Verify a frozen candidate manifest and hash exist.
- Verify Independent Verification returned `PASS` for that exact candidate hash.
- Verify Release Gate runs before merge, push, tags, and publication.

## SLO row

1. Inspect repository documentation and configuration for a service SLO.
2. If an SLO exists, compare its stated target with measurement evidence.
3. If none exists, record the inspected source paths and hashes, then use row-level `N_A_WITH_RATIONALE` with a rationale.
4. If absence or measurement is unverified, block the gate.

Expected evidence: source paths and hashes, target or source-backed absence, measurement result, and row status.
Status: `NOT RUN`

## Security row

1. Run the applicable documented static, privacy, and secret checks.
2. Record check name, version, scope, policy source/hash, command, time, exit result, and output hash.
3. Disposition every finding and attach evidence.

Expected evidence: actual check results and finding dispositions. Missing policy or unresolved findings block `PASS`.
Status: `NOT RUN`

## Rollback row

1. Identify the last known good baseline.
2. Describe reversing the candidate changes with a project-appropriate recovery method.
3. State the verification command or observable result for the restored state.
4. Mark any unexecuted rollback as untested. Do not move tags or rewrite history.

Expected evidence: baseline reference, revert procedure, and recovery check.
Status: `NOT RUN`

## Operations row

1. Review installation steps for the target project.
2. Review how to update them and recover from partial installation or update.
3. Check that each procedure identifies a role, ordered steps, and success condition.

Expected evidence: installation, update, and recovery procedures with success checks.
Status: `NOT RUN`
