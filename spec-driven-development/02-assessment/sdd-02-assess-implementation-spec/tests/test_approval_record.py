import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts.validate_assessment import validate_approval_record

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "approval-record"
SCHEMA = json.loads((ROOT / "schemas" / "workflow-record.schema.json").read_text())["$defs"]["approval_record"]
WORKFLOW_ID = "d53e1c45-7793-4b58-94e6-9687519303dd"
CURRENT = {
    "spec_hash": "8a384e33aac138794b553aac133536b7dbcb3db468b11d23d3414cc66820def7",
    "plan_hash": "b893c8e8d85b9c6d995d0dc5e2dd6ff462da0b604b7677bfec358ffe340cd9ef",
    "input_hash": "b893c8e8d85b9c6d995d0dc5e2dd6ff462da0b604b7677bfec358ffe340cd9ef",
}
SCOPE = "SDD_V02_IMPLEMENTATION_RELEASE"


def load(name):
    return json.loads((FIXTURES / name).read_text())


def evidence_for(record, content_hash):
    return [{
        "evidence_id": record["evidence_id"],
        "kind": "MANUAL",
        "relative_path": f".sdd-local/runs/{WORKFLOW_ID}/approval-record.json",
        "sha256": content_hash,
        "result": "PASS",
        "captured_at": record["decision_at"],
    }]


def test_approved_record_schema_and_evidence_contract():
    record = load("valid.json")
    assert not list(Draft202012Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(record))
    digest = hashlib.sha256(b"approval record bytes").hexdigest()
    assert validate_approval_record(record, CURRENT, SCOPE, True, "PENDING", evidence_for(record, digest), digest, WORKFLOW_ID) == []


@pytest.mark.parametrize("name", ["missing-fields.json", "wrong-types.json", "unknown-fields.json"])
def test_schema_invalid_approval_records_are_rejected(name):
    assert list(Draft202012Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(load(name)))


@pytest.mark.parametrize("name", ["pending.json", "declined.json", "invalidated.json"])
def test_non_approved_states_block_execution(name):
    record = load(name)
    digest = hashlib.sha256(b"approval record bytes").hexdigest()
    assert validate_approval_record(record, CURRENT, SCOPE, True, "RUNNING", evidence_for(record, digest), digest, WORKFLOW_ID)


def test_hash_mismatch_blocks_execution():
    record = load("hash-mismatch.json")
    digest = hashlib.sha256(b"approval record bytes").hexdigest()
    assert any("hash/scope mismatch" in e for e in validate_approval_record(record, CURRENT, SCOPE, True, "PENDING", evidence_for(record, digest), digest, WORKFLOW_ID))


def test_missing_evidence_blocks_approval():
    record = load("missing-evidence.json")
    digest = hashlib.sha256(b"approval record bytes").hexdigest()
    errors = validate_approval_record(record, CURRENT, SCOPE, True, "PENDING", [], digest, WORKFLOW_ID)
    assert any("evidence reference/hash mismatch" in e for e in errors)


def test_pending_requires_plan_ready():
    record = load("pending.json")
    assert any("requires Plan Gate READY" in e for e in validate_approval_record(record, CURRENT, SCOPE, False, "PENDING"))


def test_scope_mismatch_is_rejected_against_authorized_scope():
    record = load("scope-mismatch.json")
    digest = hashlib.sha256(b"approval record bytes").hexdigest()
    assert validate_approval_record(record, CURRENT, SCOPE, True, "PENDING", evidence_for(record, digest), digest, WORKFLOW_ID)
