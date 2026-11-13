---
name: orchestrate-agent-team
description: Coordinate software delivery across a product owner, team leaders, implementers, and independent reviewers. Use when the user requests a coordinated agent team for a substantial software project.
---

# Codex team orchestration

The main session acts as product owner (PO). Use `interview-for-requirements` when the requirements need clarification. Produce a traceable brief before dividing work. Use `by-subagent` for task and response contracts; direct each worker to read relevant specialist skills and sources itself.

Divide the goal into team-owned functional flows. Specify team objectives, task boundaries, dependencies, outputs, and one writer for each file. A team leader divides its flow into bounded implementation and verification tasks. Start parallel work only when dependencies permit it. Reviewers inspect a frozen target revision and do not edit implementation files. Invalidate their review when that target changes.

Use the existing `sdd-00-orchestrate-implementation` and its SDD gates: specification assessment, plan assessment, approval of the exact plan and scope, execution, and independent verification. Run Release Readiness when release is in scope. `READY` is not approval. If independent verification or required isolation is unavailable, record `UNVERIFIED` or `BLOCKED`; do not claim completion.

Use the available host's actual session and communication mechanisms. If direct team communication is unavailable, report that limitation and route validated handoffs through the PO. Do not treat instructions as enforced file permissions or sandbox isolation. Check the actual execution environment and Codex configuration before claiming either.
