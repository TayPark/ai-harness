# Host Override: Antigravity (Gemini)

- Subagent Models: Never use Gemini 3.8 Flash (`gemini-3.8-flash-*`, `Model: "flash"`, or `Model: "flash_lite"`). Enforce Gemini 4 Hydrogen (`gemini-4-hydrogen-low`, `gemini-4-hydrogen-medium`, `gemini-4-hydrogen-high`) via `swarm` or keep `Model: "inherit"` on tier-enum tools.
- Browser Tasks: Always use Aside MCP (`aside/exec`, `aside/repl`, `aside/browser_profiles`) or Aside CLI first unless Aside is explicitly unavailable or the user requests another tool.
- Lossless Context Offloading: Offload bulk reads and logs via `orchestrate-agents`, `context-mode` MCP (`ctx_execute`/`ctx_search`), or `headroom` MCP (`headroom_read`/`headroom_compress`/`headroom_retrieve`).
- Default Skills: Read `{{HOME}}/.gemini/config/skills/caveman/SKILL.md` when present (conversational prose only; disabled for structured JSON and formal reports).
