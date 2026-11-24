#!/usr/bin/env python3
"""Offline statistical run comparator: pass@k/pass^k, swap pairwise, bootstrap CI, McNemar, efficiency (stdlib only)."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import load_json


def pass_at_k(n: int, c: int, k: int) -> float | None:
    if n < k or k <= 0 or c < 0 or c > n:
        return None
    if n - c < k:
        return 1.0
    return round(1.0 - (math.comb(n - c, k) / math.comb(n, k)), 6)


def pass_pow_k(n: int, c: int, k: int) -> float | None:
    if n < k or k <= 0 or c < 0 or c > n:
        return None
    if c < k:
        return 0.0
    return round(math.comb(c, k) / math.comb(n, k), 6)


def nearest_rank_percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, math.ceil((pct / 100.0) * len(ordered)) - 1))
    return round(ordered[idx], 4)


def exact_mcnemar_two_sided(b: int, c: int) -> float | None:
    total = b + c
    if total == 0:
        return 1.0
    low = min(b, c)
    tail = sum(math.comb(total, i) for i in range(low + 1)) / (2 ** total)
    return round(min(1.0, 2.0 * tail), 6)


def paired_bootstrap_ci(
    deltas_by_cluster: list[list[float]],
    *,
    iterations: int = 10_000,
    seed: int = 42,
) -> tuple[float, list[float]] | None:
    if not deltas_by_cluster:
        return None
    all_vals = [v for cluster in deltas_by_cluster for v in cluster]
    if not all_vals:
        return None
    observed = sum(all_vals) / len(all_vals)
    if len(deltas_by_cluster) < 2:
        return round(observed, 6), [round(observed, 6), round(observed, 6)]
    rng = random.Random(seed)
    n_clusters = len(deltas_by_cluster)
    samples: list[float] = []
    for _ in range(iterations):
        s = 0.0
        cnt = 0
        for _ in range(n_clusters):
            cluster = deltas_by_cluster[rng.randrange(n_clusters)]
            s += sum(cluster)
            cnt += len(cluster)
        samples.append(s / cnt)
    samples.sort()
    lo_idx = max(0, int(0.025 * iterations))
    hi_idx = min(iterations - 1, int(0.975 * iterations))
    return round(observed, 6), [round(samples[lo_idx], 6), round(samples[hi_idx], 6)]


def paired_sign_flip_p_value(
    cluster_means: list[float],
    *,
    iterations: int = 10_000,
    seed: int = 42,
) -> float | None:
    if not cluster_means:
        return None
    observed = abs(sum(cluster_means) / len(cluster_means))
    if observed == 0.0:
        return 1.0
    rng = random.Random(seed + 1)
    n = len(cluster_means)
    extreme = 0
    for _ in range(iterations):
        flipped = sum(val if rng.getrandbits(1) else -val for val in cluster_means) / n
        if abs(flipped) >= observed - 1e-12:
            extreme += 1
    return round((extreme + 1) / (iterations + 1), 6)


def pearson_corr(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 2 or n != len(ys):
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0.0 or dy == 0.0:
        return None
    return round(num / (dx * dy), 4)


def summarize_efficiency(records: list[dict[str, Any]]) -> dict[str, Any]:
    latencies: list[float] = []
    tokens: list[float] = []
    total_cost = 0.0
    has_cost = False
    successful_tasks = 0
    for rec in records:
        if rec.get("passed") is True:
            successful_tasks += 1
        lat = rec.get("latency_ms")
        if isinstance(lat, (int, float)) and not isinstance(lat, bool) and math.isfinite(lat):
            latencies.append(float(lat))
        tok = rec.get("tokens")
        if isinstance(tok, (int, float)) and not isinstance(tok, bool) and math.isfinite(tok):
            tokens.append(float(tok))
        cost = rec.get("cost_usd")
        if isinstance(cost, (int, float)) and not isinstance(cost, bool) and math.isfinite(cost):
            total_cost += float(cost)
            has_cost = True
    cost_status = "OK"
    cost_per_success: float | None = None
    if has_cost:
        if successful_tasks > 0:
            cost_per_success = round(total_cost / successful_tasks, 6)
        else:
            cost_status = "NO_SUCCESSFUL_TASKS"
    else:
        cost_status = "COST_UNAVAILABLE"
    return {
        "total_runs": len(records),
        "successful_tasks": successful_tasks,
        "mean_tokens_per_request": round(sum(tokens) / len(tokens), 2) if tokens else None,
        "latency_p50_ms": nearest_rank_percentile(latencies, 50.0),
        "latency_p95_ms": nearest_rank_percentile(latencies, 95.0),
        "percentile_method": "nearest_rank",
        "total_cost_usd": round(total_cost, 6) if has_cost else None,
        "cost_per_successful_task": cost_per_success,
        "cost_status": cost_status,
    }


def summarize_reliability(records: list[dict[str, Any]], k: int) -> dict[str, Any]:
    by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
    zero_temp_noticed = False
    missing_trials = 0
    observed_failures = 0
    for rec in records:
        by_item[rec["item_id"]].append(rec)
        temp = rec.get("temperature")
        if isinstance(temp, (int, float)) and not isinstance(temp, bool) and float(temp) == 0.0:
            zero_temp_noticed = True
        if rec.get("status") == "MISSING":
            missing_trials += 1
        elif rec.get("passed") is False:
            observed_failures += 1

    pass_at_vals: list[float] = []
    pass_pow_vals: list[float] = []
    incomplete_items: list[str] = []
    for item_id, trials in sorted(by_item.items()):
        valid_trials = [t for t in trials if t.get("status") != "MISSING"]
        n = len(valid_trials)
        if n < k:
            incomplete_items.append(item_id)
            continue
        c = sum(1 for t in valid_trials if t.get("passed") is True)
        p_at = pass_at_k(n, c, k)
        p_pow = pass_pow_k(n, c, k)
        if p_at is not None:
            pass_at_vals.append(p_at)
        if p_pow is not None:
            pass_pow_vals.append(p_pow)

    notices: list[str] = []
    if zero_temp_noticed:
        notices.append("temperature=0 observed; verify whether production runs deterministically at temperature 0")
    if incomplete_items:
        notices.append(f"{len(incomplete_items)} item(s) had fewer than k={k} valid trials and were excluded from pass@k/pass^k")

    return {
        "k": k,
        "items_total": len(by_item),
        "items_evaluated": len(pass_at_vals),
        "incomplete_items": incomplete_items,
        "observed_failures": observed_failures,
        "missing_trials": missing_trials,
        "mean_pass_at_k": round(sum(pass_at_vals) / len(pass_at_vals), 4) if pass_at_vals else None,
        "mean_pass_pow_k": round(sum(pass_pow_vals) / len(pass_pow_vals), 4) if pass_pow_vals else None,
        "notices": notices,
    }


def evaluate_pairwise(
    pairs: list[dict[str, Any]],
    *,
    max_inconsistency_rate: float = 0.15,
    max_chars: int | None = None,
) -> dict[str, Any]:
    wins_cand = wins_base = ties = inconsistent = missing = 0
    budget_violations: list[str] = []
    len_deltas: list[float] = []
    pref_scores: list[float] = []

    for entry in pairs:
        item_id = entry.get("item_id", "<unknown>")
        ab = entry.get("order_ab")
        ba = entry.get("order_ba")
        if ab not in ("A", "B", "TIE") or ba not in ("A", "B", "TIE"):
            missing += 1
            continue
        # In order_ab: A=baseline, B=candidate. In order_ba: A=candidate, B=baseline.
        map_ab = {"A": "BASELINE", "B": "CANDIDATE", "TIE": "TIE"}[ab]
        map_ba = {"A": "CANDIDATE", "B": "BASELINE", "TIE": "TIE"}[ba]
        if map_ab != map_ba:
            inconsistent += 1
        elif map_ab == "CANDIDATE":
            wins_cand += 1
        elif map_ab == "BASELINE":
            wins_base += 1
        else:
            ties += 1

        b_len = entry.get("baseline_chars")
        c_len = entry.get("candidate_chars")
        if isinstance(b_len, int) and isinstance(c_len, int):
            if max_chars is not None and (b_len > max_chars or c_len > max_chars):
                budget_violations.append(item_id)
            if map_ab == map_ba:
                len_deltas.append(float(c_len - b_len))
                pref_scores.append(1.0 if map_ab == "CANDIDATE" else (-1.0 if map_ab == "BASELINE" else 0.0))

    total = len(pairs)
    concordant = wins_cand + wins_base + ties
    inconsistency_rate = round(inconsistent / total, 4) if total else None
    return {
        "total_items": total,
        "concordant_items": concordant,
        "candidate_wins": wins_cand,
        "baseline_wins": wins_base,
        "ties": ties,
        "position_inconsistent": inconsistent,
        "missing_orders": missing,
        "inconsistency_rate": inconsistency_rate,
        "inconsistency_threshold": max_inconsistency_rate,
        "inconsistency_exceeded": (inconsistency_rate is not None and inconsistency_rate > max_inconsistency_rate),
        "full_cohort_candidate_win_rate": round(wins_cand / total, 4) if total else None,
        "concordant_candidate_win_rate": round(wins_cand / concordant, 4) if concordant else None,
        "length_delta_pref_correlation_diagnostic": pearson_corr(len_deltas, pref_scores),
        "max_chars": max_chars,
        "length_budget_violations": budget_violations,
    }


def compare(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    *,
    k: int = 1,
    alpha: float = 0.05,
    iterations: int = 10_000,
    seed: int = 42,
    pairwise_records: list[dict[str, Any]] | None = None,
    max_inconsistency_rate: float = 0.15,
    max_chars: int | None = None,
    gate_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(baseline, dict) or not isinstance(baseline.get("records"), list) or not baseline["records"]:
        errors.append("baseline must be an object with a non-empty records list")
    if not isinstance(candidate, dict) or not isinstance(candidate.get("records"), list) or not candidate["records"]:
        errors.append("candidate must be an object with a non-empty records list")
    if errors:
        return {"validation_status": "INVALID", "comparison_verdict": "INVALID", "errors": errors}

    base_recs: list[dict[str, Any]] = baseline["records"]
    cand_recs: list[dict[str, Any]] = candidate["records"]

    # Group by item_id for paired stats (average across repeated runs per item_id)
    base_by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
    cand_by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in base_recs:
        if not isinstance(rec, dict) or not isinstance(rec.get("item_id"), str):
            errors.append("every baseline record requires string item_id")
            continue
        base_by_item[rec["item_id"]].append(rec)
    for rec in cand_recs:
        if not isinstance(rec, dict) or not isinstance(rec.get("item_id"), str):
            errors.append("every candidate record requires string item_id")
            continue
        cand_by_item[rec["item_id"]].append(rec)
    if errors:
        return {"validation_status": "INVALID", "comparison_verdict": "INVALID", "errors": errors}

    matched_ids = sorted(set(base_by_item) & set(cand_by_item))
    unmatched_base = sorted(set(base_by_item) - set(cand_by_item))
    unmatched_cand = sorted(set(cand_by_item) - set(base_by_item))

    # Cluster-aware paired deltas & binary McNemar counts
    deltas_by_cluster: dict[str, list[float]] = defaultdict(list)
    mcnemar_b = 0  # baseline pass, candidate fail
    mcnemar_c = 0  # baseline fail, candidate pass
    cat_base: dict[str, list[float]] = defaultdict(list)
    cat_cand: dict[str, list[float]] = defaultdict(list)

    for item_id in matched_ids:
        b_valid = [r for r in base_by_item[item_id] if r.get("status") != "MISSING"]
        c_valid = [r for r in cand_by_item[item_id] if r.get("status") != "MISSING"]
        if not b_valid or not c_valid:
            continue
        b_rate = sum(1.0 for r in b_valid if r.get("passed") is True) / len(b_valid)
        c_rate = sum(1.0 for r in c_valid if r.get("passed") is True) / len(c_valid)
        b_score_vals = [float(r["score"]) for r in b_valid if isinstance(r.get("score"), (int, float)) and not isinstance(r.get("score"), bool)]
        c_score_vals = [float(r["score"]) for r in c_valid if isinstance(r.get("score"), (int, float)) and not isinstance(r.get("score"), bool)]
        delta = (sum(c_score_vals) / len(c_score_vals) - sum(b_score_vals) / len(b_score_vals)) if (b_score_vals and c_score_vals) else (c_rate - b_rate)
        cluster_id = c_valid[0].get("cluster_id") or b_valid[0].get("cluster_id") or item_id
        deltas_by_cluster[cluster_id].append(delta)
        cat = c_valid[0].get("category") or b_valid[0].get("category") or "uncategorized"
        cat_base[cat].append(b_rate)
        cat_cand[cat].append(c_rate)
        if len(b_valid) == 1 and len(c_valid) == 1:
            bp = b_valid[0].get("passed") is True
            cp = c_valid[0].get("passed") is True
            if bp and not cp:
                mcnemar_b += 1
            elif not bp and cp:
                mcnemar_c += 1

    cluster_lists = [deltas_by_cluster[cid] for cid in sorted(deltas_by_cluster)]
    cluster_means = [sum(vals) / len(vals) for vals in cluster_lists if vals]
    boot = paired_bootstrap_ci(cluster_lists, iterations=iterations, seed=seed)
    perm_p = paired_sign_flip_p_value(cluster_means, iterations=iterations, seed=seed) if len(cluster_means) >= 2 else None
    mcnemar_p = exact_mcnemar_two_sided(mcnemar_b, mcnemar_c) if (mcnemar_b + mcnemar_c) > 0 else None

    mean_delta = boot[0] if boot else None
    ci_95 = boot[1] if boot else None
    if len(cluster_means) < 2 or ci_95 is None:
        stat_verdict = "DESCRIPTIVE_ONLY"
    elif ci_95[0] > 0 and (perm_p is None or perm_p < alpha):
        stat_verdict = "STATISTICAL_WIN"
    elif ci_95[1] < 0 and (perm_p is None or perm_p < alpha):
        stat_verdict = "STATISTICAL_REGRESSION"
    else:
        stat_verdict = "NO_STATISTICAL_WIN"

    per_category: dict[str, Any] = {}
    for cat in sorted(set(cat_base) | set(cat_cand)):
        b_mean = round(sum(cat_base[cat]) / len(cat_base[cat]), 4) if cat_base[cat] else None
        c_mean = round(sum(cat_cand[cat]) / len(cat_cand[cat]), 4) if cat_cand[cat] else None
        per_category[cat] = {
            "n": len(cat_cand[cat]),
            "baseline_pass_rate": b_mean,
            "candidate_pass_rate": c_mean,
            "delta": round(c_mean - b_mean, 4) if (b_mean is not None and c_mean is not None) else None,
        }

    gate_failures: list[str] = []
    if gate_config:
        for cat, rules in gate_config.get("per_category", {}).items():
            st = per_category.get(cat)
            if st is None:
                gate_failures.append(f"category '{cat}' missing from matched comparison cohort")
                continue
            if "min_pass_rate" in rules and (st["candidate_pass_rate"] is None or st["candidate_pass_rate"] < rules["min_pass_rate"]):
                gate_failures.append(f"category '{cat}' pass_rate {st['candidate_pass_rate']} < {rules['min_pass_rate']}")
            if "max_regression" in rules and st["delta"] is not None and st["delta"] < -abs(rules["max_regression"]):
                gate_failures.append(f"category '{cat}' delta {st['delta']} exceeds max_regression -{abs(rules['max_regression'])}")

    pairwise_summary = (
        evaluate_pairwise(pairwise_records, max_inconsistency_rate=max_inconsistency_rate, max_chars=max_chars)
        if pairwise_records is not None
        else None
    )
    if pairwise_summary:
        if pairwise_summary["missing_orders"] > 0:
            gate_failures.append(
                f"pairwise comparison has {pairwise_summary['missing_orders']} item(s) missing reverse-order verdicts"
            )
        if pairwise_summary["inconsistency_exceeded"]:
            gate_failures.append(
                f"pairwise position inconsistency {pairwise_summary['inconsistency_rate']} > {max_inconsistency_rate}"
            )

    verdict = "FAIL_GATE" if gate_failures else stat_verdict
    return {
        "validation_status": "VALID",
        "comparison_verdict": verdict,
        "matched_items": len(matched_ids),
        "independent_clusters": len(cluster_means),
        "unmatched_baseline_items": unmatched_base,
        "unmatched_candidate_items": unmatched_cand,
        "statistics": {
            "seed": seed,
            "bootstrap_iterations": iterations,
            "alpha": alpha,
            "mean_delta": mean_delta,
            "bootstrap_ci_95": ci_95,
            "sign_flip_p_value": perm_p,
            "mcnemar_b_base_only": mcnemar_b,
            "mcnemar_c_cand_only": mcnemar_c,
            "mcnemar_exact_p_value": mcnemar_p,
        },
        "baseline_reliability": summarize_reliability(base_recs, k),
        "candidate_reliability": summarize_reliability(cand_recs, k),
        "baseline_efficiency": summarize_efficiency(base_recs),
        "candidate_efficiency": summarize_efficiency(cand_recs),
        "pairwise": pairwise_summary,
        "per_category": per_category,
        "gate_failures": gate_failures,
        "errors": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path, help="Baseline run records JSON.")
    parser.add_argument("--candidate", required=True, type=Path, help="Candidate run records JSON.")
    parser.add_argument("--k", type=int, default=1, help="k for unbiased pass@k and pass^k.")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--iterations", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--pairwise", type=Path, help="Optional swapped (A,B)/(B,A) pairwise verdicts JSON.")
    parser.add_argument("--max-inconsistency-rate", type=float, default=0.15)
    parser.add_argument("--max-chars", type=int, help="Optional non-destructive output character budget.")
    parser.add_argument("--gate-config", type=Path, help="Optional per-category non-compensatory gate JSON.")
    args = parser.parse_args(argv)

    try:
        baseline = load_json(args.baseline.expanduser().resolve(strict=True))
        candidate = load_json(args.candidate.expanduser().resolve(strict=True))
        pairwise_data = load_json(args.pairwise.expanduser().resolve(strict=True)) if args.pairwise else None
        pairwise_records = pairwise_data.get("pairs") if isinstance(pairwise_data, dict) else pairwise_data
        gate_cfg = load_json(args.gate_config.expanduser().resolve(strict=True)) if args.gate_config else None
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"validation_status": "INVALID", "comparison_verdict": "INVALID", "errors": [str(exc)]}, allow_nan=False))
        return 2

    result = compare(
        baseline,
        candidate,
        k=args.k,
        alpha=args.alpha,
        iterations=args.iterations,
        seed=args.seed,
        pairwise_records=pairwise_records,
        max_inconsistency_rate=args.max_inconsistency_rate,
        max_chars=args.max_chars,
        gate_config=gate_cfg,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))
    if result["validation_status"] != "VALID" or result["comparison_verdict"] == "FAIL_GATE":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
