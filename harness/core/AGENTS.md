# Core Working Preferences

Global defaults subordinate to system/developer instructions, explicit user requests, and repository-local `AGENTS.md`.

## Precedence Order

1. System and developer instructions
2. Explicit user request in the current session
3. Project-local `AGENTS.md` (or `GEMINI.md` / `CLAUDE.md`)
4. Shared harness `core/` rules
5. Activated skills

## Execution and Evidence

- Finish: Execute authorized tasks through verification and delivery; a plan or offer alone is incomplete. Resolve routine gaps from context and ask only when missing information materially changes correctness, scope, or consent.
- Evidence-First: Back design, API, version, or behavior claims with (a) a just-executed command and its observed output, or (b) an official documentation URL and verification date. Mark unverified claims explicitly as `미확인` or `확인 필요`.
- Minimal Diff: Keep changes scoped to the active requirement. Delete obsolete code paths when behavior changes; do not add compatibility shims, `_v2` duplicates, or speculative abstractions.
- Verify: Run checks covering changed behavior and report executed commands separately from assumptions.

## Surgical Data Access (Minimal Read)

Read only the slice of data needed unless full contents are required for correctness:

- Files and logs: Use `rg`, `grep`, `sed -n`, `head`, `tail`, or bounded line ranges instead of dumping whole files with `cat`.
- SQL and databases: Always specify explicit column names (`SELECT col1, col2`, never `SELECT *`), include `WHERE` predicates, and apply `LIMIT` bounds during exploration and verification.
- Git diffs: Inspect `git diff --stat` and `git diff --name-only` before reading targeted hunks.

## Style and Context Boundaries

- Apply terse conversational style (`caveman`) for routine dialogue only when active, while preserving exact code, paths, numbers, and negations.
- Automatically disable `caveman` for structured JSON envelopes (`CONTRACTS.md`), formal reports, and `RESPONSE.md` tables so required structure is never stripped.
- Apply `anti-slop` standards to prose and `ponytail` discipline to code changes.

## Multi-Agent Entry Pointer

For single-file, low-risk, authorized tasks, execute directly without multi-agent overhead. When delegating or orchestrating multiple roles, load the on-demand role and protocol files from `{{HOST_ROLES_DIR}}/`:

- Protocol and JSON envelopes: `{{HOST_ROLES_DIR}}/CONTRACTS.md`
- HITL gates and empirical routing: `{{HOST_ROLES_DIR}}/ROUTING.md`
- Role contracts: `orchestrator.md`, `implementer.md`, `reviewer.md`, `scout.md`
