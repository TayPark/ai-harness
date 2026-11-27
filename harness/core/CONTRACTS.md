# Inter-Agent Communication Protocol and Contracts

## Transport Protocol (2-Layer File-Backed + IPC Pointer)

Cross-host multi-agent runs (Antigravity, Claude Code, Codex) use a **2-layer file-backed JSON protocol** rather than raw Unix/TCP sockets, so handoffs survive context compaction, work across heterogeneous sandboxes, and remain auditable for Human-in-the-Loop (HITL) review.

1. **Control Plane (Atomic JSON Envelope `<=4 KB`)**:
   - Format: Single UTF-8 JSON object with `"schema_version": "1.0"`, written atomically (`mktemp` + `os.replace`) to `.work/handoffs/<run_id>/<task_id>.<type>.json`.
   - Inline return: Wrap the exact JSON object in a typed fence (` ```json:ReturnPacket `, ` ```json:ReviewVerdict `, ` ```json:EscalationPacket `) with no surrounding prose that breaks extraction.
   - Host-native IPC (optional): When a host provides native messaging (Antigravity `send_message` / `swarm`, Claude Agent Teams, Orca), transmit only the compact pointer `{"task_id", "type", "status", "artifact_path", "sha256"}` while keeping the atomic JSON file as the immutable record.
2. **Data Plane (Offloaded Artifacts for `>2 KB` Payloads)**:
   - Never inline large diffs, test logs, or search dumps into JSON or chat.
   - Write large output to `.work/handoffs/<run_id>/artifacts/<task_id>.<ext>` and reference it via `{"path", "sha256", "line_count", "excerpt"}` where `excerpt` is at most 10 lines.

## Standard JSON Envelopes

### `TaskRequest` (Orchestrator -> Worker)

```json
{
  "schema_version": "1.0",
  "task_id": "T-01",
  "role": "implementer | reviewer | scout",
  "base_sha": "git-commit-sha",
  "consent_ref": "user-request-or-approved-plan-id",
  "objective": "Single bounded objective",
  "write_scope": ["path/to/allowed_file.py"],
  "inputs": [],
  "constraints": [],
  "required_reading": [],
  "verification_commands": []
}
```

### `ReturnPacket` (Implementer / Scout -> Orchestrator)

```json
{
  "schema_version": "1.0",
  "task_id": "T-01",
  "role": "implementer",
  "model_used": "model-identifier",
  "status": "complete | incomplete | blocked",
  "target_revision": "wip-commit-sha-or-git-write-tree-hash",
  "summary": "Concise factual summary",
  "changed_files": [],
  "evidence": ["command -> observed output"],
  "artifacts": [],
  "assumptions": [],
  "limitations": [],
  "open_questions": []
}
```

### `ReviewVerdict` (Reviewer -> Orchestrator)

```json
{
  "schema_version": "1.0",
  "task_id": "T-01",
  "target_revision": "frozen-commit-or-tree-hash",
  "reviewer_model": "model-identifier",
  "verdict": "PASS | FAIL | INCONCLUSIVE | BLOCKED",
  "critical_findings": [],
  "non_blocking_notes": [],
  "checks_run": []
}
```

### `EscalationPacket` (Worker -> Orchestrator)

```json
{
  "schema_version": "1.0",
  "task_id": "T-01",
  "failure_type": "logic_fail | scope_violation | interface_mismatch | consent_required | env_blocked",
  "attempts_made": 2,
  "uncommitted_state": "preserved | stashed | reverted",
  "error_trace_excerpt": "Max 10 lines",
  "root_cause_hypothesis": "Observed root cause",
  "decision_needed": "Concrete decision required from Orchestrator or HITL"
}
```

## 2-Strike Circuit Breaker

- Logic / Test Failure (`logic_fail`): Counts toward strikes.
  - Strike 1: Allow at most 1 corrective retry strictly inside `write_scope` with a root-cause change in strategy.
  - Strike 2: Stop immediately, record `uncommitted_state` (`preserved` or `stashed`), and emit `EscalationPacket`. Never reset the counter by spawning a replacement worker.
- External / Consent Blocker (`env_blocked`, `consent_required`): Does not consume a strike. Stop immediately and return `status: "blocked"` or `EscalationPacket` for HITL resolution.
- Scope / Interface Violation (`scope_violation`, `interface_mismatch`): Halt immediately and escalate; do not auto-retry.
