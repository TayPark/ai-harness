---
name: anti-slop
description: Anti-slop writing guidelines and a deterministic checker for bilingual (English & Korean) prose the agent drafts. Strips artificial AI markers, robotic transitions, sycophancy, translation-ese, and formulaic paragraph structures. Use when writing, drafting, or self-reviewing your own responses or documents in English or Korean; use remove-ai-slop to clean a document the user supplies.
---

# Anti-Slop Writing Standard (English & Korean)

Produce authentic, concise, high-signal prose in English and Korean when you draft responses, docs, or other new prose. Self-review the draft with the workflow below before delivery.

To clean up a document the user supplies, use `remove-ai-slop` instead. That skill owns edits to supplied documents and format-specific scoring; it may run this skill's checker as a supporting check.

Read [references/banned-patterns.md](references/banned-patterns.md) for full bilingual pattern tables and replacement recipes. Verify drafts with `python3 scripts/check_slop.py --strict`.

## Core Guardrails (Do-NOT Rules)

1. **Preserve facts and technical payloads.** Never change numbers, dates, units, proper nouns, model/product names, code blocks, inline code, CLI commands, file paths, URLs, legal/medical/policy terms, or speaker-attributed direct quotes (`"..." said X`, `"..."라고 밝혔다`).
2. **Preserve modality (서법 보존).** Never turn epistemic hedges (`may`, `could`, `~할 수 있다`, `~로 보인다`) into flat assertions (`is`, `~이다`), nor normative claims (`should`, `~해야 한다`) into factual claims (`~한다`). Collapse only stacked hedges (`~할 수 있을 것으로 보인다` → `~로 보인다`), and vary endings only when 4+ identical hedges cluster in a paragraph.
3. **Protect voice and register.** Match the target genre and speech level. In Korean, keep colloquial endings (`~인데요`, `~거든요`, `~한 겁니다`) when appropriate and never elevate `-했-` to `-하였-`.

## High-Priority Rules (S1 — Act on 1 Sighting)

1. **Answer first; zero chat residue.** Cut throat-clearing (`Certainly!`, `Great question!`, `좋은 질문입니다!`), meta-run-ups (`Let's dive in`, `이 글에서는 ~를 살펴보겠습니다`), and closing platitudes (`I hope this helps!`, `도움이 되셨기를 바랍니다`).
2. **No negative parallelisms or staged run-ups.** Cut `It's not (just) X; it's Y`, `Not only X, but also Y` (when ornamental), `At its core`, `Here is the thing`, `단순한 X가 아니라 Y다`, `단순한 X를 넘어 Y로`. State the claim directly.
   - Before: `It's not just a latency patch; it's a reliability shift.` → After: `The patch cuts tail latency by 40%.`
   - Before: `단순한 속도 개선을 넘어 개발 문화를 바꾼다.` → After: `속도가 빨라지면 배포 주기도 짧아진다.`
3. **No dramatic one-line closers or forced recaps.** Cut `Let that sink in.`, `Read that again.`, `That is the real win.`, `In conclusion,`, `결론적으로 말씀드리자면`, `요약하자면`, `~하는 이유다.` ("This is why ~"), `~해야 할 시점입니다`, and empty counterargument slots (`과제도 남아 있다`, `한계도 분명하다`).
4. **Kill Korean translation-ese (한국어 번역투 제거).**
   - **Double & `by`-passives:** `~되어지다` / `~지게 된다` / `~로 보여진다` → `~되다` / `~보이다`. `X에 의해 생성된` → `X가 만든`.
   - **Preposition & verb calques:** Avoid `~를 통해` overuse (`~로`, `~해서`), `~에 있어서` (`~에서`), `~와 관련하여` (`~에`), `가지고 있다` (`경쟁력을 가지고 있다` → `경쟁력이 강하다`), and nominal endings (`~하는 것을 제공합니다` / `~를 도모합니다` / `~를 제고합니다` → active verbs).
   - **Inanimate subjects:** `이 결과는 ~을 보여준다/시사한다` → `이 결과를 보면 ~이다` or `~ 때문이다`.
   - **Compound particles & unneeded pronouns:** Unpack `~에서의`, `~으로의`, `~에의`, `~으로부터의` into clauses (keep simple `~의`). Drop unnecessary `그`, `그녀`, `그것`, `이는`.
   - **Cleft sentences:** `중요한/필요한 것은 X이다` and `핵심은/문제는 ~라는 점이다` → state subject and verb directly.
5. **Ban AI buzzword clichés.** Never use overused stock markers (`delve`, `tapestry`, `testament`, `pivotal`, `underscore`, `multifaceted`, `foster`, `utilize`, `paramount`, `groundbreaking`, `seamless`, `robust`, `시사합니다`, `지평을 열다`, `잠금 해제`, `논의의 무늬`, `생각을 벼리다`, `진단은 서늘하다`).

## Rhythm, Formatting & Density Rules (S2 — Act on Clusters)

1. **Break forced triads and symmetrical antitheses.** Avoid compulsive 3-adjective lists (`fast, scalable, and robust`) and repeated binary pairings (`기술은 도구이고, 사람은 주체다` → `기술은 도구다. 사람이 그 도구를 쥔다.`).
2. **Vary sentence length and Korean endings.** Mix short sentences with complex ones. Never end 4+ consecutive Korean sentences with the exact same suffix (`~이다.`, `~고 있다.`, `~한 것이다.`). Remove commas right after Korean connective endings (`-고,`, `-며,`, `-지만,`, `-면서,`, `-아서/어서,`).
3. **Restrain formatting.** Limit em dashes (`—`) to at most 1–2 per document. Never wrap every bullet lead in bold (`- **Key**: ...`), avoid decorative emojis (`✅ 🚀 💡 ⚠️ 📊`) in prose or reports, and avoid automatic `X: Y` colon-subtitle headings.

## Workflow (Draft Self-Review)

1. **Scan:** Mark S1 tells, clustered S2 tells (2+ tells or 3+ buzzwords in one paragraph), and protected Do-NOT spans in your own draft.
2. **Edit:** Replace flagged phrases with direct, concrete language without deleting facts or altering modality.
3. **Verify:** Run `python3 scripts/check_slop.py --strict` on the result (outside code blocks/quotes) and confirm zero unintended meaning drift.
