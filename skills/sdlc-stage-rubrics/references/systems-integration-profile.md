# Systems Integration, Domain Modeling & Enterprise Environment Profile (`S1`–`S4`)

Apply this conditional profile alongside [sdlc-rubrics-v2.md](sdlc-rubrics-v2.md) whenever the evaluated system integrates with external or legacy enterprise systems (ERP, CRM, RDB, SaaS APIs, or UI-only legacy apps), models a shared domain or ontology layer, or deploys into constrained customer/enterprise environments (VPC, air-gapped, or strict RBAC). Applies equally to internal SWE integrations and forward-deployed (FDE/SI) engagements.

## Stage Mapping (`S1`–`S4`)

| Control | SDLC Stage & Dimensions | Mandatory Observable Evidence |
| --- | --- | --- |
| **S1. Domain/Ontology Model & Trust Boundaries** | Requirement (`R2`, `R3`, `R4`, `R5`) | Explicit domain or ontology contract (Objects, Properties, Links, Actions), external system dependency matrix, RBAC/SSO and data-classification boundaries, write-back authority rules, and environment constraints (network egress/ingress, VPC/air-gapped requirements if applicable). |
| **S2. Resilient Connectors & Safe Write-Back** | Implementation (`I2`, `I3`, `I4`, `I6`) | Bounded timeouts, retry budgets, rate-limit handling, and circuit breakers on external calls; explicit mapping layer isolating legacy schemas from core domain models; model-external authorization and human-approval gates for mutating write-backs; strict safety fences for UI-automation or computer-use integrations where APIs do not exist. |
| **S3. Contract, Authz & Non-Destructive Verification** | Verification (`V2`, `V4`, `V6`, `V7`) | Contract/integration tests against realistic fixtures or isolated staging environments, least-privilege and cross-tenant authorization tests, verified rollback or compensating-transaction rehearsal for write-back actions, and config/secret parity checks. |
| **S4. Connector Health, Drift & Governance Ops** | Operation (`O2`, `O3`, `O4`, `O5`) | Monitoring for connector failures, auth-token/certificate expiry, and upstream API deprecation; runbooks for external dependency degradation; periodic RBAC/permission and configuration drift audits; documented credential rotation procedures. |

## Conditional Forward-Deployed / Air-Gapped Overlay

Enable these additional controls when deploying into an external customer or network-restricted environment (record as `NOT_APPLICABLE` in `exceptions[]` for standard self-hosted cloud services):

1. **Deployment Preflight (`R4`, `I6`)**: verify OS/runtime/container registry availability, offline package mirrors, firewall/proxy egress rules, and identity-provider (SSO/OIDC/SAML) integration before implementation freezes.
2. **Legacy UI / Computer-Use Guardrails (`I3`, `I4`)**: when an external system lacks an API and requires UI-driven automation, restrict allowed URLs/windows, enforce read-only dry-run verification before live execution, log every action with screenshot/DOM evidence, and require explicit human approval before irreversible submissions.
3. **Multi-Organization Authority (`R5`, `O5`)**: separate business requester, platform administrator, and security/compliance approver roles so no single actor bypasses security review or data-marking rules.

## Non-Waivable Integration Hard-Fails

Confirmed unauthorized or unguarded write-back to a production external/legacy system, credential or sensitive-data leakage across trust boundaries, or violation of mandatory network/air-gapped security controls triggers an immediate non-waivable `FAIL`.
