"""Deterministic golden regression tests for check_slop.py (precision/recall per stratum)."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "golden-slop-v1.json"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_slop  # noqa: E402


def test_golden_slop_stratified_precision_and_recall() -> None:
    """Verify deterministic checker precision and recall per locale/stratum without false positives on controls."""
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    cases = fixture["cases"]
    assert len(cases) == sum(fixture["strata"].values())

    tp = fp = tn = fn = 0
    per_locale: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "tn": 0, "fn": 0})

    for case in cases:
        result = check_slop.analyze_text(case["text"])
        actual_slop = not case["expected_strict_pass"]
        predicted_slop = not result["strict_pass"]
        loc = case["locale"]

        if actual_slop and predicted_slop:
            tp += 1
            per_locale[loc]["tp"] += 1
        elif not actual_slop and predicted_slop:
            fp += 1
            per_locale[loc]["fp"] += 1
        elif not actual_slop and not predicted_slop:
            tn += 1
            per_locale[loc]["tn"] += 1
        else:
            fn += 1
            per_locale[loc]["fn"] += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    assert precision == 1.0, f"deterministic checker precision dropped: tp={tp}, fp={fp}"
    assert recall == 1.0, f"deterministic checker recall dropped: tp={tp}, fn={fn}"

    for loc, counts in per_locale.items():
        loc_prec = counts["tp"] / (counts["tp"] + counts["fp"]) if (counts["tp"] + counts["fp"]) > 0 else 0.0
        loc_rec = counts["tp"] / (counts["tp"] + counts["fn"]) if (counts["tp"] + counts["fn"]) > 0 else 0.0
        assert loc_prec == 1.0, f"{loc} precision regression: {counts}"
        assert loc_rec == 1.0, f"{loc} recall regression: {counts}"
