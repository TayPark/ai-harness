---
name: ask-to-web-gemini
description: Submit a user-provided question to Web Gemini (gemini.google.com) through Aside CLI using the Neon model at High thinking level, then return the complete response. Use when asked to query Web Gemini directly or get a Neon High response via Aside.
---

# Ask to Web Gemini

Use Aside CLI to open a new Web Gemini conversation, select `Neon` with `High` thinking level, submit the user's question, and return the complete response. This uses the user's Google/Gemini account and its available access. Do not promise lower cost, free usage, or any specific usage or billing outcome.

## Prerequisites

Aside CLI and an authenticated Google/Gemini session are required. If either is unavailable, report the failure and stop; do not substitute another service or model without authorization. Handle sign-in outside this workflow.

## Input

- Send the question in the current user request. Preserve its exact wording, line breaks, and requested output format.
- Include local files or other material only when the user explicitly specifies them.
- Do not include unrelated conversation or account data.

## Procedure

1. Read current Aside REPL instructions with `aside repl --help`, `aside guide repl`, and `aside skills list`. Read `aside skills show google-accounts` if account discovery or selection is needed. If a built-in Aside skill covers Web Gemini chat, check it first; otherwise follow the browser steps below.
2. Start a persistent `aside repl` session and keep the opened tab handle in REPL state (`globalThis.geminiPage = await openTab("https://gemini.google.com/")`). Do not wrap a multi-minute high-thinking wait in a single blocking REPL call (Aside REPL enforces a 120-second per-call timeout). Do not reuse or modify unrelated open conversations. Ensure final cleanup runs `await closeTab(globalThis.geminiPage)` inside a `try ... catch` block on completion, stall, or failure.
3. Wait for page controls to hydrate and read `snapshot(page, { interactive: true })`. Confirm Gemini is logged in. If the page requests login, close the opened tab, report that Gemini login is unavailable, and stop.
4. Start a new chat (`새 채팅` / `New chat`) **before** configuring model settings if the page did not already open one, so starting a new chat cannot reset the chosen model or thinking level. Ensure Chat mode (`채팅` / `Chat`) is active rather than Task mode (`태스크` / `Tasks`) when both controls are shown, unless the user explicitly requested Tasks.
5. Inspect the mode/model selector in the live UI (labels vary by locale, e.g., `모드 선택 도구` / `Neon` / `사고 수준` / `높음` or English equivalents). Select **Neon** and set thinking level to **High** (`높음` / `High`):
   - Check the thinking level even when `Neon` is already selected.
   - Check whether `Neon` or `High` (`높음`) is already `[checked]` (`aria-checked="true"`) before clicking; clicking an already-checked radio item in `aside repl` fails with `Checkbox click did not change checked state`.
   - If `Neon` or `High` is missing, disabled, ambiguous, or unselectable, close the opened tab, report that limit, and stop; do not silently substitute another model or claim `Neon High` was used.
6. Confirm both `Neon` and `High` (e.g., selector label `Neon 높음` / `Neon High` or checked menu states) in a fresh snapshot of the active new chat.
7. Prepare prompt and optional user-specified attachments:
   - Check the prompt textbox for any persisted draft text. If non-empty, focus the editor, select all (`Meta+A` on macOS / `Control+A` elsewhere), press `Backspace`, and verify empty (never call raw `fill()` on Gemini's Quill editor).
   - If the user specified local files, attach only those files through the UI upload control, wait for upload progress indicators to finish, and verify each attached filename appears ready in a fresh snapshot. If an upload fails or is unsupported, close the tab and stop without sending a partial prompt.
   - Focus the textbox and enter the exact user question using a multiline-safe method that enables Send without premature submission (`page.keyboard.insertText(question)`).
8. Take a fresh snapshot to verify the prompt, ready attachments (if any), active `Neon` + `High` selector, and enabled Send button (`메시지 보내기` / `Send`). Record the assistant turn count before clicking Send once. Confirm in a fresh snapshot that the user message was accepted and generation started (`대답 생성 중지` / `Stop generating`). If submission is uncertain, inspect the current tab before retrying.
9. Poll across bounded `<=90s` REPL calls until generation completes and output stabilizes:
   - If the tab resets to the empty `/app` landing page, report a reset. Accept completion only after a new assistant turn appears, the Stop control disappears, and the same new turn has non-empty, unchanged text across two consecutive polls.
   - If generation produces no progress across two consecutive `<=90s` poll windows or aborts/resets, capture any partial text and UI state, close the tab, and report the stall/failure without looping indefinitely.
   - Extract the final response strictly from the active assistant turn container (`model-response` / `message-content` or copy button), never full-page `document.body.innerText` (which leaks sidebar history). If snapshot output is clipped on a long reply, read the active assistant container in bounded text slices until the full response is recovered, then close `globalThis.geminiPage`.
10. Return the complete response to the user. State the model and thinking-level label only as actually observed in the UI. Report any access, upload, selection, submission, stall, or retrieval failure without implying success.

## Copyable Persistent REPL Pattern

```js
// Call 1: open the tab, then verify login, new chat, Neon High, and any attachments.
globalThis.geminiPage = await openTab("https://gemini.google.com/");
// After selecting Chat mode and focusing the editor:
await geminiPage.keyboard.insertText(question);
globalThis.geminiBaselineTurns = await geminiPage.locator("model-response").count();
// Fresh snapshot, then click the verified Send ref and confirm generation started.

// Call 2..N: one poll window per call. Adjust the selector if the live DOM differs.
{
  const deadline = Date.now() + 85_000;
  let previous = null;
  let done = false;
  let reset = false;
  while (Date.now() < deadline) {
    const { tree } = await snapshot(geminiPage, { interactive: true });
    const generating = /\bbutton "(?:Stop generating|대답 생성 중지)"/.test(tree);
    const { count, text } = await geminiPage.evaluate(() => {
      const turns = document.querySelectorAll("model-response");
      return { count: turns.length, text: turns[turns.length - 1]?.innerText.trim() ?? "" };
    });
    if (!generating && count === 0 && /^\/app\/?$/.test(new URL(geminiPage.url()).pathname)) {
      reset = true;
      break;
    }
    const ready = count > geminiBaselineTurns && !generating && text !== "";
    if (ready && previous?.count === count && previous.text === text) {
      done = true;
      break;
    }
    previous = ready ? { count, text } : null;
    await sleep(Math.max(0, Math.min(3000, deadline - Date.now())));
  }
  console.log({ done, reset });
}

// Last call: read the scoped response (in slices if needed) or capture partial output.
// Run cleanup after completion, reset, failure, or two poll windows without progress.
try { await closeTab(geminiPage); } catch (e) { console.error("cleanup failed:", e); }
```

## Limits

- Available models and thinking-level options depend on the account and can change. Check the live UI each run without hardcoding ref IDs or assuming a single locale.
- UI labels do not establish billing, quota, rate limits, or subscription details. Do not infer them.
- A successful submission does not prove response completion. Confirm active-thread URL, completion stability, and scoped response content before reporting the answer as final.
