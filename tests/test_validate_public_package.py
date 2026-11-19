#!/usr/bin/env python3
"""Unit tests for scripts/validate_public_package.py using temporary package fixtures."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_public_package.py"
SPEC = importlib.util.spec_from_file_location("validate_public_package", SCRIPT)
vpp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vpp)

ASSESSOR = "skills/spec-driven-development/02-assessment/sdd-02-assess-implementation-spec"


class ValidatorFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.write("README.md", "# Demo\n\nSee [demo](skills/demo/SKILL.md).\n")
        self.write("LICENSE", "MIT\n")
        self.write(".gitignore", "__pycache__/\n*.py[cod]\n.pytest_cache/\n")
        self.write(f"{ASSESSOR}/MANIFEST.txt", "")
        self.add_skill("demo")
        self.saved = (vpp.ROOT, vpp.SKILLS)
        vpp.ROOT, vpp.SKILLS = self.root, ("skills/demo",)

    def tearDown(self) -> None:
        vpp.ROOT, vpp.SKILLS = self.saved
        self.temp.cleanup()

    def write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def add_skill(self, name: str, *, frontmatter_name: str | None = None, metadata: bool = True) -> None:
        self.write(
            f"skills/{name}/SKILL.md",
            f"---\nname: {frontmatter_name or name}\ndescription: Demo skill. Use when testing.\n---\n\n# Demo\n",
        )
        if metadata:
            self.write(
                f"skills/{name}/agents/openai.yaml",
                'interface:\n  display_name: "Demo"\n  short_description: "Demo skill"\n',
            )

    def run_main(self) -> tuple[int, str]:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            code = vpp.main()
        return code, stderr.getvalue()

    def test_minimal_package_passes(self) -> None:
        code, errors = self.run_main()
        self.assertEqual(0, code, errors)

    def test_unregistered_skill_folder_fails(self) -> None:
        self.add_skill("extra")
        code, errors = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("unregistered skill folder", errors)
        self.assertIn("extra", errors)

    def test_frontmatter_name_mismatch_fails(self) -> None:
        self.add_skill("demo", frontmatter_name="other")
        code, errors = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("frontmatter name must match folder demo", errors)

    def test_missing_ui_metadata_fails(self) -> None:
        (self.root / "skills" / "demo" / "agents" / "openai.yaml").unlink()
        code, errors = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("missing UI metadata", errors)

    def test_personal_absolute_path_fails(self) -> None:
        self.write("skills/demo/notes.md", "Path: " + "/" + "Users" + "/alice/project\n")
        code, errors = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("personal absolute path found", errors)

    def test_broken_and_local_only_links_fail(self) -> None:
        self.write("skills/demo/links.md", "[gone](missing.md) and [private](../../.sdd-local/x.md)\n")
        code, errors = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("broken Markdown link", errors)
        self.assertIn("local-only path", errors)

    def test_manifest_drift_fails(self) -> None:
        self.write(f"{ASSESSOR}/extra.txt", "unlisted\n")
        code, errors = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("MANIFEST.txt differs", errors)


if __name__ == "__main__":
    unittest.main()
