# Aside CLI Web Transport Adapter (ChatGPT & Web Gemini)

Use this transport when running `debate-models` (`web-pair` or `hybrid-pair`) through Aside CLI against authenticated Web ChatGPT (`https://chatgpt.com/`) and/or Web Gemini (`https://gemini.google.com/`). This uses the user's web accounts via Aside browser automation. Do not promise lower cost, free usage, or specific billing or quota outcomes.

## Prerequisites & REPL Lifecycle

1. Check current Aside REPL instructions with `aside repl --help`, `aside guide repl`, and `aside skills list`. Read `aside skills show google-accounts` if Google account discovery is needed, or any matching built-in Aside skill first.
2. Persistent handles and bounded polling: Aside REPL enforces a 120-second per-call timeout while high-reasoning responses can take several minutes. Do not wrap a multi-minute wait in one blocking call:
   - Store opened page handles in persistent REPL bindings (`globalThis.chatgptPage`, `globalThis.geminiPage`).
   - Keep each polling loop bounded to `<=90` seconds per REPL call, returning cleanly across calls until generation stabilizes.
   - Never reuse or modify unrelated open browser tabs.
   - On completion, stall, or abort, capture available text/status and close each opened tab in independent `try ... catch` `closeTab()` calls so one failure cannot skip closing another tab.

## Web ChatGPT Setup (`chatgpt.com`)

1. Open a new tab at `https://chatgpt.com/` with `openTab()`.
2. Take a fresh `snapshot(chatgptPage, { interactive: true })`. Confirm login; if login is requested, close opened tabs and stop.
3. Start a new chat if not already on one.
4. Inspect both the model picker and reasoning-effort selector in Chat mode. Select the highest available reasoning model and effort without hardcoding labels. Confirm the resulting selection in a fresh snapshot. If controls are missing, ambiguous, or unselectable, close the tab, report the limit, and stop.
5. Clear any draft in the composer, insert the prompt with a multiline-safe method (`page.keyboard.insertText(prompt)`), attach only user-specified files and verify upload completion, confirm Send is enabled, and click Send once.
6. Poll fresh snapshots until generation ends and the final assistant turn is stable. Read the complete assistant message (in scoped slices if clipped), including Markdown structure, code blocks, and links.

## Web Gemini Setup (`gemini.google.com`, `Neon` + `High`)

1. Open a new tab at `https://gemini.google.com/` with `openTab()` and wait for controls to hydrate.
2. Read `snapshot(geminiPage, { interactive: true })` and confirm login. If login is requested, close opened tabs and stop.
3. Start a new chat (`새 채팅` / `New chat`) before configuring model settings if not already on one, so new-chat creation cannot reset model controls.
4. Ensure Chat mode (`채팅` / `Chat`) is active rather than Task mode (`태스크` / `Tasks`) when both appear, unless the user requested Tasks.
5. Inspect the mode/model selector (`모드 선택 도구` / `Neon` / `사고 수준` / `높음` or English equivalents). Select `Neon` and set thinking level to `High` (`높음` / `High`):
   - Check the thinking level even when `Neon` is already selected.
   - Check whether `Neon` or `High` is already `[checked]` (`aria-checked="true"`) before clicking; clicking an already-checked radio item in `aside repl` fails with `Checkbox click did not change checked state`.
   - If `Neon` or `High` is missing, disabled, ambiguous, or unselectable, close opened tabs, report the limit, and stop without substituting another model.
6. Confirm both `Neon` and `High` (`Neon 높음` / `Neon High` or checked menu states) in a fresh snapshot.
7. Prompt entry (Quill editor safety): never call raw `fill()` or `locator.fill('')` on Gemini's editor. If non-placeholder draft text exists, focus the editor, select all (`Meta+A` on macOS / `Control+A` elsewhere), press `Backspace`, and verify empty. Attach any user-specified files and wait until ready. Insert text via `geminiPage.keyboard.insertText(promptText)`.
8. Verify Send (`메시지 보내기` / `Send`) is enabled, record the baseline `model-response` count, click Send once, and confirm generation started (`대답 생성 중지` / `Stop generating`).

## Scoped Extraction, Copyable Poll Pattern & Recovery

Never scrape full-page `document.body.innerText`, which leaks unrelated sidebar conversation history. Extract strictly from the active assistant turn container (`model-response` / `message-content` or active ChatGPT turn copy/DOM container, sliced if clipped).

```js
// Call 1: open tab, verify login, new chat, model/thinking settings, and attachments.
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

### Bounded Recovery Rules

- Output budgeting: Web Gemini's stream can abort (~195-200s observed) on large multi-part prose. Keep debate Round 1 outputs concise (`<1,800` words) and send concise claim digests in Round 2+.
- Uncertain submission or stall: inspect the existing tab, URL, and partial response before retrying; never blindly duplicate an uncertain submission. Stop polling after two consecutive `<=90s` poll windows with zero new output.
- Generic non-safety refusal (such as `"I'm having a hard time fulfilling your request..."`): allow at most 1 neutral re-prompt in a fresh chat preserving exact semantics. Substantive policy refusals stop immediately.
- Stream abort or `/app` landing-page reset: allow at most 1 retry in a fresh tab at the exact same model and thinking setting with a tightened output budget (max 1 retry per round per model).
- No silent downgrade: if blocked after 1 bounded retry, preserve completed artifacts, close tabs cleanly, and report failure (or `BLOCKED_PARTIAL` in `debate` mode).
