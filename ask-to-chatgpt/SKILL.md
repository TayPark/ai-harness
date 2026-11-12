---
name: ask-to-chatgpt
description: Submit a user-provided question to ChatGPT through Aside Browser using the highest available reasoning setting, then return the complete response.
---

# Ask to ChatGPT

Use Aside CLI to open a new ChatGPT conversation, submit the user's question, and return the completed response. This uses the user's ChatGPT account and its available subscription access. Do not promise lower cost, free usage, or any specific usage or billing outcome.

## Input

- Use the question in the current user request.
- Include local files or other material only when the user specifies them.
- Keep the question's meaning and requested output format.
- Do not include unrelated conversation or account data.

## Procedure

1. Read the current Aside REPL instructions with `aside repl --help`, `aside guide repl`, and `aside skills list`. Read a matching built-in Aside skill if one covers ChatGPT. If no skill covers ChatGPT, use the browser procedure below.
2. Start `aside repl`. Open a new tab at `https://chatgpt.com/` with `openTab()`. Do not reuse or change an unrelated open conversation.
3. Read the page with `snapshot(page, { interactive: true })`. Confirm that ChatGPT is logged in. If the page requests login, report that ChatGPT login is unavailable and stop. Do not handle credentials.
4. Inspect the model and reasoning controls shown in the current ChatGPT UI. Select the model and reasoning option that provide the highest reasoning level currently available in Chat mode. Do not use a fixed model name or assume the option labels. If the setting is missing, ambiguous, or cannot be selected, report that limit and do not claim the requested setting was used.
5. Confirm the selected model and reasoning option in a fresh snapshot. Start a new chat if the page did not already open one.
6. Enter only the user's question and submit it. Take a fresh snapshot to confirm that ChatGPT accepted the message.
7. Wait while the response is generating. Read a fresh snapshot until the UI shows completion. Retrieve the full response without truncation.
8. Return the response to the user. State the model and reasoning option only when the UI showed them. Report any access, selection, submission, or completion failure without implying success.

## Limits

- The available models and reasoning options depend on the account and can change. Check the live UI each run.
- UI labels do not establish billing, quota, or subscription details. Do not infer them.
- A successful submission does not prove that a response completed. Confirm completion in the UI before reporting it as final.
