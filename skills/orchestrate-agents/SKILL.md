---
name: orchestrate-agents
description: Coordinate bounded subagent delegation and multi-team software delivery. Use when delegating independent work with JSON task contracts or coordinating a product owner, team leaders, implementers, and independent reviewers across a substantial project.
---

# Agent Orchestration

Coordinate delegated agent work across two scale tiers while keeping the main session focused on decomposition, task boundaries, integration, and final verification. Keep simple, short, dependent, or same-file work in the main session unless the user requests otherwise.

Use `interview-for-requirements` when requirements are unclear and `sdd-00-orchestrate-implementation` when formal Spec-Driven Development gates apply.

## Activation Guardrails

- Use when: work splits into independent bounded tasks (Tier 1) or multi-flow team delivery with separate write scopes and independent review (Tier 2).
- Do NOT use when: the task is short, single-file, or tightly sequential (handle directly in the main session), or when you need formal SDD phase gates without team structure (use `sdd-00-orchestrate-implementation`).
- Required before running: declare Tier 1 vs Tier 2, verify disjoint file ownership (one writer per file), and require JSON response contracts before launching workers.

## Scale Tiers

| Tier | Scope | Active roles |
| --- | --- | --- |
| Tier 1 (Bounded Workers) | Single or parallel independent research, analysis, implementation, or review tasks | Orchestrator + bounded subagents |
| Tier 2 (Multi-Team Delivery) | Substantial multi-flow software project with cross-team dependencies and rework loops | Product Owner (main session), Team Leaders, Implementers, Independent Reviewers |

## Shared Discipline

1. Do not read a worker's specialist skill or broad RAG material only to copy it into the handoff. Give workers precise skill names and source paths so each worker loads its own instructions and evidence.
2. Assign one writer per target file. Run tasks in parallel only when file ownership and interface contracts are disjoint.
3. Prompt text never enforces context isolation, file permissions, or sandbox boundaries. Inspect and rely on host-level controls when isolation is required.
4. For independent review, freeze the target and record its commit or hash first. Reviewers act as critics hunting for defects, regressions, weak assumptions, and missing evidence without editing target files. Any post-review edit invalidates reviews bound to the old revision.
5. Never present an agent's unsupported claim as verified fact. Validate returned JSON and inspect cited evidence before integrating.
6. Use the host's actual session, subagent, and messaging mechanisms. If fresh context, direct team messaging, or subagents are unavailable, record the exact limitation and fall back explicitly without claiming parallel or isolated execution.

## Tier 1: Bounded Worker Delegation

### Workflow

1. Split the request into small tasks with clear boundaries. Run independent tasks in parallel and dependent tasks in order.
2. Give each worker a unique `task_id`, objective, permitted inputs and tools, constraints, required reading paths, and expected JSON response contract.
3. Start a fresh worker context when the host supports it. Pass only the task contract and essential identifiers, not the full conversation or unrelated skills.
4. For dependent tasks, pass the prior task's full validated JSON as input rather than an unverified summary.
5. Parse each response as JSON and inspect `task_id`, `status`, `evidence`, and `limitations`. Treat invalid JSON, missing fields, or missing prerequisites as `incomplete`.
6. Check findings against evidence, resolve conflicts, and synthesize the final answer in the main session.

### Task Request Contract

```json
{
  "task_id": "stable-task-id",
  "objective": "One bounded task and its expected outcome",
  "inputs": [],
  "constraints": [],
  "required_reading": [],
  "expected_result": "One JSON object matching the response contract"
}
```

### Worker Response Contract

Require one valid JSON object with all fields below (`null` or `[]` when empty). Evidence must cite a supporting file and location, URL, or observed command result. Use `complete` only when the requested result and its evidence are present; otherwise use `incomplete` or `blocked`.

```json
{
  "task_id": "stable-task-id",
  "status": "complete | incomplete | blocked",
  "result": "Concise findings or output",
  "evidence": [],
  "assumptions": [],
  "limitations": [],
  "open_questions": []
}
```

## Tier 2: Multi-Team Delivery

