# Scoring anchors

Evaluate as a critic using only source evidence. Actively probe how an implementer or autonomous agent could misinterpret or break each requirement; do not give the benefit of the doubt. A polished document earns no points by itself.

## clarity
0: Behavior and terminology entirely absent.
1: Behavior and terminology mentioned vaguely; substantial interpretation required.
2: Some behavior and terminology specified; major implementation gaps remain.
3: Behavior and terminology implementable with explicitly bounded assumptions; gaps below score 4 remain.
4: Consistent unambiguous critical requirements.
5: Score 4 plus alternative interpretations resolved; no material ambiguity in this dimension.

## completeness
0: Scope and constraints entirely absent.
1: Scope and constraints mentioned vaguely; substantial interpretation required.
2: Some scope and constraints specified; major implementation gaps remain.
3: Scope and constraints implementable with explicitly bounded assumptions; gaps below score 4 remain.
4: Critical requirements and exclusions covered.
5: Score 4 plus relevant edge cases and decision ownership; no material ambiguity in this dimension.

## decomposition
0: Component boundaries entirely absent.
1: Component boundaries mentioned vaguely; substantial interpretation required.
2: Some component boundaries specified; major implementation gaps remain.
3: Component boundaries implementable with explicitly bounded assumptions; gaps below score 4 remain.
4: Clear components and dependencies.
5: Score 4 plus independent ownership and complete integration boundaries; no material ambiguity in this dimension.

## interface_contracts
0: Input/output contracts entirely absent.
1: Input/output contracts mentioned vaguely; substantial interpretation required.
2: Some input/output contracts specified; major implementation gaps remain.
3: Input/output contracts implementable with explicitly bounded assumptions; gaps below score 4 remain.
4: Explicit schemas, validation and errors.
5: Score 4 plus state transitions, invariants, compatibility and boundary cases; no material ambiguity in this dimension.

## implementability
0: Technical execution approach entirely absent.
1: Technical execution approach mentioned vaguely; substantial interpretation required.
2: Some technical execution approach specified; major implementation gaps remain.
3: Technical execution approach implementable with explicitly bounded assumptions; gaps below score 4 remain.
4: Technologies, resources and executable approach.
5: Score 4 plus feasibility evidence and environment-specific execution guidance; no material ambiguity in this dimension.

## testability
0: Verification criteria entirely absent.
1: Verification criteria mentioned vaguely; substantial interpretation required.
2: Some verification criteria specified; major implementation gaps remain.
3: Verification criteria implementable with explicitly bounded assumptions; gaps below score 4 remain.
4: Objective acceptance and representative fixtures.
5: Score 4 plus negative, boundary, regression and integration coverage; no material ambiguity in this dimension.

## reproducibility
0: Repeatability controls entirely absent.
1: Repeatability controls mentioned vaguely; substantial interpretation required.
2: Some repeatability controls specified; major implementation gaps remain.
3: Repeatability controls implementable with explicitly bounded assumptions; gaps below score 4 remain.
4: Environment/config controls and rerun procedure.
5: Score 4 plus provenance, variability policy and repeat-run verification; no material ambiguity in this dimension.

## reliability
0: Failure handling entirely absent.
1: Failure handling mentioned vaguely; substantial interpretation required.
2: Some failure handling specified; major implementation gaps remain.
3: Failure handling implementable with explicitly bounded assumptions; gaps below score 4 remain.
4: Expected failures and recovery behavior.
5: Score 4 plus recovery, idempotency and failure propagation verification defined; no material ambiguity in this dimension.

## observability
0: Diagnostics entirely absent.
1: Diagnostics mentioned vaguely; substantial interpretation required.
2: Some diagnostics specified; major implementation gaps remain.
3: Diagnostics implementable with explicitly bounded assumptions; gaps below score 4 remain.
4: Sufficient structured diagnostics.
5: Score 4 plus correlated provenance and inspectable decisions; no material ambiguity in this dimension.

## agent_executability
0: Agent execution plan entirely absent.
1: Agent execution plan mentioned vaguely; substantial interpretation required.
2: Some agent execution plan specified; major implementation gaps remain.
3: Agent execution plan implementable with explicitly bounded assumptions; gaps below score 4 remain.
4: Ownership, dependencies and verification gates.
5: Score 4 plus handoffs, permissions, integration checks and completion evidence; no material ambiguity in this dimension.

## Mandatory caps
Undefined critical inputs/outputs: interface_contracts <=3. Undefined critical owner/handoffs: agent_executability <=3. Record cap maximum and evidence-backed reason. No objective system acceptance: evidence_gaps includes NO_OBJECTIVE_ACCEPTANCE; testability <=3. No reproducibility controls: NO_REPRODUCIBILITY_CONTROLS; reproducibility <=3. Critical contradiction: CRITICAL_CONTRADICTION; clarity <=2. Unsupported critical decisions penalize all affected dimensions and produce findings; do not credit assumptions. These tokens declare absence for deterministic checking, not source keywords. Never award 5 with undefined critical boundaries.
