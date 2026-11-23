---
name: orchestrate-agent-team
description: Coordinate software delivery across a product owner, team leaders, implementers, and independent reviewers. Use when the user requests a coordinated multi-team agent workflow for a substantial software project, not for a single bounded worker.
---

# Agent Team Orchestration

Coordinate multi-team software delivery across four distinct roles while keeping the main session as Product Owner (PO). Use `by-subagent` for bounded single-worker delegation, `interview-for-requirements` when requirements are unclear, and `sdd-00-orchestrate-implementation` for formal SDD gates.

## Roles and Ownership Boundaries

- Product Owner (PO, main session): Produces a traceable brief before dividing work, defines team-owned functional flows, resolves cross-team scope or priority conflicts, holds user approvals, and integrates validated handoffs into SDD gate state.
- Team Leader: Splits an assigned functional flow into bounded implementation and verification tasks (`by-subagent` contracts), enforces single-writer file ownership within the team, owns intra-team reassignment when a worker fails or times out, and routes reviewer rework back to the owning implementer.
- Implementer: Executes assigned bounded tasks within its declared write scope, reads its own specialist skills and source paths, and returns a validated `by-subagent` JSON packet with file and check evidence.
- Independent Reviewer (Critic): Reviews a frozen target revision (`commit`/`hash`) actively hunting for defects, regressions, and unproven claims without editing target files. Any post-review edit invalidates reviews bound to the old revision.

## Reassignment, Dependency Resumption, and Rework Rules

1. Parallel vs. dependent flows: Start cross-team work in parallel only when file ownership and interface contracts are disjoint. Keep dependent teams blocked until prerequisite interface packets reach `status: "complete"` with verified evidence.
2. Failed or timed-out worker: The owning Team Leader inspects partial artifacts, preserves valid work, reassigns the bounded task (or narrows scope) to a new worker with explicit handoff state, and records the limitation. If a blocker crosses team boundaries, escalate to the PO to reassign ownership or adjust scope.
3. Dependency resumption: The PO releases blocked downstream teams only after validating the upstream `by-subagent` JSON packet (`status: "complete"`, cited revision/hash, passing check output) and publishing the updated frozen contract.
4. Reviewer-to-implementer rework loop: Reviewer returns defect findings against frozen revision `R1` without editing files; Team Leader assigns fixes to the single file owner; implementer produces revision `R2` and check evidence; PO invalidates `R1` review state and dispatches a fresh independent review against `R2`.

## SDD Gate Handoff Mapping

Map validated team `by-subagent` JSON packets into `sdd-00-orchestrate-implementation` gates:

| Team Packet Outcome | Required Evidence | Owning SDD Gate State |
| --- | --- | --- |
| Spec/Plan packets `complete` | Source paths, exact hashes, requirement map | Submit to `SPECIFICATION_ASSESSMENT` / `PLAN_ASSESSMENT` (`READY` is not approval) |
| Any mandatory team packet `incomplete` or `blocked` | Task ID, blocker, affected files/deps | Keep owning gate `BLOCKED`; do not advance dependent teams |
| All approved execution packets `complete` + sandbox verified | Diff, command outputs, traces, checkpoints | Record `AGENT_EXECUTION: PASS`, freeze candidate, dispatch independent review |
| Independent Reviewer returns `PASS` on frozen candidate | Separate reviewer identity, revision hash, check outputs | Record `INDEPENDENT_VERIFICATION: PASS`; invoke `sdd-05-assess-release-readiness` if release is in scope |
| Independent review or required isolation unavailable | Explicit host/runtime limitation | Record `UNVERIFIED` / gate `BLOCKED`; never claim completion |

## Host and Isolation Discipline

Use the host's actual session, subagent, and communication mechanisms. If direct team-to-team messaging is unavailable, record that limitation and route validated JSON handoffs through the PO. Prompt text never enforces file permissions or sandbox isolation; inspect the actual execution environment and host configuration before claiming either.

## Worked PO Handoff Example

```text
PO -> Team-API Leader (flow: export-endpoint, write scope: api/export.py, tests/test_export.py)
  Input: approved plan hash <plan-hash>, spec brief R-01..R-02.
  Team-API Leader dispatches Implementer-1 via by-subagent JSON contract.
  Implementer-1 times out -> Team-API Leader inspects diff, reassigns T-02 to Implementer-2.
  Implementer-2 returns {"task_id":"T-02","status":"complete","evidence":["pytest -q tests/test_export.py: 6 passed"],"limitations":[]}.
PO verifies packet JSON -> marks AGENT_EXECUTION candidate frozen at commit <sha-R1> -> dispatches Independent Reviewer-A.
Reviewer-A finds missing 413 check -> returns defect on <sha-R1> (no edits).
Team-API Leader assigns fix to Implementer-2 -> commit <sha-R2> -> PO invalidates <sha-R1> review -> Reviewer-A verifies <sha-R2> -> PASS -> PO records INDEPENDENT_VERIFICATION: PASS.
```
