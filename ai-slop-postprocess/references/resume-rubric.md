# Resume AI-slop rubric

Score only observable slop patterns in the supplied resume text. Do not score factual accuracy, evidence sufficiency, contribution completeness, technical quality, JD fit, or missing content. Flag defects in those areas separately without changing them. Apply the shared scoring anchors in the parent skill. Weights total 100.

| Slop pattern | Weight | Full-weight target |
|---|---:|---|
| Vague broad-impact claims | 25 | Existing claims avoid vague praise or broad impact language that adds little to the action already described. Do not assess factual support here. |
| Contribution boilerplate | 20 | Existing contribution statements avoid filler such as “played a key role” or “was responsible for” when used without a concrete point. Do not judge whether the actual contribution is sufficient. |
| Empty specificity or metric language | 20 | Existing sentences avoid empty intensifiers, generic impact terms, and numbers used as decoration. Do not validate metric accuracy here. |
| Keyword stuffing | 15 | Existing text avoids repetitive keyword strings and generic skill phrases. Do not score whether a relevant qualification is missing. |
| Repetition and density | 10 | Claims are not repeated among peer bullets or adjacent summary blocks without added context. Do not penalize a concise resume summary or strengths section that previews results substantiated later in experience details. |
| Formulaic phrasing and inflated self-praise | 10 | Existing sentences avoid stock constructions, grand claims, and unnatural self-praise. |

The Ask-to-ChatGPT answer proposed weights for broad resume quality: factuality/evidence 25, individual contribution 20, specificity/metric quality 20, job relevance 15, information density/non-repetition 10, and naturalness/restraint 10. Those are not AI-slop weights. The table above adapts the proposal's weight pattern to observable slop only; it does not score factuality, completeness, or fit. These weights are a research-informed local adaptation, not an established standard.

Record the text location and visible slop pattern for each score. A missing metric, action, result, skill, or qualification is not slop and does not lower this score.

## Research basis

The broader approach evaluates observable text features rather than inferring authorship from prose style. See [Findings of ACL 2025, paper 1303](https://aclanthology.org/2025.findings-acl.1303/) and [EMNLP 2026, paper 1725](https://aclanthology.org/2026.emnlp-main.1725/).

[Yale Office of Career Strategy's resume-bullet guidance](https://ocs.yale.edu/resources/writing-impactful-resume-bullets/) informs the general resume context. Its broader content quality criteria are not scored as slop here.
