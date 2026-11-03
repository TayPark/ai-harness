# Rubric 1.0.0

Exactly ten dimensions. Never redistribute weights. Evidence must come from source, not conventions.

- clarity: 10%. Terminology, ambiguity, consistency and precision.
- completeness: 10%. Functional/nonfunctional scope, constraints, exclusions and missing decisions.
- decomposition: 10%. Responsibilities, cohesion, coupling and dependency ordering.
- interface_contracts: 15%. Schemas, validation, errors, invariants, state and compatibility.
- implementability: 10%. Feasibility, resources, environment and actionable implementation.
- testability: 15%. Objective acceptance, negative/boundary/integration tests and fixtures.
- reproducibility: 10%. Pinned environment, configuration, provenance and variability.
- reliability: 5%. Failures, retry, idempotency, timeout, recovery and propagation.
- observability: 5%. Structured diagnostics, correlation, provenance and audit.
- agent_executability: 10%. Ownership, handoffs, permissions, dependencies and completion evidence.

weighted_score = weight * integer_score / 5. Sum without intermediate rounding. These weights yield exact integer points. Assess dimensions before aggregation. No score adjustment from the total.

Default mandatory gates: overall >=90; interface_contracts, testability, reproducibility >=4; no unresolved critical blocker; every explicitly required component has specified owner and acceptance criteria. Policy may override numeric thresholds only. scripts/validate_assessment.py is the authoritative deterministic gate engine. READY iff all gates pass and source is usable. BLOCKED iff source unusable or unresolved CRITICAL external decision. Otherwise NEEDS_REVISION. Contradictions requiring unavailable resolution are critical external decisions.
