import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts.validate_assessment import (
    downstream_gates_invalidated,
    parse_requirement_matrix,
    validate_gate_transition,
    validate_requirement_map,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "requirement-map"
SCHEMA = json.loads((ROOT / "schemas" / "workflow-record.schema.json").read_text())
EXPECTED = json.loads((FIXTURES / "valid.json").read_text())
MAP_SCHEMA = SCHEMA["$defs"]["requirement_map"]


def test_authoritative_matrix_fixture_is_valid():
    assert not list(Draft202012Validator(MAP_SCHEMA, format_checker=FormatChecker()).iter_errors(EXPECTED))
    assert validate_requirement_map(EXPECTED, EXPECTED) == []


@pytest.mark.parametrize(
    "name",
    [
        "empty-map.json",
        "missing-task-ids.json",
        "wrong-id-type.json",
        "duplicate-r-id.json",
        "duplicate-link-id.json",
        "unknown-r-id.json",
        "dangling-ac-id.json",
        "dangling-task-id.json",
        "dangling-v-id.json",
        "mapping-mismatch.json",
    ],
)
def test_invalid_requirement_maps_are_rejected(name):
    candidate = json.loads((FIXTURES / name).read_text())
    assert validate_requirement_map(candidate, EXPECTED)


def test_source_parser_extracts_exact_registry_and_matrix():
    source = """## 요구사항 → AC → task → verification 매핑

| Requirement | AC IDs | Task IDs | Verification IDs |
|---|---|---|---|
| R-01 First | AC-01 | T-02 | V-02 |
| R-02 Second | AC-02, AC-03 | T-03, T-04 | V-03, V-20 |
"""
    assert parse_requirement_matrix(source) == [
        {"requirement_id": "R-01", "acceptance_ids": ["AC-01"], "task_ids": ["T-02"], "verification_ids": ["V-02"]},
        {"requirement_id": "R-02", "acceptance_ids": ["AC-02", "AC-03"], "task_ids": ["T-03", "T-04"], "verification_ids": ["V-03", "V-20"]},
    ]


@pytest.mark.parametrize(
    "heading",
    [
        "## Requirement → AC → Task → Verification Mapping",
        "## Requirement -> AC -> Task -> Verification Mapping",
    ],
)
def test_source_parser_accepts_english_matrix_headings(heading):
    source = f"""{heading}

| Requirement | AC IDs | Task IDs | Verification IDs |
|---|---|---|---|
| R-01 First | AC-01 | T-02 | V-02 |
"""
    assert parse_requirement_matrix(source) == [
        {"requirement_id": "R-01", "acceptance_ids": ["AC-01"], "task_ids": ["T-02"], "verification_ids": ["V-02"]},
    ]


def test_gate_transitions_fail_closed():
    assert not validate_gate_transition("PLAN_ASSESSMENT", "NOT_RUN", "IN_PROGRESS")
    assert not validate_gate_transition("PLAN_ASSESSMENT", "IN_PROGRESS", "READY")
    assert not validate_gate_transition("PLAN_ASSESSMENT", "NEEDS_REVISION", "BLOCKED")
    assert validate_gate_transition("PLAN_ASSESSMENT", "READY", "IN_PROGRESS")
    assert validate_gate_transition("RELEASE_READINESS", "IN_PROGRESS", "NOT_REQUIRED", release_in_scope=True)
    assert not validate_gate_transition("RELEASE_READINESS", "IN_PROGRESS", "NOT_REQUIRED", release_in_scope=False)


def test_hash_changes_invalidate_dependent_gates():
    assert downstream_gates_invalidated("specification") == {
        "PLAN_ASSESSMENT", "AGENT_EXECUTION", "INDEPENDENT_VERIFICATION", "RELEASE_READINESS"
    }
    assert downstream_gates_invalidated("package") == {"INDEPENDENT_VERIFICATION", "RELEASE_READINESS"}
