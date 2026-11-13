import copy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from scripts.validate_assessment import (
    canonical_report_hash,
    downstream_gates_invalidated,
    validate_approval_invalidation,
    validate_gate_report,
    validate_gate_transition,
    validate_retry_counters,
    validate_spec_plan_crosswalk,
    validate_tool_trace,
    validate_workflow_record,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "tests" / "fixtures"
MATRIX = json.loads((FIXTURES / "requirement-map" / "valid.json").read_text())
WORKFLOW_ID = "d53e1c45-7793-4b58-94e6-9687519303dd"
SPEC_HASH = "8a384e33aac138794b553aac133536b7dbcb3db468b11d23d3414cc66820def7"
PLAN_HASH = "b893c8e8d85b9c6d995d0dc5e2dd6ff462da0b604b7677bfec358ffe340cd9ef"
GIT_SHA = "47f0571e37315c85623a814213d914ce50546d58"
NOW = "2026-11-12T12:00:00Z"


def make_gate(gate_name, status, input_hash, report_id, links=None, evidence=None):
    report = {
        "schema_version": "1.0",
        "workflow_id": WORKFLOW_ID,
        "report_id": report_id,
        "gate_name": gate_name,
        "input_hash": input_hash,
        "report_hash": "0" * 64,
        "hash_method": "stdlib-json-v1-no-report_hash",
        "assessor_version": "1.0.0",
        "status": status,
        "attempt": 1,
        "generated_at": NOW,
        "requirement_links": links or [],
        "checklist": [],
        "evidence": evidence or [],
        "findings": [],
        "errors": [],
    }
    report["report_hash"] = canonical_report_hash(report)
    return report


def make_workflow():
    gate_names = ["SPECIFICATION_ASSESSMENT", "PLAN_ASSESSMENT", "AGENT_EXECUTION", "INDEPENDENT_VERIFICATION", "RELEASE_READINESS"]
    return {
        "schema_version": "1.0",
        "workflow_id": WORKFLOW_ID,
        "created_at": NOW,
        "supersedes_workflow_id": None,
        "spec_hash": SPEC_HASH,
        "plan_hash": PLAN_HASH,
        "repo_commit": GIT_SHA,
        "worktree_id": "implementation",
        "release_in_scope": True,
        "requirement_map": copy.deepcopy(MATRIX),
        "environment": {
            "os": "macOS",
            "architecture": "arm64",
            "python_version": "3.13.1",
            "agent_name": "Codex",
            "agent_version": "unavailable",
            "tool_versions": [{"name": "pytest", "version": "8.3.4"}],
            "sandbox_provider": "sandbox-exec",
            "sandbox_policy_version": "2",
            "sandbox_policy_hash": "5" * 64,
            "sandbox_profile_version": "2",
            "sandbox_profile_hash": "5" * 64,
        },
        "sandbox": {"status": "NOT_ATTEMPTED", "provider": "sandbox-exec", "policy_hash": None, "profile_hash": None, "probes": []},
        "gate_state_map": {
            name: {"status": "NOT_RUN", "report_id": None, "input_hash": None, "attempt": 0, "updated_at": NOW, "superseded_by_report_id": None}
            for name in gate_names
        },
        "execution_state": "PENDING",
        "retry_counters": {"refine_reassess_attempt": 0, "prompt_version": 1, "whole_prompt_fallback_count": 0, "execution_attempt": 0},
        "gate_report_refs": [],
        "checkpoints": [],
        "storage": {"relative_path": f".sdd-local/runs/{WORKFLOW_ID}/", "local_only": True, "excluded_from_package": True, "exclusion_evidence_id": "E-EXCLUDE"},
        "redactions": {"secrets_redacted": True, "absolute_home_paths_redacted": True, "redaction_evidence_ids": ["E-REDACT"]},
        "approval_record": {"status": "NOT_REQUESTED", "approval_id": None, "scope": None, "spec_hash": None, "plan_hash": None, "input_hash": None, "approver_role": None, "decision_at": None, "evidence_id": None, "supersedes_approval_id": None, "invalidation_reason": None},
    }


def test_gate_report_schema_and_hash():
    schema = json.loads((SCHEMAS / "gate-report.schema.json").read_text())
    evidence = [{"evidence_id": "E-01", "kind": "REPORT", "relative_path": "reports/plan.json", "sha256": "1" * 64, "result": "PASS", "captured_at": NOW}]
    report = make_gate("PLAN_ASSESSMENT", "READY", PLAN_HASH, "plan-gate-1", MATRIX, evidence)
    report["checklist"] = [{"check_id": "traceability", "requirement_ids": ["R-01"], "criterion": "All links match.", "status": "PASS", "evidence_ids": ["E-01"], "rationale": None}]
    report["report_hash"] = canonical_report_hash(report)
    assert not list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(report))
    assert validate_gate_report(report) == []
    report["checklist"][0]["criterion"] = "mutated"
    assert any("report hash mismatch" in e for e in validate_gate_report(report))


