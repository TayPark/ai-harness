# HITL-First Routing and Benchmark Policy

## Human-in-the-Loop (HITL) Decision Gates

Multi-agent execution centers on 4 explicit human gates rather than open-ended autonomy:

1. **Plan and Consent Gate**: Human approves scope, `write_scope` boundaries, and any state-mutating or destructive operations.
2. **Execution Checkpoint Gate**: Orchestrator verifies `git diff --name-only <base_sha>` against `write_scope` and confirms targeted tests pass before freezing a candidate revision.
3. **Independent Review Gate**: A separate Reviewer model inspects the frozen revision read-only and returns `ReviewVerdict`.
4. **Mutation / Release Gate**: Human explicitly approves remote pushes, merges, deployments, or external data mutations.

## Empirical Model-to-Role Selection

Treat model-to-role assignments as provisional defaults and adjust them using measured HITL performance rather than speculation.

| Role | Provisional Default Pool | Selection Metric |
| --- | --- | --- |
| Orchestrator | Gemini Neon / Claude Opus / Codex | Plan clarity, low HITL rework turns, strict gate adherence |
| Implementer | Gemini 4 Hydrogen / Claude Haiku | `write_scope` compliance, first-pass test rate, minimal diff |
| Reviewer | Claude Opus / Gemini Neon / Codex | P0/P1 defect catch rate, low false-positive `FAIL` noise |
| Scout | Gemini 4 Hydrogen / Claude Haiku | Surgical read efficiency, zero fabricated paths |

- **Model Floor**: Never downgrade subagents to Gemini 3.8 Flash.

## Local Benchmark Log Schema

Record empirical multi-agent observations outside the repository at `~/.local/state/ai-harness/benchmarks.jsonl` (one JSON object per line):

```json
{
  "ts": "2026-11-27T14:30:00+09:00",
  "role": "orchestrator | implementer | reviewer | scout",
  "model": "model-identifier",
  "host": "antigravity | claude | codex",
  "task_type": "plan | implement | review | explore",
  "hitl_turns": 1,
  "schema_valid": true,
  "scope_violations": 0,
  "defects_caught": 2,
  "verdict_agreed": true,
  "latency_s": 18.4
}
```
