#!/usr/bin/env python3
"""Check the public skill package for structural and privacy mistakes."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised by missing dependency
    raise SystemExit("Install PyYAML before running this check.") from exc


ROOT = Path(__file__).resolve().parents[1]
SKILLS = (
    "spec-driven-development/01-plan/repository-implementation-planner",
    "spec-driven-development/02-assessment/implementation-spec-assessor",
    "spec-driven-development/03-execution-and-verification/implementation-plan-executor",
)
REQUIRED_ROOT_FILES = ("README.md", "LICENSE", ".gitignore")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
USER_PATH = re.compile(r"(?:/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|[A-Za-z]:\\Users\\[^\\\s]+)")
TRAVERSAL_IGNORED = {".git", ".venv", ".work"}
CACHE_PARTS = {"__pycache__", ".pytest_cache"}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def package_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not any(part in TRAVERSAL_IGNORED for part in path.relative_to(ROOT).parts)
    ]


def check_frontmatter(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(errors, f"missing YAML frontmatter: {path.relative_to(ROOT)}")
        return
    closing = text.find("\n---\n", 4)
    if closing < 0:
        fail(errors, f"unterminated YAML frontmatter: {path.relative_to(ROOT)}")
        return
    try:
        data = yaml.safe_load(text[4:closing])
    except yaml.YAMLError as exc:
        fail(errors, f"invalid frontmatter in {path.relative_to(ROOT)}: {exc}")
        return
    if not isinstance(data, dict):
        fail(errors, f"frontmatter must be a mapping: {path.relative_to(ROOT)}")
        return
    expected_name = path.parent.name
    if data.get("name") != expected_name:
        fail(errors, f"frontmatter name must match folder {expected_name}: {path.relative_to(ROOT)}")
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        fail(errors, f"frontmatter description is missing: {path.relative_to(ROOT)}")


def check_links(path: Path, text: str, errors: list[str]) -> None:
    for raw_target in MARKDOWN_LINK.findall(text):
        target = raw_target.strip().strip("<>")
        parsed = urlsplit(target)
        if parsed.scheme or target.startswith("#"):
            continue
        local = unquote(parsed.path)
        if not local:
            continue
        resolved = (path.parent / local).resolve()
        if not resolved.exists():
            fail(errors, f"broken Markdown link in {path.relative_to(ROOT)}: {target}")


def main() -> int:
    errors: list[str] = []
    for name in REQUIRED_ROOT_FILES:
        if not (ROOT / name).is_file():
            fail(errors, f"missing root file: {name}")

    for skill in SKILLS:
        directory = ROOT / skill
        skill_file = directory / "SKILL.md"
        if not directory.is_dir() or not skill_file.is_file():
            fail(errors, f"missing skill folder or SKILL.md: {skill}")
            continue
        check_frontmatter(skill_file, errors)
        metadata = directory / "agents" / "openai.yaml"
        if not metadata.is_file():
            fail(errors, f"missing UI metadata: {metadata.relative_to(ROOT)}")
        else:
            try:
                data = yaml.safe_load(metadata.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                fail(errors, f"invalid UI metadata in {metadata.relative_to(ROOT)}: {exc}")
            else:
                interface = data.get("interface") if isinstance(data, dict) else None
                if not isinstance(interface, dict) or not interface.get("display_name") or not interface.get("short_description"):
                    fail(errors, f"incomplete UI metadata: {metadata.relative_to(ROOT)}")

    assessor = ROOT / "spec-driven-development" / "02-assessment" / "implementation-spec-assessor"
    manifest_path = assessor / "MANIFEST.txt"
    if manifest_path.is_file():
        listed = {line.strip() for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()}
        actual = {
            path.relative_to(assessor).as_posix()
            for path in assessor.rglob("*")
            if path.is_file() and path.name != "MANIFEST.txt"
            and not any(part in TRAVERSAL_IGNORED for part in path.relative_to(assessor).parts)
        }
        if listed != actual:
            fail(errors, f"Assessor MANIFEST.txt differs: missing={sorted(actual - listed)}, extra={sorted(listed - actual)}")
    else:
        fail(errors, "missing spec-driven-development/02-assessment/implementation-spec-assessor/MANIFEST.txt")

    files = package_files()
    for path in files:
        relative = path.relative_to(ROOT)
        if path.suffix == ".pyc" or any(part in CACHE_PARTS for part in relative.parts):
            fail(errors, f"cache file must not be packaged: {relative}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if USER_PATH.search(text):
            fail(errors, f"personal absolute path found: {relative}")
        if path.suffix == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                fail(errors, f"invalid JSON in {relative}: {exc}")
        if path.suffix == ".yaml":
            try:
                yaml.safe_load(text)
            except yaml.YAMLError as exc:
                fail(errors, f"invalid YAML in {relative}: {exc}")
        if path.suffix == ".md":
            check_links(path, text, errors)

    ignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8") if (ROOT / ".gitignore").exists() else ""
    for required_pattern in ("__pycache__/", "*.py[cod]", ".pytest_cache/"):
        if required_pattern not in ignore_text:
            fail(errors, f".gitignore is missing {required_pattern}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: checked {len(files)} files across {len(SKILLS)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
