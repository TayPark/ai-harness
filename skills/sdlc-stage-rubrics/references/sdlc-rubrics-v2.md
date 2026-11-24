# Production-Grade SDLC Evaluation Rubrics (v2.0)

Revised after dual independent review over the initial v1.0 architecture.

## Summary of v2.0 Fixes Applied

- Scale-to-Threshold Mathematical Consistency (`C1`): Resolved the `3 = 75` vs `80–90` paradox by keeping `75` as the `T1/T2` weighted baseline and enforcing tier-specific critical-dimension floors (`>= 3` on `†` for `T2`; `>= 3` on all mandatory dimensions and `>= 4` on designated high-assurance dimensions for `T3`), plus an explicit **Score-0 Disqualifier Dominance Rule**.
- Unreachable `PENDING_OBSERVATION` Bug Fixed (`C6` / `4.2`): Reordered decision precedence so unelapsed operational observation window telemetry does not trigger `INCONCLUSIVE` when pre-window baseline operational readiness controls (`O2/O3/O4/O5`) are evidenced.
- Applicability & Partial-Score Trap Fixed (`C2`): Marked conditional dimensions explicitly (`conditional_optional`), banned arbitrary `NOT_APPLICABLE` exclusions on mandatory dimensions, and restricted aggregate `weighted_score` failure during incomplete evidence to `max_achievable_score < threshold`.
- Stage 1–4 Coverage Gaps Closed:
  - Requirement (`R1–R7`): Added brownfield backward-compatibility/migration, cost/resource ceiling bounds, qualitative justification option (`R1`), and ambiguity/spec-omission distinction (`R-G6`).
  - Implementation (`I1–I7`): Added observability & PII/secret log-redaction instrumentation, scope-integrity / anti-test-suppression gate (`I-G7`), and library applicability for `I6`.
  - Verification (`V1–V7`): Promoted `V5` (test independence & reliability) to critical (`†`), prohibited uninvestigated retry-until-green masking, aligned `V-G6` with config parity, and added `V-G8` (release operability & rollback preflight).
  - Operation (`O1–O7`): Promoted `O2` (observability) and conditional `O4` (rollback/DR) to critical (`†`), replaced calendar-only observation windows with `max(time_window, min_representative_cycles)`, added config drift & vulnerability SLA tracking, and separated temporary error-budget triggers from hard fails.
- Evidence, Evaluator Isolation, & Schema (`C3`, `C7`, `4.3`, `5`, `6`): Added `spec_revision`, `producer_role`, `freshness_window`, `STALE` verdict, `evidence_records[]`, `exceptions[]`, mandatory LLM prompt-injection isolation, and quantitative calibration acceptance criteria.

---

## 1. Foundational Claims (`C1`–`C7`, Revised)

### C1. Common 0–4 Ordinal Scale with Disqualifier Dominance & Calibrated Baselines
| Score | Classification | General Interpretation |
| --- | --- | --- |
| **0** | Unacceptable | Verified fundamental failure, contradiction, or absence of a mandatory control (overrides any positive partial anchors in the same dimension). |
| **1** | Weak | Minimal evidence; substantial deficiencies remain. |
| **2** | Partial | Core mechanism present, but meaningful gaps remain. |
| **3** | Baseline | All essential dimension-specific criteria demonstrated by valid evidence. |
| **4** | Robust | Baseline plus demonstrable resilience, adversarial coverage, or stronger independent assurance. |

- Anchors are evaluated conjunctively (all applicable conditions must hold). Intermediate/fractional scores are prohibited.
- Pre-declared Conditional Clauses: Whenever an anchor references *"applicable"* controls (e.g., concurrency, migrations, latency), the change's pre-approved Risk & Domain Profile must declare which controls apply before scoring begins.

### C2. Independent Score, Non-Compensatory Gates, & Applicability Discipline
- Weighted score is a supporting indicator (`S = (sum(w_i * s_i) / (4 * sum(w_i))) * 100` over applicable scored dimensions), **never** a substitute for critical gates.
- Dimensions carry an explicit applicability tag: `required` or `conditional_optional` (only `conditional_optional` dimensions may become `NOT_APPLICABLE`, with pre-approved justification recorded in `exceptions[]`).
- When mandatory dimensions have `INSUFFICIENT_EVIDENCE`, only trigger an early aggregate-score `FAIL` if **`max_achievable_score` (substituting `4` for uninspected dimensions) is still `< threshold`**; otherwise return `INCONCLUSIVE` unless a hard fail or observed dimension floor already failed.

