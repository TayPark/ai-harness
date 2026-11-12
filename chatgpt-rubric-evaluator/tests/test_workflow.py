from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from common import evaluate_report, load_json, make_packet, packet_errors, packet_snapshot_matches, validate_rubric  # noqa: E402

SKILL = SCRIPTS.parent
DEFAULT_RUBRIC = load_json(SKILL / "rubrics" / "default.json")
FIXED_TIME = "2026-01-02T03:04:05Z"


def make_report(packet: dict, *, optional_na: bool = False) -> dict:
    spec = packet["rubric"]["target_types"][packet["target_type"]]
    ref = packet["evidence"][0]["id"]
    dimensions = []
    for rule in spec["dimensions"]:
        if optional_na and rule["applicability"] == "optional":
            dimensions.append({
                "id": rule["id"], "status": "NOT_APPLICABLE", "score": None,
                "evidence_refs": [], "rationale": "Not in the stated task scope.",
            })
        else:
            dimensions.append({
                "id": rule["id"], "status": "SCORED", "score": 4,
                "evidence_refs": [ref], "rationale": "The cited target evidence meets this criterion.",
            })
    conditions = [{
        "id": rule["id"], "status": "CLEAR", "evidence_refs": [ref],
        "rationale": "The cited target evidence shows no trigger.",
    } for rule in spec["critical_conditions"]]
    report = {
        "packet_id": packet["packet_id"],
        "rubric_version": packet["rubric"]["version"],
        "target_type": packet["target_type"],
        "dimensions": dimensions,
        "critical_conditions": conditions,
        "summary": {"weighted_score": 100, "decision": "PASS"},
    }
    return report


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.target = self.root / "sample.py"
        self.target.write_text("def answer():\n    return 42\n", encoding="utf-8")
        self.packet = make_packet(self.target, "code", "Review answer()", DEFAULT_RUBRIC, FIXED_TIME)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_default_rubric_is_valid_and_weights_sum(self) -> None:
        self.assertEqual([], validate_rubric(DEFAULT_RUBRIC))
        self.assertEqual([], packet_errors(self.packet))

    def test_packet_is_deterministic_for_same_timestamp_and_target(self) -> None:
        repeated = make_packet(self.target, "code", "Review answer()", DEFAULT_RUBRIC, FIXED_TIME)
        self.assertEqual(self.packet, repeated)

    def test_redacts_known_secrets_and_email(self) -> None:
        self.target.write_text('api_key = "sk_live_value"\nowner = "person@example.com"\n', encoding="utf-8")
        packet = make_packet(self.target, "code", "Review file", DEFAULT_RUBRIC, FIXED_TIME)
        content = packet["evidence"][0]["content"]
        self.assertNotIn("sk_live_value", content)
        self.assertNotIn("person@example.com", content)
        self.assertIn("[REDACTED_SECRET]", content)
        self.assertIn("[REDACTED_EMAIL]", content)

    def test_secret_named_file_is_omitted_but_hash_tracked(self) -> None:
        target_dir = self.root / "tree"
        target_dir.mkdir()
        (target_dir / "main.py").write_text("print('ok')\n", encoding="utf-8")
        secret = target_dir / ".env"
        secret.write_text("API_KEY=hidden\n", encoding="utf-8")
        packet = make_packet(target_dir, "code", "Review source", DEFAULT_RUBRIC, FIXED_TIME)
        item = next(item for item in packet["evidence"] if item["path"] == ".env")
        self.assertEqual("OMITTED", item["content_status"])
        self.assertEqual("sensitive_filename", item["omission_reason"])
        self.assertIsNotNone(item["sha256"])
        self.assertIsNone(item["content"])

    def test_symlink_retargeting_makes_packet_stale(self) -> None:
        target_dir = self.root / "links"
        target_dir.mkdir()
        (target_dir / "source.py").write_text("print('ok')\n", encoding="utf-8")
        link = target_dir / "link.py"
        link.symlink_to("source.py")
        packet = make_packet(target_dir, "code", "Review source", DEFAULT_RUBRIC, FIXED_TIME)
        entry = next(item for item in packet["evidence"] if item["path"] == "link.py")
        self.assertEqual("symbolic_link", entry["omission_reason"])
        self.assertIsNotNone(entry["sha256"])
        link.unlink()
        link.symlink_to("./source.py")
        self.assertFalse(packet_snapshot_matches(packet, target_dir))

    def test_report_accepts_optional_not_applicable_dimension(self) -> None:
        report = make_report(self.packet, optional_na=True)
        errors, score, decision = evaluate_report(self.packet, report)
        self.assertEqual([], errors)
        self.assertEqual(100, score)
        self.assertEqual("PASS", decision)

    def test_threshold_and_weighted_score_are_calculated_locally(self) -> None:
        report = make_report(self.packet)
        for dimension in report["dimensions"]:
            dimension["score"] = 3
        report["summary"].update(weighted_score=75, decision="FAIL")
        errors, score, decision = evaluate_report(self.packet, report)
        self.assertEqual([], errors)
        self.assertEqual(75, score)
        self.assertEqual("FAIL", decision)
        report["summary"]["decision"] = "PASS"
        errors, _, _ = evaluate_report(self.packet, report)
        self.assertTrue(any("locally calculated FAIL" in error for error in errors))

    def test_missing_or_unknown_evidence_reference_is_rejected(self) -> None:
        report = make_report(self.packet)
        report["dimensions"][0]["evidence_refs"] = ["E9999"]
        errors, _, _ = evaluate_report(self.packet, report)
        self.assertTrue(any("unknown evidence" in error for error in errors))

    def test_malformed_report_ids_are_rejected_without_crashing(self) -> None:
        report = make_report(self.packet)
        report["dimensions"][0]["id"] = []
        errors, _, _ = evaluate_report(self.packet, report)
        self.assertTrue(any("invalid report dimension id" in error for error in errors))

    def test_required_dimension_cannot_be_not_applicable(self) -> None:
        report = make_report(self.packet)
        report["dimensions"][0].update(status="NOT_APPLICABLE", score=None, evidence_refs=[])
        errors, _, _ = evaluate_report(self.packet, report)
        self.assertTrue(any("required dimension" in error for error in errors))

    def test_out_of_range_score_is_rejected(self) -> None:
        report = make_report(self.packet)
        report["dimensions"][0]["score"] = 5
        errors, _, _ = evaluate_report(self.packet, report)
        self.assertTrue(any("integer from 0 through 4" in error for error in errors))

    def test_false_pass_over_triggered_critical_condition_is_rejected(self) -> None:
        report = make_report(self.packet)
        report["critical_conditions"][0]["status"] = "TRIGGERED"
        errors, _, decision = evaluate_report(self.packet, report)
        self.assertEqual("FAIL", decision)
        self.assertTrue(any("decision must equal locally calculated FAIL" in error for error in errors))

    def test_insufficient_required_evidence_cannot_pass(self) -> None:
        report = make_report(self.packet)
        report["dimensions"][0].update(
            status="INSUFFICIENT_EVIDENCE", score=None, evidence_refs=[],
            rationale="The packet does not contain the needed check result.",
        )
        report["summary"]["decision"] = "INCONCLUSIVE"
        errors, score, decision = evaluate_report(self.packet, report)
        self.assertEqual([], errors)
        self.assertEqual(100, score)
        self.assertEqual("INCONCLUSIVE", decision)

    def test_target_change_makes_packet_stale(self) -> None:
        self.target.write_text("def answer():\n    return 0\n", encoding="utf-8")
        self.assertFalse(packet_snapshot_matches(self.packet, self.target))

    def test_bad_packet_hash_is_rejected(self) -> None:
        self.packet["evidence"][0]["content"] = "changed"
        self.assertTrue(any("packet id" in error for error in packet_errors(self.packet)))

    def test_bad_rubric_weight_sum_is_rejected(self) -> None:
        rubric = json.loads(json.dumps(DEFAULT_RUBRIC))
        rubric["target_types"]["code"]["dimensions"][0]["weight"] -= 1
        self.assertTrue(any("sum to 100" in error for error in validate_rubric(rubric)))

    def test_duplicate_json_keys_are_rejected(self) -> None:
        path = self.root / "duplicate.json"
        path.write_text('{"decision":"PASS","decision":"FAIL"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            load_json(path)

    def test_cli_packet_and_report_round_trip(self) -> None:
        packet_path = self.root / "packet.json"
        report_path = self.root / "report.json"
        create = subprocess.run([
            sys.executable, str(SKILL / "scripts" / "create_packet.py"),
            "--target", str(self.target), "--target-type", "code", "--task", "Review answer()",
            "--output", str(packet_path), "--collected-at", FIXED_TIME,
        ], capture_output=True, text=True, check=False)
        self.assertEqual(0, create.returncode, create.stderr)
        packet = load_json(packet_path)
        report_path.write_text(json.dumps(make_report(packet)), encoding="utf-8")
        validate = subprocess.run([
            sys.executable, str(SKILL / "scripts" / "validate_report.py"),
            "--packet", str(packet_path), "--report", str(report_path), "--target", str(self.target),
        ], capture_output=True, text=True, check=False)
        self.assertEqual(0, validate.returncode, validate.stdout + validate.stderr)
        self.assertEqual({
            "validation_status": "VALID", "decision": "PASS", "weighted_score": 100, "errors": [],
        }, json.loads(validate.stdout))


if __name__ == "__main__":
    unittest.main()
