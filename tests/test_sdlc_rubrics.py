#!/usr/bin/env python3
"""Verify the canonical SDLC stage rubric and its normative T1-T3 gate evaluator."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
COMMON_PATH = ROOT / "skills" / "evaluate-with-rubric" / "scripts" / "common.py"
SPEC = importlib.util.spec_from_file_location("eval_rubric_common", COMMON_PATH)
common = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(common)

GATE_SCRIPT = ROOT / "skills" / "sdlc-stage-rubrics" / "scripts" / "evaluate_sdlc_gate.py"
GATE_SPEC = importlib.util.spec_from_file_location("evaluate_sdlc_gate", GATE_SCRIPT)
sdlc_gate = importlib.util.module_from_spec(GATE_SPEC)
GATE_SPEC.loader.exec_module(sdlc_gate)

CANONICAL_RUBRIC = ROOT / "skills" / "sdlc-stage-rubrics" / "rubrics" / "sdlc-stages.json"
DUPLICATE_RUBRIC = ROOT / "skills" / "evaluate-with-rubric" / "rubrics" / "sdlc-stages.json"
NOW = "2026-11-23T12:00:00Z"
FUTURE = "2026-11-23T21:00:01+09:00"
OPTIONAL_DIMENSIONS = (
    ("implementation", "I6", "i6_deployment_migration_recovery"),
    ("operation", "O4", "o4_deployment_safety_drift_dr"),
)


def build_stage_report(
    rubric: dict,
    stage: str,
    risk_tier: str,
    scores: dict[str, int | None] | None = None,
    statuses: dict[str, str] | None = None,
    hf_overrides: dict[str, str] | None = None,
    *,
    stale: bool = False,
    observation_window_complete: bool = True,
    human_signoff: bool | None = None,
    exceptions: list[dict] | None = None,
) -> dict:
    scores = scores or {}
    statuses = statuses or {}
    hf_overrides = hf_overrides or {}
    spec = rubric["target_types"][stage]
    dims = []
    for dim in spec["dimensions"]:
        ident = dim["id"]
        st = statuses.get(ident, "SCORED")
        sc = None if st != "SCORED" else scores.get(ident, 3)
        dims.append(
            {
                "id": ident,
                "status": st,
                "score": sc,
                "evidence_ids": ["E0001"] if st == "SCORED" else [],
                "rationale": f"Evidence for {ident}.",
            }
        )
    hfs = []
    for cond in spec["critical_conditions"]:
        ident = cond["id"]
        st = hf_overrides.get(ident, "CLEAR")
        hfs.append(
            {
                "id": ident,
                "status": st,
                "evidence_ids": ["E0001"] if st in ("CLEAR", "TRIGGERED") else [],
                "rationale": f"Status for {ident}.",
            }
        )
    report: dict = {
        "schema_version": "2.0",
        "stage": stage,
        "risk_tier": risk_tier,
        "stale": stale,
        "observation_window_complete": observation_window_complete,
        "evidence_records": [{"evidence_id": "E0001"}],
        "dimensions": dims,
        "critical_conditions": hfs,
        "exceptions": exceptions or [],
    }
    if human_signoff is not None:
        report["human_signoff"] = human_signoff
    return report


def as_overlay(report: dict) -> dict:
    """Convert a fixture to the generic evaluate-with-chatgpt report format."""
    del report["schema_version"], report["evidence_records"], report["risk_tier"]
    report["target_type"] = report.pop("stage")
    for entry in report["dimensions"] + report["critical_conditions"]:
        entry["evidence_refs"] = entry.pop("evidence_ids")
    return report


def run_gate_cli(report: dict, *args: str) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as tmp:
        report_path = Path(tmp) / "report.json"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(GATE_SCRIPT), "--report", str(report_path), *args],
            capture_output=True,
            text=True,
            timeout=10,
        )
    return proc.returncode, json.loads(proc.stdout)


class CanonicalSdlcRubricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rubric = common.load_json(CANONICAL_RUBRIC)

    def test_canonical_rubric_is_valid_and_covers_all_stages(self) -> None:
        self.assertTrue(CANONICAL_RUBRIC.is_file(), f"missing canonical rubric: {CANONICAL_RUBRIC}")
        self.assertEqual([], common.validate_rubric(self.rubric))
        self.assertEqual(
            {"requirement", "implementation", "verification", "operation"},
            set(self.rubric["target_types"]),
        )

    def test_no_duplicate_sdlc_rubric_in_evaluate_with_chatgpt(self) -> None:
        self.assertFalse(
            DUPLICATE_RUBRIC.exists(),
            f"duplicate rubric copy should not exist: {DUPLICATE_RUBRIC}",
        )

    def test_short_ids_match_canonical_pass_and_hard_fail_for_every_stage(self) -> None:
        for stage, prefix, hard_fail_count in (
            ("requirement", "R", 4),
            ("implementation", "I", 6),
            ("verification", "V", 5),
            ("operation", "O", 5),
        ):
            for trigger in range(hard_fail_count + 1):
                with self.subTest(stage=stage, trigger=trigger):
                    report = build_stage_report(self.rubric, stage, "T2")
                    report["dimensions"][0]["score"] = 4
                    if trigger:
                        report["critical_conditions"][trigger - 1]["status"] = "TRIGGERED"
                    canonical = sdlc_gate.evaluate_sdlc_report(report, self.rubric)
                    self.assertEqual("FAIL" if trigger else "PASS", canonical["decision"])
                    for number, entry in enumerate(report["dimensions"], 1):
                        entry["id"] = f"{prefix}{number}"
                    for number, entry in enumerate(report["critical_conditions"], 1):
                        entry["id"] = f"{prefix}-HF{number:02}"
                    report["dimensions"].reverse()
                    report["critical_conditions"].reverse()
                    self.assertEqual(canonical, sdlc_gate.evaluate_sdlc_report(report, self.rubric))

    def test_duplicate_alias_and_slug_are_rejected(self) -> None:
        for field, short_id in (("dimensions", "V1"), ("critical_conditions", "V-HF01")):
            with self.subTest(field=field):
                report = build_stage_report(self.rubric, "verification", "T2")
                report[field].insert(0, dict(report[field][0], id=short_id))
                result = sdlc_gate.evaluate_sdlc_report(report, self.rubric)
                self.assertEqual("INVALID", result["validation_status"])
                self.assertTrue(any("duplicate" in error for error in result["errors"]), result)

    def test_unknown_cross_stage_and_inexact_ids_are_rejected(self) -> None:
        for field, ids in (
            ("dimensions", ("V8", "R1", "r1_problem_outcomes_scope", "v1", "V01", "V1 ")),
            ("critical_conditions", ("V-HF06", "R-HF01", "v_hf01", "V-HF1", " V-HF01")),
        ):
            for ident in ids:
                with self.subTest(field=field, ident=ident):
                    report = build_stage_report(self.rubric, "verification", "T2")
                    report[field][0]["id"] = ident
                    result = sdlc_gate.evaluate_sdlc_report(report, self.rubric)
                    self.assertEqual("INVALID", result["validation_status"])
                    self.assertTrue(any("unknown" in error for error in result["errors"]), result)

    def test_t2_verification_all_threes_fails_80_threshold(self) -> None:
        report = build_stage_report(self.rubric, "verification", "T2")
        result = sdlc_gate.evaluate_sdlc_report(report, self.rubric)
        self.assertEqual("VALID", result["validation_status"])
        self.assertEqual(75.0, result["weighted_score"])
        self.assertEqual(80.0, result["threshold"])
        self.assertEqual("FAIL", result["decision"])

    def test_t2_verification_reaches_80_and_passes(self) -> None:
        report = build_stage_report(
            self.rubric,
            "verification",
            "T2",
            scores={"v1_coverage_oracle_validity": 4},
        )
        result = sdlc_gate.evaluate_sdlc_report(report, self.rubric)
        self.assertEqual("VALID", result["validation_status"])
        self.assertEqual(80.0, result["weighted_score"])
        self.assertEqual("PASS", result["decision"])

    def test_t2_critical_dimension_floor_blocks_high_weighted_score(self) -> None:
        report = build_stage_report(
            self.rubric,
            "verification",
            "T2",
            scores={
                "v1_coverage_oracle_validity": 4,
                "v2_functional_integration_compatibility": 4,
                "v3_performance_resilience_data_quality": 4,
                "v4_security_abuse_resistance": 2,
                "v5_test_independence_reliability": 4,
                "v6_artifact_provenance_config_parity": 4,
                "v7_defect_disposition_preflight_signoff": 4,
            },
        )
        result = sdlc_gate.evaluate_sdlc_report(report, self.rubric)
        self.assertEqual("VALID", result["validation_status"])
        self.assertGreater(result["weighted_score"], 85.0)
        self.assertEqual("FAIL", result["decision"])

    def test_t3_verification_requires_85_two_critical_fours_and_human_signoff(self) -> None:
        # 85.0 weighted score with two critical 4s (V1=20, V2=20 -> +40 points = 85.0)
        report = build_stage_report(
            self.rubric,
            "verification",
            "T3",
            scores={
                "v1_coverage_oracle_validity": 4,
                "v2_functional_integration_compatibility": 4,
            },
            human_signoff=False,
        )
        res_no_signoff = sdlc_gate.evaluate_sdlc_report(report, self.rubric)
        self.assertEqual("INCONCLUSIVE", res_no_signoff["decision"])

        report["human_signoff"] = True
        res_signed = sdlc_gate.evaluate_sdlc_report(report, self.rubric)
        self.assertEqual("PASS", res_signed["decision"])

        # Only one critical 4 (V1=20) + non-critical V3=15 + V7=10 => 86.25% but <2 critical 4s -> FAIL
        one_crit = build_stage_report(
            self.rubric,
            "verification",
            "T3",
            scores={
                "v1_coverage_oracle_validity": 4,
                "v3_performance_resilience_data_quality": 4,
                "v7_defect_disposition_preflight_signoff": 4,
            },
            human_signoff=True,
        )
        self.assertEqual("FAIL", sdlc_gate.evaluate_sdlc_report(one_crit, self.rubric)["decision"])

    def test_operation_pending_observation_and_baseline_floor_precedence(self) -> None:
        report = build_stage_report(
            self.rubric,
            "operation",
            "T2",
            statuses={"o1_reliability_slo_dora_health": "INSUFFICIENT_EVIDENCE"},
            observation_window_complete=False,
        )
        res = sdlc_gate.evaluate_sdlc_report(report, self.rubric)
        self.assertEqual("PENDING_OBSERVATION", res["decision"])

        # Baseline O2 floor failure overrides PENDING_OBSERVATION with FAIL
        report_bad_o2 = build_stage_report(
            self.rubric,
            "operation",
            "T2",
            scores={"o2_observability_alert_effectiveness": 2},
            statuses={"o1_reliability_slo_dora_health": "INSUFFICIENT_EVIDENCE"},
            observation_window_complete=False,
        )
        self.assertEqual("FAIL", sdlc_gate.evaluate_sdlc_report(report_bad_o2, self.rubric)["decision"])

    def test_stale_overrides_pass_and_fail(self) -> None:
        report = build_stage_report(
            self.rubric,
            "requirement",
            "T2",
            hf_overrides={"r_hf01_incompatible_outcomes": "TRIGGERED"},
            stale=True,
        )
        self.assertEqual("STALE", sdlc_gate.evaluate_sdlc_report(report, self.rubric)["decision"])

    def test_early_fail_when_max_achievable_below_threshold(self) -> None:
        report = build_stage_report(
            self.rubric,
            "requirement",
            "T1",
            scores={
                "r1_problem_outcomes_scope": 2,
                "r2_behavioral_acceptance_criteria": 2,
                "r3_nfr_data_compatibility": 2,
                "r4_feasibility_dependencies": 2,
                "r5_security_privacy_safety": 2,
            },
            statuses={"r6_traceability_change_control": "INSUFFICIENT_EVIDENCE"},
        )
        # Scored: 2*80 + 3*10 = 190; max for R6(10) = 40 -> 230/400 = 57.5 < 75.0 -> early FAIL
        res = sdlc_gate.evaluate_sdlc_report(report, self.rubric)
        self.assertEqual("FAIL", res["decision"])
        self.assertLess(res["max_achievable_score"], 75.0)

    def test_conditional_optional_not_applicable_requires_exception(self) -> None:
        for stage, short_id, slug in OPTIONAL_DIMENSIONS:
            for expires_at in (None, "2026-11-23T11:59:59Z", "2026-11-23T21:00:00+09:00"):
                with self.subTest(stage=stage, expires_at=expires_at):
                    report = build_stage_report(self.rubric, stage, "T2", statuses={slug: "NOT_APPLICABLE"})
                    if expires_at is not None:
                        report["exceptions"] = [{"target_id": short_id, "approved_by": "lead", "expires_at": expires_at}]
                    result = sdlc_gate.evaluate_sdlc_report(report, self.rubric, now=NOW)
                    self.assertEqual("INVALID", result["validation_status"])
                    self.assertTrue(any("active approved exception" in error for error in result["errors"]), result)

    def test_unexpired_exception_accepts_exact_short_id_and_slug(self) -> None:
        for stage, short_id, slug in OPTIONAL_DIMENSIONS:
            for target in (short_id, slug):
                with self.subTest(stage=stage, target=target):
                    report = build_stage_report(
                        self.rubric, stage, "T2", statuses={slug: "NOT_APPLICABLE"},
                        exceptions=[{"target_id": target, "approved_by": "lead", "expires_at": FUTURE}],
                    )
                    next(entry for entry in report["dimensions"] if entry["id"] == slug)["id"] = short_id
                    result = sdlc_gate.evaluate_sdlc_report(report, self.rubric, now=NOW)
                    self.assertEqual("PASS", result["decision"], result)

    def test_malformed_exceptions_invalidate_even_scored_reports(self) -> None:
        report = build_stage_report(self.rubric, "implementation", "T2")
        approval = {"target_id": "I6", "approved_by": "lead", "expires_at": FUTURE}
        for exceptions in (None, {}, "invalid", [None], [False]):
            with self.subTest(exceptions=exceptions):
                report["exceptions"] = exceptions
                result = sdlc_gate.evaluate_sdlc_report(report, self.rubric, now=NOW)
                self.assertEqual("INVALID", result["validation_status"])
                self.assertTrue(any("exceptions" in error for error in result["errors"]), result)
        for key, invalid_values in (
            ("target_id", ("I1", "I-HF01", "O4", "i6", "I6 ")),
            ("approved_by", ()),
            ("expires_at", ("tomorrow", "2026-11-23T12:00:00", "2026-11-23")),
        ):
            malformed = [{k: v for k, v in approval.items() if k != key}]
            malformed.extend(dict(approval, **{key: val}) for val in ("", " ", 42, None, *invalid_values))
            for exception in malformed:
                with self.subTest(key=key, exception=exception):
                    report["exceptions"] = [approval, exception]
                    result = sdlc_gate.evaluate_sdlc_report(report, self.rubric, now=NOW)
                    self.assertEqual("INVALID", result["validation_status"])
                    self.assertTrue(any(f"exceptions[1].{key}" in error for error in result["errors"]), result)

    def test_unused_expired_exception_is_valid(self) -> None:
        for stage, short_id, _ in OPTIONAL_DIMENSIONS:
            with self.subTest(stage=stage):
                report = build_stage_report(
                    self.rubric, stage, "T2",
                    exceptions=[{"target_id": short_id, "approved_by": "lead", "expires_at": NOW}],
                )
                result = sdlc_gate.evaluate_sdlc_report(report, self.rubric, now=datetime.fromisoformat(NOW[:-1] + "+00:00"))
                self.assertEqual("PASS", result["decision"], result)

    def test_default_clock_is_sampled_once_per_report(self) -> None:
        samples = []

        class FixedClock(datetime):
            @classmethod
            def now(cls, tz):
                samples.append(tz)
                return cls(2026, 11, 23, 12, tzinfo=tz)

        stage, short_id, slug = OPTIONAL_DIMENSIONS[0]
        report = build_stage_report(
            self.rubric, stage, "T2", statuses={slug: "NOT_APPLICABLE"},
            exceptions=[{"target_id": short_id, "approved_by": "lead", "expires_at": FUTURE}],
        )
        with patch.object(sdlc_gate, "datetime", FixedClock):
            result = sdlc_gate.evaluate_sdlc_report(report, self.rubric)
        self.assertEqual("PASS", result["decision"], result)
        self.assertEqual([timezone.utc], samples)

    def test_cli_now_replays_expiry_boundary_and_rejects_invalid_time(self) -> None:
        stage, short_id, slug = OPTIONAL_DIMENSIONS[0]
        report = build_stage_report(
            self.rubric, stage, "T2", statuses={slug: "NOT_APPLICABLE"},
            exceptions=[{"target_id": short_id, "approved_by": "lead", "expires_at": NOW}],
        )
        for now, expected_code, expected_error in (
            ("2026-11-23T11:59:59Z", 0, None),
            ("2026-11-23T21:00:00+09:00", 1, "active approved exception"),
            ("not-a-timestamp", 1, "now must be"),
            ("2026-11-23T11:59:59", 1, "now must be"),
        ):
            with self.subTest(now=now):
                code, result = run_gate_cli(report, "--now", now, "--strict-pass")
                self.assertEqual(expected_code, code)
                if expected_error:
                    self.assertEqual("INVALID", result["validation_status"])
                    self.assertTrue(any(expected_error in error for error in result["errors"]), result)
                else:
                    self.assertEqual("PASS", result["decision"], result)

    def test_overlay_exemption_flag_cannot_bypass_native_or_expired_approval(self) -> None:
        stage, short_id, slug = OPTIONAL_DIMENSIONS[0]
        report = build_stage_report(self.rubric, stage, "T2", statuses={slug: "NOT_APPLICABLE"})
        kwargs = dict(risk_tier_override="T2", stateless_exemption_override=True, now=NOW)
        result = sdlc_gate.evaluate_sdlc_report(report, self.rubric, **kwargs)
        self.assertEqual("INVALID", result["validation_status"])
        overlay = as_overlay(report)
        self.assertEqual("PASS", sdlc_gate.evaluate_sdlc_report(overlay, self.rubric, **kwargs)["decision"])
        overlay["exceptions"] = [{"target_id": short_id, "approved_by": "lead", "expires_at": NOW}]
        result = sdlc_gate.evaluate_sdlc_report(overlay, self.rubric, **kwargs)
        self.assertEqual("INVALID", result["validation_status"])

    def test_native_markers_and_t3_prevent_registry_free_overlay(self) -> None:
        for marker in ("T3", "schema_version", "dimensions", "critical_conditions"):
            with self.subTest(marker=marker):
                report = as_overlay(build_stage_report(self.rubric, "verification", "T2"))
                if marker == "schema_version":
                    report[marker] = "2.0"
                elif marker != "T3":
                    report[marker][-1]["evidence_ids"] = report[marker][-1].pop("evidence_refs")
                result = sdlc_gate.evaluate_sdlc_report(
                    report, self.rubric, risk_tier_override="T3" if marker == "T3" else "T2"
                )
                self.assertEqual("INVALID", result["validation_status"])
                self.assertIn("evidence_records must be a non-empty list", result["errors"])

    def test_invalid_evidence_registry_shapes_are_rejected(self) -> None:
        report = as_overlay(build_stage_report(self.rubric, "implementation", "T2"))
        valid = {"evidence_id": "E0001"}
        cases = (
            (None, "non-empty list"), ({}, "non-empty list"), ([], "non-empty list"),
            ([valid, None], "non-empty evidence_id"), ([valid, {}], "non-empty evidence_id"),
            ([valid, {"evidence_id": ""}], "non-empty evidence_id"),
            ([valid, {"evidence_id": " "}], "non-empty evidence_id"),
            ([valid, {"evidence_id": 1}], "non-empty evidence_id"),
            ([valid, valid], "duplicate evidence_id"),
        )
        for records, error in cases:
            with self.subTest(records=records):
                report["evidence_records"] = records
                result = sdlc_gate.evaluate_sdlc_report(report, self.rubric, risk_tier_override="T2")
                self.assertEqual("INVALID", result["validation_status"])
                self.assertTrue(any(error in message for message in result["errors"]), result)

    def test_dangling_refs_and_invalid_evidence_arrays_are_rejected(self) -> None:
        for entries in ("dimensions", "critical_conditions"):
            for key in ("evidence_refs", "evidence_ids"):
                for bad in ([""], [" "], [1], [{}], "E0001", {}, None, ["unregistered"]):
                    with self.subTest(entries=entries, key=key, bad=bad):
                        report = build_stage_report(self.rubric, "implementation", "T2")
                        # A valid primary evidence_ids array cannot hide a bad evidence_refs array.
                        report[entries][0][key] = bad
                        result = sdlc_gate.evaluate_sdlc_report(report, self.rubric)
                        self.assertEqual("INVALID", result["validation_status"])
                        expected_error = "unknown evidence IDs" if bad == ["unregistered"] else "list of non-empty strings"
                        self.assertTrue(any(key in error and expected_error in error for error in result["errors"]), result)

    def test_overlay_evidence_refs_work_at_t1_and_t2(self) -> None:
        report = as_overlay(build_stage_report(self.rubric, "implementation", "T2"))
        for tier in ("T1", "T2"):
            with self.subTest(tier=tier):
                result = sdlc_gate.evaluate_sdlc_report(report, self.rubric, risk_tier_override=tier)
                self.assertEqual("PASS", result["decision"], result)
        report["dimensions"][0]["evidence_refs"] = [""]
        result = sdlc_gate.evaluate_sdlc_report(report, self.rubric, risk_tier_override="T2")
        self.assertEqual("INVALID", result["validation_status"])

    def test_cli_overlay_rejects_chatgpt_t2_verification_75_report(self) -> None:
        report = as_overlay(build_stage_report(self.rubric, "verification", "T2"))
        code, payload = run_gate_cli(report, "--stage", "verification", "--risk-tier", "T2", "--strict-pass")
        self.assertEqual(1, code)
        self.assertEqual("VALID", payload["validation_status"])
        self.assertEqual("FAIL", payload["decision"])
        self.assertEqual(75.0, payload["weighted_score"])


if __name__ == "__main__":
    unittest.main()
