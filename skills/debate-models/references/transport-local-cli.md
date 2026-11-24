# Local CLI & Subagent Transport Adapter (`codex`, `gemini`, Isolated Subagents)

Use this transport when local API or CLI token budget is ample, when non-interactive automation is preferred, or when browser access via Aside is unavailable or unnecessary.

## Supported Local Backends

| Backend | Typical command / mechanism | Best fit |
| --- | --- | --- |
| Codex CLI | `codex exec ...` (inspect `codex --help` / `codex exec --help` for exact flags in your installed version) | Cross-family OpenAI peer in `debate-models` (`local-pair` or `hybrid-pair`) |
| Gemini CLI | `gemini -p ...` (inspect `gemini --help` for exact model/output flags in your installed version) | Cross-family Gemini peer in `debate-models` (`local-pair` or `hybrid-pair`) |
| Isolated Subagent | Host subagent tool with fresh context and read-only scope | Only when explicitly approved by the user; never silently substitute for a requested cross-family peer |

## Setup & Invocation Rules

1. Verify binary availability and exact flags (`command -v codex`, `command -v gemini`, `--help`) before invoking. Never guess or hardcode deprecated CLI flags.
2. Model and effort fidelity: pass the user-requested model and reasoning/thinking flags explicitly when supported by the installed CLI. If a requested model or effort flag is unavailable or fails, report the error and stop without silent downgrade.
3. Read-only / isolation discipline:
   - For `consult`, `debate`, and `evaluate`, run CLIs in read-only or non-mutating mode (for example `codex exec --sandbox read-only` or equivalent) so reviewed content cannot modify workspace files.
   - Pass prompts via stdin or a temporary prompt file outside the target directory to preserve exact line breaks and avoid shell escaping corruption.
4. Multi-round state in `debate` mode:
   - Either resume the same CLI session/thread per peer across Rounds 1-3, or pass a self-contained canonical packet (Round 1 summary + canonical claim log + fenced peer rebuttal) on each fresh invocation. Record which session strategy was used in debate metadata.
5. Output capture and budgeting:
   - Capture stdout, stderr, and exit code cleanly.
   - Keep `debate` Round 1 outputs bounded (`<1,800` words) and `evaluate` outputs strictly raw JSON (strip nothing silently; fail validation if malformed).
   - Enforce a bounded timeout per call; on timeout or non-zero exit, capture partial output and stderr. Allow at most 1 bounded transport retry per round per model. If still blocked, report the exact failure (or `BLOCKED_PARTIAL` in `debate` mode).

## Limits

- Running local CLIs consumes the user's configured CLI/API quota or billing. Do not infer or guarantee cost outcomes.
- Cross-family diversity in `debate` mode requires two distinct model families (for example `codex` + `gemini`). If only one family is available locally, inform the user before proceeding or pair one local CLI with one `web-aside` peer.
