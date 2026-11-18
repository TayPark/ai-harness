#!/usr/bin/env python3
"""Deterministic bilingual (English & Korean) AI-slop checker.

Checks prose outside fenced code blocks, inline code, markdown tables, and
speaker-attributed direct quotes for countable AI writing tells.
Zero third-party dependencies (Python 3 stdlib only).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Strip blocks that must remain verbatim (code, tables, attributed quotes).
FENCED_CODE_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
MARKDOWN_TABLE_RE = re.compile(r"^\s*\|.*\|\s*$", re.M)

EN_SPEECH_VERBS = (
    r"said|stated|noted|wrote|explained|reported|added|claimed|argued|remarked|replied"
)
KO_SPEECH_VERBS = (
    r"말했다|밝혔다|전했다|설명했다|지적했다|강조했다|덧붙였다|주장했다|적었다|답했다"
)
EN_QUOTE_BEFORE_RE = re.compile(
    rf'(?:"[^"\n]*"|“[^”\n]*”)(\s*(?:,\s*)?(?:{EN_SPEECH_VERBS})\b)', re.I
)
EN_QUOTE_AFTER_RE = re.compile(
    rf'(\b(?:{EN_SPEECH_VERBS}|according\s+to)\b[^.\n]{{0,50}})(?:"[^"\n]*"|“[^”\n]*”)',
    re.I,
)
KO_QUOTE_RE = re.compile(
    rf'(?:"[^"\n]*"|“[^”\n]*”)(\s*(?:이라고|라고|이라며|라고도)\s*(?:{KO_SPEECH_VERBS}))'
)
KO_ACCORDING_QUOTE_RE = re.compile(
    r'(에\s*따르면[^.\n]{0,40})(?:"[^"\n]*"|“[^”\n]*”)'
)

EN_BUZZWORDS_RE = re.compile(
    r"\b("
    r"delv(?:e|ed|es|ing)|tapestr(?:y|ies)|testament|pivotal|"
    r"underscor(?:e|ed|es|ing)|multifaceted|foster(?:ed|ing|s)?|"
    r"utiliz(?:e|ed|es|ing)|commenc(?:e|ed|es|ing)|paramount|"
    r"groundbreaking|cutting-edge|game-changing|transformative|"
    r"revolutioniz(?:e|ed|es|ing)|seamless(?:ly)?|robust(?:ness)?|"
    r"aforementioned|spearhead(?:ed|ing|s)?|showcas(?:e|ed|es|ing)|"
    r"unprecedented|realms?|beacons?|intricate(?:ly)?|meticulous(?:ly)?|"
    r"bolster(?:ed|ing|s)?|garner(?:ed|ing|s)?|interplay"
    r")\b",
    re.I,
)

EN_FORMULA_RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "en-not-just-x-but-y",
        re.compile(
            r"\b(?:it'?s\s+)?not\s+(?:just|only|merely)\b[^.!?\n]{1,120}?"
            r"(?:[;,]\s*it'?s\b|\bbut\s+also\b)",
            re.I,
        ),
    ),
    ("en-stands-as", re.compile(r"\bstands\s+as\s+an?\b", re.I)),
    ("en-serves-as", re.compile(r"\bserves\s+as\s+an?\b", re.I)),
    ("en-represents-a", re.compile(r"\brepresents\s+an?\b", re.I)),
    ("en-at-its-core", re.compile(r"\bat\s+its\s+core\b", re.I)),
    (
        "en-in-todays-world",
        re.compile(
            r"\bin\s+today'?s\b[^.!?\n]{0,50}?\b(?:world|landscape)\b", re.I
        ),
    ),
    (
        "en-worth-noting",
        re.compile(r"\bit(?:'s|\s+is)\s+worth\s+noting\b", re.I),
    ),
    (
        "en-lets-dive",
        re.compile(r"\blet'?s\s+(?:dive\s+in|unpack)\b", re.I),
    ),
    ("en-let-that-sink-in", re.compile(r"\blet\s+that\s+sink\s+in\b", re.I)),
    ("en-read-that-again", re.compile(r"\bread\s+that\s+again\b", re.I)),
    (
        "en-end-of-the-day",
        re.compile(r"\bat\s+the\s+end\s+of\s+the\s+day\b", re.I),
    ),
]

EN_SCAFFOLD_RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "en-opener-filler",
        re.compile(
            r"^\s*(?:certainly|absolutely|great\s+question)[!,.]",
            re.I | re.M,
        ),
    ),
    ("en-hope-helps", re.compile(r"\bi\s+hope\s+this\s+helps\b", re.I)),
    ("en-in-conclusion", re.compile(r"\bin\s+conclusion\s*,", re.I)),
    ("en-to-summarize", re.compile(r"\bto\s+summarize\s*,", re.I)),
    ("en-let-me-know", re.compile(r"\blet\s+me\s+know\s+if\s+you\b", re.I)),
]

# Korean translation-ese rules: (rule_id, pattern, severity)
KO_TRANSLATIONESE_RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "ko-double-passive",
        re.compile(r"(?:되어지|보여지|만들어지|이루어지|주어지)(?:고|는|며|다|ㄴ|었)"),
        "high",
    ),
    ("ko-passive-suffix-yeojida", re.compile(r"[가-힣]+여진다"), "high"),
    ("ko-e-iss-eoseo", re.compile(r"에\s*있어서"), "high"),
    ("ko-beyond-mere", re.compile(r"단순한\s+[^\n.?!]{1,30}\s+넘어"), "high"),
    (
        "ko-nominal-ending",
        re.compile(r"(?:하는\s*것을\s*제공합니다|를\s*도모합니다|을\s*도모합니다|를\s*제고합니다|을\s*제고합니다)"),
        "high",
    ),
    (
        "ko-unlock-metaphor",
        re.compile(
            r"(?<!스마트폰\s)(?<!화면\s)(?<!계정\s)(?<!기능\s)(?<!비밀번호\s)(?<!기기\s)(?<!아이폰\s)(?<!앱\s)잠금\s?해제"
        ),
        "high",
    ),
    ("ko-informed-decision", re.compile(r"정보에\s*입각한"), "med"),
    ("ko-actionable-insight", re.compile(r"실행\s*가능한\s*통찰"), "high"),
    ("ko-experience-benefit", re.compile(r"혜택을\s*경험"), "high"),
    ("ko-optimize-experience", re.compile(r"경험을\s*최적화"), "high"),
    ("ko-by-passive", re.compile(r"에\s*의해"), "med"),
    ("ko-have-calque", re.compile(r"가지고\s*있"), "med"),
    ("ko-regarding", re.compile(r"와\s*관련하여|과\s*관련하여"), "med"),
    (
        "ko-double-particle",
        re.compile(r"[가-힣]+(?:에서의|에로의|으로의|로의|으로부터의|로부터의)"),
        "med",
    ),
    ("ko-through-calque", re.compile(r"(?:를|을)\s*통해(?:서)?|통하여"), "low"),
]

KO_FORMULA_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("ko-conclusion-phrase", re.compile(r"결론적으로\s*말씀드리자면")),
    ("ko-holistic-summary", re.compile(r"총체적으로\s*살펴보면")),
    ("ko-summarize", re.compile(r"요약하자면")),
    ("ko-implies-much", re.compile(r"시사하는\s*바가\s*크|시사합니다")),
    ("ko-open-horizon", re.compile(r"지평을\s*열|초석을\s*다지")),
    ("ko-cannot-overemphasize", re.compile(r"아무리\s*강조해도\s*지나치지")),
    (
        "ko-cleft-important",
        re.compile(r"(?:중요한|필요한)\s*것은\s+[^\n.?!]{1,40}이다"),
    ),
    (
        "ko-cleft-issue",
        re.compile(r"(?:문제는|핵심은|관건은)\s+[^\n.?!]{1,40}점이다"),
    ),
    ("ko-reverse-reason", re.compile(r"하는\s*이유다(?=[.\s]|$)")),
    ("ko-empty-counterpoint", re.compile(r"과제도\s*남아\s*있다|한계도\s*분명하다")),
    ("ko-time-to-act", re.compile(r"해야\s*할\s*(?:때|시점)입니다")),
    ("ko-three-ways", re.compile(r"크게\s*세\s*가지로")),
    (
        "ko-ai-metaphor",
        re.compile(
            r"논의의\s*무늬|생각을\s*벼리|의미를\s*길어\s*올리|진단은\s*서늘하다|경고는\s*아프다"
        ),
    ),
]

KO_SCAFFOLD_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("ko-great-question", re.compile(r"좋은\s*질문|날카로운\s*지적")),
    ("ko-hope-helps", re.compile(r"도움이\s*되셨기를")),
    ("ko-more-questions", re.compile(r"추가\s*질문이\s*있으시면")),
]

KO_CONNECTIVE_COMMA_RE = re.compile(
    r"(?<![가-힣])(?!(?:창고|재고|사고|신고|보고|원고|경고|공고|광고|참고|유고|최고|잔고),)"
    r"[가-힣]{2,}(?:하고|되고|이고|고|으며|이며|며|지만|면서|아서|어서|해서|여서),"
)

BOLD_BULLET_RE = re.compile(r"^\s*[-*]\s+\*\*.+?\*\*\s*:", re.M)
EMOJI_RE = re.compile(r"[✅🚀💡⚠️📊✨🎯]")


def sanitize_text(text: str) -> str:
    """Remove code blocks, inline code, markdown tables, and attributed quotes."""
    cleaned = FENCED_CODE_RE.sub("", text)
    cleaned = INLINE_CODE_RE.sub("", cleaned)
    cleaned = MARKDOWN_TABLE_RE.sub("", cleaned)
    cleaned = EN_QUOTE_BEFORE_RE.sub(r"\1", cleaned)
    cleaned = EN_QUOTE_AFTER_RE.sub(r"\1", cleaned)
    cleaned = KO_QUOTE_RE.sub(r"\1", cleaned)
    cleaned = KO_ACCORDING_QUOTE_RE.sub(r"\1", cleaned)
    return cleaned


def split_paragraphs(text: str) -> list[str]:
    """Split text into non-empty blank-line-delimited paragraphs."""
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _add_finding(
    findings: list[dict[str, Any]],
    rule_id: str,
    category: str,
    severity: str,
    paragraph_index: int | None,
    quoted_text: str,
) -> None:
    findings.append(
        {
            "rule_id": rule_id,
            "category": category,
            "severity": severity,
            "paragraph_index": paragraph_index,
            "quoted_text": quoted_text.strip(),
        }
    )


def _check_ko_ending_monotony(
    cleaned_text: str, findings: list[dict[str, Any]]
) -> None:
    """Flag consecutive Korean sentences ending in identical boilerplate suffixes."""
    sentences = [
        s.strip()
        for s in re.split(r"[.!?]+(?:\s+|$)", cleaned_text)
        if s.strip()
    ]
    checks = [
        ("ko-monotony-ida", "이다", 4),
        ("ko-monotony-go-itda", "고 있다", 4),
        ("ko-monotony-geotida", "것이다", 3),
    ]
    for rule_id, suffix, threshold in checks:
        streak = 0
        sample: list[str] = []
        for sent in sentences:
            if sent.endswith(suffix):
                streak += 1
                sample.append(sent)
                if streak == threshold:
                    _add_finding(
                        findings,
                        rule_id,
                        "ko-ending-monotony",
                        "high",
                        None,
                        f"{threshold}+ consecutive '...{suffix}.' sentences",
                    )
            else:
                streak = 0
                sample = []


def analyze_text(text: str) -> dict[str, Any]:
    """Scan text and return deterministic findings, summary, and strict pass status."""
    cleaned = sanitize_text(text)
    paragraphs = split_paragraphs(cleaned)
    findings: list[dict[str, Any]] = []

    for idx, para in enumerate(paragraphs):
        for match in EN_BUZZWORDS_RE.finditer(para):
            _add_finding(
                findings,
                "en-buzzword",
                "en-buzzwords",
                "low",
                idx,
                match.group(0),
            )

        for rule_id, pattern in EN_FORMULA_RULES:
            for match in pattern.finditer(para):
                _add_finding(
                    findings, rule_id, "en-formulas", "high", idx, match.group(0)
                )

        for rule_id, pattern in EN_SCAFFOLD_RULES:
            for match in pattern.finditer(para):
                _add_finding(
                    findings,
                    rule_id,
                    "en-scaffolding",
                    "high",
                    idx,
                    match.group(0),
                )

        for rule_id, pattern, severity in KO_TRANSLATIONESE_RULES:
            for match in pattern.finditer(para):
                _add_finding(
                    findings,
                    rule_id,
                    "ko-translationese",
                    severity,
                    idx,
                    match.group(0),
                )

        for rule_id, pattern in KO_FORMULA_RULES:
            for match in pattern.finditer(para):
                _add_finding(
                    findings, rule_id, "ko-formulas", "high", idx, match.group(0)
                )

        for rule_id, pattern in KO_SCAFFOLD_RULES:
            for match in pattern.finditer(para):
                _add_finding(
                    findings,
                    rule_id,
                    "ko-scaffolding",
                    "high",
                    idx,
                    match.group(0),
                )

    conn_commas = KO_CONNECTIVE_COMMA_RE.findall(cleaned)
    if len(conn_commas) >= 3:
        _add_finding(
            findings,
            "ko-connective-comma",
            "ko-connective-comma",
            "high",
            None,
            f"{len(conn_commas)}x: {', '.join(conn_commas[:5])}",
        )

    _check_ko_ending_monotony(cleaned, findings)

    em_dash_count = cleaned.count("—")
    if em_dash_count > 2:
        _add_finding(
            findings,
            "em-dash-overuse",
            "formatting-tells",
            "high",
            None,
            f"{em_dash_count} em dashes (max 2)",
        )

    bold_bullets = BOLD_BULLET_RE.findall(cleaned)
    if len(bold_bullets) >= 3:
        _add_finding(
            findings,
            "bold-bullet-soup",
            "formatting-tells",
            "high",
            None,
            f"{len(bold_bullets)} bold-lead bullets",
        )

    emojis = EMOJI_RE.findall(cleaned)
    if emojis:
        _add_finding(
            findings,
            "decorative-emoji",
            "formatting-tells",
            "high",
            None,
            "".join(emojis),
        )

    summary: dict[str, int] = {}
    for item in findings:
        cat = item["category"]
        summary[cat] = summary.get(cat, 0) + 1

    strict_failed = any(item["severity"] == "high" for item in findings)
    if not strict_failed:
        by_para: dict[int, list[dict[str, Any]]] = {}
        for item in findings:
            p_idx = item["paragraph_index"]
            if p_idx is not None:
                by_para.setdefault(p_idx, []).append(item)
        for items in by_para.values():
            med_count = sum(1 for x in items if x["severity"] == "med")
            low_count = sum(1 for x in items if x["severity"] == "low")
            if med_count >= 2 or (med_count >= 1 and len(items) >= 2) or low_count >= 3:
                strict_failed = True
                break

    return {
        "findings": findings,
        "summary": summary,
        "total_findings": len(findings),
        "strict_pass": not strict_failed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check English and Korean prose for deterministic AI-slop tells."
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Path to input text/markdown file (defaults to stdin).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if high-severity tells or paragraph co-occurrence thresholds trigger.",
    )
    args = parser.parse_args(argv)

    if args.file is not None:
        text = args.file.read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    result = analyze_text(text)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if result["strict_pass"] else "FAIL"
        print(f"STATUS: {status} (total findings: {result['total_findings']})")
        for item in result["findings"]:
            loc = (
                f"p{item['paragraph_index'] + 1}"
                if item["paragraph_index"] is not None
                else "doc"
            )
            print(
                f"  [{item['severity']}] {item['category']} ({item['rule_id']}) @ {loc}: "
                f"{item['quoted_text']}"
            )

    if args.strict and not result["strict_pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
