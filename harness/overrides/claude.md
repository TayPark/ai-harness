# Host Override: Claude Code

- Subagent Granularity: Delegate at most 1 bounded step per subagent; pass only that step's input paths, output contract, and verification command (do not pass internal implementation details of other steps).
- Compaction Continuity: After compaction or session resume, treat the injected plan artifact on disk as authoritative over recalled decisions.
- Model Tuning: Keep Opus responses concise and bound `FAIL` verdicts strictly to P0/P1 defects; enforce strict `write_scope` boundaries when delegating to Haiku.
- Lossless Context Offloading: Offload bulk reads and logs via subagents (`CONTRACTS.md` / `scout`), `context-mode` MCP (`ctx_execute`/`ctx_search`), or `headroom` MCP (`headroom_read`/`headroom_compress`/`headroom_retrieve`).
- Default Skills: Apply `{{HOME}}/.claude/skills/caveman/SKILL.md` (conversational prose only), `{{HOME}}/.claude/skills/ponytail/SKILL.md`, and `{{HOME}}/.claude/skills/anti-slop/SKILL.md` when present.
