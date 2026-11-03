# Ledger CSV sum CLI — Implementation Specification v2

## Objective and scope
Implement a local Python CLI that sums decimal amounts in a UTF-8 CSV file. Use Python 3.11.9 and the standard library. Read one input file. Do not access the network or write files. Support macOS and Ubuntu 24.04. Input is trusted local data; do not execute file contents.

## Components and ownership
C-001 parser: owned by the data engineer. Accept decoded CSV records and return a Decimal total or a typed validation error. No I/O or mutation.
C-002 CLI: owned by the application engineer. Parse arguments, read UTF-8 input, call C-001, and write exactly one result line or one error record. Depends on C-001.
C-003 verifier: owned by the quality engineer. Independently runs unit and end-to-end fixtures after C-001 and C-002 integration. It does not change implementation code.

## Input and output contract
Input header must contain exactly one `amount` column. Rows may contain additional columns, which are ignored. Accept 0–1000 data rows. Each amount must be a finite base-10 decimal with at most two fractional digits. Reject missing values, extra CSV fields, malformed quoting, invalid UTF-8, duplicate or absent amount headers, and more than 1000 data rows.
Round no values. Sum using Decimal. Format total with exactly two fractional digits and a trailing newline. Empty data produces `0.00`. Success writes only the result to stdout and exits 0.
On failure, stdout is empty. Stderr contains one JSON object with keys `code`, `message`, and `run_id`, followed by newline. Codes are INVALID_UTF8, INVALID_CSV, INVALID_HEADER, INVALID_AMOUNT, ROW_LIMIT, and IO_ERROR. Exit 2 for input validation errors. Exit 3 for file I/O errors. Messages contain no file contents. Generate a UUID run_id per invocation.

## Reliability and observability
Do not retry. Do not return partial totals. Propagate parser errors to CLI unchanged. A failed read emits IO_ERROR. Do not mutate inputs. Include run_id in every error. Do not log amounts or file contents. The parser is pure and idempotent for identical records.

## Reproducibility
Pin Python 3.11.9 and pytest 8.3.5. Use a container image pinned by digest in the release pipeline; the release owner must record and verify the digest before release. Do not invent the digest in this prompt. Set locale to C.UTF-8 and timezone to UTC. Fixtures are committed as UTF-8 text with SHA-256 recorded in the test manifest. Unit tests use fixed run_id injection; CLI tests validate UUID format without comparing generated values.

## Acceptance and verification
Unit tests cover zero, one, and 1000 rows; empty data; two decimal places; trailing zeros; negative values; malformed UTF-8; bad quoting; missing/duplicate headers; missing amount; >2 fractional digits; 1001 rows; and no partial output. End-to-end tests verify stdout, stderr JSON keys, exit codes, UUID format, and no file writes. Run `python -m pytest -q` in the pinned image. All tests must pass. Run once, repeat in a clean container, and compare stdout, stderr after normalizing run_id, and exit codes. Compare fixture hashes. Record command, image digest, interpreter version, fixture hash, result, and run_id in the report.

## Agent execution and handoff
Implement C-001, then C-002, then C-003 verification. Each owner records changed files and unit results. Handoff artifact has schema `{component_id: string, status: PASS|FAIL, test_command: string, exit_code: integer, evidence_path: string}`. The integrator verifies dependency order, both component outputs, error propagation and end-to-end fixtures. Tools may read/write only the task checkout and fixture directory. Completion requires all acceptance tests, clean repeat-run comparison, reviewed image digest, and a final evidence report.

## Explicit release decision
The release owner must choose and approve the container image digest. Until then implementation and local tests may proceed, but release readiness is blocked.