def test_spec_gate_requires_nonempty_exact_workflow_links():
    schema = json.loads((SCHEMAS / "gate-report.schema.json").read_text())
    empty_spec = make_gate("SPECIFICATION_ASSESSMENT", "PASS", SPEC_HASH, "spec-empty")
    assert list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(empty_spec))
    assert any("requirement_links must be non-empty" in error for error in validate_gate_report(empty_spec))

    workflow = make_workflow()
    spec = make_gate("SPECIFICATION_ASSESSMENT", "PASS", SPEC_HASH, "spec-mapped", MATRIX[:1])
    assert not list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(spec))
    assert validate_gate_report(spec, workflow) == []


def test_ready_is_restricted_to_plan_gate():
    report = make_gate("SPECIFICATION_ASSESSMENT", "READY", SPEC_HASH, "spec-gate-1")
    assert validate_gate_report(report)


def test_not_required_release_gate_requires_out_of_scope_workflow():
    workflow = make_workflow()
    report = make_gate("RELEASE_READINESS", "NOT_REQUIRED", PLAN_HASH, "release-gate-1", MATRIX)
    assert any("NOT_REQUIRED" in e for e in validate_gate_report(report, workflow))


def test_workflow_record_schema_and_traceability():
    workflow = make_workflow()
    schema = json.loads((SCHEMAS / "workflow-record.schema.json").read_text())
    assert not list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(workflow))
    assert validate_workflow_record(workflow, MATRIX) == []
    workflow["requirement_map"][0]["task_ids"] = ["T-03"]
    assert any("authoritative matrix" in e for e in validate_workflow_record(workflow, MATRIX))


def test_workflow_crosswalk_requires_separate_plan_assessment_report():
    workflow = make_workflow()
    errors = validate_workflow_record(
        workflow,
        MATRIX,
        crosswalk={},
        spec_report={"requirements": []},
        spec_source="",
        plan_source="",
    )
    assert "crosswalk provenance inputs missing" in errors


def test_workflow_record_path_and_privacy_are_checked():
    workflow = make_workflow()
    workflow["storage"]["relative_path"] = ".sdd-local/runs/sdd-v02-20261112/"
    assert any("storage path must match workflow_id" in e for e in validate_workflow_record(workflow, MATRIX))
    workflow = make_workflow()
    workflow["storage"]["exclusion_evidence_id"] = "/Users" + "/private/workflow"
    assert any("privacy violation" in e for e in validate_workflow_record(workflow, MATRIX))


def test_approved_workflow_requires_plan_gate_manual_evidence():
    workflow = make_workflow()
    approval = json.loads((FIXTURES / "approval-record" / "valid.json").read_text())
    approval_bytes = (json.dumps(approval, indent=2) + "\n").encode()
    approval_hash = hashlib.sha256(approval_bytes).hexdigest()
    plan_evidence = [
        {"evidence_id": "E-PLAN", "kind": "REPORT", "relative_path": ".sdd-local/runs/run/plan-assessment.json", "sha256": "2" * 64, "result": "PASS", "captured_at": NOW},
        {"evidence_id": approval["evidence_id"], "kind": "MANUAL", "relative_path": f".sdd-local/runs/{WORKFLOW_ID}/approval-record.json", "sha256": approval_hash, "result": "PASS", "captured_at": NOW},
    ]
    spec_evidence = [{"evidence_id": "E-SPEC", "kind": "REPORT", "relative_path": ".sdd-local/runs/run/specification-assessment.json", "sha256": "3" * 64, "result": "PASS", "captured_at": NOW}]
    spec = make_gate("SPECIFICATION_ASSESSMENT", "PASS", SPEC_HASH, "spec-gate-1", MATRIX[:1], spec_evidence)
    plan = make_gate("PLAN_ASSESSMENT", "READY", PLAN_HASH, "plan-gate-1", MATRIX, plan_evidence)
    plan["checklist"] = [{"check_id": "approval", "requirement_ids": ["R-02"], "criterion": "Approval evidence is bound to exact hashes.", "status": "PASS", "evidence_ids": ["E-PLAN", approval["evidence_id"]], "rationale": None}]
    plan["report_hash"] = canonical_report_hash(plan)
    for report in (spec, plan):
        gate = report["gate_name"]
        workflow["gate_state_map"][gate] = {"status": report["status"], "report_id": report["report_id"], "input_hash": report["input_hash"], "attempt": 1, "updated_at": NOW, "superseded_by_report_id": None}
        workflow["gate_report_refs"].append({"gate_name": gate, "report_id": report["report_id"], "report_hash": report["report_hash"], "status": report["status"]})
    workflow["approval_record"] = approval
    assert validate_workflow_record(workflow, MATRIX, [spec, plan], hashlib.sha256(approval_bytes).hexdigest()) == []
    workflow["approved_scope"] = "OTHER_PROJECT_IMPLEMENTATION"
    assert any("hash/scope mismatch" in e for e in validate_workflow_record(workflow, MATRIX, [spec, plan], approval_hash))
    workflow.pop("approved_scope")
    plan["evidence"][1]["sha256"] = "0" * 64
    plan["report_hash"] = canonical_report_hash(plan)
    workflow["gate_report_refs"][1]["report_hash"] = plan["report_hash"]
    errors = validate_workflow_record(workflow, MATRIX, [spec, plan], hashlib.sha256(approval_bytes).hexdigest())
    assert any("approval evidence reference/hash mismatch" in e for e in errors)


