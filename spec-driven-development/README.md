# Spec Driven Development

Start with the Orchestrator for substantial implementation work. The Planner may draft a read-only plan before the assessment gates so its exact requirement map is available to both reports. Keep the specification/input packet and plan as separate sources.

1. `00-orchestration/implementation-workflow-orchestrator`: coordinate the workflow and record state.
2. `01-plan/repository-implementation-planner`: inspect the repository and draft a read-only plan.
3. `02-assessment/implementation-spec-assessor`: run Spec Assessment on the exact specification/input packet. This is the first assessment gate.
4. If Spec Assessment needs revision or is blocked, stop before Plan Assessment, approval, and implementation. Revise the specification/plan draft with the Planner, then reassess.
5. After Spec Assessment is `READY`, run Plan Assessment on the exact plan. Require its `READY` verdict and 100% requirement-to-acceptance-to-task-to-verification mapping.
6. Require explicit approval for the same plan version, scope, and hashes.
7. `03-execution-and-verification/implementation-plan-executor`: implement approved phases and record sandbox, trace, checkpoint, and verification evidence.
8. `04-independent-verification/independent-workflow-verifier`: use a different subagent to verify the frozen candidate. Continue only after `PASS`.
9. `05-release-readiness/release-readiness-assessor`: after Independent `PASS`, assess SLO disposition, security, rollback, and operations before publication.

The Release Gate is pre-publication. It uses existing SLO targets and measurements. A row-level SLO N/A requires source-backed evidence that no service SLO exists. The gate does not invent thresholds or use merge, tag, push, or release results as its evidence.

For a small, direct implementation request, use the normal implementation workflow without the full sequence.
