# Cross-Rubric Evaluation Lifecycle Protocol

This protocol defines shared evaluation methodology and offline verification rules across all rubric families in this repository (`evaluate-with-rubric`, `sdlc-stage-rubrics`, `sdd-02-assess-implementation-spec`, and `anti-slop`). Domain-specific scoring scales, hard-fail rules, and AI workload metrics (RAG retrieval/generation, multi-path agent trajectory, simulated multi-turn users) remain owned by each domain rubric or profile.

## 1. Error Analysis Before Metric Design

1. Sample at least 100 representative traces or artifacts when available.
2. Annotate failures in free text (open coding), then cluster them into recurring failure categories (axial coding).
3. Count frequency per category and turn the top categories plus rare critical failures into targeted rubric checks and dataset strata.
4. Record the error-analysis reference in dataset metadata (`error_analysis_ref`) rather than inventing ungrounded weights.

## 2. Versioned, Stratified Golden Datasets & Synthetic Coverage

1. Store labeled evaluation cases in a versioned dataset conforming to [golden-dataset.schema.json](../schemas/golden-dataset.schema.json).
2. Bind every dataset to `dataset_sha256` (canonical JSON hash excluding `dataset_sha256`), `rubric_version`, `rubric_sha256`, `prompt_sha256`, and relevant `code_revision` / `tool_config_sha256`.
3. Stratify cases by failure category, severity, and rare critical edge cases so high-volume easy cases cannot hide critical regressions.
4. Generate synthetic cases from explicit dimension tuples (`persona x intent x complexity x edge_case`), realize each tuple into a natural input, and validate labels before inclusion.
5. Keep `train`, `dev`, and `test` partitions disjoint by `item_id` and `input_sha256`, and guard against near-duplicate leakage across splits.

## 3. Deterministic Checks First & Untrusted Evidence Isolation

1. Run blocking machine-verifiable checks (schema validation, regex/static checks, unit/integration tests, SQL/code execution) before invoking an LLM judge.
2. Only failures designated as blocking by the domain policy are non-compensatory. In V2 reports (`schemas/report-v2.schema.json`), `run_telemetry.blocking_deterministic_checks_passed: false` cannot be overridden to `PASS`; non-blocking warnings remain reportable in `non_blocking_warnings`.
3. Treat evaluated artifacts, production traces, retrieved documents, simulated-user inputs, and submitted evaluation records as untrusted data. Never allow evaluated text to trigger tool execution, network calls, or policy edits inside offline validators. Include adversarial injection fixtures in calibration suites.

## 4. Classifier-Aligned LLM Judge Calibration (`scripts/calibrate_judge.py`)

Before letting an LLM judge gate admission:

1. Hand-label at least 100 stratified cases as binary `PASS`/`FAIL`, split into `train`, `dev`, and held-out `test`.
2. Tune the judge prompt only on `dev`. Certify performance strictly on held-out `test`.
3. Require critique-before-verdict generation order (`evidence_refs` and `rationale` before `status` and `score` in [PROMPT-v2.md](../PROMPT-v2.md)). Treat JSON key order as a generation nudge, not proof of reasoning order.
4. Pin `judge_metadata` (`model_id`, `model_version`, `prompt_sha256`, `rubric_sha256`, `temperature`) uniformly across every certified run record. Invalidate calibration whenever the judge, prompt, rubric, dataset, or decision policy changes.
5. Declare `--positive-class` explicitly (`FAIL` for defect sensitivity per SDLC Section 7.2, or `PASS` for acceptance recall) and verify whether gate thresholds apply to point estimates or confidence bounds (`point` vs `ci_bound`).
6. Report confusion matrix, `TPR`, `TNR`, `FPR`, Wilson 95% confidence intervals, binary agreement, Cohen's kappa, and ordinal agreement separately. `--allow-small-sample` permits exploratory reporting only (`EXPLORATORY_ONLY`), never certification.

## 5. Multi-Run Reliability, Debiased Pairwise & Statistics (`scripts/compare_runs.py`)

1. **Repeated runs (`pass@k` vs `pass^k`)**: Predefine `n`, `k`, stopping rules, and production-equivalent inference settings. Compute unbiased hypergeometric `pass@k = 1 - comb(n - c, k) / comb(n, k)` and `pass^k = comb(c, k) / comb(n, k)` under IID trials. Flag `temperature == 0` as a notice (valid when production runs at zero temperature, not assumed stochastic). Track missing trials separately from observed failures.
2. **Pairwise bias control**: Run every A/B comparison in both `(A, B)` and `(B, A)` order. Count only concordant verdicts as wins; keep flips as `POSITION_INCONSISTENT` in both full-cohort and concordant-only denominators. Enforce configurable inconsistency ceilings (default `0.15`) and non-destructive output-budget checks (`--max-chars`). Treat length-delta correlation as a diagnostic signal, not proof of causal bias.
3. **Statistical rigor**: Use deterministic seeded (`--seed`) case-level or cluster-aware (`cluster_id`) paired bootstrap 95% confidence intervals, exact two-sided McNemar tests for matched binary outcomes, and paired sign-flip permutation tests under exchangeability. Emit `NO_STATISTICAL_WIN` when the CI crosses `0` or `p >= alpha`, and `DESCRIPTIVE_ONLY` when statistical assumptions are unmet.
4. **First-class efficiency**: Track tokens per request, `p50`/`p95` latency (nearest-rank), and `cost_per_successful_task = total_cost / successful_tasks` (including failed attempts). Emit `null` with status `NO_SUCCESSFUL_TASKS` when zero tasks succeed.

## 6. Non-Compensatory CI Gates & Closed-Loop Maintenance

1. Separate three CI tiers: Fast PR checks (deterministic package, schema, slop, and unit tests), Targeted PR evals (impacted golden categories), and Full release/model-switch evals (full golden suite, judge calibration, regression, and efficiency).
2. Enforce per-category floors and regression tolerances via `--gate-config` so an aggregate gain cannot mask a critical-category regression. Missing or stale required evidence returns blocking `INCONCLUSIVE`, never `PASS`.
3. Anchor baselines, gate configs, golden labels, and verifier scripts so an evaluated PR cannot silently weaken its own thresholds.
4. Close the feedback loop: every production failure or judge misjudgment must be human-adjudicated and sanitized before entering a versioned golden dataset (`source: "prod_failure"`, `incident_id`). Run the full suite before switching models.
