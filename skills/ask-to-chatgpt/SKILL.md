---
name: ask-to-chatgpt
description: Submit a user-provided question to Web ChatGPT (chatgpt.com) through Aside CLI using the highest available reasoning setting and return the full response. Use when querying ChatGPT directly via Aside Web to conserve local CLI/API tokens.
---

# Ask to ChatGPT (Aside Web)

Use Aside CLI and an authenticated Web ChatGPT session to submit a single user-provided question and return the full response.

## Activation Guardrails

- Use when: the user asks to query Web ChatGPT directly, or you want a single-shot external answer via Aside Web to conserve local CLI/API tokens.
- Do NOT use when: you need a multi-round cross-model debate (use `debate-models`), a privacy-filtered rubric evaluation with local JSON validation (use `evaluate-with-rubric`), or a Web Gemini query (use `ask-to-gemini`).
- Required before running: confirm Aside CLI and an authenticated `chatgpt.com` session are available. If login is requested or controls are missing, report the blocker and stop without substituting another model or handling credentials.

## Input

- Send the question in the current request. Preserve its exact wording, line breaks, and requested output format.
- Include only files or material the user explicitly specifies for this request. Exclude unrelated conversation or account data.

## Procedure

1. Check `aside repl --help`, `aside guide repl`, and `aside skills list`. Read a matching built-in Aside skill if available.
2. Start a persistent `aside repl` session and open a new tab at `https://chatgpt.com/` (`globalThis.chatgptPage = await openTab("https://chatgpt.com/")`). Keep polling calls bounded to `<=90` seconds (Aside REPL enforces a 120-second per-call timeout). Always run `closeTab(globalThis.chatgptPage)` inside `try ... catch` on success, stall, or failure.
3. Take a fresh `snapshot(chatgptPage, { interactive: true })`. Confirm the account is signed in and the tab shows a new chat. Start a new chat if needed, then inspect both the model picker and reasoning-effort controls.
4. Select the highest reasoning model and effort that the live UI offers in Chat mode. Check the effort menu separately when exposed. Confirm the selected model and effort in a fresh snapshot. If controls are missing, ambiguous, or unselectable, close the tab, report the limit, and stop before sending.
5. Clear any draft in the composer. Insert the prompt without submitting it using a multiline-safe method (`page.keyboard.insertText(question)`). Attach only user-specified files and verify each upload completes. Confirm the composer contains the intended prompt and Send is enabled.
6. Click Send once using a fresh snapshot. Confirm the submitted message and active generation in the same chat. If acceptance is uncertain, inspect the current chat before any retry; never blindly duplicate a submission.
7. Poll across bounded `<=90s` calls until generation ends and the final assistant turn is stable. Read the complete assistant turn (in scoped slices if clipped), including Markdown structure, code blocks, and links, before closing the tab.
8. Return the complete response and state only the model and effort actually observed in the UI. Report any visible fallback, interruption, or incomplete retrieval separately.

## Limits

Model and effort labels depend on account access and locale. Use fresh snapshots for selectors and ref IDs. UI labels provide no evidence about billing, quotas, or cost.
