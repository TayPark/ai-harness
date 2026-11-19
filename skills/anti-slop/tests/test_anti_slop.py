#!/usr/bin/env python3
"""Unit tests for the bilingual anti-slop skill and deterministic checker."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
CHECK_SCRIPT = SCRIPTS_DIR / "check_slop.py"

sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS_DIR))
import check_slop  # noqa: E402


class TestAntiSlopSkillFiles(unittest.TestCase):
    """Verify skill structure, frontmatter, references, and markdown links."""

    def test_skill_frontmatter_and_references(self) -> None:
        skill_md = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_md.is_file(), "SKILL.md must exist")
        text = skill_md.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"), "SKILL.md must start with YAML frontmatter")
        closing = text.find("\n---\n", 4)
        self.assertGreater(closing, 4, "SKILL.md frontmatter must be terminated")
        frontmatter = text[4:closing]
        self.assertIn("name: anti-slop", frontmatter)
        self.assertIn("description:", frontmatter)

        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "#")):
                continue
            self.assertTrue(
                (SKILL_DIR / target).exists(),
                f"Broken relative markdown link in SKILL.md: {target}",
            )

    def test_banned_patterns_has_bilingual_sections(self) -> None:
        ref_md = SKILL_DIR / "references" / "banned-patterns.md"
        self.assertTrue(ref_md.is_file(), "references/banned-patterns.md must exist")
        text = ref_md.read_text(encoding="utf-8")
        self.assertIn("Part 1: English AI Tells", text)
        self.assertIn("Part 2: Korean AI Tells", text)
        self.assertIn("서법 보존", text)


class TestEnglishAntiSlop(unittest.TestCase):
    """Verify English AI-slop detection, rewrite passing, and clean-text guardrails."""

    SLOP_EN = (
        "Certainly! Great question! In today's fast-paced digital landscape, "
        "let's delve into how Redis caching works. It's not just a speed boost; "
        "it's a transformative paradigm shift that stands as a testament to "
        "seamless scalability — offering robust performance — and leveraging "
        "meticulous memory indexing — while fostering unprecedented reliability.\n\n"
        "- **Latency**: Cut p99 latency from 120 ms to 8 ms.\n"
        "- **Throughput**: Handle 45,000 req/s per node.\n"
        "- **Hit Ratio**: Maintain a 94% cache hit ratio.\n\n"
        "In conclusion, Redis serves as a crucial cornerstone. Let that sink in. "
        "I hope this helps!"
    )

    CLEAN_EN_REWRITE = (
        "Redis cuts p99 read latency from 120 ms to 8 ms by serving hot keys "
        "from RAM.\n\n"
        "A single node handles 45,000 req/s at a 94% cache hit ratio. Configure "
        "eviction before deployment:\n\n"
        "```sh\n"
        "redis-cli CONFIG SET maxmemory-policy allkeys-lru\n"
        "```\n\n"
        "Set `maxmemory` below 75% of host RAM so snapshots have headroom."
    )

    CLEAN_EN_WITH_QUOTES = (
        '"Let\'s delve into this tapestry," said the keynote speaker, "because '
        'it stands as a testament to seamless engineering." '
        "Our service stores user sessions in `PostgreSQL` with a 30-day TTL — "
        "measured across 12,000 active accounts.\n\n"
        "```python\n"
        "# Comments inside code blocks stay verbatim: leverage robust seamless\n"
        "TTL_SECONDS = 30 * 86400\n"
        "```"
    )

    def test_english_slop_triggers_all_expected_categories(self) -> None:
        result = check_slop.analyze_text(self.SLOP_EN)
        self.assertFalse(result["strict_pass"])
        categories = set(result["summary"].keys())
        self.assertIn("en-scaffolding", categories)
        self.assertIn("en-formulas", categories)
        self.assertIn("en-buzzwords", categories)
        self.assertIn("formatting-tells", categories)

    def test_english_rewrite_passes_strict_with_zero_findings(self) -> None:
        result = check_slop.analyze_text(self.CLEAN_EN_REWRITE)
        self.assertTrue(result["strict_pass"], result["findings"])
        self.assertEqual(result["total_findings"], 0)
        for fact in ("120 ms", "8 ms", "45,000 req/s", "94%", "allkeys-lru"):
            self.assertIn(fact, self.CLEAN_EN_REWRITE)

    def test_english_clean_with_code_and_quotes_has_zero_false_positives(self) -> None:
        result = check_slop.analyze_text(self.CLEAN_EN_WITH_QUOTES)
        self.assertTrue(result["strict_pass"], result["findings"])
        self.assertEqual(result["total_findings"], 0)


class TestKoreanAntiSlop(unittest.TestCase):
    """Verify Korean translation-ese detection, rewrite passing, and guardrails."""

    SLOP_KO = (
        "좋은 질문입니다! 이 글에서는 Redis 캐시의 동작을 살펴보겠습니다.\n\n"
        "Redis는 메모리를 통해 데이터를 처리하는 데 있어서 높은 성능을 가지고 있다. "
        "캐시 정책은 엔지니어에 의해 설정되어진다. "
        "이 기술은 단순한 속도 개선을 넘어 시스템 전체의 잠재력을 잠금 해제한다. "
        "결국 중요한 것은 94%의 적중률을 유지하는 것이다. "
        "이를 통해 p99 지연 시간을 120ms에서 8ms로 줄이는 이유다.\n\n"
        "빠르고, 안정적이며, 설정이 간단하지만, 메모리가 부족해서, 장애가 발생할 수 있다. "
        "첫 번째 장점은 속도이다. 두 번째 특징은 구조이다. "
        "세 번째 요소는 복제이다. 네 번째 강점은 확장성이다.\n\n"
        "이는 시사하는 바가 크다. 도움이 되셨기를 바랍니다!"
    )

    CLEAN_KO_REWRITE = (
        "Redis는 데이터를 RAM에 올려 p99 지연 시간을 120ms에서 8ms로 줄인다. "
        "적중률은 94% 수준을 유지한다.\n\n"
        "엔지니어가 `allkeys-lru` 정책을 설정하면 메모리 한도에 도달했을 때 오래된 "
        "키부터 비운다. 빠르고 안정적이며 설정도 간단하지만 메모리가 부족하면 "
        "성능이 급격히 떨어질 수 있다.\n\n"
        "스냅샷 저장 공간을 확보하려면 `maxmemory`를 전체 RAM의 75% 이하로 "
        "잡는 편이 안전해 보인다."
    )

    CLEAN_KO_WITH_QUOTES_AND_HEDGES = (
        '김 팀장은 "이번 개편이 단순한 속도 개선을 넘어 새로운 지평을 열었다"라고 밝혔다. '
        "실제 측정 결과 서버의 응답 속도는 평균 14ms로 줄어든 것으로 보인다. "
        "스마트폰 잠금 해제 속도와 앱의 초기 로딩 시간도 함께 단축됐다.\n\n"
        "```bash\n"
        "# 되어진다 / 잠금 해제 같은 코드 주석은 검사에서 제외\n"
        "echo 'ok'\n"
        "```"
    )

    def test_korean_slop_triggers_all_expected_categories(self) -> None:
        result = check_slop.analyze_text(self.SLOP_KO)
        self.assertFalse(result["strict_pass"])
        categories = set(result["summary"].keys())
        self.assertIn("ko-scaffolding", categories)
        self.assertIn("ko-translationese", categories)
        self.assertIn("ko-formulas", categories)
        self.assertIn("ko-connective-comma", categories)
        self.assertIn("ko-ending-monotony", categories)

    def test_korean_rewrite_passes_strict_with_zero_findings(self) -> None:
        result = check_slop.analyze_text(self.CLEAN_KO_REWRITE)
        self.assertTrue(result["strict_pass"], result["findings"])
        self.assertEqual(result["total_findings"], 0)
        for preserved in ("120ms", "8ms", "94%", "allkeys-lru", "75%", "안전해 보인다"):
            self.assertIn(preserved, self.CLEAN_KO_REWRITE)

    def test_korean_clean_with_quotes_and_literal_unlock_has_zero_false_positives(self) -> None:
        result = check_slop.analyze_text(self.CLEAN_KO_WITH_QUOTES_AND_HEDGES)
        self.assertTrue(result["strict_pass"], result["findings"])
        self.assertEqual(result["total_findings"], 0)


class TestThresholdsAndCLI(unittest.TestCase):
    """Verify co-occurrence thresholds and CLI --strict / --json interface."""

    def test_single_low_severity_tell_passes_strict(self) -> None:
        single_en = check_slop.analyze_text("Let us delve into the kernel page cache.")
        self.assertTrue(single_en["strict_pass"])
        self.assertEqual(single_en["total_findings"], 1)

        single_ko = check_slop.analyze_text("이 도구를 통해 로그를 빠르게 확인한다.")
        self.assertTrue(single_ko["strict_pass"])
        self.assertEqual(single_ko["total_findings"], 1)

    def test_three_buzzwords_in_same_paragraph_fail_strict(self) -> None:
        clustered = check_slop.analyze_text(
            "We delve into a seamless, robust framework for query caching."
        )
        self.assertFalse(clustered["strict_pass"])
        self.assertGreaterEqual(clustered["total_findings"], 3)

    def test_cli_strict_json_behavior(self) -> None:
        bad_proc = subprocess.run(
            [sys.executable, str(CHECK_SCRIPT), "--strict", "--json"],
            input="Certainly! Let's delve into this tapestry.",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(bad_proc.returncode, 1)
        payload = json.loads(bad_proc.stdout)
        self.assertFalse(payload["strict_pass"])

        good_proc = subprocess.run(
            [sys.executable, str(CHECK_SCRIPT), "--strict", "--json"],
            input="The kernel page cache stores recently read disk blocks in RAM.",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(good_proc.returncode, 0)
        good_payload = json.loads(good_proc.stdout)
        self.assertTrue(good_payload["strict_pass"])
        self.assertEqual(good_payload["total_findings"], 0)


if __name__ == "__main__":
    unittest.main()