Use Tier 2 when a software project spans multiple functional flows or requires coordinated team ownership.

### Roles and Ownership Boundaries

- Product Owner (PO, main session): writes a traceable brief before dividing work, defines team-owned functional flows, resolves cross-team scope or priority conflicts, holds user approvals, and integrates validated handoffs into SDD gate state.
- Team Leader: splits an assigned functional flow into bounded Tier 1 tasks, enforces single-writer file ownership within the team, handles intra-team reassignment on worker failure or timeout, and routes reviewer rework to the owning implementer.
- Implementer: executes bounded tasks within its declared write scope, reads its own specialist skills and source paths, and returns a validated Tier 1 JSON packet with file and check evidence.
- Independent Reviewer (Critic): reviews a frozen target revision (`commit`/`hash`) for defects, regressions, and unproven claims without editing target files.

### Reassignment, Dependency Resumption, and Rework Rules

1. Parallel vs. dependent flows: start cross-team work in parallel only when file ownership and interface contracts are disjoint. Keep dependent teams blocked until prerequisite interface packets reach `status: "complete"` with verified evidence.
2. Failed or timed-out worker: the owning Team Leader inspects partial artifacts, preserves valid work, reassigns the bounded task (or narrows scope) to a new worker with explicit handoff state, and records the limitation. Escalate cross-team blockers to the PO.
3. Dependency resumption: the PO unblocks downstream teams only after validating the upstream JSON packet (`status: "complete"`, cited revision/hash, passing check output) and publishing the updated frozen contract.
4. Reviewer-to-implementer rework loop: the Reviewer returns defect findings against frozen revision `R1` without editing files; the Team Leader assigns fixes to the single file owner; the Implementer produces revision `R2` and check evidence; the PO invalidates `R1` review state and dispatches a fresh independent review against `R2`.

### SDD Gate Handoff Mapping

Map validated team JSON packets into `sdd-00-orchestrate-implementation` gates:

| Team Packet Outcome | Required Evidence | Owning SDD Gate State |
| --- | --- | --- |
| Spec/Plan packets `complete` | Source paths, exact hashes, requirement map | Submit to `SPECIFICATION_ASSESSMENT` / `PLAN_ASSESSMENT` (`READY` is not approval) |
| Any mandatory team packet `incomplete` or `blocked` | Task ID, blocker, affected files/deps | Keep owning gate `BLOCKED`; do not advance dependent teams |
| All approved execution packets `complete` + sandbox verified | Diff, command outputs, traces, checkpoints | Record `AGENT_EXECUTION: PASS`, freeze candidate, dispatch independent review |
| Independent Reviewer returns `PASS` on frozen candidate | Separate reviewer identity, revision hash, check outputs | Record `INDEPENDENT_VERIFICATION: PASS`; invoke `sdd-05-assess-release-readiness` if release is in scope |
| Independent review or required isolation unavailable | Explicit host/runtime limitation | Record `UNVERIFIED` / gate `BLOCKED`; never claim completion |

### Worked PO Handoff Example

```text
PO -> Team-API Leader (flow: export-endpoint, write scope: api/export.py, tests/test_export.py)
  Input: approved plan hash <plan-hash>, spec brief R-01..R-02.
  Team-API Leader dispatches Implementer-1 via Tier 1 JSON contract.
  Implementer-1 times out -> Team-API Leader inspects diff, reassigns T-02 to Implementer-2.
  Implementer-2 returns {"task_id":"T-02","status":"complete","evidence":["pytest -q tests/test_export.py: 6 passed"],"limitations":[]}.
PO verifies packet JSON -> marks AGENT_EXECUTION candidate frozen at commit <sha-R1> -> dispatches Independent Reviewer-A.
Reviewer-A finds missing 413 check -> returns defect on <sha-R1> (no edits).
Team-API Leader assigns fix to Implementer-2 -> commit <sha-R2> -> PO invalidates <sha-R1> review -> Reviewer-A verifies <sha-R2> -> PASS -> PO records INDEPENDENT_VERIFICATION: PASS.
```
