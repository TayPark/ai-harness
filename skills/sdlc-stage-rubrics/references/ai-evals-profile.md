# AI / LLM / Autonomous Agent Evaluation Profile (`A1`–`A4`)

Apply this conditional profile alongside [sdlc-rubrics-v2.md](sdlc-rubrics-v2.md) whenever the evaluated system includes LLM generation, retrieval-augmented generation (RAG), multi-turn dialogue, or autonomous tool-using agents. Non-AI software and prose-only rubrics exclude these workload controls.

## Stage Mapping (`A1`–`A4`)

| Control | SDLC Stage & Dimensions | Mandatory Observable Evidence |
| --- | --- | --- |
| **A1. Error-Driven Baseline & Tool Authority** | Requirement (`R1`, `R2`, `R3`, `R5`) | Sample 100+ representative traces (when available) with open-to-axial failure coding naming the top 3 failure categories plus rare critical risks; define bounded tool allowlists, sample-size/error-rate contracts, `cost_per_successful_task` ceilings, and `p50`/`p95` latency targets. |
| **A2. Deterministic Controls & Isolation** | Implementation (`I3`, `I4`, `I5`) | Model-external authorization allowlists, retry/token/step caps, deterministic schema/execution checks before any LLM judge, and strict prompt-injection fencing treating traces, retrieved chunks, and user inputs as untrusted data. |
| **A3. Workload Verification & Reliability** | Verification (`V1`, `V2`, `V3`, `V4`, `V5`) | Apply only the workload controls active in the system (see below), enforce `pass^k` reliability under production-equivalent temperature, qualify LLM judges via `calibrate_judge.py`, and run paired statistical comparisons (`compare_runs.py`) with non-compensatory per-category CI gates. |
| **A4. Online Evals, Drift & Closed Loop** | Operation (`O1`, `O2`, `O4`, `O6`, `O7`) | Sample live traffic for asynchronous judging, alert on per-category drift, verify side-effect-safe shadow deployments before promotion, track `cost_per_successful_task` and `p50`/`p95` latency, adjudicate production failures into versioned golden datasets, and run the full eval suite before model switches. |

## Conditional Workload Verification Rules (`A3`)

Select applicable workload modules in Requirement and record justified exclusions in `exceptions[]`:

1. **RAG Systems (`V1`, `V2`): Separate Retrieval from Generation**
   - Retrieval: measure `recall@k`, `MRR`, or `nDCG` against defined relevance judgments. Missing relevance labels yield `INCONCLUSIVE`, not `PASS`.
   - Generation: measure faithfulness (every material claim grounded in retrieved context). Scoring only final answers cannot isolate retrieval vs generation failures.
2. **Tool-Using Agents (`V2`, `V3`): Multi-Path Trajectory Evaluation**
   - Log every step: tool name, arguments, output, tokens, latency, and error recovery.
   - Evaluate acceptable outcomes, tool/argument validity, error recovery, and step budgets across valid paths rather than penalizing legitimate alternatives to a single reference sequence.
3. **Multi-Turn Conversational Systems (`V2`, `V4`): Simulated Users**
   - Run simulated users with explicit personas, hidden goals, and policy constraints until goal completion or turn limit.
   - Grade goal completion, turns-to-resolution, state/memory retention, and policy violations.
4. **Stochastic Reliability (`V5`): `pass@k` vs `pass^k`**
   - Predefine `n`, `k`, stopping rules, and production-equivalent inference settings (`temperature`).
   - Measure both `pass@k` (solvability) and `pass^k` (all-`k` production reliability). Do not certify `T2`/`T3` stochastic workflows from single-run `pass@k` or uninvestigated retry-until-green runs.

## Production Online Evaluation & Feedback Closure (`A4`)

- External infrastructure boundary: Online sampling, async judge queues, drift alerting, and shadow routing belong to deployment infrastructure; local skill execution requires zero live services and prohibits raw sensitive production traces in public fixtures.
- Shadow safety: Shadow deployments must isolate or disable external writes so production side effects are never duplicated.
- Adjudicated feedback loop: Production failures become labeled golden test cases (`source: "prod_failure"`, `incident_id`) only after human adjudication and sanitization.
- Model-switch gate: Run the full golden dataset, judge calibration, and efficiency comparison before switching production models.

## Non-Waivable AI Hard-Fails

Confirmed unauthorized irreversible action, credential exfiltration, bypass of a mandatory human-approval gate, or prompt-injection override of admission policy triggers an immediate non-waivable `FAIL`.
