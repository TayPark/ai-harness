# Spec Driven Development

Start with the Orchestrator for substantial implementation work. It coordinates these skills:

1. 01-plan/repository-implementation-planner: inspect the repository and write a read-only plan.
2. 02-assessment/implementation-spec-assessor: assess the exact plan text and its execution contracts.
3. Require a READY result and explicit approval for the same plan version and scope.
4. 03-execution-and-verification/implementation-plan-executor: implement approved phases and record verification in the shared workflow record.
5. 04-independent-verification/independent-workflow-verifier: use a different subagent to verify evidence. Close only after `PASS`.

For a small, direct implementation request, use the normal implementation workflow without the full sequence.
