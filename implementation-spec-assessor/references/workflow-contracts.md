# Phase interfaces

DAG: A→B; A→C; B,C→D; C,D→E; D,E→F; F→I. Optional F→G→H→I. H invokes A–F on revised text.

Logical types: NormalizedRequirements uses normalized-requirements.schema.json. DimensionAssessments, ComponentInventory, IntegrationGaps, Findings, CriticalBlockers, GateResults and Recommendations use their named arrays/objects in assessment.schema.json. A source is plain text passed as a string and encoded as UTF-8 before hashing. Empty or whitespace-only text is unusable and returns BLOCKED. Each source has a source_id matching `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`. COMPARE uses two source IDs that differ without case sensitivity. Policy uses report.policy. Preservation mapping rows contain requirement_id, revised_location, classification, preservation_status, explanation, semantic_review, authorization (nullable). Classification: UNCHANGED, CLARIFIED, RESTRUCTURED, PROPOSED_ADDITION, AUTHORIZED_CHANGE, REMOVED_WITH_AUTHORIZATION, UNRESOLVED.

## Phase A
Responsibility: Extract scope, requirements, deliverables, acceptance, decisions; stable R IDs.
Required input/logical type: source text, source metadata, policy.
Output/logical type: NormalizedRequirements.
Precondition: all named inputs present and validated; source evidence remains isolated.
Postcondition: output complete, IDs stable and references resolvable.
Failure: stop dependent phases; report explicit phase error. No fabricated output or silent retry.
Consumers: B,C.

## Phase B
Responsibility: Independently score ten dimensions with evidence and caps.
Required input/logical type: source, NormalizedRequirements, rubric.
Output/logical type: DimensionAssessments.
Precondition: all named inputs present and validated; source evidence remains isolated.
Postcondition: output complete, IDs stable and references resolvable.
Failure: stop dependent phases; report explicit phase error. No fabricated output or silent retry.
Consumers: D.

## Phase C
Responsibility: Inspect schema compatibility, dependency graph, errors and state.
Required input/logical type: NormalizedRequirements.
Output/logical type: ComponentInventory, IntegrationGaps.
Precondition: all named inputs present and validated; source evidence remains isolated.
Postcondition: output complete, IDs stable and references resolvable.
Failure: stop dependent phases; report explicit phase error. No fabricated output or silent retry.
Consumers: D,E.

## Phase D
Responsibility: Classify impact and remediation; stable F IDs.
Required input/logical type: DimensionAssessments, ComponentInventory, IntegrationGaps.
Output/logical type: Findings, CriticalBlockers.
Precondition: all named inputs present and validated; source evidence remains isolated.
Postcondition: output complete, IDs stable and references resolvable.
Failure: stop dependent phases; report explicit phase error. No fabricated output or silent retry.
Consumers: E,F.

## Phase E
Responsibility: Use deterministic gate engine.
Required input/logical type: dimensions, findings, components, policy.
Output/logical type: GateResults, status.
Precondition: all named inputs present and validated; source evidence remains isolated.
Postcondition: output complete, IDs stable and references resolvable.
Failure: stop dependent phases; report explicit phase error. No fabricated output or silent retry.
Consumers: F,I.

## Phase F
Responsibility: Sort criticality, impact, blocking dependencies, verification impact, supportable effort.
Required input/logical type: findings, failed gates, dependencies.
Output/logical type: Recommendations.
Precondition: all named inputs present and validated; source evidence remains isolated.
Postcondition: output complete, IDs stable and references resolvable.
Failure: stop dependent phases; report explicit phase error. No fabricated output or silent retry.
Consumers: G,I.

## Phase G
Responsibility: Preserve requirements; never invent decisions.
Required input/logical type: source, findings, normalization, approved policy.
Output/logical type: revised source, preservation mapping, unresolved decisions.
Precondition: all named inputs present and validated; source evidence remains isolated.
Postcondition: output complete, IDs stable and references resolvable.
Failure: stop dependent phases; report explicit phase error. No fabricated output or silent retry.
Consumers: H.

## Phase H
Responsibility: Re-run A–F without inheriting conclusions.
Required input/logical type: revised source, same rubric and policy.
Output/logical type: new complete assessment, deltas, remaining findings.
Precondition: all named inputs present and validated; source evidence remains isolated.
Postcondition: output complete, IDs stable and references resolvable.
Failure: stop dependent phases; report explicit phase error. No fabricated output or silent retry.
Consumers: I.

## Phase I
Responsibility: Validate and report exact results.
Required input/logical type: assessment, revision metadata.
Output/logical type: assessment.json, assessment.md, validation results.
Precondition: all named inputs present and validated; source evidence remains isolated.
Postcondition: output complete, IDs stable and references resolvable.
Failure: stop dependent phases; report explicit phase error. No fabricated output or silent retry.
Consumers: user.

Requirement IDs follow first source occurrence R-001 onward; retain identity across revisions. Components C-001, findings F-001 and gaps G-001 follow source order. Sort unordered references lexically; dimensions follow rubric order. Each finding has severity, affected IDs, evidence/absence, impact, remediation and verification. CRITICAL prevents safe meaningful implementation/verification; HIGH creates major assumptions/integration risk; MEDIUM affects quality/reliability/maintenance; LOW affects minor precision. Priority is evaluator classification unless explicitly sourced.

Failure policy: invalid source blocks; missing evidence becomes a gap; failed normalization stops scoring; inconsistent intermediate data or schema errors stop publication until corrected; missing optional tools continues with stated reduced capability; disagreement follows review protocol; failed preservation stops revision adoption; unavailable indispensable decision returns BLOCKED. Do not retry external calls automatically.
