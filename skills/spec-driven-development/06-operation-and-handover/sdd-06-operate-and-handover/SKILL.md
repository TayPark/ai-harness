---
name: sdd-06-operate-and-handover
description: Run post-launch operational stabilization, 5 Whys incident closure, and structured internal team or external client handover after Release Readiness PASS and deployment. Use when closing a production observation window, transferring ownership to on-call or client teams, or formalizing roll-off sign-off.
---

# Post-Launch Operation & Handover

Stabilize a deployed release against operational targets (`O1`–`O7` in `sdlc-stage-rubrics`), close incidents through evidence-bound 5 Whys feedback loops, and transfer ongoing ownership to an internal operations team or external client organization without platform decay.

## Authority and Boundaries

- Post-deployment only: run this skill after `sdd-05-assess-release-readiness` returns `PASS` and deployment completes. Do not use it as a substitute for pre-publication release checks.
- Loose coupling with `sdd-02` schemas: this stage consumes the frozen candidate digest and `sdd-05` release report as read-only inputs and writes a standalone operation and handover record; it does not modify `sdd-02` workflow-record JSON schemas.
- No silent ownership transfer: never declare handover complete while critical roles remain `unassigned`, alerts are unrouted, or receiving owners have not executed a live or simulated recovery drill.

## 1. Post-Launch Observation & Stabilization (`O1`–`O7`)

1. Bind the record to the deployed candidate digest, deployment timestamp, risk tier (`T1`/`T2`/`T3`), and active domain profiles (`core`, `data-cdc`, `systems-integration`, `ai-agent`).
2. Track the required observation window (`max(min_time_window, min_representative_cycles)`). While elapsed exposure is incomplete and baseline controls (`O2`–`O5`) pass, keep status as `PENDING_OBSERVATION`.
3. Verify live operational signals:
   - Core (`O1`–`O6`): SLO/error-budget burn, alert delivery latency, config-drift detection, backup/rollback health, vulnerability SLA, and capacity/cost headroom.
   - Data (`D4`, if applicable): freshness, volume anomalies, CDC lag, and DLQ/checkpoint recovery readiness.
   - Systems Integration (`S4`, if applicable): connector health, credential/certificate expiry alerts, and external dependency fallback behavior.
   - AI / Agent (`A4`, if applicable): async online quality sampling, per-category drift alerts, `cost_per_successful_task`, and `p50`/`p95` latency.

## 2. Incident Closure & 5 Whys Feedback Loop (`O7`)

For every Sev-1/Sev-2 incident, SLO freeze, or recurring operational failure during stabilization:

1. Invoke `root-cause-analysis` (evidence-bound 5 Whys) to identify systemic causes across code, data contracts, observability, or runbooks.
2. Convert each verified failure into three artifacts before closing the action item:
   - Systemic Fix (with owner and due date),
   - Detective Control (alert rule or automated check catching recurrence),
   - Regression / Golden Test Case (sanitized failure fixture added to CI or evaluation datasets with `incident_id`).

## 3. Structured Team or Client Handover

Assign explicit, named owners across four operational responsibilities (one team may hold multiple roles in smaller internal services; record `unassigned` if missing and block roll-off):

| Operational Role | Core Ownership Scope | Required Handover Evidence |
| --- | --- | --- |
| **Data / Pipeline Owner** | Source connectors, sync health, transforms, schema drift, backfill | Clean data lineage map, reconciliation queries, DLQ/backfill runbook |
| **Application / Domain Owner** | Business logic, domain/ontology objects and actions, agent workflows | Architecture and domain/ontology docs, eval suite execution guide |
| **Platform / Security Admin** | RBAC, SSO, data markings, secret rotation, audit logs, quotas | Verified access matrix, secret-rotation schedule, security audit sign-off |
| **Business / Service Owner** | Budget, SLA/exception approval, future use-case prioritization | Agreed SLO/cost thresholds, escalation path, backlog ownership |

### Shadowing → Reverse-Shadowing Protocol

1. **Documentation & Lineage Audit**: confirm architecture diagrams, data lineage, runbooks, and alert escalation paths match the live deployed state (zero stale references).
2. **Shadowing**: receiving owners observe builders executing routine updates, alert triage, and incident/rollback procedures.
3. **Reverse-Shadowing**: receiving owners independently execute at least one controlled configuration or pipeline change and one non-destructive recovery/rollback game-day drill while builders coach without taking over keyboard control.
4. **Access & Governance Cutover**: revoke temporary builder privileges where policy requires, confirm client/ops admin controls work independently, and record explicit sign-off from receiving owners.

## 4. Roll-Off Sign-Off & Output Contract

Emit an `operation-and-handover-record.md` containing:

1. **Deployment Provenance**: candidate digest, release report ref, risk tier, active profiles, observation window status (`PENDING_OBSERVATION | PASS | FAIL`).
2. **Operational Readiness Summary (`O1`–`O7`)**: observed metrics, alert/drift checks, and open corrective actions.
3. **5 Whys Postmortem & Feedback Closure Log**: linked incidents, root causes, and regression/golden-dataset additions.
4. **Handover & Reverse-Shadowing Matrix**: named owners per role, completed drills, revoked temporary access, and explicit receiving-owner sign-off (`PENDING | SIGNED_OFF`).
