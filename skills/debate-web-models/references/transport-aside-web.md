# Aside CLI Web Transport Adapter (ChatGPT + Web Gemini Neon High)

Use this transport guide when executing `debate-web-models` through Aside CLI against Web ChatGPT (`https://chatgpt.com/`) and Web Gemini (`https://gemini.google.com/`). Keep protocol rules in [SKILL.md](../SKILL.md) independent of UI selectors.

## Phase 1: Session Setup (Persistent Tabs Across Rounds 1–3)

1. Read current Aside REPL instructions with `aside repl --help`, `aside guide repl`, and `aside skills list`. Read `aside skills show google-accounts` if Google account discovery or selection is needed, or any matching built-in Aside skill covering ChatGPT or Web Gemini.
2. REPL Lifecycle & Bounded Polling: Aside REPL enforces a 120-second timeout per tool call while high-reasoning responses can take several minutes. Do not wrap an entire multi-minute debate inside one blocking `try ... finally` call:
   - Store `chatgptPage` and `geminiPage` handles in persistent REPL session bindings (`globalThis.chatgptPage`, `globalThis.geminiPage`) across calls.
   - Keep each polling loop bounded to `<=90` seconds per REPL call, returning control cleanly across calls until both models stabilize.
   - Do not reuse or modify unrelated open browser tabs.
   - On completion or abort, capture any available response text and status before running per-tab `closeTab()` inside independent `try ... catch` blocks so one close failure does not skip closing the other tab; report any cleanup failure.
3. Prepare the Web ChatGPT tab (`chatgptPage`):
   - Open a new tab at `https://chatgpt.com/` with `openTab()`.
   - Read `snapshot(chatgptPage, { interactive: true })` and confirm login. If login is requested, close opened tabs and stop.
   - Start a new chat if not already on one.
   - Inspect both the model picker and reasoning-effort selector in Chat mode and select the combination offering the highest reasoning level currently available. Do not hardcode model names or assume option labels. Stop and report if missing, ambiguous, or unselectable.
   - Confirm the selected model and reasoning option in a fresh snapshot.
4. Prepare the Web Gemini tab (`geminiPage`):
   - Open a new tab at `https://gemini.google.com/` with `openTab()`.
   - Wait for controls to hydrate, read `snapshot(geminiPage, { interactive: true })`, and confirm login. If login is requested, close opened tabs and stop.
   - Start a new chat (`새 채팅` / `New chat`) first if the page did not already open one so new-chat creation cannot reset selected model controls.
   - Ensure Chat mode (`채팅` / `Chat`) is active rather than Task mode (`태스크` / `Tasks`) when both controls are shown, unless the user explicitly requested Tasks.
   - Inspect the mode/model selector in the live UI (`모드 선택 도구` / `Neon` / `사고 수준` / `높음` or English equivalents). Select `Neon` and set thinking level to `High` (`높음` / `High`):
     - Check the thinking level even when `Neon` is already selected.
     - Check whether `Neon` or `High` (`높음`) is already `[checked]` (`aria-checked="true"`) before clicking; clicking an already-checked radio item in `aside repl` fails with `Checkbox click did not change checked state`.
     - If `Neon` or `High` is missing, disabled, ambiguous, or unselectable, close opened tabs and report that limit.
   - Confirm both `Neon` and `High` (for example `Neon 높음` / `Neon High` or checked menu states) in a fresh snapshot before submitting.

## Round-by-Round Input, Extraction, and Abort Recovery

- Gemini Quill Editor Entry: Never call `locator.fill('')` or raw `fill()` on Gemini's prompt editor; it breaks Quill editor state. Inspect whether non-placeholder draft text exists; if non-empty, focus the editor, select all (`Meta+A` on macOS / `Control+A` elsewhere) and press `Backspace`, verify empty, then enter text via `geminiPage.keyboard.insertText(promptText)`. Take a fresh snapshot confirming the Send button (`메시지 보내기` / `Send`) is visible and enabled before clicking, then confirm generation started (`대답 생성 중지` / `Stop generating`).
- Response Verification & Privacy Scoping: Never scrape full-page `document.body.innerText`, which leaks unrelated sidebar conversation history. Scope extraction strictly to the active assistant message container (`model-response` / `message-content` / active ChatGPT turn via copy control or scoped DOM after expanding collapsed turn controls if needed). Before accepting a Gemini completion, verify that the tab did not silently reset to the empty landing page (`https://gemini.google.com/app` with `무엇을 도와드릴까요?` / `Hello` and zero assistant turns).
- Output Budgeting: Web Gemini's `processSession` stream can abort (~195–200s observed in prior runs) when asked for large multi-part prose. Keep Round 1 outputs concise using compact structured claim tables and bounded artifacts (target `<1,800` words), or split claim generation from bulky final artifact formatting. In Round 2, pass a concise Peer Claim Digest & Canonical Claim Table rather than raw 40KB+ dumps.
- Bounded Recovery on Timeout, Refusal, or Abort:
  - Uncertain submission or timeout: Inspect the existing tab, URL, and partial response first before retrying; never blindly duplicate an uncertain submission. If a tab stalls with zero new output across two consecutive `<=90s` poll windows, stop polling and treat the node as stalled or aborted.
  - Generic non-safety refusal (for example `"I'm having a hard time fulfilling your request..."`): Allow at most 1 neutral non-persona re-prompt in a fresh chat preserving exact topic semantics. A substantive policy refusal remains a refusal; stop and report rather than bypassing boundaries.
  - Stream abort or landing-page reset: Allow at most 1 retry in a fresh tab at the exact same `Neon High` setting with a tightened output-length budget (does not consume an extra debate round; max 1 retry per round per model).
  - No silent downgrade: Never switch Gemini off `Neon High` or ChatGPT off highest reasoning without user authorization. If a node remains blocked after 1 bounded retry, preserve all completed peer artifacts, close tabs cleanly, and return `BLOCKED_PARTIAL` with exact failure evidence.

## Transport Limits

- Available models, reasoning controls, and thinking-level options depend on each account and can change. Check the live UI on each run without hardcoding element refs or assuming a single locale.
- UI labels do not establish billing, quota, rate limits, or subscription details. Do not infer them.
- A successful prompt submission does not prove response completion. Confirm active-thread URL, completion stability, and scoped response content before advancing rounds.