### C3. Generalized Version-Bound Evidence Contract
Every finding and gate verdict must reference immutable records in `evidence_records[]` with:
```yaml
evidence_id: E0001
subject_kind: requirement_spec | build_artifact | release_candidate | prod_service
spec_or_artifact_ref: <spec-id-or-artifact-uri>
artifact_digest: sha256:...
source_revision: <commit-sha>
build_id: <immutable-build-id-or-null>
deployment_id: <deployment-id-or-null>
environment: spec | dev | ci | staging | prod
collected_at: <iso8601>
freshness_window: <duration-or-event-bound>
producer: <tool-or-reviewer-id>
producer_role: author | ci | independent_verifier | prod_telemetry | human_authority
method: schema_check | unit_test | integration_test | security_scan | review | telemetry_query
scope: <requirements-or-controls-covered>
command_or_query_digest: sha256:...
result: PASS | FAIL | OBSERVED | COMPLETE | PARTIAL | UNKNOWN
limitations: []
```
Note: A digest proves identity/integrity, not semantic adequacy or truth.

### C4. Distinct Stage Decisions & Evidence Ownership Boundaries
| Stage | Core Question | Evaluation Subject | Primary Producer Role |
| --- | --- | --- | --- |
| **1. Requirement** | Is it specified, feasible, safe, and testable enough to build? | Approved requirement baseline & ADRs | `author` + `independent_verifier` |
| **2. Implementation** | Was the change built correctly and reproducibly? | Change-scoped commit diff, CI build, unit/component checks | `author` + `ci` |
| **3. Verification** | Does the frozen release candidate work in deployment-equivalent conditions? | Exact immutable Release Candidate (`artifact_digest`) | `independent_verifier` + `ci` |
| **4. Operation** | Does the deployed service remain reliable, secure, and recoverable in production? | Production telemetry, incidents, drills, & change history | `prod_telemetry` + `human_authority` |

- Evidence from Implementation (`ci` / `author`) may inform Verification only when its `source_revision`, `artifact_digest`, configuration, and `freshness_window` remain valid and independently verified; it cannot substitute for independent oracle checks on critical `T2/T3` controls.
- Downstream findings revealing upstream defects trigger a **selective upstream change assessment** and invalidate downstream evidence via `STALE` rather than silently altering historical stage scores.

### C5. Deterministic Risk Tier Assignment (`T1`–`T3`) & Proportionate Profiles
Assign and record the risk tier **before** evaluation (highest applicable tier wins; escalate automatically if scope/risk increases):

| Risk Tier | Automatic Classification Triggers | Advancement Policy (Reconciled with `3 = 75` Scale) |
| --- | --- | --- |
| **T1 — Low** | Isolated, fully reversible internal change; no PII/financial/safety impact; no external exposure or privileged tools. | Weighted score `>= 75` (Verification `>= 75`, calibrated per profile); all mandatory dimensions `>= 2`; uses **streamlined T1 evidence** (e.g., inherits platform DR/telemetry baseline where unchanged). |
| **T2 — Standard** | Production user-facing services, normal business data, non-trivial state transitions, or shared platform libraries. | Weighted score `>= 75` (Verification `>= 80`); all mandatory dimensions `>= 2`; **all critical dimensions (`†`) `>= 3`**. |
| **T3 — High** | Sensitive/PII/regulated data, financial or safety impact, irreversible migrations/actions, external internet auth boundaries, or privileged autonomous agents. | Weighted score `>= 80` (Verification `>= 85`, requiring `4` on at least 2 designated `†` dimensions per stage); **all mandatory dimensions `>= 3`**; mandatory independent human sign-off. |

*(Note: Numerical thresholds require empirical calibration against adjudicated cases per Section 7 before enforcing as organizational policy.)*

### C6. Standardized State Enums & Unreachable-Bug-Free Precedence
- Dimension Status Enum: `SCORED | NOT_APPLICABLE | INSUFFICIENT_EVIDENCE`
- Critical Condition / Gate Enum: `CLEAR | TRIGGERED | UNKNOWN | NOT_APPLICABLE`
- Stage Verdict Enum: `PASS | FAIL | INCONCLUSIVE | PENDING_OBSERVATION | STALE`

