---
name: interview-for-requirements
description: Elicit and structure software requirements through a focused interview before planning. Use when goals, user flows, constraints, or acceptance criteria are unclear; not for tutoring or when clear requirements already exist.
---

# Requirements Interview

Elicit the goal, affected actors, core user flows, functional requirements, constraints, observable acceptance criteria, and unresolved decisions before planning begins.

## Interview Rules

- Ask only questions whose answers materially change architecture, scope, safety, or acceptance criteria. Group related questions into compact turns.
- Continue read-only analysis or independent work that does not depend on a missing answer.
- Separate user-confirmed facts (`CONFIRMED`), proposed defaults (`PROPOSED_DEFAULT`), assumptions (`ASSUMPTION`), and blocking open decisions (`BLOCKING_OPEN_DECISION`). Never present an assumption or example as a confirmed requirement.

## Stopping and Handoff Rules

- **Ready for planning (`COMPLETE_BRIEF`)**: Stop interviewing as soon as every material requirement (goal, actors, core flows, hard constraints, observable completion criteria, and blocking decisions) traces to a user answer or supplied source. Record remaining optional or non-blocking details as labeled `PROPOSED_DEFAULT` items and hand off without asking extra rounds.
- **User unavailable or blocking decision deferred (`PARTIAL_BRIEF`)**: If the user cannot answer blocking questions in the current session, stop asking, set brief status to `PARTIAL_BRIEF (BLOCKED_ON_USER_DECISION)`, list each blocking open decision with its downstream effect, and state which independent read-only planning or repository inspection can proceed while awaiting input.
- Pass the brief to `sdd-01-plan-repository-implementation` and `sdd-02-assess-implementation-spec` as specification input. This interview never substitutes for specification assessment or implementation approval.
- For teaching or practice toward mastery, use upstream [`socratic-tutor`](https://github.com/janestreet/agent_skills/blob/master/socratic-tutor/SKILL.md) instead.

## Requirements Brief Contract

Include these sections in every brief:

1. **Status**: `COMPLETE_BRIEF` or `PARTIAL_BRIEF (BLOCKED_ON_USER_DECISION)`
2. **Goal & Actors** (with source attribution)
3. **Confirmed Requirements & Core Flows** (`R-01..Rn`, each traced to user answer or source)
4. **Constraints & Non-Goals**
5. **Observable Completion Criteria** (`AC-01..ACn`)
6. **Proposed Defaults & Unconfirmed Assumptions** (explicitly labeled)
7. **Blocking Open Decisions & Safe Parallel Work**

## Worked Example (Partial Handoff)

```markdown
### Requirements Brief — CSV Export for Reports
- Status: PARTIAL_BRIEF (BLOCKED_ON_USER_DECISION)
- Goal & Actors: Finance analysts export filtered monthly report rows to CSV (source: user turn 1).
- Confirmed Requirements:
  - R-01 [CONFIRMED, user turn 1]: Export matches active UI date and status filters.
  - R-02 [CONFIRMED, user turn 2]: Reject exports above 100,000 rows with HTTP 413 and guidance.
- Constraints & Non-Goals: Read-only query path; scheduled email delivery is out of scope (user turn 1).
- Observable Completion Criteria:
  - AC-01: Downloaded CSV headers and row counts match the filtered query for 0, 1, and 100,000 rows.
  - AC-02: Requests exceeding 100,000 rows return HTTP 413 without partial file download.
- Proposed Defaults & Assumptions:
  - [PROPOSED_DEFAULT] UTF-8 with RFC 4180 quoting; optional unless finance tools require UTF-8 BOM.
  - [ASSUMPTION] Existing report endpoint authorization middleware applies unchanged.
- Blocking Open Decisions:
  - D-01 [BLOCKING_OPEN_DECISION]: Must PII columns (`email`, `tax_id`) be masked or excluded? Blocks schema contract and security review.
- Safe Parallel Work: Planner may inspect the existing report query service and auth middleware read-only while awaiting D-01.
```
