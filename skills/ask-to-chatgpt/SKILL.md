---
name: ask-to-chatgpt
description: Submit a user-provided question to ChatGPT (chatgpt.com) through Aside CLI using the highest available reasoning setting and return the full response. Use when asked to query ChatGPT directly through Aside.
---

# Ask to ChatGPT

Use Aside CLI and an authenticated ChatGPT session. If access fails or ChatGPT requests login, report the blocker and stop. Handle sign-in outside this workflow.

## Input

- Send the question in the current request. Preserve its wording, line breaks, and requested output format.
- Include only files or other material the user specifies for this request.

## Procedure

1. Check `aside repl --help`, `aside guide repl`, and `aside skills list`. Read a matching built-in Aside skill if available. Use the [Aside REPL documentation](https://aside.com/developers) for browser control.
2. Start a persistent `aside repl` session. Open a new tab at `https://chatgpt.com/` with `openTab()` and keep its page handle. Use `closeTab()` in a `finally` block or equivalent cleanup for this tab on success and failure.
3. Take a fresh interactive snapshot. Confirm that the account is signed in and the tab shows a new chat. Start a new chat in that tab if needed, then inspect the model picker and reasoning controls.
4. Select the highest reasoning model and effort that the live UI offers in Chat mode. Check the effort menu separately when the model exposes one. Keep any already-correct selection and confirm the resulting model and effort in a fresh snapshot. If the controls are missing or ambiguous, or the selection fails, report the limit and stop before sending.
5. Clear any draft in the new chat composer. Insert the prompt without submitting it, using a multiline-safe input method such as `page.keyboard.insertText(question)` if supported. Attach only user-specified files and verify that each upload completes. Confirm the composer contains the intended prompt and Send is enabled.
6. Click Send once using a fresh snapshot. Confirm the submitted user message and generation or a completed reply in the same chat. If acceptance is uncertain, inspect the current chat before any retry. Report an unconfirmed submission if the UI cannot resolve it.
7. Poll fresh snapshots until the UI shows generation has ended and the assistant reply is stable. Read the full reply, including Markdown structure, code blocks, and links where available. If the snapshot output is clipped, read the final assistant message in scoped sections before closing the tab.
8. Return the complete response and identify the model and effort observed in the UI. Report any visible fallback, interruption, or incomplete retrieval separately.

## Limits

Model and effort labels depend on account access and locale. Use fresh snapshots for selectors and ref IDs. UI labels alone provide no evidence about billing or quotas.