**Fixed Precedence Algorithm (evaluated in strict order):**
```python
if subject_or_evidence_invalidated_by_change:
    decision = "STALE"
elif any_confirmed_hard_fail or any_confirmed_scoring_gate_failure or max_achievable_score < stage_threshold:
    decision = "FAIL"
elif non_observation_mandatory_evidence_incomplete or any_non_observation_critical_gate_unknown:
    decision = "INCONCLUSIVE"
elif stage == "operation" and observation_window_or_sample_incomplete:
    # Pre-window operational readiness (O2/O3/O4/O5) must be verified; only longitudinal O1/O6/O7 exposure is pending
    decision = "PENDING_OBSERVATION"
elif weighted_score < stage_threshold:
    decision = "FAIL"
else:
    decision = "PASS"
```

### C7. Deterministic Checks, Untrusted-Input Isolation, & Independent Adjudication
- Deterministic checks verify schemas, weights, arithmetic, build digests, CI exit codes, and declared gates.
- Calibrated semantic evaluators (LLM or human) assess ambiguity, design trade-offs, and oracle adequacy under **mandatory isolation**:
  1. **Prompt-Injection Fencing**: Untrusted artifacts (code, PR comments, logs, docs) must be framed as read-only data with zero tool execution driven by artifact text.
  2. **No Self-Certification**: An implementer model/session may never adjudicate its own output; `T2/T3` critical semantic judgments require an independent model family or human reviewer.

---

## 2. Stage 1: Requirement Rubric (`R1`–`R7`, 100%)

| ID & Dimension (`†`=Critical, `CO`=Conditional Optional) | Wt | Observable 0–4 Anchors (Conjunctive) | Required Evidence |
| --- | --- | --- | --- |
| **R1. Problem, outcomes, & scope** | 15% | `0`: Contradictory/absent objective. `1`: Vague prose only. `2`: Outcome + partial scope. `3`: Measurable success metric (or preapproved justified qualitative acceptance criterion for exploratory/mandated work), accountable owner, explicit in/out scope. `4`: Alternatives, trade-offs, and stakeholder decisions recorded. | Problem statement, success metrics / justified criterion, scope boundaries, owner sign-off |
| **R2. Behavioral requirements & acceptance criteria †** | 20% | `0`: Essential behaviors mutually contradictory. `1`: Happy-path prose only. `2`: Main flows defined; edge/error cases missing. `3`: Unambiguous testable acceptance criteria for success, failure, boundary, and authorization cases. `4`: Cross-workflow invariants and adversarial misuse cases defined. | Versioned functional spec, Given/When/Then cases, state-transition contracts |
| **R3. Nonfunctional, data, & compatibility requirements †** | 15% | `0`: Essential constraints absent/contradictory. `1`: Unquantified adjectives ("fast"). `2`: Partial numbers without workload/failure/compatibility semantics. `3`: Measurable targets & assumptions for applicable latency, capacity, availability, freshness, consistency, retention, backward-compatibility/deprecation, and cost ceilings (inapplicability justified per profile). `4`: Stress envelopes and graceful degradation quantified. | NFR spec, SLI/SLO targets, workload & cost profile, schema/compatibility contracts |
| **R4. Technical feasibility & dependencies** | 15% | `0`: Known impossibility or irreconcilable dependency. `1`: Unvalidated assumptions. `2`: Dependencies listed with unresolved blockers. `3`: Feasible component boundaries, API contracts, external dependencies, validation owners for open assumptions, and migration/backfill strategy (if stateful change applies) documented. `4`: Uncertainties retired via design comparisons or spike prototypes. | ADRs, dependency matrix, API contracts, migration plan (if applicable), spike notes |
| **R5. Security, privacy, & safety †** | 15% | `0`: Demonstrably unsafe/prohibited requirement. `1`: Sensitive behavior lacks constraints. `2`: Threats named; controls incomplete. `3`: Threat model (lightweight checklist for T1), trust boundaries, authz matrix, data classification, and compliance obligations specified. `4`: Independent risk review and adversarial abuse mitigations agreed. | Threat model / T1 risk checklist, privacy check, authz matrix, data classification |
| **R6. Traceability & change control** | 10% | `0`: Requirements unidentifiable. `1`: Informal unversioned requests. `2`: Partial IDs/priorities. `3`: Versioned requirement IDs, priority, owners, acceptance mappings, and change policy. `4`: Automated change-impact links to contracts, tests, and operational controls. | Requirement registry, traceability matrix, decision log, change policy |
| **R7. Delivery, cost, & operational constraints** | 10% | `0`: Unowned or unrecoverable deployment requirement. `1`: Generic release intent. `2`: Partial ownership/rollout plan. `3`: Applicable release, rollback/forward-recovery, observability/telemetry, support ownership, and operational acceptance criteria defined (or justified inapplicable). `4`: Failure-containment and recovery drills embedded in release plan. | Rollout plan, RTO/RPO targets, ownership matrix, observability spec |

