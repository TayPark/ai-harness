# Spec Driven Development

Start with the Orchestrator for substantial implementation work. The Planner may draft a read-only plan before the assessment gates so its exact requirement map is available to both reports. Keep the specification/input packet and plan as separate sources.

1. `00-orchestration/sdd-00-orchestrate-implementation`: coordinate the workflow and record state.
2. `01-plan/sdd-01-plan-repository-implementation`: inspect the repository and draft a read-only plan.
3. `02-assessment/sdd-02-assess-implementation-spec`: run Spec Assessment on the exact specification/input packet. This is the first assessment gate.
4. If Spec Assessment needs revision or is blocked, stop before Plan Assessment, approval, and implementation. Revise the specification/plan draft with the Planner, then reassess.
5. After Spec Assessment is `READY`, run Plan Assessment on the exact plan. Require its `READY` verdict and 100% requirement-to-acceptance-to-task-to-verification mapping.
6. Require explicit approval for the same plan version, scope, and hashes.
7. `03-execution-and-verification/sdd-03-execute-implementation-plan`: implement approved phases and record sandbox, trace, checkpoint, and verification evidence.
8. `04-independent-verification/sdd-04-verify-implementation-independently`: use a different subagent to verify the frozen candidate. Continue only after `PASS`.
9. `05-release-readiness/sdd-05-assess-release-readiness`: after Independent `PASS`, assess SLO disposition, security, rollback, and operations before publication.

The Release Gate is pre-publication. It uses existing SLO targets and measurements. A row-level SLO N/A requires source-backed evidence that no service SLO exists. The gate does not invent thresholds or use merge, tag, push, or release results as its evidence.

For a small, direct implementation request, use the normal implementation workflow without the full sequence.
