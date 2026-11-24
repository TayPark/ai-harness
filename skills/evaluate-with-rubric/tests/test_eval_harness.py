"""Unit tests for V2 calibrated reports, calibrate_judge.py, and compare_runs.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import calibrate_judge  # noqa: E402
import common  # noqa: E402
import compare_runs  # noqa: E402


RUBRIC_PATH = Path(__file__).resolve().parents[1] / "rubrics" / "default.json"


def _sample_v2_report(packet: dict) -> dict:
    return {
        "report_schema_version": "2.0",
        "packet_id": packet["packet_id"],
        "rubric_version": packet["rubric"]["version"],
        "target_type": packet["target_type"],
        "judge_metadata": {
            "provider": "openai",
            "model_id": "gpt-test",
            "model_version": "2026-11-01",
            "prompt_sha256": "a" * 64,
            "rubric_sha256": packet["rubric_sha256"],
            "temperature": 0.2,
            "run_index": 1,
        },
        "run_telemetry": {
            "blocking_deterministic_checks_passed": True,
            "non_blocking_warnings": ["style-note"],
            "input_tokens": 500,
            "output_tokens": 180,
            "latency_ms": 1200,
            "cost_usd": 0.012,
        },
        "dimensions": [
            {"id": "correctness", "evidence_refs": ["E0001"], "rationale": "Checked behavior.", "status": "SCORED", "score": 4},
            {"id": "security", "evidence_refs": ["E0001"], "rationale": "No secret leaks.", "status": "SCORED", "score": 3},
            {"id": "maintainability", "evidence_refs": ["E0001"], "rationale": "Readable code.", "status": "SCORED", "score": 3},
            {"id": "verification", "evidence_refs": ["E0001"], "rationale": "Unit test shown.", "status": "SCORED", "score": 3},
            {"id": "compatibility", "evidence_refs": [], "rationale": "Not requested.", "status": "NOT_APPLICABLE", "score": None},
        ],
        "critical_conditions": [
            {"id": "credential_exposure", "evidence_refs": ["E0001"], "rationale": "No live keys.", "status": "CLEAR"},
            {"id": "destructive_behavior", "evidence_refs": ["E0001"], "rationale": "Read-only helper.", "status": "CLEAR"},
        ],
        "summary": {
            "weighted_score": 83.33,
            "decision": "PASS",
        },
    }


def _make_dataset(n_test: int = 100, *, leak_hash: bool = False) -> dict:
    cases = []
    for i in range(n_test):
        label = "FAIL" if i % 2 == 0 else "PASS"
        cases.append({
            "item_id": f"case-{i:03d}",
            "split": "test",
            "category": "security" if i % 2 == 0 else "correctness",
            "severity": "critical" if i % 2 == 0 else "major",
            "source": "human",
            "adjudication_provenance": "expert-panel-v1",
            "input_sha256": common.digest(f"input-{i}".encode("utf-8")),
            "expected_label": label,
            "expected_score": 1 if label == "FAIL" else 3,
            "is_adversarial": (i < 4),
        })
    cases.append({
        "item_id": "dev-001",
        "split": "dev",
        "category": "security",
        "severity": "critical",
        "source": "human",
        "adjudication_provenance": "expert-panel-v1",
        "input_sha256": cases[0]["input_sha256"] if leak_hash else common.digest(b"dev-unique"),
        "expected_label": "FAIL",
        "expected_score": 0,
    })
    dataset = {
        "dataset_schema_version": "1.0",
        "dataset_id": "test-golden",
        "dataset_version": "1.0.0",
        "rubric_version": "1.0.0",
        "rubric_sha256": "b" * 64,
        "prompt_sha256": "c" * 64,
        "strata": {"security": n_test // 2 + 1, "correctness": n_test - n_test // 2},
        "cases": cases,
    }
    dataset["dataset_sha256"] = common.digest(common.canonical_json(dataset))
    return dataset


class TestV2ReportAndStrictJson(unittest.TestCase):
    def test_v1_rejects_v2_fields_while_v2_accepts(self) -> None:
        rubric = common.load_json(RUBRIC_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp) / "app.py"
            sample.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
            packet = common.make_packet(sample, "code", "Review helper", rubric, "2026-11-24T00:00:00Z")
            v2_report = _sample_v2_report(packet)

            v1_errors, _, _ = common.evaluate_report(packet, v2_report)
            self.assertTrue(v1_errors)

            v2_errors, score, decision = common.evaluate_report_v2(packet, v2_report)
            self.assertEqual(v2_errors, [])
            self.assertEqual(score, 83.33)
            self.assertEqual(decision, "PASS")

    def test_v2_blocks_pass_when_blocking_deterministic_checks_fail(self) -> None:
        rubric = common.load_json(RUBRIC_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp) / "app.py"
            sample.write_text("x = 1\n", encoding="utf-8")
            packet = common.make_packet(sample, "code", "Review", rubric, "2026-11-24T00:00:00Z")
            report = _sample_v2_report(packet)
            report["run_telemetry"]["blocking_deterministic_checks_passed"] = False
            errors, _, _ = common.evaluate_report_v2(packet, report)
            self.assertTrue(any("blocking_deterministic_checks_passed=false" in e for e in errors))

    def test_strict_json_rejects_overflow_float_and_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            overflow = Path(tmp) / "overflow.json"
            overflow.write_text('{"x": 1e999}', encoding="utf-8")
            with self.assertRaises(ValueError):
                common.load_json(overflow)

            dup = Path(tmp) / "dup.json"
            dup.write_text('{"decision": "FAIL", "decision": "PASS"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                common.load_json(dup)


class TestCalibrateJudge(unittest.TestCase):
    def test_certified_calibration_and_exploratory_small_sample(self) -> None:
        dataset = _make_dataset(100)
        meta = {
            "model_id": "judge-x",
            "model_version": "2026-11-01",
            "prompt_sha256": dataset["prompt_sha256"],
            "rubric_sha256": dataset["rubric_sha256"],
            "temperature": 0.0,
        }
        records = [
            {
                "item_id": c["item_id"],
                "predicted_label": c["expected_label"],
                "predicted_score": c["expected_score"],
                "judge_metadata": meta,
            }
            for c in dataset["cases"]
            if c["split"] == "test"
        ]
        runs = {"dataset_sha256": dataset["dataset_sha256"], "records": records}
        res = calibrate_judge.calibrate(dataset, runs, positive_class="FAIL", gate_config=calibrate_judge.SDLC_V2_PRESET)
        self.assertEqual(res["validation_status"], "VALID")
        self.assertEqual(res["certification_status"], "CERTIFIED")
        self.assertEqual(res["metrics"]["tpr"], 1.0)
        self.assertEqual(res["metrics"]["fpr"], 0.0)
        self.assertEqual(res["metrics"]["cohens_kappa"], 1.0)

        small_ds = _make_dataset(20)
        small_runs = {
            "dataset_sha256": small_ds["dataset_sha256"],
            "records": [
                {"item_id": c["item_id"], "predicted_label": c["expected_label"], "judge_metadata": meta}
                for c in small_ds["cases"]
                if c["split"] == "test"
            ],
        }
        exp = calibrate_judge.calibrate(small_ds, small_runs, allow_small_sample=True)
        self.assertEqual(exp["certification_status"], "EXPLORATORY_ONLY")

    def test_rejects_cross_split_leakage_and_judge_drift(self) -> None:
        leaked = _make_dataset(10, leak_hash=True)
        meta = {
            "model_id": "judge-x",
            "model_version": "v1",
            "prompt_sha256": leaked["prompt_sha256"],
            "rubric_sha256": leaked["rubric_sha256"],
            "temperature": 0.0,
        }
        runs = {
            "dataset_sha256": leaked["dataset_sha256"],
            "records": [{"item_id": "case-000", "predicted_label": "FAIL", "judge_metadata": meta}],
        }
        res = calibrate_judge.calibrate(leaked, runs, allow_small_sample=True)
        self.assertEqual(res["validation_status"], "INVALID")
        self.assertTrue(any("leakage" in e for e in res["errors"]))

        clean = _make_dataset(10)
        meta2 = dict(meta, model_version="v2")
        drift_runs = {
            "dataset_sha256": clean["dataset_sha256"],
            "records": [
                {"item_id": "case-000", "predicted_label": "FAIL", "judge_metadata": meta},
                {"item_id": "case-001", "predicted_label": "PASS", "judge_metadata": meta2},
            ],
        }
        res2 = calibrate_judge.calibrate(clean, drift_runs, allow_small_sample=True)
        self.assertEqual(res2["validation_status"], "INVALID")
        self.assertTrue(any("drift" in e for e in res2["errors"]))

    def test_sdlc_preset_fails_when_adversarial_or_ordinal_missing(self) -> None:
        dataset = _make_dataset(100)
        for case in dataset["cases"]:
            case.pop("is_adversarial", None)
            case.pop("expected_score", None)
        dataset.pop("dataset_sha256")
        dataset["dataset_sha256"] = common.digest(common.canonical_json(dataset))
        meta = {
            "model_id": "judge-x",
            "model_version": "2026-11-01",
            "prompt_sha256": dataset["prompt_sha256"],
            "rubric_sha256": dataset["rubric_sha256"],
            "temperature": 0.0,
        }
        runs = {
            "dataset_sha256": dataset["dataset_sha256"],
            "records": [
                {"item_id": c["item_id"], "predicted_label": c["expected_label"], "judge_metadata": meta}
                for c in dataset["cases"]
                if c["split"] == "test"
            ],
        }
        res = calibrate_judge.calibrate(dataset, runs, gate_config=calibrate_judge.SDLC_V2_PRESET)
        self.assertEqual(res["certification_status"], "FAILED")
        self.assertTrue(any("adversarial" in f for f in res["gate_failures"]))
        self.assertTrue(any("ordinal" in f for f in res["gate_failures"]))


class TestCompareRuns(unittest.TestCase):
    def test_pass_at_k_and_pass_pow_k_and_zero_success_cost(self) -> None:
        self.assertEqual(compare_runs.pass_at_k(5, 4, 2), 1.0)
        self.assertEqual(compare_runs.pass_pow_k(5, 4, 2), 0.6)
        eff = compare_runs.summarize_efficiency([
            {"item_id": "a", "passed": False, "cost_usd": 0.05, "latency_ms": 100, "tokens": 200},
            {"item_id": "b", "passed": False, "cost_usd": 0.05, "latency_ms": 300, "tokens": 400},
        ])
        self.assertIsNone(eff["cost_per_successful_task"])
        self.assertEqual(eff["cost_status"], "NO_SUCCESSFUL_TASKS")
        json.dumps(eff, allow_nan=False)

    def test_swap_pairwise_and_non_compensatory_category_gate(self) -> None:
        base = {
            "records": [
                {"item_id": f"s-{i}", "category": "security", "passed": True, "score": 3, "cost_usd": 0.02, "latency_ms": 100}
                for i in range(10)
            ] + [
                {"item_id": f"c-{i}", "category": "correctness", "passed": False, "score": 1, "cost_usd": 0.02, "latency_ms": 100}
                for i in range(10)
            ]
        }
        cand = {
            "records": [
                {"item_id": f"s-{i}", "category": "security", "passed": (i < 5), "score": 2, "cost_usd": 0.01, "latency_ms": 90}
                for i in range(10)
            ] + [
                {"item_id": f"c-{i}", "category": "correctness", "passed": True, "score": 4, "cost_usd": 0.01, "latency_ms": 90}
                for i in range(10)
            ]
        }
        pairs = [
            {"item_id": "s-0", "order_ab": "B", "order_ba": "A", "baseline_chars": 500, "candidate_chars": 510},
            {"item_id": "s-1", "order_ab": "B", "order_ba": "B", "baseline_chars": 500, "candidate_chars": 900},
        ]
        gate = {"per_category": {"security": {"min_pass_rate": 0.9, "max_regression": 0.05}}}
        res = compare_runs.compare(
            base, cand, iterations=500, seed=7, pairwise_records=pairs, max_inconsistency_rate=0.15, gate_config=gate
        )
        self.assertEqual(res["comparison_verdict"], "FAIL_GATE")
        self.assertEqual(res["pairwise"]["candidate_wins"], 1)
        self.assertEqual(res["pairwise"]["position_inconsistent"], 1)
        self.assertTrue(res["pairwise"]["inconsistency_exceeded"])
        self.assertTrue(any("security" in f for f in res["gate_failures"]))

    def test_missing_reverse_order_fails_pairwise_gate(self) -> None:
        base = {"records": [{"item_id": "x-1", "passed": True}, {"item_id": "x-2", "passed": True}]}
        cand = {"records": [{"item_id": "x-1", "passed": True}, {"item_id": "x-2", "passed": True}]}
        pairs = [{"item_id": "x-1", "order_ab": "B"}]
        res = compare_runs.compare(base, cand, iterations=100, seed=1, pairwise_records=pairs)
        self.assertEqual(res["comparison_verdict"], "FAIL_GATE")
        self.assertEqual(res["pairwise"]["missing_orders"], 1)
        self.assertTrue(any("missing reverse-order" in f for f in res["gate_failures"]))


if __name__ == "__main__":
    unittest.main()
