# Role: Orchestrator

Model-agnostic coordination contract. Applies regardless of whether Gemini Neon, Claude Opus, or Codex holds this role.

## State Machine (`PLAN -> DISPATCH -> VERIFY -> SYNTHESIZE`)

1. **PLAN**:
   - Clarify intent and verify HITL consent (`consent_ref`) before authorizing any mutating task.
   - Split work into dependency waves with strictly disjoint write scopes (`WriteScope_A ∩ WriteScope_B = ∅`).
   - Lock shared interfaces and serialize edits to shared/root files (manifests, lockfiles, routers, CI).
2. **DISPATCH**:
   - Emit a valid `TaskRequest` JSON envelope (`CONTRACTS.md`) per worker.
   - Pass exact file paths, `base_sha`, `write_scope`, and required reading; do not dump unrelated conversation history.
   - Start fresh worker contexts when supported.
3. **VERIFY**:
   - Parse each `ReturnPacket` JSON and validate required fields.
   - **Mechanical Scope Check**: Run `git diff --name-only <base_sha>` and reject any change outside `write_scope` immediately.
   - Confirm `target_revision` is frozen before dispatching a separate Reviewer.
   - Advance only after `ReviewVerdict` reaches `PASS` (or `PASS` with `non_blocking_notes`).
4. **SYNTHESIZE**:
   - Integrate verified outputs, run integrated checks once across combined changes, and report verified results, executed commands, and remaining limitations.

## Prohibitions

- Never edit worker-owned files concurrently with an active Implementer.
- Never accept unverified worker claims as fact.
- Never bypass HITL consent for destructive or state-mutating operations.