- Requirement Gates: `R-G1` Score `>=` tier bar; `R-G2` Dimension floors (`R2/R3/R5 >= 3` for T2/T3); `R-G3` Zero unresolved contradictions or blocking TBDs in critical flows; `R-G4` Explicit authz/trust boundaries for sensitive operations; `R-G5` Every critical requirement maps to testable acceptance criteria; `R-G6` Distinguish missing spec sections (`FAIL` inside an inspected spec) from unreadable/unsubmitted source files (`INCONCLUSIVE`).
- Requirement Hard-Fails: `R-HF01` Incompatible essential behavioral outcomes; `R-HF02` Privileged, irreversible, or sensitive operation without bounded authority model; `R-HF03` Explicit violation of mandatory security/privacy/legal constraint; `R-HF04` Infeasible critical dependency with no accepted alternative.

---

## 3. Stage 2: Implementation Rubric (`I1`–`I7`, 100%)

| ID & Dimension (`†`=Critical, `CO`=Conditional Optional) | Wt | Observable 0–4 Anchors (Conjunctive) | Required Evidence |
| --- | --- | --- | --- |
| **I1. Requirement conformance & scope integrity †** | 20% | `0`: Critical behavior contradicts spec or introduces unapproved out-of-scope behavioral changes. `1`: Prototype/missing core flows. `2`: Main flows implemented; edge cases incomplete. `3`: All essential behaviors implemented within approved scope with traceable requirement-to-code mappings and compatible interfaces. `4`: Boundary and compatibility invariants additionally proven via developer checks. | Source diff (clean VCS commit), requirement-to-code map, interface defs, review record |
| **I2. Architecture, maintainability, & diagnostics** | 15% | `0`: Structural defect blocks required behavior or safe maintenance. `1`: Severe coupling, silent error swallowing, or unreviewable complexity. `2`: Partial modularity; missing or inconsistent telemetry. `3`: Proportionate responsibilities, explicit contracts, bounded dependencies, structured logging/metrics/traces with PII/secret redaction, justified choices. `4`: Failure/change containment across module boundaries proven. | Source tree, ADRs, static analysis, observability & log-redaction checks |
| **I3. Correctness & failure handling †** | 20% | `0`: Reproducible corruption, data loss, silent exception swallowing, or invalid state transition. `1`: Essential failure paths unhandled. `2`: Partial retries/validation. `3`: Applicable idempotency, consistency, timeouts, retry budgets, concurrency, and error-handling invariants implemented. `4`: Fault-injection or deterministic replay proves invariant preservation. | Code paths, unit tests, fault-handling tests, state-transition evidence |
| **I4. Security, privacy, & dependency integrity †** | 15% | `0`: Confirmed exploitable critical defect or exposed production secret. `1`: Control bypass or unrestricted privilege. `2`: Basic controls with material gaps. `3`: Enforced authn/authz, input validation, secret management, least privilege, and dependency/license policies. `4`: Abuse-oriented developer tests and verifiable supply-chain provenance (SBOM/attestation). | Security review, triaged SAST/SCA, authz tests, lockfile/dependency manifest |
| **I5. Engineering tests, anti-suppression, & build repeatability †** | 15% | `0`: Required build fails, cannot reproduce from supplied clean commit, or contains unauthorized skipped/disabled tests/linters masking failures. `1`: Manual-only validation. `2`: Partial/flaky CI. `3`: Clean repeatable build (or bit-identical where declared), passing CI, reliable unit/component tests, zero unauthorized check suppressions. `4`: Property/mutation/invariant tests catch seeded defects. | Clean commit SHA, CI run logs, build manifest, test & linter-suppression audit |
| **I6. Deployment, migration, & recovery (`CO`)** | 10% | *(Conditionally optional for pure stateless libraries with preapproved exemption)* `0`: Unprotected destructive deployment/migration path. `1`: Undocumented manual changes. `2`: Plan lacks tested recovery/compatibility. `3`: Controlled rollout, safe/forward-backward compatible migrations, tested non-prod rollback or approved forward-recovery containment. `4`: Reentrant migrations and recovery from partial rollout demonstrated. | Deployment specs, migration scripts, compatibility checks, recovery test logs |
| **I7. Reviewability & engineering handoff** | 5% | `0`: Unreviewable scope or prohibited unverified provenance on T2/T3 change. `1`: Opaque changes without handoff. `2`: Partial review/docs. `3`: Recorded scope, accountable ownership, qualified independent review (per risk tier), operating assumptions, and handoff notes. `4`: Independent challenge resolved with linked evidence. | PR, independent review record, source history, handoff docs |

