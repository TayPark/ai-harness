# Discovery Protocol (Frontier Ordering & Hidden-Context Probes)

Load this reference before Round 1 whenever the request involves branching decisions, multiple stakeholders, or an existing system whose constraints the requester may not know.

## 1. Read-Only Pre-Probe (Facts Before Questions)

Before asking the requester anything, inspect accessible code, schemas, APIs, tests, and docs read-only:

- Extract existing contracts, auth/permission boundaries, data formats, rate/size limits, and error patterns as `OBSERVED_FACT` items with exact source path and symbol.
- Remove any question answerable from observed facts. Replace it with a short confirmation only if the observed behavior might need to change.
- Surface facts the requester likely does not know (for example, an existing middleware limit or PII column) when they create a real product trade-off.

## 2. Conditional Frontier Ordering

Use a lightweight dependency ordering when one answer changes downstream questions:

1. **Goal & Success**: What problem is being solved, for whom, and how is Slice 1 verified?
2. **Scope & Boundary**: What must be in Slice 1 vs. Later Slices vs. Non-Goals?
3. **Policy & Authority**: Security, permissions, data handling, external contracts, and who owns approval.
4. **Exceptions & Edge Cases**: Failure modes, empty/max bounds, concurrency, and rollback expectations.

Rules:
- Ask only questions whose prerequisites are settled. Defer dependent follow-ups to the next round.
- Ask at most 4 questions per round (default 2-4; ask 1 when only one blocking question is on the Frontier).
- Stop as soon as Slice 1 completion criteria are met, or at round 3 (max 5 for high complexity).

## 3. Reversibility-Based Framing

| Decision Risk | Framing Rule |
| --- | --- |
| Reversible, low-risk (formatting, pagination default, naming) | State a concrete `PROPOSED_DEFAULT` and note when it can be overridden. |
| Irreversible or high-risk (auth, PII/security, data deletion, billing, external API contract) | Present 2-3 neutral options with explicit trade-offs and downstream impact. Never phrase the question so `"yes"` rubber-stamps an agent recommendation. Confirm Owner authority before marking `CONFIRMED`. |

## 4. Universal Hidden-Context Probe Checklist

Check these areas read-only or during elicitation when relevant to the domain:

- Permissions and authority: who may trigger the action, who approves policy exceptions, and what fails closed?
- Tacit workflows and shadow processes: what manual workarounds (spreadsheets, chat approvals, ad hoc scripts) do operators currently rely on that are absent from official docs?
- Stakeholder conflict boundaries: where do business operators, IT/platform owners, and security/compliance teams hold competing priorities, and who owns the tie-breaking decision?
- Data integrity and lifecycle: idempotency, partial failure, retention or deletion, and migration compatibility.
- Scale and bounds: zero-item, single-item, and upper-bound limits; timeouts and backpressure.
- External interfaces and observability: backward compatibility for callers, error contract, and audit or log redaction.
