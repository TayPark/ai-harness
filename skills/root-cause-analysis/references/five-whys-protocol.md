# Evidence-Bound 5 Whys Protocol Across SDLC Stages

Use this reference when applying `root-cause-analysis` across software engineering (SWE) and forward-deployed / systems-integration (FDE/SI) lifecycles.

## 1. Stage-by-Stage 5 Whys Application Matrix

| SDLC Stage | Typical Trigger | Core 5 Whys Question Chain | Primary Evidence Sources | Handoff Target |
| --- | --- | --- | --- | --- |
| **1. Analyze** | Stakeholder asks for a surface feature ("build a chatbot/dashboard") without clear bottleneck evidence | Why is this tool requested? -> Why is the current workflow slow or error-prone? -> Why are operators using manual spreadsheets or chat workarounds? | Stakeholder interviews, read-only schema/log inspection, current SOPs | `interview-for-requirements` |
| **2. Design** | Contested boundary, legacy coupling, or repeated architecture rework | Why must component A call legacy system B directly? -> Why does no domain contract or idempotency key exist? -> Why is write authority unbounded? | Existing APIs, authz matrices, ADRs, latency/cost constraints | `sdd-01-plan-repository-implementation` (or `debate-models` if two valid designs compete) |
| **3. Implement** | Recurring bug, flaky pipeline transform, or data duplication | Why did duplicates appear in target table X? -> Why did replay re-insert rows? -> Why did the upstream source lack a stable primary/tombstone key? | Sample data profiles, unit/integration logs, git blame/diff | `sdd-03-execute-implementation-plan` |
| **4. Verify** | Acceptance test fails, AI eval drops, or reconciliation mismatches | Why did the agent or pipeline fail on slice Y? -> Retrieval miss, ontology/schema mismatch, prompt flaw, or corrupted source fixture? | Execution traces, open-to-axial failure coding, reconciliation diffs | `sdd-04-verify-implementation-independently` (triggers upstream `STALE` if spec/design defect) |
| **5. Operate** | Production outage, SLA breach, drift alert, or failed customer handover | Why did the outage last 45 minutes? -> Why did alerts fire late? -> Why could the on-call or client admin not recover from the runbook alone? | Telemetry, incident timelines, alert logs, game-day / shadowing notes | `sdd-06-operate-and-handover` |

## 2. Branching Causal Tree Pattern

Real engineering failures rarely have a single linear cause. Split branches whenever two independent conditions were required for the symptom to occur:

```text
Symptom: Downstream analytics and agent answers showed stale inventory for 6 hours.
├── W1a [OBSERVED_FACT]: Nightly sync job exited 0 while writing 0 rows (job_log#L142).
│   ├── W2a [OBSERVED_FACT]: Upstream ERP renamed column `qty_avail` to `avail_qty` (schema_diff).
│   └── W3a [OBSERVED_FACT]: Transform caught KeyError and returned empty batch instead of failing closed (transform.py:88).
└── W1b [OBSERVED_FACT]: On-call received no alert during the 6-hour window (alert_history).
    └── W2b [OBSERVED_FACT]: Monitoring checked process exit code only, with no row-count or freshness floor (alerts.yaml:24).
```

Both branches (`W3a` silent exception swallowing and `W2b` missing freshness/volume alert) are verified root causes requiring separate fixes.

## 3. Anti-Patterns to Reject

- Symptom-level patching: fixing `W1` (restarting the job or tweaking one prompt sentence) without addressing `W3a` and `W2b`.
- Unverified speculation chains: writing five plausible-sounding "whys" without checking a single file, log, or query. Mark unverified links `HYPOTHESIS` and stop the branch until checked.
- Human-blame termination: ending at "developer missed the edge case" instead of identifying the missing schema contract, automated check, or review gate.
- Single-cause tunnel vision: forcing a linear 5-step chain when both a code defect and an observability gap contributed.

## 4. Countermeasure Verification Checklist

Before closing a root-cause report, confirm:

1. Every terminal root cause maps to at least one **Systemic Fix** and one **Detective Control** (test, schema check, or alert).
2. If the incident occurred in production, the failing case is scheduled for sanitized addition to the regression suite or golden dataset (`sdd-06-operate-and-handover`).
3. Any finding that invalidates an upstream requirement or architecture assumption is flagged to mark downstream verification artifacts `STALE`.