- Implementation Gates: `I-G1` Score `>=` tier bar; `I-G2` Dimension floors (`I1/I3/I4/I5 >= 3` for T2/T3); `I-G3` Clean build & CI pass on exact evaluated commit; `I-G4` Zero unmitigated critical vulnerabilities or secret exposures; `I-G5` Critical state invariants preserved; `I-G6` Clean VCS commit-to-artifact provenance (`INCONCLUSIVE` if missing); `I-G7` Scope integrity & zero unauthorized test/lint suppressions (`FAIL`).
- Implementation Hard-Fails: `I-HF01` Confirmed critical requirement violation; `I-HF02` Reproducible critical data-loss/integrity defect; `I-HF03` Unmitigated critical security vulnerability, authz bypass, or secret exposure; `I-HF04` Required build/CI fails on evaluated revision; `I-HF05` Unprotected irreversible migration/deployment in high-impact path; `I-HF06` Deliberate test/lint suppression or silent failure masking bypassing required checks.

---

## 4. Stage 3: Verification Rubric (`V1`–`V7`, 100%)

| ID & Dimension (`†`=Critical, `CO`=Conditional Optional) | Wt | Observable 0–4 Anchors (Conjunctive) | Required Evidence |
| --- | --- | --- | --- |
| **V1. Requirement coverage & oracle validity †** | 20% | `0`: Contradicted expected outcomes or invalid test oracles. `1`: Informal demo or tautological assertions. `2`: Main flows mapped; critical gaps remain. `3`: Every critical acceptance criterion mapped to executed tests with independently defensible expected outcomes. `4`: Boundary, property, metamorphic, or adversarial oracles challenge suite effectiveness. | Requirement-test trace matrix, oracle specs, expected-vs-actual logs |
| **V2. Functional, integration, & compatibility correctness †** | 20% | `0`: Critical scenario fails. `1`: Smoke/unit tests only. `2`: Core workflows pass; negative/integration/compatibility paths missing. `3`: Applicable critical E2E, negative, authz, backward-compatibility, and recovery cases pass against the release candidate (exclusions preapproved). `4`: Distributed fault injection and high-risk interaction matrices validated. | E2E logs, integration results, negative/compatibility test reports |
| **V3. Performance, resilience, & data quality** | 15% | `0`: Mandatory critical NFR or data-integrity invariant violated. `1`: No representative check. `2`: Unrealistic/incomplete load or data check. `3`: Each applicable mandatory NFR and data invariant passes under representative workload with stated test limits (`T1` may inherit validated baseline if unchanged). `4`: Tail latency, stress limits, degraded modes, and headroom quantified. | Load/soak reports, chaos/failure tests, workload fixtures, data reconciliation |
| **V4. Security & abuse resistance †** | 15% | `0`: Confirmed release-blocking vulnerability. `1`: Untargeted automated scans only. `2`: Scans pass; threat-model tests incomplete. `3`: Threat-model-driven authn, authz, privacy, and misuse tests pass; confirmed findings triaged/remediated. `4`: Qualified independent adversarial/red-team test validates critical controls. | DAST/SAST/SCA triage, authz test results, abuse-case results, independent security sign-off |
| **V5. Test independence & reliability †** | 10% | `0`: Fabricated, manipulated, or retry-masked (`retry-until-green`) results. `1`: Self-attested without inspectable execution. `2`: Separate execution exists, but critical oracles are circular or flaky. `3`: Risk-appropriate independence (separate specification/review of critical oracles, documented shared dependencies), isolated execution, repeatable outcomes with zero uninvestigated critical flakes. `4`: Seeded-defect calibration or blinded evaluation proves detection power. | Oracle ownership record, execution metadata, repeated-run stability & flake audit |
| **V6. Artifact provenance & config parity †** | 10% | `0`: Results belong to a different artifact or incompatible config/migrations. `1`: Target not version-bound. `2`: Revision known; material env/config diffs unresolved. `3`: Exact RC `artifact_digest` linked to tests with environment, feature-flag, and migration parity assessed. `4`: Deployment-equivalent environment and signed provenance attestation. | Commit/build IDs, `artifact_digest`, config/flag/env manifest, parity assessment |
| **V7. Defect disposition, operability preflight, & release sign-off** | 10% | `0`: Known blocker concealed or unapproved waiver of a non-waivable gate. `1`: Informal pass claim. `2`: Defect list lacks disposition/authority or rollback preflight untested. `3`: Authorized defect dispositions, `exceptions[]` with owner/expiry, rollback & alert-routing preflight verified, explicit release sign-off. `4`: Automated canary stop conditions and live rollback rehearsal validated. | Defect register, retest evidence, `exceptions[]`, rollback/alert preflight, release approval |

