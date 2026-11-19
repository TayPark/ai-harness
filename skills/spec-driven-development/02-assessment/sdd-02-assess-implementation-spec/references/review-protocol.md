# Independent review

A: specification/architecture; B: contracts/verification; C: execution/operations.

- clarity: primary A, secondary C.
- completeness: primary A, secondary B.
- decomposition: primary A, secondary C.
- interface_contracts: primary B, secondary A.
- implementability: primary A, secondary B.
- testability: primary B, secondary C.
- reproducibility: primary B, secondary C.
- reliability: primary B, secondary A.
- observability: primary C, secondary B.
- agent_executability: primary C, secondary A.

If authorized genuine subagents exist, provide the same raw source and rubric. Isolate initial conclusions until submission. Retain reviewer IDs, raw scores, evidence, blockers, gate results and contract/severity positions. Otherwise sequential roles are single-agent role simulation; independent_review=false.

Flag score differences >=2, unmatched critical blockers, material severity differences, specified-contract disagreement and gate disagreement. Reconcile against evidence and anchors, never average. Record original scores, reviewer IDs, supporting evidence, decision, final score and remaining disagreement. Each reviewer must act as an independent critic attempting to falsify readiness and uncover overlooked blockers, not confirm the draft. Agreement does not prove correctness.

For repeated model assessments record model identifier/configuration if available, rubric version, input hash, scores, variance and material disagreements. No repeat-model run means repeated_scores=[] and observed_variance=null.
