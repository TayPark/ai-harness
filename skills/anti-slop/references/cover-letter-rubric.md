# Cover-letter AI-slop rubric

Score only observable slop patterns in supplied or chat-drafted letter text. Do not score fit, motivation quality, factual completeness, company research, or missing company facts. Flag factual or format defects separately without changing them. Apply the shared scoring anchors in the parent skill. These equal weights are local design choices and total 100.

| Slop pattern | Weight | Full-weight target |
|---|---:|---|
| Company-name substitution | 20 | Existing company-specific language is not a generic template where only the company name could be swapped. Do not penalize a lack of company facts the user did not supply. |
| Stock flattery or motivation | 20 | Existing text avoids interchangeable praise and stock claims about admiration, innovation, culture, or passion. |
| Keyword paraphrase | 20 | Existing text avoids mechanically restating the job description's keywords as claims about the candidate. Do not score whether the candidate is a fit. |
| Resume copy and repetition | 20 | Existing text avoids copied resume bullets and repeated claims without new context. |
| Inflated or repetitive claims | 20 | Existing text avoids unsupported grand language, intensifiers, and repeated statements of enthusiasm or impact. |

The Ask-to-ChatGPT answer supplied qualitative priorities: company/job specificity, evidence-backed fit, and avoiding resume repetition. It supplied no point weights. The equal weights and slop-pattern interpretation above are local design choices, not research-derived weights or a letter quality standard.

Record the exact text location and visible slop span **before** assigning each percentage score (critique-before-score). Run `scripts/check_slop.py --strict` first; calibrate any future weight revisions from stratified EN/KO error analysis rather than ad hoc intuition. If company or role facts were not supplied, do not invent them and do not lower the slop score for their absence. Flag any separate factual concern without changing it.

Keep all letter text in chat. Never create, edit, or save a cover-letter file.

## Research basis

[University of Michigan Career Center's cover-letter resources](https://careercenter.umich.edu/content/cover-letter-resources/) informs the general context of role-specific letters. Its broader content-quality criteria are not scored as slop here.

The broader approach evaluates observable text features rather than inferring authorship from prose style. See [Findings of ACL 2025, paper 1303](https://aclanthology.org/2025.findings-acl.1303/) and [EMNLP 2026, paper 1725](https://aclanthology.org/2026.emnlp-main.1725/).
