---
name: root-cause-analysis
description: Run evidence-bound 5 Whys causal analysis across Analyze, Design, Implement, Verify, and Operate stages to separate symptoms from verifiable root causes and prescribe preventive countermeasures. Use when a stakeholder request masks an unverified bottleneck, a defect or test failure recurs, an architecture trade-off is contested, or a production incident needs postmortem closure.
---

# Root Cause Analysis (Evidence-Bound 5 Whys)

Trace observable problems, defects, test failures, or production incidents back to verifiable systemic root causes across all five SDLC stages (Analyze, Design, Implement, Verify, Operate), then bind each root cause to concrete containment, detection, and preventive countermeasures.

Read [references/five-whys-protocol.md](references/five-whys-protocol.md) before running a multi-branch investigation or cross-stage handoff.

## Activation Guardrails

- Use when: a surface request ("build X") hides an unverified operational bottleneck, a bug or data-quality failure recurs after hotfixes, an agent or test suite fails intermittently, or a production incident requires postmortem closure.
- Do NOT use when: you need full Slice 1 scope elicitation (`interview-for-requirements`), a 2-model architectural debate (`debate-models`), or weighted rubric scoring (`evaluate-with-rubric`).
- Read-only investigation: inspect code, schemas, logs, metrics, and configs read-only during causal analysis. Never modify production state or source files while diagnosing.

## Evidence-Binding Rules

Every link in a causal chain must obey strict epistemic separation:

1. **Observed link (`OBSERVED_FACT`)**: backed by an exact file path and symbol, executed command output, log timestamp, metric query, or verified user statement.
2. **Hypothesis link (`HYPOTHESIS`)**: an unverified explanation paired with one concrete, falsifiable check needed to confirm or reject it.
3. **No speculative chaining**: never stack two `HYPOTHESIS` links in a row. Stop the branch and run the falsification check (or mark the branch `INSUFFICIENT_EVIDENCE`) before drilling deeper.
4. **No human-blame stopping**: "engineer forgot" or "operator made a mistake" is never a terminal root cause. Ask why the system, contract, review gate, or runbook allowed that error to reach impact.

## Core 5 Whys Execution Workflow

1. **Frame the observable symptom**: state the exact failure, bottleneck, or deviation with scope, frequency, timeline, and affected actors.
2. **Drill down with bounded branching (typically 3-5 levels)**:
   - Ask why the current state occurred using evidence from the environment.
   - When multiple independent factors contribute (for example, an upstream schema change plus a missing validation gate), split into labeled branches (`W2a`, `W2b`) instead of forcing one linear chain.
3. **Run the reverse-causality ("Therefore") check**: read each branch bottom-up (`Root Cause -> Therefore -> ... -> Symptom`). If any step does not logically entail the next, revise or split the branch.
4. **Classify countermeasures by layer**:
   - Immediate Containment: stops active impact or data corruption right now.
   - Detective Control: automated test, reconciliation check, or alert that catches recurrence early.
   - Systemic Fix: requirement, architecture, data-contract, code, or runbook change that removes the root cause.
5. **Hand off to the matching SDLC stage**:
   - Analyze bottleneck reframed -> pass confirmed problem statement to `interview-for-requirements`.
   - Design or contract defect -> pass ADR constraints to `sdd-01-plan-repository-implementation`.
   - Implementation or test failure -> pass root cause and regression target to `sdd-03-execute-implementation-plan` or `sdd-04-verify-implementation-independently`.
   - Production incident -> pass postmortem, golden test case, and runbook update to `sdd-06-operate-and-handover`.

## Output Contract

Report every investigation in four compact blocks:

1. **Symptom & Scope**: exact observed failure or bottleneck, timeline, and impact.
2. **Evidence-Bound Causal Chain (`W1..Wn`)**: table listing `Level`, `Claim`, `Status` (`OBSERVED_FACT | HYPOTHESIS | FALSIFIED`), and `Evidence / Falsification Check`.
3. **Verified Root Cause(s) & Reverse-Causality Check**: terminal systemic cause(s) and confirmation that the backward chain holds (or `INCONCLUSIVE` with blocking evidence gaps).
4. **Countermeasure & Handoff Map**: `Containment`, `Detective Control`, `Systemic Fix`, `Owner` (`unassigned` if unknown), and `Target SDLC Stage`.
