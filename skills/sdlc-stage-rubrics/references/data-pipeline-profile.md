# Data Pipeline, CDC & Lakehouse Profile (`D1`–`D4`)

Apply this conditional profile alongside [sdlc-rubrics-v2.md](sdlc-rubrics-v2.md) whenever the evaluated system ingests, transforms, reconciles, or serves batch, streaming, or CDC data pipelines (including analytics lakehouses, operational data syncs, and ontology/AI context feeds). Exclude these controls for pure stateless software with no persistent data pipeline.

## Stage Mapping (`D1`–`D4`)

| Control | SDLC Stage & Dimensions | Mandatory Observable Evidence |
| --- | --- | --- |
| **D1. Data Contracts, Grain & Lifecycle** | Requirement (`R1`, `R2`, `R3`, `R5`) | Named source-of-truth systems, table/entity grain, primary and idempotency keys, tombstone/soft-delete semantics, schema-evolution policy (breaking vs additive), freshness/completeness SLOs, and PII/retention classification. |
| **D2. Idempotent Transforms, Backfill & Lineage** | Implementation (`I1`, `I3`, `I5`, `I6`) | Idempotent write/upsert logic, deterministic replay and backfill scripts, late-arriving and out-of-order event handling, dead-letter queue (DLQ) or quarantine path for malformed rows, and documented end-to-end data lineage. |
| **D3. Reconciliation & Schema-Drift Verification** | Verification (`V1`, `V2`, `V3`, `V6`) | Source-to-target reconciliation report (row counts, key uniqueness, aggregate checksums, business invariants), schema-drift regression tests, duplicate/out-of-order/null fault-injection checks, and staging config/migration parity against production. |
| **D4. Freshness, Lag & Recovery Operations** | Operation (`O1`, `O2`, `O3`, `O4`, `O7`) | Automated freshness, volume-anomaly, and CDC-lag alerts (not exit-code-only checks), tested DLQ replay and checkpoint restoration drills, upstream schema-change runbooks, and 5 Whys postmortem closure adding failed payloads to regression fixtures. |

## Mandatory Pipeline Controls & Verification Checks (`D2`–`D3`)

Select applicable pipeline checks in Requirement and record justified exclusions in `exceptions[]`:

1. **Source-to-Target Reconciliation (`V3`)**:
   - Compare source and target across row count, distinct primary keys, null rates on mandatory columns, and numeric control totals (for example, sum of amounts or quantities) within declared tolerance.
2. **Idempotency & Replay Safety (`I3`, `V2`)**:
   - Re-run the same batch or event window at least twice and verify zero duplicate records and unchanged control totals.
3. **Schema-Drift & Malformed-Payload Handling (`I3`, `V3`)**:
   - Inject missing columns, renamed fields, type widening/narrowing, and malformed rows; verify the pipeline either quarantines records into a DLQ or fails closed with an actionable alert rather than silently emitting empty or corrupted outputs.
4. **Lineage & Downstream Impact Traceability (`I2`, `O3`)**:
   - Map each output table, feature, or ontology object back to upstream sources and transforms so operators can trace blast radius when an upstream schema or sync breaks.

## Non-Waivable Data Hard-Fails

Confirmed silent data loss or truncation, unquarantined schema corruption propagating into downstream operational or AI decision tables, or a non-idempotent backfill duplicating regulated/financial records triggers an immediate non-waivable `FAIL`.
