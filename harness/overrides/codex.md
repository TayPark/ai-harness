# Host Override: Codex

- Patch-First Discipline: Prefer `apply_patch` for edits and verify `git diff --name-only` against `write_scope` before applying or integrating worker patches.
- Read-Only Role Caution: When acting as `reviewer` or `scout`, avoid shell commands that mutate tracked or untracked files (build caches, formatters, auto-fixers).
- Lossless Context Offloading: Offload bulk reads and logs via subagents (`CONTRACTS.md` / `scout`), `context-mode` MCP (`ctx_execute`/`ctx_search`), or `headroom` MCP (`headroom_read`/`headroom_compress`/`headroom_retrieve`).
- Default Skills: Apply `{{HOME}}/.codex/skills/caveman/SKILL.md` (conversational prose only), `{{HOME}}/.codex/skills/ponytail/SKILL.md`, and `{{HOME}}/.codex/skills/anti-slop/SKILL.md` when present.