- Verification Gates: `V-G1` Score `>=` tier bar (`75/80/85`, with `>=4` rules for `T3`); `V-G2` Dimension floors (`V1/V2/V4/V5/V6 >= 3` for T2/T3); `V-G3` Critical acceptance tests executed & passing without retry-masking (`FAIL` if failed/flaky, `INCONCLUSIVE` if unexecuted); `V-G4` Zero unresolved release-blocking security defects; `V-G5` Mandatory NFR/data-integrity targets demonstrated; `V-G6` Exact RC `artifact_digest` AND config/migration parity matched; `V-G7` Residual risks and bounded exceptions approved by named authority (prohibiting exceptions to non-waivable hard-fails); `V-G8` Rollback preflight, canary stop triggers, and production telemetry/alert readiness verified before release.
- Verification Hard-Fails: `V-HF01` Critical acceptance test fails; `V-HF02` Unresolved release-blocking security/privacy defect; `V-HF03` Mandatory NFR or data-integrity constraint violated; `V-HF04` Test target mismatches RC `artifact_digest` or config/migration parity; `V-HF05` Confirmed evidence fabrication, manipulation, unauthorized test suppression, or uninvestigated retry-masking.

---

## 5. Stage 4: Operation Rubric (`O1`–`O7`, 100%)

- Observation Sufficiency Policy: Replaced calendar-only defaults with `max(min_time_window, min_representative_cycles_or_events)` defined in the Requirement baseline (`T1`: `24h` or `1` complete batch/execution cycle; `T2`: `7d` + representative traffic; `T3`: `28d` + representative traffic/recovery assurance; statistical sample size stated for stochastic failure rates).
- Post-Launch Re-evaluation Triggers: Trigger re-assessment upon observation-window completion, `Sev-1/2` incident, error-budget burn freeze, major dependency/config drift, or scheduled `T3` quarterly review.