def test_approved_record_without_plan_evidence_is_rejected():
    approval = json.loads((FIXTURES / "approval-record" / "valid.json").read_text())
    assert any("approval evidence report unavailable" in e for e in validate_approval_record_for_test(approval))


def validate_approval_record_for_test(approval):
    from scripts.validate_assessment import validate_approval_record
    current = {"spec_hash": SPEC_HASH, "plan_hash": PLAN_HASH, "input_hash": PLAN_HASH}
    return validate_approval_record(approval, current, "SDD_V02_IMPLEMENTATION_RELEASE", True, "RUNNING")


def test_retry_counters_and_terminal_reentry_are_bounded():
    valid = {"refine_reassess_attempt": 5, "prompt_version": 2, "whole_prompt_fallback_count": 1, "execution_attempt": 1}
    assert validate_retry_counters(valid) == []
    invalid = dict(valid, refine_reassess_attempt=6)
    assert validate_retry_counters(invalid)
    assert validate_gate_transition("PLAN_ASSESSMENT", "READY", "IN_PROGRESS")
    assert validate_gate_transition("PLAN_ASSESSMENT", "READY", "IN_PROGRESS", previous_report_id="r1", next_report_id="r1", supersedes_report_id="r1")
    assert validate_gate_transition("PLAN_ASSESSMENT", "READY", "IN_PROGRESS", previous_report_id="r1", next_report_id="r2", supersedes_report_id="r1") == []


def test_hash_change_requires_approval_invalidation_and_new_workflow():
    previous = json.loads((FIXTURES / "approval-record" / "valid.json").read_text())
    invalidated = json.loads((FIXTURES / "approval-record" / "invalidated.json").read_text())
    old = {"spec_hash": SPEC_HASH, "plan_hash": PLAN_HASH, "input_hash": PLAN_HASH}
    changed = dict(old, plan_hash="a" * 64, input_hash="a" * 64)
    assert validate_approval_invalidation(old, changed, previous, invalidated, "old-workflow", WORKFLOW_ID, "SDD_V02_IMPLEMENTATION_RELEASE", "SDD_V02_IMPLEMENTATION_RELEASE") == []
    assert validate_approval_invalidation(old, changed, previous, previous, "old-workflow", "old-workflow", "SDD_V02_IMPLEMENTATION_RELEASE", "SDD_V02_IMPLEMENTATION_RELEASE")
    old_record = make_workflow()
    old_record["approval_record"] = previous
    new_record = make_workflow()
    new_record["workflow_id"] = "ab8a3a91-a9e4-44b1-8b02-df4ef55a1af2"
    new_record["storage"]["relative_path"] = f".sdd-local/runs/{new_record['workflow_id']}/"
    new_record["supersedes_workflow_id"] = old_record["workflow_id"]
    new_record["plan_hash"] = "a" * 64
    new_record["approval_record"] = invalidated
    assert validate_workflow_record(new_record, MATRIX, previous_record=old_record) == []
    new_record["approval_record"]["status"] = "APPROVED"
    assert validate_workflow_record(new_record, MATRIX, previous_record=old_record)


def test_hash_change_requires_downstream_gate_invalidation():
    workflow = make_workflow()
    workflow["gate_state_map"]["PLAN_ASSESSMENT"]["status"] = "READY"
    assert validate_downstream_for_test(workflow["gate_state_map"], "specification")
    workflow["gate_state_map"]["PLAN_ASSESSMENT"]["status"] = "NOT_RUN"
    assert validate_downstream_for_test(workflow["gate_state_map"], "specification") == []
    assert downstream_gates_invalidated("package") == {"INDEPENDENT_VERIFICATION", "RELEASE_READINESS"}


def validate_downstream_for_test(states, changed_input):
    from scripts.validate_assessment import validate_downstream_invalidation
    return validate_downstream_invalidation(states, changed_input)


