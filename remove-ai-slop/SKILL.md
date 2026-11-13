---
name: remove-ai-slop
description: Remove observable AI slop from prose documents while preserving meaning, author voice, content, and required format. Does not infer AI authorship or rewrite documents.
---

# AI slop postprocess

Remove only observable slop: empty generalities, formulaic transitions, repetition, inflated phrasing, and unsupported self-praise. The goal is cleaner prose, not to detect who wrote it or to rewrite content or format.

## Boundaries

- Preserve facts, meaning, author voice, structure, requested language, legal and technical terms, citations, and the document's required format.
- Edit only text that exhibits observable slop. Do not change sound content, add evidence, restructure sections, rewrite claims, or apply unrelated style preferences.
- Keep factual concerns separate from slop edits. Flag them; do not resolve them by inventing or silently changing facts.
- Follow existing instructions for the document type, including required structure and layout. These instructions take precedence over style changes.
- For a format without existing guidance, research only when format knowledge could materially change the edit. Use `$ask-chatgpt` through an independent agent. Distinguish sourced findings from editorial choices. If research is unavailable or inconclusive, preserve the supplied format and ask only about material ambiguity.
- A supplied or chat-drafted cover letter may be reviewed in chat, but must never be written to or saved in a file.

## Process

1. Identify the document's purpose, audience, supplied format rules, and any explicit voice or preservation constraints.
2. Select the generic review below. If the document is a resume, portfolio, or cover letter, read only its matching scoring module.
3. Mark observable slop. Explain the concrete issue in its context; do not label prose as slop only because it sounds polished, formal, or AI-like.
4. Make the smallest edits that remove the marked slop. Preserve adjacent content and formatting.
5. Read the full document after edits. Check that meaning, facts, voice, structure, required format, and technical or legal language remain intact.
6. For a named format, score only the observable slop patterns in its rubric. Revise those patterns and rescore until the slop score reaches 90/100 or higher. Do not lower the score for missing content, factual or technical defects, fit, or format. Flag such defects separately and leave them unchanged. For other document types, provide a concise qualitative slop review unless the user requests a score.

## Generic prose review

For an arbitrary prose document, check only these observable slop patterns as `present` or `not observed`:

- **Boilerplate:** Stock introductions, transitions, conclusions, or praise that could fit many documents.
- **Empty abstraction:** Inflated or generic wording that adds no meaning to the existing sentence.
- **Evidence-free generic claim:** Broad claim already in the text that uses vague benefit language to sound persuasive.
- **Repetition:** Repeated claims, points, transitions, or summaries.
- **Formulaic phrasing:** Stilted, symmetrical, or unnatural wording that obscures the author's existing point.

This qualitative review has no default numerical threshold. Do not score completeness, factuality, technical quality, fit, or missing content as slop. The named format modules score only patterns in this list, interpreted through the format.

## Non-scored guardrails

Flag factual, legal, technical, citation, structure, and required-format defects separately. Do not edit them as part of slop removal. Preserve the original format and terms even when they appear unusual. These guardrails do not change the slop score.

## Scoring anchors

For each criterion, use its listed weight as the maximum and assign 0%, 25%, 50%, 75%, or 100% of that weight:

| Anchor | Meaning |
|---:|---|
| 0% | The slop pattern is pervasive in the supplied text. |
| 25% | The pattern appears often and affects many existing sentences. |
| 50% | Several clear instances remain. |
| 75% | One isolated, minor instance remains. |
| 100% | No observable instance of this slop pattern appears in the supplied text. |

Keep fractional points when a weight does not divide evenly. A high slop score does not certify factual, technical, legal, or format quality. If an edit changes any protected content, restore it; report the defect separately.

## Format-specific scoring modules

- Resume: read [references/resume-rubric.md](references/resume-rubric.md).
- Portfolio: read [references/portfolio-rubric.md](references/portfolio-rubric.md).
- Cover letter: read [references/cover-letter-rubric.md](references/cover-letter-rubric.md). Keep all text in chat; never save the letter.

Each named module totals 100 points. A slop score of 90/100 or higher passes this slop-removal gate only. This is a user-required threshold, not a research standard, document-quality certification, JD-fit score, or hiring prediction. Do not combine scores across documents.

The research and editorial basis are separate. Research-derived claims are linked in the matching module. Criteria and weights without sourced support are labeled local design choices.
