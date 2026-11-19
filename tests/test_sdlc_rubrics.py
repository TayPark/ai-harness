#!/usr/bin/env python3
"""Verify the canonical SDLC stage rubric and prevent duplicate copies."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
COMMON_PATH = ROOT / "skills" / "evaluate-with-chatgpt" / "scripts" / "common.py"
SPEC = importlib.util.spec_from_file_location("eval_chatgpt_common", COMMON_PATH)
common = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(common)

CANONICAL_RUBRIC = ROOT / "skills" / "sdlc-stage-rubrics" / "rubrics" / "sdlc-stages.json"
DUPLICATE_RUBRIC = ROOT / "skills" / "evaluate-with-chatgpt" / "rubrics" / "sdlc-stages.json"


class CanonicalSdlcRubricTests(unittest.TestCase):
    def test_canonical_rubric_is_valid_and_covers_all_stages(self) -> None:
        self.assertTrue(CANONICAL_RUBRIC.is_file(), f"missing canonical rubric: {CANONICAL_RUBRIC}")
        rubric = common.load_json(CANONICAL_RUBRIC)
        self.assertEqual([], common.validate_rubric(rubric))
        self.assertEqual(
            {"requirement", "implementation", "verification", "operation"},
            set(rubric["target_types"]),
        )

    def test_no_duplicate_sdlc_rubric_in_evaluate_with_chatgpt(self) -> None:
        self.assertFalse(
            DUPLICATE_RUBRIC.exists(),
            f"duplicate rubric copy should not exist: {DUPLICATE_RUBRIC}",
        )


if __name__ == "__main__":
    unittest.main()
