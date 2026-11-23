#!/usr/bin/env python3
"""Evaluate normative T1-T3 SDLC stage gates against rubrics/sdlc-stages.json."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUBRIC_PATH = SKILL_ROOT / "rubrics" / "sdlc-stages.json"

STAGE_THRESHOLDS: dict[str, dict[str, float]] = {
    "T1": {"requirement": 75.0, "implementation": 75.0, "verification": 75.0, "operation": 75.0},
    "T2": {"requirement": 75.0, "implementation": 75.0, "verification": 80.0, "operation": 75.0},
    "T3": {"requirement": 80.0, "implementation": 80.0, "verification": 85.0, "operation": 80.0},
}

STAGE_ID_ALIASES = {
    "requirement": {
        "R1": "r1_problem_outcomes_scope",
        "R2": "r2_behavioral_acceptance_criteria",
        "R3": "r3_nfr_data_compatibility",
        "R4": "r4_feasibility_dependencies",
        "R5": "r5_security_privacy_safety",
        "R6": "r6_traceability_change_control",
        "R7": "r7_delivery_cost_operational_constraints",
        "R-HF01": "r_hf01_incompatible_outcomes",
        "R-HF02": "r_hf02_unbounded_privileged_authority",
        "R-HF03": "r_hf03_security_privacy_legal_violation",
        "R-HF04": "r_hf04_infeasible_critical_dependency",
    },
    "implementation": {
        "I1": "i1_requirement_conformance_scope",
        "I2": "i2_architecture_maintainability_diagnostics",
        "I3": "i3_correctness_failure_handling",
        "I4": "i4_security_privacy_dependencies",
        "I5": "i5_tests_anti_suppression_build",
        "I6": "i6_deployment_migration_recovery",
        "I7": "i7_reviewability_handoff",
        "I-HF01": "i_hf01_critical_requirement_violation",
        "I-HF02": "i_hf02_data_loss_or_corruption",
        "I-HF03": "i_hf03_critical_vuln_or_secret_exposure",
        "I-HF04": "i_hf04_build_or_ci_failure",
        "I-HF05": "i_hf05_unprotected_irreversible_migration",
        "I-HF06": "i_hf06_unauthorized_test_suppression",
    },
    "verification": {
        "V1": "v1_coverage_oracle_validity",
        "V2": "v2_functional_integration_compatibility",
        "V3": "v3_performance_resilience_data_quality",
        "V4": "v4_security_abuse_resistance",
        "V5": "v5_test_independence_reliability",
        "V6": "v6_artifact_provenance_config_parity",
        "V7": "v7_defect_disposition_preflight_signoff",
        "V-HF01": "v_hf01_critical_acceptance_test_failure",
        "V-HF02": "v_hf02_unresolved_blocking_security_defect",
        "V-HF03": "v_hf03_mandatory_nfr_integrity_violation",
        "V-HF04": "v_hf04_mismatched_artifact_or_config",
        "V-HF05": "v_hf05_evidence_fabrication_or_retry_mask",
    },
    "operation": {
        "O1": "o1_reliability_slo_dora_health",
        "O2": "o2_observability_alert_effectiveness",
        "O3": "o3_incident_response_recovery",
        "O4": "o4_deployment_safety_drift_dr",
        "O5": "o5_continuous_security_compliance",
        "O6": "o6_capacity_cost_degradation",
        "O7": "o7_learning_corrective_closure",
        "O-HF01": "o_hf01_uncontained_critical_incident",
        "O-HF02": "o_hf02_ineffective_recovery_capability",
        "O-HF03": "o_hf03_uncontained_integrity_privacy_breach",
        "O-HF04": "o_hf04_error_budget_freeze_violation",
        "O-HF05": "o_hf05_operational_telemetry_manipulation",
    },
}

CRITICAL_DIMENSIONS: dict[str, set[str]] = {
    "requirement": {
        "r2_behavioral_acceptance_criteria",
        "r3_nfr_data_compatibility",
        "r5_security_privacy_safety",
    },
    "implementation": {
        "i1_requirement_conformance_scope",
        "i3_correctness_failure_handling",
        "i4_security_privacy_dependencies",
        "i5_tests_anti_suppression_build",
    },
    "verification": {
        "v1_coverage_oracle_validity",
        "v2_functional_integration_compatibility",
        "v4_security_abuse_resistance",
        "v5_test_independence_reliability",
        "v6_artifact_provenance_config_parity",
    },
    "operation": {
        "o1_reliability_slo_dora_health",
        "o2_observability_alert_effectiveness",
        "o3_incident_response_recovery",
        "o4_deployment_safety_drift_dr",
        "o5_continuous_security_compliance",
    },
}

OPERATION_OBSERVATION_ONLY_DIMS = {
    "o1_reliability_slo_dora_health",
    "o6_capacity_cost_degradation",
    "o7_learning_corrective_closure",
}
OPERATION_PREWINDOW_BASELINE_DIMS = {
    "o2_observability_alert_effectiveness",
    "o3_incident_response_recovery",
    "o4_deployment_safety_drift_dr",
    "o5_continuous_security_compliance",
}
CONDITIONAL_OPTIONAL_DIMS = {
    "i6_deployment_migration_recovery",
    "o4_deployment_safety_drift_dr",
}

VALID_DIM_STATUSES = {"SCORED", "NOT_APPLICABLE", "INSUFFICIENT_EVIDENCE"}
VALID_GATE_STATUSES = {"CLEAR", "TRIGGERED", "UNKNOWN", "INSUFFICIENT_EVIDENCE", "NOT_APPLICABLE"}


def load_json_strict(path: Path) -> Any:
    def no_dups(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"duplicate JSON key: {key}")
            out[key] = value
        return out

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_dups)


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _canonical_id(value: Any, aliases: dict[str, str]) -> str | None:
    return aliases.get(value, value) if _nonempty_string(value) else None


def _validate_evidence_refs(
    item: dict[str, Any], label: str, registry: set[str] | None, errors: list[str]
) -> list[str]:
    primary_key = "evidence_ids" if "evidence_ids" in item else "evidence_refs"
    primary_refs = []
    if registry is None and "evidence_refs" not in item:
        errors.append(f"{label} requires evidence_refs in an overlay report")
    for key in ("evidence_ids", "evidence_refs"):
        if key not in item:
            continue
        refs = item[key]
        if not isinstance(refs, list) or not all(_nonempty_string(ref) for ref in refs):
            errors.append(f"{label} {key} must be a list of non-empty strings")
            continue
        if registry is not None:
            unknown_refs = [ref for ref in refs if ref not in registry]
            if unknown_refs:
                errors.append(f"{label} {key} references unknown evidence IDs: {unknown_refs}")
        if key == primary_key:
            primary_refs = refs
    return primary_refs


def _extract_evidence_ids(records: Any, errors: list[str]) -> set[str]:
    ids: set[str] = set()
    if not isinstance(records, list) or not records:
        errors.append("evidence_records must be a non-empty list")
        return ids
    for index, entry in enumerate(records):
        evidence_id = entry.get("evidence_id") if isinstance(entry, dict) else None
        if not _nonempty_string(evidence_id):
            errors.append(f"evidence_records[{index}] must be an object with a non-empty evidence_id")
        elif evidence_id in ids:
            errors.append(f"duplicate evidence_id: {evidence_id}")
        else:
            ids.add(evidence_id)
    return ids


def _aware_datetime(value: str | datetime) -> datetime:
    if isinstance(value, str):
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        value = datetime.fromisoformat(value)
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("expected a timezone-aware datetime")
    return value


def _approved_exception_targets(
    exceptions: Any,
    aliases: dict[str, str],
    allowed_targets: set[str],
    now: datetime | None,
    errors: list[str],
) -> set[str]:
    targets: set[str] = set()
    if not isinstance(exceptions, list):
        errors.append("exceptions must be a list")
        return targets
    for index, exc in enumerate(exceptions):
        label = f"exceptions[{index}]"
        if not isinstance(exc, dict):
            errors.append(f"{label} must be an object")
            continue
        target = _canonical_id(exc.get("target_id"), aliases)
        if target not in allowed_targets:
            errors.append(f"{label}.target_id must identify a conditional-optional dimension for this stage")
        approved = _nonempty_string(exc.get("approved_by"))
        if not approved:
            errors.append(f"{label}.approved_by must be a non-empty string")
        expires_at = exc.get("expires_at")
        try:
            if not isinstance(expires_at, str):
                raise ValueError("expected a timestamp string")
            expires = _aware_datetime(expires_at)
        except ValueError:
            errors.append(f"{label}.expires_at must be a timezone-aware ISO-8601 timestamp")
            continue
        if target in allowed_targets and approved and now is not None and expires > now:
            targets.add(target)
    return targets


def evaluate_sdlc_report(
    report: dict[str, Any],
    rubric: dict[str, Any],
    *,
    stage_override: str | None = None,
    risk_tier_override: str | None = None,
    stale_override: bool | None = None,
    observation_complete_override: bool | None = None,
    human_signoff_override: bool | None = None,
    stateless_exemption_override: bool = False,
    now: str | datetime | None = None,
) -> dict[str, Any]:
    """Compute normative T1-T3 SDLC stage decision and contract errors."""
    errors: list[str] = []
    reasons: list[str] = []

    stage = stage_override or report.get("stage") or report.get("target_type")
    if stage not in rubric.get("target_types", {}):
        return {
            "validation_status": "INVALID",
            "decision": None,
            "stage": stage,
            "risk_tier": risk_tier_override or report.get("risk_tier"),
            "threshold": None,
            "weighted_score": None,
            "max_achievable_score": None,
            "reasons": [],
            "errors": [f"unsupported or missing SDLC stage: {stage}"],
        }

    risk_tier = risk_tier_override or report.get("risk_tier")
    if risk_tier not in STAGE_THRESHOLDS:
        return {
            "validation_status": "INVALID",
            "decision": None,
            "stage": stage,
            "risk_tier": risk_tier,
            "threshold": None,
            "weighted_score": None,
            "max_achievable_score": None,
            "reasons": [],
            "errors": [f"risk_tier must be one of T1, T2, T3; got {risk_tier!r}"],
        }

    stage_spec = rubric["target_types"][stage]
    expected_dims = {d["id"]: d for d in stage_spec["dimensions"]}
    expected_hfs = {c["id"]: c for c in stage_spec["critical_conditions"]}
    aliases = STAGE_ID_ALIASES[stage]
    critical_set = set(CRITICAL_DIMENSIONS[stage])
    threshold = STAGE_THRESHOLDS[risk_tier][stage]

    stale = bool(stale_override if stale_override is not None else report.get("stale", False))
    obs_complete = (
        observation_complete_override
        if observation_complete_override is not None
        else report.get("observation_window_complete", True)
    )
    if not isinstance(obs_complete, bool):
        errors.append("observation_window_complete must be a boolean")
        obs_complete = True

    human_signoff = (
        human_signoff_override
        if human_signoff_override is not None
        else report.get("human_signoff")
    )
    if human_signoff is not None and not isinstance(human_signoff, bool):
        errors.append("human_signoff must be a boolean when provided")
        human_signoff = None

    try:
        now_dt = datetime.now(timezone.utc) if now is None else _aware_datetime(now)
    except ValueError:
        errors.append("now must be a timezone-aware ISO-8601 timestamp or datetime")
        now_dt = None

    exceptions = report.get("exceptions", [])
    exception_targets = _approved_exception_targets(
        exceptions, aliases, CONDITIONAL_OPTIONAL_DIMS.intersection(expected_dims), now_dt, errors
    )

    raw_dims = report.get("dimensions")
    if not isinstance(raw_dims, list):
        errors.append("dimensions must be a list")
        raw_dims = []

    raw_hfs = report.get("critical_conditions")
    if not isinstance(raw_hfs, list):
        errors.append("critical_conditions must be a list")
        raw_hfs = []

    requires_evidence_records = (
        risk_tier == "T3"
        or "schema_version" in report
        or "evidence_records" in report
        or any(isinstance(entry, dict) and "evidence_ids" in entry for entry in raw_dims + raw_hfs)
    )
    evidence_registry = (
        _extract_evidence_ids(report.get("evidence_records"), errors) if requires_evidence_records else None
    )
    overlay_exemption = stateless_exemption_override and not requires_evidence_records and not exceptions

    seen_dims: set[str] = set()
    dim_by_id: dict[str, dict[str, Any]] = {}
    for entry in raw_dims:
        if not isinstance(entry, dict):
            errors.append("each dimension entry must be an object")
            continue
        ident = _canonical_id(entry.get("id"), aliases)
        if ident not in expected_dims:
            errors.append(f"unknown dimension id for stage {stage}: {entry.get('id')}")
            continue
        if ident in seen_dims:
            errors.append(f"duplicate dimension id: {ident}")
            continue
        seen_dims.add(ident)
        dim_by_id[ident] = entry

    missing_dims = sorted(set(expected_dims) - seen_dims)
    if missing_dims:
        errors.append(f"missing dimensions for stage {stage}: {missing_dims}")

    seen_hfs: set[str] = set()
    hf_by_id: dict[str, dict[str, Any]] = {}
    for entry in raw_hfs:
        if not isinstance(entry, dict):
            errors.append("each critical_condition entry must be an object")
            continue
        ident = _canonical_id(entry.get("id"), aliases)
        if ident not in expected_hfs:
            errors.append(f"unknown critical_condition id for stage {stage}: {entry.get('id')}")
            continue
        if ident in seen_hfs:
            errors.append(f"duplicate critical_condition id: {ident}")
            continue
        seen_hfs.add(ident)
        hf_by_id[ident] = entry

    missing_hfs = sorted(set(expected_hfs) - seen_hfs)
    if missing_hfs:
        errors.append(f"missing critical_conditions for stage {stage}: {missing_hfs}")

    # Validate dimension entries and collect scoring state
    scored_num = 0
    scored_weight = 0
    applicable_weight = 0
    max_num = 0
    floor_failures: list[str] = []
    non_obs_incomplete: list[str] = []
    obs_incomplete: list[str] = []
    critical_four_count = 0
    critical_possible_four_count = 0

    for ident, spec in expected_dims.items():
        entry = dim_by_id.get(ident)
        if entry is None:
            continue
        status = entry.get("status")
        refs = _validate_evidence_refs(entry, f"dimension {ident}", evidence_registry, errors)
        if not isinstance(status, str) or status not in VALID_DIM_STATUSES:
            errors.append(f"dimension {ident} has invalid status: {status}")
            continue

        weight = spec["weight"]
        is_critical = ident in critical_set
        is_conditional = ident in CONDITIONAL_OPTIONAL_DIMS

        if status == "NOT_APPLICABLE":
            if not is_conditional:
                errors.append(f"mandatory dimension {ident} cannot be NOT_APPLICABLE")
                continue
            if not overlay_exemption and ident not in exception_targets:
                errors.append(
                    f"conditional_optional dimension {ident} marked NOT_APPLICABLE without an active approved exception"
                )
            continue

        applicable_weight += weight
        if status == "SCORED":
            score = entry.get("score")
            if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 4:
                errors.append(f"dimension {ident} score must be an integer 0..4")
                continue
            if not refs:
                errors.append(f"scored dimension {ident} must cite at least one evidence ID")
            scored_num += score * weight
            scored_weight += weight
            max_num += score * weight

            if score == 0:
                floor_failures.append(f"{ident}=0 (disqualifier dominance)")
            else:
                if risk_tier == "T1" and score < 2:
                    floor_failures.append(f"{ident}={score} < T1 mandatory floor 2")
                elif risk_tier == "T2":
                    if is_critical and score < 3:
                        floor_failures.append(f"{ident}={score} < T2 critical floor 3")
                    elif score < 2:
                        floor_failures.append(f"{ident}={score} < T2 mandatory floor 2")
                elif risk_tier == "T3":
                    if score < 3:
                        floor_failures.append(f"{ident}={score} < T3 mandatory floor 3")
            if is_critical and score == 4:
                critical_four_count += 1
                critical_possible_four_count += 1
        elif status == "INSUFFICIENT_EVIDENCE":
            if entry.get("score") is not None:
                errors.append(f"dimension {ident} with INSUFFICIENT_EVIDENCE must have null score")
            max_num += 4 * weight
            if is_critical:
                critical_possible_four_count += 1
            if stage == "operation" and not obs_complete and ident in OPERATION_OBSERVATION_ONLY_DIMS:
                obs_incomplete.append(ident)
            else:
                non_obs_incomplete.append(ident)

    # Validate critical conditions (hard fails)
    triggered_hfs: list[str] = []
    unknown_non_obs_hfs: list[str] = []
    for ident, spec in expected_hfs.items():
        entry = hf_by_id.get(ident)
        if entry is None:
            continue
        status = entry.get("status")
        refs = _validate_evidence_refs(entry, f"critical_condition {ident}", evidence_registry, errors)
        if not isinstance(status, str) or status not in VALID_GATE_STATUSES:
            errors.append(f"critical_condition {ident} has invalid status: {status}")
            continue
        if status == "TRIGGERED":
            if not refs:
                errors.append(f"triggered critical_condition {ident} must cite evidence")
            triggered_hfs.append(ident)
        elif status == "CLEAR":
            if not refs:
                errors.append(f"clear critical_condition {ident} must cite evidence")
        elif status in ("UNKNOWN", "INSUFFICIENT_EVIDENCE"):
            unknown_non_obs_hfs.append(ident)
        elif status == "NOT_APPLICABLE":
            if spec["applicability"] != "optional":
                errors.append(f"required critical_condition {ident} cannot be NOT_APPLICABLE")

    if errors:
        return {
            "validation_status": "INVALID",
            "decision": None,
            "stage": stage,
            "risk_tier": risk_tier,
            "threshold": threshold,
            "weighted_score": None,
            "max_achievable_score": None,
            "reasons": [],
            "errors": errors,
        }

    weighted_score = round((scored_num / (4 * scored_weight)) * 100.0, 2) if scored_weight else None
    max_achievable = round((max_num / (4 * applicable_weight)) * 100.0, 2) if applicable_weight else None

    # T3 Verification requires >= 2 critical dimensions at score 4
    t3_verif_four_impossible = (
        risk_tier == "T3" and stage == "verification" and critical_possible_four_count < 2
    )
    t3_verif_four_missing = (
        risk_tier == "T3" and stage == "verification" and critical_four_count < 2
    )

    # Strict verdict precedence (sdlc-rubrics-v2.md C6):
    # STALE > FAIL (hard fail / floor miss / max_achievable < threshold / T3 four-count impossible)
    # > INCONCLUSIVE (non-observation mandatory evidence or unknown critical gate or missing T3 sign-off)
    # > PENDING_OBSERVATION (operation observation window unelapsed with pre-window baseline controls passing)
    # > FAIL (weighted_score < threshold or T3 Verification four-count unmet)
    # > PASS
    if stale:
        decision = "STALE"
        reasons.append("subject or evidence invalidated by upstream/artifact change")
    elif triggered_hfs or floor_failures or t3_verif_four_impossible or (
        max_achievable is not None and max_achievable < threshold
    ):
        decision = "FAIL"
        if triggered_hfs:
            reasons.append(f"triggered hard-fail(s): {', '.join(triggered_hfs)}")
        if floor_failures:
            reasons.append(f"dimension floor failure(s): {'; '.join(floor_failures)}")
        if t3_verif_four_impossible:
            reasons.append(
                f"T3 Verification requires score 4 on >=2 critical dimensions; max achievable is {critical_possible_four_count}"
            )
        if max_achievable is not None and max_achievable < threshold:
            reasons.append(
                f"max_achievable_score {max_achievable} < {risk_tier} {stage} threshold {threshold}"
            )
    elif non_obs_incomplete or unknown_non_obs_hfs:
        decision = "INCONCLUSIVE"
        if non_obs_incomplete:
            reasons.append(f"missing non-observation mandatory evidence: {', '.join(non_obs_incomplete)}")
        if unknown_non_obs_hfs:
            reasons.append(f"unknown critical condition(s): {', '.join(unknown_non_obs_hfs)}")
    elif stage == "operation" and not obs_complete:
        decision = "PENDING_OBSERVATION"
        reasons.append(
            "operation observation window or representative exposure incomplete while pre-window baseline controls (O2-O5) pass"
        )
    elif weighted_score is None:
        decision = "INCONCLUSIVE"
        reasons.append("no applicable dimensions were scored")
    elif weighted_score < threshold:
        decision = "FAIL"
        reasons.append(f"weighted_score {weighted_score} < {risk_tier} {stage} threshold {threshold}")
    elif t3_verif_four_missing:
        decision = "FAIL"
        reasons.append(
            f"T3 Verification requires score 4 on >=2 critical dimensions; observed {critical_four_count}"
        )
    elif risk_tier == "T3" and human_signoff is not True:
        decision = "INCONCLUSIVE"
        reasons.append("T3 High risk tier requires independent human_signoff=true before PASS")
    else:
        decision = "PASS"
        reasons.append(
            f"weighted_score {weighted_score} >= {risk_tier} {stage} threshold {threshold} with all floors and gates clear"
        )

    return {
        "validation_status": "VALID",
        "decision": decision,
        "stage": stage,
        "risk_tier": risk_tier,
        "threshold": threshold,
        "weighted_score": weighted_score,
        "max_achievable_score": max_achievable,
        "critical_four_count": critical_four_count,
        "reasons": reasons,
        "errors": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate normative T1-T3 SDLC stage gates against rubrics/sdlc-stages.json."
    )
    parser.add_argument("--report", required=True, type=Path, help="Path to SDLC v2 or evaluate-with-chatgpt report JSON.")
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC_PATH, help="Path to sdlc-stages.json.")
    parser.add_argument("--stage", choices=["requirement", "implementation", "verification", "operation"], help="Override/provide stage for evaluate-with-chatgpt reports.")
    parser.add_argument("--risk-tier", choices=["T1", "T2", "T3"], help="Risk tier (required if absent from report JSON).")
    parser.add_argument("--now", help="Timezone-aware ISO-8601 time for exception expiry checks (default: current UTC time).")
    parser.add_argument("--stale", action="store_true", help="Mark subject/evidence as invalidated (STALE).")
    parser.add_argument(
        "--observation-incomplete",
        action="store_true",
        help="Mark Operation observation window as unelapsed (enables PENDING_OBSERVATION check).",
    )
    parser.add_argument(
        "--human-signoff",
        action="store_true",
        help="Record verified independent human sign-off (required for T3 PASS).",
    )
    parser.add_argument(
        "--stateless-exemption",
        action="store_true",
        help="Acknowledge preapproved stateless exemption for conditional_optional I6/O4 when using evaluate-with-chatgpt reports.",
    )
    parser.add_argument(
        "--strict-pass",
        action="store_true",
        help="Exit non-zero unless validation_status == VALID and decision == PASS.",
    )
    args = parser.parse_args(argv)

    try:
        rubric = load_json_strict(args.rubric)
        report = load_json_strict(args.report)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"validation_status": "INVALID", "decision": None, "errors": [str(exc)]}, indent=2))
        return 2

    result = evaluate_sdlc_report(
        report,
        rubric,
        stage_override=args.stage,
        risk_tier_override=args.risk_tier,
        stale_override=True if args.stale else None,
        observation_complete_override=False if args.observation_incomplete else None,
        human_signoff_override=True if args.human_signoff else None,
        stateless_exemption_override=args.stateless_exemption,
        now=args.now,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["validation_status"] != "VALID":
        return 1
    if args.strict_pass and result["decision"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