def test_tool_trace_schema_rejects_extra_nested_fields():
    schema = json.loads((SCHEMAS / "tool-trace.schema.json").read_text())
    trace = {"trace_id": "trace-1", "workflow_id": WORKFLOW_ID, "task_id": "T-04", "tool_name": "pytest", "tool_version": "8.3.4", "started_at": NOW, "ended_at": NOW, "input_summary": "schema suite", "output_summary": "passed", "exit_code": 0, "status": "PASS", "artifact_hashes": ["1" * 64], "checkpoint_id": None, "relative_cwd": "spec-driven-development/02-assessment/sdd-02-assess-implementation-spec", "redactions": {"secrets_redacted": True, "absolute_home_paths_redacted": True, "evidence_ids": ["E-TEST"]}}
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    assert not list(validator.iter_errors(trace))
    assert validate_tool_trace(trace) == []
    trace["redactions"]["raw_input"] = "secret"
    assert list(validator.iter_errors(trace))
    trace.pop("redactions")["absolute_home_paths_redacted"] = True
    trace["relative_cwd"] = "../../private"
    trace["redactions"] = {"secrets_redacted": True, "absolute_home_paths_redacted": True, "evidence_ids": []}
    assert validate_tool_trace(trace)


def test_spec_plan_crosswalk_requires_exact_ids_and_reports_gaps():
    spec_source = "Spec R-001 first. Spec R-002 second."
    plan_source = """## 요구사항 → AC → task → verification 매핑

| Requirement | AC IDs | Task IDs | Verification IDs |
|---|---|---|---|
| R-01 First | AC-01 | T-02 | V-02 |
"""
    spec_report = {"requirements": [{"requirement_id": "R-001"}, {"requirement_id": "R-002"}]}
    plan_row = {"requirement_id": "R-01", "acceptance_ids": ["AC-01"], "task_ids": ["T-02"], "verification_ids": ["V-02"]}
    plan_report = {"input_hash": PLAN_HASH, "requirements": [{"requirement_id": "R-01"}], "requirement_links": [plan_row]}
    crosswalk = {
        "mapping": [
            {"spec_requirement_id": "R-001", "spec_evidence": {"quote": "Spec R-001 first."}, "plan_links": [{"plan_requirement_id": "R-01", **{k: plan_row[k] for k in ("acceptance_ids", "task_ids", "verification_ids")}, "source_evidence": {"quote": "| R-01 First | AC-01 | T-02 | V-02 |", "input_sha256": PLAN_HASH}},], "coverage": "FULL"},
            {"spec_requirement_id": "R-002", "spec_evidence": {"quote": "Spec R-002 second."}, "plan_links": [], "coverage": "PARTIAL", "uncovered_clause": "No Plan task maps this requirement."},
        ],
        "overall_coverage": "PARTIAL",
        "gate_result": "BLOCKED",
        "unmapped_spec_requirement_ids": ["R-002"],
    }
    result = validate_spec_plan_crosswalk(spec_report, plan_report, crosswalk, spec_source, plan_source)
    assert result == {"errors": [], "overall_coverage": "PARTIAL", "gate_result": "BLOCKED", "unmapped_spec_requirement_ids": ["R-002"]}
    crosswalk["gate_result"] = "READY"
    assert any("gate result mismatch" in error for error in validate_spec_plan_crosswalk(spec_report, plan_report, crosswalk, spec_source, plan_source)["errors"])


def test_independent_gate_hash_must_match_frozen_candidate_and_gate_state():
    workflow = make_workflow()
    candidate_hash = "c" * 64
    workflow["checkpoints"].append({"checkpoint_id": "freeze-1", "task_id": "T-09", "created_at": NOW, "state": "COMPLETE", "repo_commit": GIT_SHA, "trace_ids": [], "artifact_hashes": [candidate_hash], "resume_allowed": False})
    workflow["gate_state_map"]["INDEPENDENT_VERIFICATION"].update(status="PASS", report_id="verify-1", input_hash=candidate_hash, attempt=1)
    report = make_gate("INDEPENDENT_VERIFICATION", "PASS", candidate_hash, "verify-1", MATRIX)
    assert validate_gate_report(report, workflow) == []
    report["input_hash"] = PLAN_HASH
    report["report_hash"] = canonical_report_hash(report)
    errors = validate_gate_report(report, workflow)
    assert any("input hash" in error or "frozen candidate" in error for error in errors)


def test_new_project_scope_and_worktree_are_supported():
    workflow = make_workflow()
    workflow["worktree_id"] = "another-project"
    workflow["approved_scope"] = "IMPLEMENTATION_ONLY"
    assert validate_workflow_record(workflow, MATRIX) == []
