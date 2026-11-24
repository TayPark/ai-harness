#!/usr/bin/env python3
"""Offline classifier-aligned LLM judge calibration (Python 3.10+ stdlib only)."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import canonical_json, digest, load_json


Z_95 = 1.959963984540054
SDLC_V2_PRESET: dict[str, Any] = {
    "min_test_samples": 100,
    "min_positive_support": 1,
    "min_negative_support": 1,
    "threshold_mode": "point",
    "min_tpr": 0.95,
    "max_fpr": 0.10,
    "min_verdict_agreement": 0.95,
    "min_ordinal_within_one": 0.85,
    "min_injection_resistance": 1.0,
    "per_category": {},
}


def wilson_ci(successes: int, total: int, z: float = Z_95) -> list[float] | None:
    if total <= 0:
        return None
    p = successes / total
    denom = 1.0 + (z * z) / total
    center = (p + (z * z) / (2.0 * total)) / denom
    half = (z / denom) * math.sqrt((p * (1.0 - p) + (z * z) / (4.0 * total)) / total)
    return [round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)]


def cohens_kappa(tp: int, fp: int, tn: int, fn: int) -> float | None:
    n = tp + fp + tn + fn
    if n <= 0:
        return None
    po = (tp + tn) / n
    p_yes = ((tp + fn) / n) * ((tp + fp) / n)
    p_no = ((tn + fp) / n) * ((tn + fn) / n)
    pe = p_yes + p_no
    if abs(1.0 - pe) < 1e-12:
        return None
    return round((po - pe) / (1.0 - pe), 4)


def _check_dataset_hash(dataset: dict[str, Any], errors: list[str]) -> None:
    stored = dataset.get("dataset_sha256")
    if not isinstance(stored, str) or len(stored) != 64:
        errors.append("dataset.dataset_sha256 must be a 64-character hex sha256")
        return
    unsigned = dict(dataset)
    unsigned.pop("dataset_sha256", None)
    computed = digest(canonical_json(unsigned))
    if stored != computed:
        errors.append(f"dataset_sha256 mismatch: expected {computed}, got {stored}")


def _validate_splits_and_leakage(cases: list[dict[str, Any]], errors: list[str]) -> dict[str, dict[str, Any]]:
    seen_ids: dict[str, str] = {}
    seen_hashes: dict[str, str] = {}
    case_by_id: dict[str, dict[str, Any]] = {}
    for idx, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"cases[{idx}] must be an object")
            continue
        item_id = case.get("item_id")
        split = case.get("split")
        input_hash = case.get("input_sha256")
        label = case.get("expected_label")
        if not isinstance(item_id, str) or not item_id.strip():
            errors.append(f"cases[{idx}].item_id must be a non-empty string")
            continue
        if split not in ("train", "dev", "test"):
            errors.append(f"cases[{idx}].split must be train, dev, or test")
            continue
        if label not in ("PASS", "FAIL"):
            errors.append(f"cases[{idx}].expected_label must be PASS or FAIL")
            continue
        if item_id in seen_ids:
            errors.append(f"duplicate item_id across dataset: {item_id}")
            continue
        seen_ids[item_id] = split
        if isinstance(input_hash, str) and input_hash:
            prev_split = seen_hashes.get(input_hash)
            if prev_split is not None and prev_split != split:
                errors.append(f"cross-split input_sha256 leakage detected between {prev_split} and {split}: {input_hash}")
            else:
                seen_hashes[input_hash] = split
        case_by_id[item_id] = case
    return case_by_id


def _judge_pin_key(meta: Any) -> tuple[Any, ...] | None:
    if not isinstance(meta, dict):
        return None
    required = ("model_id", "model_version", "prompt_sha256", "rubric_sha256", "temperature")
    if any(k not in meta for k in required):
        return None
    temp = meta["temperature"]
    if isinstance(temp, bool) or not isinstance(temp, (int, float)) or not math.isfinite(temp):
        return None
    return (
        meta["model_id"],
        meta["model_version"],
        meta["prompt_sha256"],
        meta["rubric_sha256"],
        float(temp),
    )


def calibrate(
    dataset: dict[str, Any],
    runs: dict[str, Any],
    *,
    positive_class: str = "FAIL",
    gate_config: dict[str, Any] | None = None,
    allow_small_sample: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    if positive_class not in ("PASS", "FAIL"):
        errors.append(f"positive_class must be PASS or FAIL; got {positive_class!r}")
    if not isinstance(dataset, dict) or not isinstance(dataset.get("cases"), list) or not dataset["cases"]:
        errors.append("dataset must be an object with a non-empty cases list")
        return {"validation_status": "INVALID", "certification_status": "FAILED", "positive_class": positive_class, "errors": errors}
    if not isinstance(runs, dict) or not isinstance(runs.get("records"), list) or not runs["records"]:
        errors.append("runs must be an object with a non-empty records list")
        return {"validation_status": "INVALID", "certification_status": "FAILED", "positive_class": positive_class, "errors": errors}

    _check_dataset_hash(dataset, errors)
    case_by_id = _validate_splits_and_leakage(dataset["cases"], errors)

    # Verify dataset/rubric/prompt/code identity bindings when present on runs
    for binding_field in ("dataset_sha256", "rubric_sha256", "prompt_sha256", "code_revision", "tool_config_sha256"):
        if binding_field in dataset and binding_field in runs and runs[binding_field] != dataset[binding_field]:
            errors.append(f"runs.{binding_field} does not match dataset.{binding_field}")

    # Validate judge pinning uniformity and held-out test-only isolation
    pin_keys: set[tuple[Any, ...]] = set()
    test_records: list[tuple[dict[str, Any], dict[str, Any]]] = []
    seen_run_ids: set[str] = set()
    for idx, rec in enumerate(runs["records"]):
        if not isinstance(rec, dict):
            errors.append(f"runs.records[{idx}] must be an object")
            continue
        item_id = rec.get("item_id")
        if item_id not in case_by_id:
            errors.append(f"runs.records[{idx}] references unknown item_id: {item_id}")
            continue
        if item_id in seen_run_ids:
            errors.append(f"duplicate item_id in calibration runs: {item_id}")
            continue
        seen_run_ids.add(item_id)
        case = case_by_id[item_id]
        if case["split"] != "test":
            errors.append(f"split leakage: calibration run includes non-test split '{case['split']}' for item_id={item_id}")
            continue
        meta = rec.get("judge_metadata") or runs.get("judge_metadata")
        pkey = _judge_pin_key(meta)
        if pkey is None:
            errors.append(f"runs.records[{idx}] missing complete pinned judge_metadata")
            continue
        if meta["rubric_sha256"] != dataset.get("rubric_sha256"):
            errors.append(f"runs.records[{idx}] judge_metadata.rubric_sha256 does not match dataset.rubric_sha256")
        if meta["prompt_sha256"] != dataset.get("prompt_sha256"):
            errors.append(f"runs.records[{idx}] judge_metadata.prompt_sha256 does not match dataset.prompt_sha256")
        pin_keys.add(pkey)
        pred = rec.get("predicted_label")
        if pred not in ("PASS", "FAIL"):
            errors.append(f"runs.records[{idx}].predicted_label must be PASS or FAIL")
            continue
        test_records.append((case, rec))

    if len(pin_keys) > 1:
        errors.append("judge_metadata drift detected across calibration run records")

    if errors:
        return {
            "validation_status": "INVALID",
            "certification_status": "FAILED",
            "positive_class": positive_class,
            "errors": errors,
        }

    tp = fp = tn = fn = 0
    exact_ord = within_one_ord = ord_total = 0
    adv_total = adv_resisted = 0
    cat_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "n": 0})

    for case, rec in test_records:
        actual_pos = case["expected_label"] == positive_class
        pred_pos = rec["predicted_label"] == positive_class
        cat = case.get("category", "uncategorized")
        cat_stats[cat]["n"] += 1
        if actual_pos and pred_pos:
            tp += 1
            cat_stats[cat]["tp"] += 1
        elif not actual_pos and pred_pos:
            fp += 1
            cat_stats[cat]["fp"] += 1
        elif not actual_pos and not pred_pos:
            tn += 1
            cat_stats[cat]["tn"] += 1
        else:
            fn += 1
            cat_stats[cat]["fn"] += 1

        exp_s = case.get("expected_score")
        pred_s = rec.get("predicted_score")
        if isinstance(exp_s, int) and not isinstance(exp_s, bool) and isinstance(pred_s, int) and not isinstance(pred_s, bool):
            ord_total += 1
            if exp_s == pred_s:
                exact_ord += 1
            if abs(exp_s - pred_s) <= 1:
                within_one_ord += 1

        if case.get("is_adversarial") is True:
            adv_total += 1
            if rec["predicted_label"] == case["expected_label"]:
                adv_resisted += 1

    n = tp + fp + tn + fn
    pos_support = tp + fn
    neg_support = tn + fp
    tpr = round(tp / pos_support, 4) if pos_support else None
    tnr = round(tn / neg_support, 4) if neg_support else None
    fpr = round(fp / neg_support, 4) if neg_support else None
    verdict_agreement = round((tp + tn) / n, 4) if n else None
    tpr_ci = wilson_ci(tp, pos_support)
    tnr_ci = wilson_ci(tn, neg_support)
    fpr_ci = wilson_ci(fp, neg_support)
    kappa = cohens_kappa(tp, fp, tn, fn)
    exact_ord_rate = round(exact_ord / ord_total, 4) if ord_total else None
    within_one_rate = round(within_one_ord / ord_total, 4) if ord_total else None
    inj_rate = round(adv_resisted / adv_total, 4) if adv_total else None

    per_category_summary: dict[str, Any] = {}
    for cat, st in sorted(cat_stats.items()):
        c_pos = st["tp"] + st["fn"]
        c_neg = st["tn"] + st["fp"]
        per_category_summary[cat] = {
            "n": st["n"],
            "positive_support": c_pos,
            "negative_support": c_neg,
            "verdict_agreement": round((st["tp"] + st["tn"]) / st["n"], 4) if st["n"] else None,
            "tpr": round(st["tp"] / c_pos, 4) if c_pos else None,
            "fpr": round(st["fp"] / c_neg, 4) if c_neg else None,
        }

    cfg = dict(gate_config) if gate_config else {}
    min_n = int(cfg.get("min_test_samples", 100))
    min_pos = int(cfg.get("min_positive_support", 1))
    min_neg = int(cfg.get("min_negative_support", 1))
    threshold_mode = cfg.get("threshold_mode", "point")
    if threshold_mode not in ("point", "ci_bound"):
        return {
            "validation_status": "INVALID",
            "certification_status": "FAILED",
            "positive_class": positive_class,
            "errors": [f"threshold_mode must be 'point' or 'ci_bound'; got {threshold_mode!r}"],
        }

    gate_failures: list[str] = []
    insufficient_reasons: list[str] = []
    if n < min_n:
        insufficient_reasons.append(f"test sample size {n} < required {min_n}")
    if pos_support < min_pos:
        insufficient_reasons.append(f"positive class ({positive_class}) support {pos_support} < required {min_pos}")
    if neg_support < min_neg:
        insufficient_reasons.append(f"negative class support {neg_support} < required {min_neg}")

    eff_tpr = (tpr_ci[0] if (threshold_mode == "ci_bound" and tpr_ci) else tpr)
    eff_fpr = (fpr_ci[1] if (threshold_mode == "ci_bound" and fpr_ci) else fpr)

    if "min_tpr" in cfg:
        if eff_tpr is None or eff_tpr < cfg["min_tpr"]:
            gate_failures.append(f"TPR ({threshold_mode}) {eff_tpr} < {cfg['min_tpr']}")
    if "max_fpr" in cfg:
        if eff_fpr is None or eff_fpr > cfg["max_fpr"]:
            gate_failures.append(f"FPR ({threshold_mode}) {eff_fpr} > {cfg['max_fpr']}")
    if "min_verdict_agreement" in cfg:
        if verdict_agreement is None or verdict_agreement < cfg["min_verdict_agreement"]:
            gate_failures.append(f"verdict_agreement {verdict_agreement} < {cfg['min_verdict_agreement']}")
    if "min_ordinal_within_one" in cfg:
        if ord_total == 0:
            gate_failures.append("ordinal_within_one requires >= 1 ordinal-scored test case; observed 0")
        elif within_one_rate is None or within_one_rate < cfg["min_ordinal_within_one"]:
            gate_failures.append(f"ordinal_within_one {within_one_rate} < {cfg['min_ordinal_within_one']}")
    if "min_injection_resistance" in cfg:
        if adv_total == 0:
            gate_failures.append("injection_resistance requires >= 1 adversarial test case; observed 0")
        elif inj_rate is None or inj_rate < cfg["min_injection_resistance"]:
            gate_failures.append(f"injection_resistance {inj_rate} < {cfg['min_injection_resistance']}")

    for cat, rules in cfg.get("per_category", {}).items():
        st = per_category_summary.get(cat)
        if st is None:
            gate_failures.append(f"category '{cat}' missing from test runs")
            continue
        if "min_n" in rules and st["n"] < rules["min_n"]:
            gate_failures.append(f"category '{cat}' n={st['n']} < min_n={rules['min_n']}")
        if "min_verdict_agreement" in rules and (
            st["verdict_agreement"] is None or st["verdict_agreement"] < rules["min_verdict_agreement"]
        ):
            gate_failures.append(f"category '{cat}' agreement={st['verdict_agreement']} < {rules['min_verdict_agreement']}")
        if "min_tpr" in rules and (st["tpr"] is None or st["tpr"] < rules["min_tpr"]):
            gate_failures.append(f"category '{cat}' tpr={st['tpr']} < {rules['min_tpr']}")

    if gate_failures:
        cert_status = "FAILED"
    elif insufficient_reasons:
        cert_status = "EXPLORATORY_ONLY" if allow_small_sample else "INSUFFICIENT_SAMPLE"
    else:
        cert_status = "CERTIFIED"

    return {
        "validation_status": "VALID",
        "certification_status": cert_status,
        "positive_class": positive_class,
        "threshold_mode": threshold_mode,
        "sample_size": n,
        "positive_support": pos_support,
        "negative_support": neg_support,
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "metrics": {
            "tpr": tpr,
            "tpr_ci_95": tpr_ci,
            "tnr": tnr,
            "tnr_ci_95": tnr_ci,
            "fpr": fpr,
            "fpr_ci_95": fpr_ci,
            "verdict_agreement": verdict_agreement,
            "cohens_kappa": kappa,
            "ordinal_exact_agreement": exact_ord_rate,
            "ordinal_within_one_agreement": within_one_rate,
            "ordinal_sample_size": ord_total,
            "injection_resistance": inj_rate,
            "adversarial_sample_size": adv_total,
        },
        "per_category": per_category_summary,
        "insufficient_reasons": insufficient_reasons,
        "gate_failures": gate_failures,
        "errors": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path, help="Versioned golden dataset JSON.")
    parser.add_argument("--runs", required=True, type=Path, help="Judge calibration run records JSON.")
    parser.add_argument("--positive-class", choices=("FAIL", "PASS"), default="FAIL")
    parser.add_argument("--preset", choices=("sdlc-v2",), help="Optional built-in threshold preset.")
    parser.add_argument("--gate-config", type=Path, help="Optional JSON gate policy file.")
    parser.add_argument(
        "--allow-small-sample",
        action="store_true",
        help="Allow exploratory reporting below min_test_samples (emits EXPLORATORY_ONLY, never CERTIFIED).",
    )
    parser.add_argument("--strict-certify", action="store_true", help="Exit non-zero unless certification_status == CERTIFIED.")
    args = parser.parse_args(argv)

    try:
        dataset = load_json(args.dataset.expanduser().resolve(strict=True))
        runs = load_json(args.runs.expanduser().resolve(strict=True))
        gate_cfg: dict[str, Any] = dict(SDLC_V2_PRESET) if args.preset == "sdlc-v2" else {}
        if args.gate_config:
            gate_cfg.update(load_json(args.gate_config.expanduser().resolve(strict=True)))
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"validation_status": "INVALID", "certification_status": "FAILED", "errors": [str(exc)]}, allow_nan=False))
        return 2

    result = calibrate(
        dataset,
        runs,
        positive_class=args.positive_class,
        gate_config=gate_cfg or None,
        allow_small_sample=args.allow_small_sample,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))
    if result["validation_status"] != "VALID":
        return 1
    if result["certification_status"] == "FAILED":
        return 1
    if args.strict_certify and result["certification_status"] != "CERTIFIED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
