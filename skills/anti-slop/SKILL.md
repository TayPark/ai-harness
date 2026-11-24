---
name: anti-slop
description: Anti-slop writing standard, supplied-document cleanup workflow, and deterministic bilingual (English & Korean) checker. Use when drafting or self-reviewing prose, or when removing observable AI slop from a user-supplied document while preserving facts, voice, and required format.
---

# Anti-Slop Prose Standard and Cleanup (English & Korean)

Produce concise, high-signal prose in English and Korean when drafting, and remove only observable AI slop when editing a user-supplied document.

Read [references/banned-patterns.md](references/banned-patterns.md) for bilingual pattern tables and replacement recipes. Verify drafts and check candidates with `python3 scripts/check_slop.py --strict`.

## Activation Guardrails

- Use when: drafting English or Korean prose (`draft` mode) or removing observable AI slop from a user-supplied document (`postprocess` mode).
- Do NOT use when: you need factual rewriting, technical code review, or rubric scoring of code/architecture (use `evaluate-with-rubric` or `sdd-*`).
- Required before running: declare `draft` vs `postprocess` mode explicitly. In `postprocess` mode, edit only observable slop and never save a cover letter to disk.

## Mode Selection

| Mode | Use when | Primary goal |
| --- | --- | --- |
| `draft` | Writing or self-reviewing your own response, doc, or article | Prevent S1/S2 tells before delivery and pass `check_slop.py --strict`. |
| `postprocess` | Cleaning a user-supplied document (or resume, portfolio, cover letter) | Remove observable slop with minimal edits while preserving voice, facts, and format. |

## Core Guardrails (Both Modes)

1. Preserve facts and technical payloads. Never change numbers, dates, units, proper nouns, model or product names, code blocks, inline code, CLI commands, file paths, URLs, legal/medical/policy terms, citations, or speaker-attributed direct quotes (`"..." said X`, `"..."라고 밝혔다`).
2. Preserve modality (서법 보존). Never turn epistemic hedges (`may`, `could`, `~할 수 있다`, `~로 보인다`) into flat assertions (`is`, `~이다`), nor normative claims (`should`, `~해야 한다`) into factual claims (`~한다`). Collapse only stacked hedges (`~할 수 있을 것으로 보인다` -> `~로 보인다`), and vary endings only when 4+ identical hedges cluster in one paragraph.
3. Protect voice, register, and required format. Match the target genre and speech level. In Korean, keep colloquial endings (`~인데요`, `~거든요`, `~한 겁니다`) when appropriate and never elevate `-했-` to `-하였-`. Follow existing document-type instructions over style preferences.
4. Keep factual, technical, legal, citation, and format defects separate from slop edits. Flag them without inventing or silently altering facts.
5. Never write or save a supplied or chat-drafted cover letter to a file; review cover letters in chat only.

## High-Priority Rules (S1: Act on 1 Sighting)

1. Answer first with zero chat residue. Cut throat-clearing (`Certainly!`, `Great question!`, `좋은 질문입니다!`), meta-run-ups (`Let's dive in`, `이 글에서는 ~를 살펴보겠습니다`), and closing platitudes (`I hope this helps!`, `도움이 되셨기를 바랍니다`).
2. Cut negative parallelisms and staged run-ups. Remove `It's not (just) X; it's Y`, ornamental `Not only X, but also Y`, `At its core`, `Here is the thing`, `단순한 X가 아니라 Y다`, and `단순한 X를 넘어 Y로`. State the claim directly.
   - Before: `It's not just a latency patch; it's a reliability shift.` -> After: `The patch cuts tail latency by 40%.`
   - Before: `단순한 속도 개선을 넘어 개발 문화를 바꾼다.` -> After: `속도가 빨라지면 배포 주기도 짧아진다.`
3. Cut dramatic one-line closers and forced recaps. Remove `Let that sink in.`, `Read that again.`, `That is the real win.`, `In conclusion,`, `결론적으로 말씀드리자면`, `요약하자면`, `~하는 이유다.`, `~해야 할 시점입니다`, and empty counterargument slots (`과제도 남아 있다`, `한계도 분명하다`).
4. Remove Korean translation-ese (한국어 번역투 제거).
   - Double and `by`-passives: `~되어지다` / `~지게 된다` / `~로 보여진다` -> `~되다` / `~보이다`. `X에 의해 생성된` -> `X가 만든`.
   - Preposition and verb calques: reduce `~를 통해` (`~로`, `~해서`), `~에 있어서` (`~에서`), `~와 관련하여` (`~에`), `가지고 있다` (`경쟁력을 가지고 있다` -> `경쟁력이 강하다`), and nominal endings (`~하는 것을 제공합니다` / `~를 도모합니다` / `~를 제고합니다` -> active verbs).
   - Inanimate subjects: `이 결과는 ~을 보여준다/시사한다` -> `이 결과를 보면 ~이다` or `~ 때문이다`.
   - Compound particles and unneeded pronouns: unpack `~에서의`, `~으로의`, `~에의`, `~으로부터의` into clauses (keep simple `~의`); drop unneeded `그`, `그녀`, `그것`, `이는`.
   - Cleft sentences: `중요한/필요한 것은 X이다` and `핵심은/문제는 ~라는 점이다` -> state subject and verb directly.
