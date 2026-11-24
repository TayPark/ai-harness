#!/usr/bin/env python3
"""Validate a ChatGPT report and compute its local decision."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from common import (
    canonical_json,
    digest,
    evaluate_report,
    evaluate_report_v2,
    load_json,
    packet_errors,
    packet_snapshot_matches,
    validate_rubric,
)


def emit(status: str, decision: str | None = None, score: float | None = None, errors: list[str] | None = None) -> None:
    print(json.dumps({
        "validation_status": status,
        "decision": decision,
        "weighted_score": score,
        "errors": errors or [],
    }, ensure_ascii=False, allow_nan=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path, help="same file or directory used to create the packet")
    parser.add_argument("--rubric", type=Path, help="pass the same custom rubric used to create the packet")
    parser.add_argument(
        "--report-schema",
        choices=("v1", "v2"),
        default="v1",
        help="select report schema version (default: v1; v2 requires report_schema_version 2.0 and judge_metadata)",
    )
    args = parser.parse_args()

    try:
        packet = load_json(args.packet.expanduser().resolve(strict=True))
        report: Any = load_json(args.report.expanduser().resolve(strict=True))
    except (OSError, UnicodeError, ValueError) as exc:
        emit("INVALID", errors=[f"cannot read packet or report: {exc}"])
        return 1

    errors = packet_errors(packet)
    if errors:
        emit("INVALID", errors=errors)
        return 1
    try:
        if args.rubric:
            current_rubric = load_json(args.rubric.expanduser().resolve(strict=True))
            rubric_errors = validate_rubric(current_rubric)
            if rubric_errors:
                emit("INVALID", errors=["invalid current rubric: " + "; ".join(rubric_errors)])
                return 1
            if digest(canonical_json(current_rubric)) != packet["rubric_sha256"]:
                emit("STALE", errors=["current rubric differs from the packet rubric"])
                return 2
        if not packet_snapshot_matches(packet, args.target):
            emit("STALE", errors=["target files or packet evidence differ from the captured snapshot"])
            return 2
    except (OSError, ValueError, RuntimeError) as exc:
        emit("STALE", errors=[f"cannot verify current target or rubric: {exc}"])
        return 2

    evaluator = evaluate_report_v2 if args.report_schema == "v2" else evaluate_report
    report_errors, score, decision = evaluator(packet, report)
    if report_errors:
        emit("INVALID", errors=report_errors)
        return 1
    emit("VALID", decision=decision, score=score)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