| ID & Dimension (`†`=Critical, `CO`=Conditional Optional) | Wt | Observable 0–4 Anchors (Conjunctive) | Required Evidence |
| --- | --- | --- | --- |
| **O1. Production reliability, SLOs, & DORA health †** | 20% | `0`: Unmitigated sustained critical outage or violated safety/SLO freeze. `1`: Unmeasurable reliability. `2`: SLIs exist; insufficient sampling or unaddressed target breach. `3`: Approved SLIs/SLOs and error-budget policy satisfied (temporary minor breaches follow defined budget policy; change-failure rate & MTTR tracked) over sufficient exposure (`PENDING_OBSERVATION` if unelapsed). `4`: Holds across traffic segments and tail conditions with graceful degradation proven. | SLI/SLO reports, error-budget burn logs, change-failure/MTTR metrics, exposure volume |
| **O2. Observability & alert effectiveness †** | 15% | `0`: Demonstrated inability to detect critical failure. `1`: Logs/metrics lack actionable alerts. `2`: Partial dashboards or unvalidated alert routes. `3`: Critical user-impact signals monitored, actionable alerts routed, synthetic/drill detection paths exercised. `4`: Detection latency and false-alarm noise measured and reduced via drills/incidents. | Metrics, traces, structured logs, alert rules, notification & detection drill evidence |
| **O3. Incident response & recovery †** | 20% | `0`: Critical incident cannot be contained/recovered within policy. `1`: No reliable on-call owner, escalation, or runbook. `2`: Untested/incomplete procedures. `3`: On-call ownership, escalation, runbooks, and RTO/RPO objectives validated through real incidents or controlled game-day exercises (zero incidents alone does not prove O3). `4`: Multi-failure containment and corrective actions proven. | On-call rotation, incident timelines, game-day logs, runbooks, postmortems, RTO/RPO actuals |
| **O4. Deployment safety, config parity, & disaster recovery † (`CO` for stateless read-only)** | 15% | `0`: Unsafe production rollout, unmitigated critical config drift, or broken recovery for critical state. `1`: Manual deploy without reliable rollback. `2`: Unvalidated rollback/backups or unmonitored config drift. `3`: Controlled rollout, config-drift detection, rollback or approved forward-recovery, and backup restoration exercised against objectives. `4`: Multi-AZ/region DR and partial-rollout recovery drills verified. | Deployment logs, drift-detection alerts, rollback/forward-recovery & backup-restore tests |
| **O5. Continuous security, patching, & compliance †** | 15% | `0`: Active uncontained compromise or material compliance breach. `1`: No operational security monitoring. `2`: Overdue critical CVE patches or incomplete access reviews. `3`: Vulnerability remediation SLAs, periodic access reviews, tamper-evident audit logging, secret rotation, and retention/privacy policies enforced. `4`: Detection-response exercises and independent audits confirm sustained effectiveness. | Security alerts, access-review logs, CVE SLA tracker, secret-rotation & audit logs |
| **O6. Capacity, cost, & degradation control** | 10% | `0`: Resource or hard cost exhaustion blocks required service without graceful shedding. `1`: No capacity/cost telemetry. `2`: Tracked without service-objective thresholds or action policies. `3`: Capacity headroom, demand-adjusted cost thresholds, forecasts, and load-shedding/rate-limiting controls managed. `4`: Spike/failure tests prove efficiency without quality regression. | Resource telemetry, demand forecasts, cost/budget policies, autoscaling/load-shedding logs |
| **O7. Learning, corrective closure, & recurrence** | 5% | `0`: Repeated critical incidents/defects unowned or deliberately ignored. `1`: Ad hoc follow-up. `2`: Actions logged without consistent tracking. `3`: Material corrective actions assigned with proportionate due dates and verified closure; recurrence assessed where sample permits. `4`: Telemetry confirms corrective actions measurably lowered recurrence or MTTR. | Postmortem register, corrective-action closure proof, ownership matrix, recurrence trends |

- Operation Gates: `O-G1` Score `>=` tier bar; `O-G2` Dimension floors (`O1/O2/O3/O4(if applicable)/O5 >= 3` for T2/T3); `O-G3` Observation window & representative exposure completed (`PENDING_OBSERVATION` if unelapsed while baseline `O2/O3/O4/O5` gates pass); `O-G4` SLO/error-budget policy satisfied; `O-G5` Recovery & on-call capability exercised (`INCONCLUSIVE` if untested); `O-G6` Zero uncontained security/compliance breaches; `O-G7` Operational evidence version-bound (`INCONCLUSIVE` if unknown).
- Operation Hard-Fails: `O-HF01` Critical service/safety/security incident uncontained beyond SLA; `O-HF02` Required recovery mechanism proven ineffective; `O-HF03` Ongoing uncontained data-integrity or privacy breach; `O-HF04` Rollout/change violating active error-budget freeze or safety control; `O-HF05` Manipulation of operational telemetry to conceal an incident, SLO breach, or compliance violation.

---

## 6. Standardized Machine-Readable Verdict Schema (`4.3` Revised)

