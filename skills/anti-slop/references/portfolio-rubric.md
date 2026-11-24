# Portfolio AI-slop rubric

Score only observable slop patterns in the supplied portfolio text and captions. Do not score completeness, technical quality, factual accuracy, ownership sufficiency, project fit, or absence or quality of verification. Flag factual or format defects separately without changing them. Apply the shared scoring anchors in the parent skill. Weights total 100.

| Slop pattern | Weight | Full-weight target |
|---|---:|---|
| Generic problem framing | 20 | Existing problem statements avoid boilerplate such as “needed a scalable solution” when it adds no detail to the stated problem. |
| Ownership boilerplate | 20 | Existing text avoids vague filler such as “played a key role” and “was deeply involved.” Do not judge whether ownership details are complete. |
| Formulaic decision language | 20 | Existing reasoning avoids empty phrases such as “after considering various options” when no concrete meaning follows. Do not grade the quality or presence of decisions. |
| Inflated implementation language | 20 | Existing implementation descriptions avoid unsupported superlatives or stock claims such as “seamlessly integrated,” “robust,” or “highly scalable.” Do not assess technical correctness. |
| Generic verification or status claims | 20 | Existing statements avoid stock certainty such as “comprehensive testing proved reliability” or inflated wording that makes a proposal sound proven. A concise table or overview may state a concrete completion status that the detailed case later explains. Score the wording pattern only; flag actual status or verification errors separately. Do not grade whether verification exists or is sufficient. |

The Ask-to-ChatGPT answer supplied qualitative priorities: problem, ownership, decisions/trade-offs, implementation, and verification. It supplied no point weights. The equal weights and slop-pattern interpretation above are local design choices, not research-derived weights or a portfolio quality standard.

Record the text or caption location and visible slop pattern for each score. A missing problem detail, ownership detail, decision, implementation detail, verification, or result is not slop and does not lower this score. A diagram alone does not establish facts; flag any evidence concern separately.

## Research basis

The broader approach evaluates observable text features rather than inferring authorship from prose style. See [Findings of ACL 2025, paper 1303](https://aclanthology.org/2025.findings-acl.1303/) and [EMNLP 2026, paper 1725](https://aclanthology.org/2026.emnlp-main.1725/).
