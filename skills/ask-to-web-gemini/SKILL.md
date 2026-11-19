---
name: ask-to-web-gemini
description: Submit a user-provided question to Web Gemini (gemini.google.com) through Aside CLI using the Argon model at High thinking level, then return the complete response. Use when asked to query Web Gemini directly or get an Argon High response via Aside.
---

# Ask to Web Gemini

Use Aside CLI to open a new Web Gemini conversation, select Argon with High thinking level, submit the user's question, and return the completed response. This uses the user's Google/Gemini account and its available access. Do not promise lower cost, free usage, or any specific usage or billing outcome.

## Prerequisites

Aside CLI and an authenticated Google/Gemini session are required. If either is unavailable, report the failure and stop; do not substitute another service or model without authorization.

## Input

- Use the question in the current user request.
- Include local files or other material only when the user specifies them.
- Keep the question's meaning and requested output format.
- Do not include unrelated conversation or account data.

## Procedure

1. Read the current Aside REPL instructions with `aside repl --help`, `aside guide repl`, and `aside skills list`. Read `aside skills show google-accounts` if account discovery or selection is needed. If no built-in Aside skill covers Web Gemini chat, use the browser procedure below.
2. Start `aside repl` (with `try ... finally { await closeTab(page); }` or equivalent cleanup). Open a new tab at `https://gemini.google.com/` with `openTab()`. Do not reuse or modify an unrelated open conversation.
3. Wait for the page controls to hydrate and read the page with `snapshot(page, { interactive: true })`. Confirm that Gemini is logged in. If the page requests login, report that Gemini login is unavailable and stop. Do not handle credentials.
4. Ensure Chat mode (`채팅` / `Chat`) is active rather than Task mode (`태스크` / `Tasks`) when both controls are shown, unless the user explicitly requested Tasks.
5. Inspect the mode/model selector in the live UI (labels vary by locale, e.g., `모드 선택 도구` / `Argon` / `사고 수준` / `높음` or English equivalents). Select **Argon** and set its thinking level to **High** (`높음` / `High`):
   - Do not assume `Argon` alone implies `High`; a new tab can keep `Argon` selected while defaulting thinking level to `Low` (`낮음`).
   - Check whether `Argon` or `High` (`높음`) is already `[checked]` in the menu before clicking; clicking an already-checked radio item in `aside repl` fails with `Checkbox click did not change checked state`.
   - If `Argon` or the `High` thinking-level option is missing, disabled, ambiguous, or cannot be selected, report that limit and stop; do not silently substitute another model or claim `Argon High` was used.
6. Confirm both the `Argon` model and `High` thinking level (e.g., selector label `Argon 높음` / `Argon High`, or checked states in the menu) in a fresh snapshot. Start a new chat (`새 채팅` / `New chat`) if the page did not already open one.
7. Check the prompt textbox for any persisted draft text and clear it if non-empty. Focus the textbox and enter only the user's question using an input method that triggers the UI's Send button and preserves newlines without premature `Enter` submission (e.g., click the textbox and call `page.keyboard.insertText(question)` rather than raw `fill()` or `keyboard.type()`).
8. Take a fresh snapshot to confirm the Send button (`메시지 보내기` / `Send`) is visible and click it, then take another snapshot to confirm Gemini accepted and started generating the response.
9. Wait while the response is generating. Poll with fresh snapshots (`snapshot(page)` / `snapshot(page, { interactive: true })`) until the UI shows generation has completed and the output is stable. Retrieve the complete final response without truncation, then close the tab opened for this request.
10. Return the response to the user. State the model and thinking-level option only as actually observed in the UI. Report any access, selection, submission, or completion failure without implying success.

## Limits

- Available models and thinking-level options depend on the account and can change. Check the live UI each run without hardcoding ref IDs or assuming a single locale.
- UI labels do not establish billing, quota, rate limits, or subscription details. Do not infer them.
- A successful submission does not prove that a response completed. Confirm completion in the UI before reporting it as final.
