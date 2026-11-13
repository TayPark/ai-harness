# Verification map

Run `python -m pytest -q` from the skill directory.

- test_validator: valid/invalid schema, required fields, malformed JSON, CLI errors, valid calibration reports, repeated deterministic results.
- test_scoring: weights, integer bounds, arithmetic, totals, duplicate dimensions and caps.
- test_acceptance_gates: each mandatory gate, forged readiness, policy configuration, BLOCKED source and source injection strings.
- test_traceability: missing/dangling/duplicate identifiers, false quotes, absent source, hash and capability/reviewer claims.
- test_requirement_preservation: unchanged/clarified text, missing requirements, numeric weakening, default promotion, new declared contradiction, hidden decision, authorized removal.

Calibration scores are authored examples. Tests assert readiness properties and objective report validity, not universal LLM score constants. Injection tests cover deterministic isolation, not empirical model robustness. Semantic preservation review remains explicitly unverified without a reviewer assertion. Model repeatability is not tested by repeated validator calls.
