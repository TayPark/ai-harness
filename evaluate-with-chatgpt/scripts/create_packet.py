#!/usr/bin/env python3
"""Create a privacy-filtered, hash-bound evaluation packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import load_json, make_packet, validate_rubric


DEFAULT_RUBRIC = Path(__file__).resolve().parents[1] / "rubrics" / "default.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path, help="one file or directory to evaluate")
    parser.add_argument("--target-type", required=True, help="type defined by the selected rubric")
    parser.add_argument("--task", required=True, help="short statement of evaluation goal")
    parser.add_argument("--output", required=True, type=Path, help="new packet JSON file outside the target")
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC, help="custom JSON rubric")
    parser.add_argument("--collected-at", help="ISO 8601 timestamp; set this for byte-for-byte reproducibility")
    args = parser.parse_args()

    try:
        target = args.target.expanduser().resolve(strict=True)
        rubric = load_json(args.rubric.expanduser().resolve(strict=True))
        errors = validate_rubric(rubric)
        if errors:
            raise ValueError("invalid rubric: " + "; ".join(errors))
        output = args.output.expanduser().resolve()
        if target.is_dir() and output.is_relative_to(target):
            raise ValueError("packet output must be outside the target directory")
        if target.is_file() and output == target:
            raise ValueError("packet output must not overwrite the target")
        if output.suffix.lower() != ".json":
            raise ValueError("packet output must use a .json extension")
        packet = make_packet(target, args.target_type, args.task, rubric, args.collected_at)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(packet, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({
        "packet_id": packet["packet_id"],
        "output": str(output),
        "included": packet["target"]["files_included"],
        "omitted": packet["target"]["files_omitted"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
