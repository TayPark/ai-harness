---
name: ask-to-gemini
description: Submit a user-provided question to Web Gemini (gemini.google.com) through Aside CLI using the Neon model at High thinking level and return the full response. Use when querying Web Gemini directly via Aside Web to conserve local CLI/API tokens.
---

# Ask to Gemini (Aside Web, Neon High)

Use Aside CLI to open a new Web Gemini conversation, select `Neon` with `High` thinking level, submit the user's question, and return the complete response.

## Activation Guardrails

- Use when: the user asks to query Web Gemini directly, or you want a single-shot `Neon High` answer via Aside Web to conserve local CLI/API tokens.
- Do NOT use when: you need a multi-round cross-model debate (use `debate-models`), a privacy-filtered rubric evaluation with local JSON validation (use `evaluate-with-rubric`), or a Web ChatGPT query (use `ask-to-chatgpt`).
- Required before running: confirm Aside CLI, an authenticated Google/Gemini session, and live `Neon` + `High` controls are available. If any prerequisite is missing, close opened tabs, report the failure, and stop without substituting another model or handling credentials.

## Input

- Send the question in the current user request. Preserve its exact wording, line breaks, and requested output format.
- Include local files only when the user explicitly specifies them. Exclude unrelated conversation or account data.

## Procedure

1. Read current Aside REPL instructions with `aside repl --help`, `aside guide repl`, and `aside skills list`. Read `aside skills show google-accounts` if account discovery or selection is needed.
2. Start a persistent `aside repl` session and keep the opened tab handle in REPL state (`globalThis.geminiPage = await openTab("https://gemini.google.com/")`). Keep polling calls bounded to `<=90` seconds (Aside REPL enforces a 120-second per-call timeout). Do not reuse or modify unrelated tabs. Always run `await closeTab(globalThis.geminiPage)` inside `try ... catch` on completion, stall, or failure.
3. Wait for page controls to hydrate and read `snapshot(geminiPage, { interactive: true })`. Confirm Gemini is logged in. If login is requested, close the tab and stop.
4. Start a new chat (`새 채팅` / `New chat`) before configuring model settings if the page did not already open one, so starting a new chat cannot reset the chosen model or thinking level. Ensure Chat mode (`채팅` / `Chat`) is active rather than Task mode (`태스크` / `Tasks`) unless the user requested Tasks.
5. Inspect the mode/model selector (`모드 선택 도구` / `Neon` / `사고 수준` / `높음` or English equivalents). Select `Neon` and set thinking level to `High` (`높음` / `High`):
   - Check the thinking level even when `Neon` is already selected.
   - Check whether `Neon` or `High` is already `[checked]` (`aria-checked="true"`) before clicking; clicking an already-checked radio item fails with `Checkbox click did not change checked state`.
   - If `Neon` or `High` is missing, disabled, ambiguous, or unselectable, close the tab, report that limit, and stop.
6. Confirm both `Neon` and `High` (`Neon 높음` / `Neon High` or checked menu states) in a fresh snapshot.
7. Prepare prompt and optional user-specified attachments (Quill editor safety):
   - Never call raw `fill()` on Gemini's editor. If persisted draft text exists, focus the editor, select all (`Meta+A` on macOS / `Control+A` elsewhere), press `Backspace`, and verify empty.
   - Attach only user-specified files, wait for upload completion, and verify each filename is ready. If upload fails, close the tab and stop.
   - Insert the exact prompt via `geminiPage.keyboard.insertText(question)`.
8. Verify prompt, attachments, `Neon` + `High`, and enabled Send button (`메시지 보내기` / `Send`) in a fresh snapshot. Record baseline `model-response` count, click Send once, and confirm generation started (`대답 생성 중지` / `Stop generating`).
9. Poll across bounded `<=90s` calls until generation completes and output stabilizes:
   - If the tab resets to the empty `/app` landing page, report a reset. Accept completion only after a new assistant turn appears, the Stop control disappears, and the turn text is non-empty and unchanged across two consecutive polls.
   - If two consecutive `<=90s` poll windows show no progress, capture partial text and UI state, close the tab, and report the stall.
   - Extract strictly from the active assistant turn (`model-response` / `message-content` or copy control), never full-page `document.body.innerText` (which leaks sidebar history). Slice long replies if clipped, then close `globalThis.geminiPage`.
10. Return the complete response and state only the observed model and thinking-level label.

## Copyable Persistent REPL Pattern

```js
// Call 1: open tab, verify login, new chat, Neon High, and attachments.
globalThis.geminiPage = await openTab("https://gemini.google.com/");
await geminiPage.keyboard.insertText(question);
globalThis.geminiBaselineTurns = await geminiPage.locator("model-response").count();
// Fresh snapshot, then click verified Send ref and confirm generation started.

// Call 2..N: bounded <=90s poll window per REPL call.
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

// Cleanup after completion, reset, failure, or two stagnant poll windows:
try { await closeTab(geminiPage); } catch (e) { console.error("cleanup failed:", e); }
```

## Limits

Available models and thinking levels depend on account access and locale. UI labels do not establish billing, quota, or subscription details. Confirm active-thread URL, completion stability, and scoped content before reporting completion.
