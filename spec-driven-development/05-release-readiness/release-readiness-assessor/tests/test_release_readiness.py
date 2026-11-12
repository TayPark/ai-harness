import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
ASSESSOR = REPO_ROOT / "spec-driven-development" / "02-assessment" / "implementation-spec-assessor"
sys.path.insert(0, str(ASSESSOR))
from scripts.validate_assessment import canonical_report_hash, validate_gate_report

REQUIREMENT_MAP = json.loads((ASSESSOR / "tests" / "fixtures" / "requirement-map" / "valid.json").read_text(encoding="utf-8"))

SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
SCENARIO = (ROOT / "scenarios" / "pre-publication-release-gate.md").read_text(encoding="utf-8")
NOW = "2026-11-12T12:00:00Z"
CANDIDATE_HASH = "a" * 64


def test_release_gate_requires_independent_pass_before_publication():
    assert "Independent Verification `PASS`" in SKILL
    assert "before publication" in SKILL
    assert "Do not publish" in SKILL


def test_slo_na_requires_source_backed_absence():
    assert "source-backed inspection shows that no service SLO is defined" in SKILL
    assert "Do not create a numeric target" in SKILL


def test_security_records_actual_checks_and_findings():
    for field in ("name, version, scope", "policy source path and hash", "exit result", "findings"):
        assert field in SKILL
    assert "unresolved findings block `PASS`" in SKILL


def test_rollback_and_operations_have_required_evidence():
    assert "`v0.1b` baseline" in SKILL
    assert "new revert commit" in SKILL
    assert "installation, update, and recovery" in SKILL
    assert "observable success condition" in SKILL


def test_manual_scenario_is_marked_unrun():
    assert "Manual scenario" in SCENARIO
    assert "Status: `NOT RUN`" in SCENARIO


def release_report(with_evidence):
    source_paths = {
        "E-SLO-README": "README.md",
        "E-SLO-SDD-README": "spec-driven-development/README.md",
        "E-SECURITY": "scripts/validate_public_package.py",
        "E-ROLLBACK": "spec-driven-development/README.md",
        "E-OPERATIONS": "README.md",
    }
    evidence = []
    if with_evidence:
        for evidence_id, relative_path in source_paths.items():
            digest = hashlib.sha256((REPO_ROOT / relative_path).read_bytes()).hexdigest()
            evidence.append({
                "evidence_id": evidence_id,
                "kind": "SCAN" if evidence_id == "E-SECURITY" else "REPORT",
                "relative_path": relative_path,
                "sha256": digest,
                "result": "PASS",
                "captured_at": NOW,
            })
    checklist = [
        {"check_id": "SLO", "requirement_ids": ["R-12"], "criterion": "Use the existing SLO or source-backed absence.", "status": "N_A_WITH_RATIONALE" if with_evidence else "PASS", "evidence_ids": ["E-SLO-README", "E-SLO-SDD-README"] if with_evidence else [], "rationale": "The inspected package documentation defines no service SLO." if with_evidence else None},
        {"check_id": "SECURITY", "requirement_ids": ["R-12"], "criterion": "Record applicable security check results and findings.", "status": "PASS", "evidence_ids": ["E-SECURITY"] if with_evidence else [], "rationale": None},
        {"check_id": "ROLLBACK", "requirement_ids": ["R-12"], "criterion": "Provide the v0.1b restore and v0.2 revert procedure.", "status": "PASS", "evidence_ids": ["E-ROLLBACK"] if with_evidence else [], "rationale": None},
        {"check_id": "OPERATIONS", "requirement_ids": ["R-12"], "criterion": "Provide installation, update, and recovery checks.", "status": "PASS", "evidence_ids": ["E-OPERATIONS"] if with_evidence else [], "rationale": None},
    ]
    report = {
        "schema_version": "1.0",
        "workflow_id": "d53e1c45-7793-4b58-94e6-9687519303dd",
        "report_id": "release-test-001",
        "gate_name": "RELEASE_READINESS",
        "input_hash": CANDIDATE_HASH,
        "report_hash": "0" * 64,
        "hash_method": "stdlib-json-v1-no-report_hash",
        "assessor_version": "1.0.0",
        "status": "PASS",
        "attempt": 1,
        "generated_at": NOW,
        "requirement_links": REQUIREMENT_MAP,
        "checklist": checklist,
        "evidence": evidence,
        "findings": [],
        "errors": [],
    }
    report["report_hash"] = canonical_report_hash(report)
    return report


def release_workflow():
    return {
        "workflow_id": "d53e1c45-7793-4b58-94e6-9687519303dd",
        "release_in_scope": True,
        "requirement_map": REQUIREMENT_MAP,
        "gate_state_map": {
            "INDEPENDENT_VERIFICATION": {"status": "PASS", "input_hash": CANDIDATE_HASH},
            "RELEASE_READINESS": {"status": "PASS", "input_hash": CANDIDATE_HASH},
        },
        "checkpoints": [{"task_id": "T-09", "state": "COMPLETE", "artifact_hashes": [CANDIDATE_HASH]}],
    }


def test_release_pass_requires_evidence_and_accepts_source_backed_slo_na():
    workflow = release_workflow()
    errors = validate_gate_report(release_report(with_evidence=False), workflow)
    for required in ("SECURITY", "ROLLBACK", "OPERATIONS", "SLO"):
        assert any(required in error and "evidence" in error for error in errors), (required, errors)

    assert validate_gate_report(release_report(with_evidence=True), workflow) == []
