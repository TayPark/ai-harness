# Spec Driven Development

Start with the Orchestrator for substantial implementation work. When requirements, user flows, constraints, or acceptance criteria are unclear, `sdd-00` invokes [`interview-for-requirements`](../interview-for-requirements/SKILL.md) first to produce a frozen `COMPLETE_BRIEF` (or `PARTIAL_BRIEF` for read-only `Safe Parallel Work`). The Planner may draft a read-only plan before the assessment gates so its exact requirement map is available to both reports. Keep the specification/input packet and plan as separate sources.

1. `00-orchestration/sdd-00-orchestrate-implementation`: coordinate the workflow and record state.
2. `01-plan/sdd-01-plan-repository-implementation`: inspect the repository and draft a read-only plan.
3. `02-assessment/sdd-02-assess-implementation-spec`: run Spec Assessment on the exact specification/input packet. This is the first assessment gate.
4. If Spec Assessment needs revision or is blocked, stop before Plan Assessment, approval, and implementation. Revise the specification/plan draft with the Planner, then reassess.
5. After Spec Assessment is `READY`, run Plan Assessment on the exact plan. Require its `READY` verdict and 100% requirement-to-acceptance-to-task-to-verification mapping.
6. Require explicit approval for the same plan version, scope, and hashes.
7. `03-execution-and-verification/sdd-03-execute-implementation-plan`: implement approved phases and record sandbox, trace, checkpoint, and verification evidence.
8. `04-independent-verification/sdd-04-verify-implementation-independently`: use a different subagent to verify the frozen candidate. Continue only after `PASS`.
9. `05-release-readiness/sdd-05-assess-release-readiness`: after Independent `PASS`, assess SLO disposition, security, rollback, and operations before publication.
10. `06-operation-and-handover/sdd-06-operate-and-handover`: after authorized deployment, close the observation window (`O1`–`O7`), run 5 Whys incident feedback closure, and complete internal team or external client handover (including Reverse-Shadowing sign-off).

The Release Gate (`sdd-05`) is pre-publication; `sdd-06` is strictly post-deployment and consumes release artifacts read-only without modifying `sdd-02` schemas. For rapid feasibility exploration, use `sdd-00`'s Discovery/Spike track and require its Production Graduation Gate before promoting prototypes into production.

For a small, direct implementation request, use the normal implementation workflow without the full sequence.

See [sdlc-stage-rubrics](../sdlc-stage-rubrics/SKILL.md) for the portable 4-stage SDLC evaluation rubrics (Requirement, Implementation, Verification, Operation) and machine-readable gate definitions.