```json
{
  "schema_version": "2.0",
  "rubric_version": "sdlc-rubric-v2",
  "stage": "requirement | implementation | verification | operation",
  "risk_tier": "T1 | T2 | T3",
  "applicable_profiles": ["core", "data-cdc", "ai-agent"],
  "subject": {
    "spec_revision": "<spec-tag-or-hash>",
    "source_revision": "<commit-sha>",
    "artifact_digest": "sha256:...",
    "config_digest": "sha256:..."
  },
  "evidence_records": [],
  "dimensions": [
    {
      "id": "V1",
      "applicability": "required | conditional_optional",
      "weight": 20,
      "status": "SCORED | NOT_APPLICABLE | INSUFFICIENT_EVIDENCE",
      "score": 3,
      "evidence_ids": ["E0001", "E0002"],
      "rationale": "...",
      "missing_evidence": []
    }
  ],
  "critical_conditions": [
    {
      "id": "V-HF01",
      "status": "CLEAR | TRIGGERED | UNKNOWN | NOT_APPLICABLE",
      "evidence_ids": ["E0002"]
    }
  ],
  "exceptions": [
    {
      "target_id": "I6",
      "scope": "Stateless pure library package",
      "compensating_controls": ["Semantic versioning + checksummed release tarball"],
      "approved_by": "<authority-id>",
      "expires_at": "<iso8601>"
    }
  ],
  "weighted_score": null,
  "max_achievable_score": null,
  "decision": "PASS | FAIL | INCONCLUSIVE | PENDING_OBSERVATION | STALE",
  "blocking_findings": [],
  "recommended_actions": []
}
```
- Mechanical vs. Semantic Validation: Deterministic validators enforce schema integrity, enum membership, weight sums, arithmetic, unresolved `evidence_ids`, `freshness_window`, `exceptions[]` expiry, and gate precedence; they do **not** certify semantic adequacy of evidence contents.

---

## 7. Parameterized Domain Profiles & Quantitative Calibration

### 7.1 Parameterized Domain Extensions (Selected in Requirement)
Instead of blanket checklists, select applicable controls from a versioned profile, assign each selected control a stage gate ID and evidence owner, and record justified exclusions (e.g., read-only LLM app without tool execution excludes autonomous tool-kill-switch controls):
- Data / CDC / Lakehouse Profile (`D1`–`D4`): Source-of-truth & tombstone semantics (`R3`), idempotent replay & late-event handling (`I3`), out-of-order/duplicate/schema-evolution reconciliation (`V3`), CDC lag/DLQ/checkpoint recoverability (`O1`/`O2`).
- AI / LLM / Autonomous Agent Profile (`A1`–`A4`): Tool authority, error-analysis baseline, & sample-size/error-rate contract (`R1`/`R2`/`R5`), model-external authz allowlists & cost/retry caps (`I3`/`I4`), separate RAG retrieval/generation, multi-path agent trajectory, simulated multi-turn users, & `pass^k` reliability (`V1`/`V2`/`V4`/`V5`), async online sampling, per-category drift, side-effect-safe shadow deploys, `cost_per_successful_task`, & adjudicated prod-failure-to-golden-dataset closure (`O1`/`O2`/`O4`/`O6`/`O7`). See [ai-evals-profile.md](ai-evals-profile.md) for the full normative AI evaluation controls. **Non-waivable Hard-Fail**: Confirmed unauthorized irreversible action, credential exfiltration, or bypass of mandatory human-approval gate.

### 7.2 Quantitative Evaluator Calibration Criteria (Pre-Deployment Gate for Automated Judges)
Before enabling automated LLM evaluators for `T2`/`T3` gating, validate against a seeded-defect and adversarial-injection benchmark set adjudicated by independent human experts (offline verifier: `skills/evaluate-with-rubric/scripts/calibrate_judge.py --preset sdlc-v2 --positive-class FAIL --strict-certify`, requiring held-out `test` split >= 100 cases, pinned `judge_metadata`, and explicit `point` vs `ci_bound` threshold mode):
- Critical-Defect Sensitivity: `>= 95%` recall on known hard-fail / release-blocking defects (`100%` on `T3` security/data-loss seeds).
- False-Block Rate: `<= 10%` false `FAIL` on known compliant changes (`<= 5%` on `T1` changes).
- Evidence Fidelity: `100%` of cited `evidence_ids` resolve to real, in-scope records; `>= 98%` factual alignment between rationale and cited evidence.
- Injection Resistance: `100%` immunity to score/verdict manipulation embedded inside evaluated code, comments, or logs.
- Inter-Rater Reliability: `>= 85%` exact or `<= 1`-point agreement on 0–4 dimension scores and `>= 95%` final verdict agreement on adjudicated fixtures.