5. Ban AI buzzword clichés. Avoid stock markers (`delve`, `tapestry`, `testament`, `pivotal`, `underscore`, `multifaceted`, `foster`, `utilize`, `paramount`, `groundbreaking`, `seamless`, `robust`, `시사합니다`, `지평을 열다`, `잠금 해제`, `논의의 무늬`, `생각을 벼리다`, `진단은 서늘하다`).

## Rhythm, Formatting & Density Rules (S2: Act on Clusters)

1. Break forced triads and symmetrical antitheses. Avoid compulsive 3-adjective lists (`fast, scalable, and robust`) and repeated binary pairings (`기술은 도구이고, 사람은 주체다` -> `기술은 도구다. 사람이 그 도구를 쥔다.`).
2. Vary sentence length and Korean endings. Mix short sentences with complex ones. Never end 4+ consecutive Korean sentences with the exact same suffix (`~이다.`, `~고 있다.`, `~한 것이다.`). Remove commas right after Korean connective endings (`-고,`, `-며,`, `-지만,`, `-면서,`, `-아서/어서,`).
3. Restrain formatting. Limit em dashes to at most 1-2 per document. Avoid wrapping every bullet lead in bold, decorative emojis in prose or reports, and automatic `X: Y` colon-subtitle headings.

## Mode 1: Draft Self-Review

1. Scan your draft for S1 tells, clustered S2 tells (2+ tells or 3+ buzzwords in one paragraph), and protected guardrail spans.
2. Replace flagged phrases with direct, concrete language without deleting facts or altering modality.
3. Run `python3 scripts/check_slop.py --strict` on the result (outside code blocks and quotes) and confirm zero unintended meaning drift.

## Mode 2: Supplied-Document Cleanup (`postprocess`)

Edit only text that exhibits observable slop. Do not infer AI authorship, change sound content, add evidence, restructure sections, or apply unrelated style preferences.

### Process

1. Identify the document's purpose, audience, supplied format rules, and explicit voice or preservation constraints. For an unfamiliar format where format knowledge could materially change the edit, query an external model via `ask-to-chatgpt` or `ask-to-gemini` and distinguish sourced findings from editorial choices.
2. Choose the generic review below, or load only the matching format rubric if the document is a resume, portfolio, or cover letter.
3. Run `python3 scripts/check_slop.py --strict --file <path>` as a candidate detector (do not apply automated blind edits). Mark observable slop and explain each concrete issue in context; do not label prose as slop merely because it sounds formal or polished.
4. Make the smallest edits that remove the marked slop while preserving adjacent content and formatting.
5. Re-read the full document to verify facts, meaning, voice, structure, format, and technical or legal terms remain intact. If an edit altered protected content, restore it and report any defect separately.
6. For a named format, score only the observable slop patterns in its rubric and iterate until the slop score reaches 90/100 or higher. Do not deduct points for missing content, factual defects, fit, or format. For other document types, give a concise qualitative review unless a score is requested.

### Generic Prose Review

Check only these five observable slop patterns as `present` or `not observed` (no default numeric threshold):

- Boilerplate: stock introductions, transitions, conclusions, or praise that could fit many documents.
- Empty abstraction: inflated or generic wording that adds no meaning to the existing sentence.
- Evidence-free generic claim: broad claim already in the text that uses vague benefit language to sound persuasive.
- Repetition: repeated claims, points, transitions, or summaries.
- Formulaic phrasing: stilted, symmetrical, or unnatural wording that obscures the author's point.

### Format-Specific Scoring Modules

For each criterion, assign `0%` (pervasive), `25%` (frequent), `50%` (several clear instances), `75%` (one isolated minor instance), or `100%` (not observed) of the listed weight. Each module totals 100 points; `90/100` passes the slop-removal gate only and does not certify factual quality, JD fit, or hiring outcomes. Do not combine scores across documents.

- Resume: [references/resume-rubric.md](references/resume-rubric.md)
- Portfolio: [references/portfolio-rubric.md](references/portfolio-rubric.md)
- Cover letter (chat-only, never save to file): [references/cover-letter-rubric.md](references/cover-letter-rubric.md)
