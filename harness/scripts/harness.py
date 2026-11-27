#!/usr/bin/env python3
"""Multi-model SSOT agent harness CLI (Python 3 standard library only)."""

from __future__ import annotations

import argparse
import datetime
import fcntl
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = REPO_ROOT / "harness"
CORE_DIR = HARNESS_DIR / "core"
ROLES_DIR = HARNESS_DIR / "roles"
OVERRIDES_DIR = HARNESS_DIR / "overrides"
UPSTREAM_LOCK = HARNESS_DIR / "upstream-skills.lock.json"

GENERATED_HEADER = "# GENERATED FROM ai-harness (TayPark/ai-harness) - DO NOT EDIT DIRECTLY\n"
HOOK_MARKER = "# ai-harness-sync"
ANTIGRAVITY_HOOK_KEY = "ai-harness-sync"
DEFAULT_TTL_SECONDS = 10800  # 3 hours
MAX_BACKUPS = 10
PUBLIC_EXCLUDED_SKILLS = {"career-management", ".sdd-local"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def strip_jsonc(raw: str) -> str:
    """Remove // and /* */ comments outside JSON string literals."""
    out: list[str] = []
    i = 0
    n = len(raw)
    in_str = False
    escape = False
    while i < n:
        ch = raw[i]
        if in_str:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and raw[i + 1] == "/":
            i += 2
            while i < n and raw[i] not in ("\n", "\r"):
                i += 1
            continue
        if ch == "/" and i + 1 < n and raw[i + 1] == "*":
            i += 2
            while i + 1 < n and not (raw[i] == "*" and raw[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def load_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return {}
    data = json.loads(strip_jsonc(raw))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def atomic_write_text(target: Path, content: str, mode: int | None = None) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=f".{target.name}.tmp.")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(tmp_path, mode)
        elif target.exists() and not target.is_symlink():
            os.chmod(tmp_path, stat.S_IMODE(target.stat().st_mode))
        os.replace(tmp_path, target)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def atomic_write_json(target: Path, data: dict[str, Any], mode: int | None = None) -> None:
    atomic_write_text(target, json.dumps(data, indent=2, ensure_ascii=False) + "\n", mode=mode)


def host_specs(home: Path) -> dict[str, dict[str, Any]]:
    return {
        "gemini": {
            "config_dir": home / ".gemini" / "config",
            "root_instruction": home / ".gemini" / "config" / "AGENTS.md",
            "retired_files": [],
            "response_file": home / ".gemini" / "config" / "RESPONSE.md",
            "roles_dir": home / ".gemini" / "config" / "roles",
            "skills_dir": home / ".gemini" / "config" / "skills",
            "hooks_file": home / ".gemini" / "config" / "hooks.json",
            "hooks_kind": "antigravity",
            "extra_backup_files": [home / ".gemini" / "config" / "mcp_config.json"],
            "override": OVERRIDES_DIR / "gemini.md",
        },
        "claude": {
            "config_dir": home / ".claude",
            "root_instruction": home / ".claude" / "CLAUDE.md",
            "retired_files": [home / ".claude" / "AGENTS.md"],
            "response_file": home / ".claude" / "RESPONSE.md",
            "roles_dir": home / ".claude" / "roles",
            "skills_dir": home / ".claude" / "skills",
            "hooks_file": home / ".claude" / "settings.json",
            "hooks_kind": "claude",
            "extra_backup_files": [],
            "override": OVERRIDES_DIR / "claude.md",
        },
        "codex": {
            "config_dir": home / ".codex",
            "root_instruction": home / ".codex" / "AGENTS.md",
            "retired_files": [],
            "response_file": home / ".codex" / "RESPONSE.md",
            "roles_dir": home / ".codex" / "roles",
            "skills_dir": home / ".codex" / "skills",
            "hooks_file": home / ".codex" / "hooks.json",
            "hooks_kind": "codex",
            "extra_backup_files": [home / ".codex" / "config.toml"],
            "override": OVERRIDES_DIR / "codex.md",
        },
    }


def state_dir_for(home: Path) -> Path:
    return home / ".local" / "state" / "ai-harness"


def backup_root_for(home: Path) -> Path:
    return home / ".ai-harness-backups"


def upstream_cache_for(home: Path) -> Path:
    return home / ".cache" / "ai-harness" / "upstream"


def discover_local_skills(repo_root: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    skills_root = repo_root / "skills"
    if not skills_root.is_dir():
        return found
    candidates = list(skills_root.glob("*")) + list(skills_root.glob("spec-driven-development/*/sdd-*"))
    for candidate in sorted(candidates):
        if not candidate.is_dir():
            continue
        if candidate.name in PUBLIC_EXCLUDED_SKILLS:
            continue
        if (candidate / "SKILL.md").is_file():
            found[candidate.name] = candidate.resolve()
    return found


def discover_upstream_skills(home: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not UPSTREAM_LOCK.is_file():
        return found
    lock = load_json_file(UPSTREAM_LOCK)
    cache_root = upstream_cache_for(home)
    for entry in lock.get("skills", []):
        name = entry.get("name")
        subpath = entry.get("subpath", "")
        if not name:
            continue
        target = (cache_root / name / subpath).resolve() if subpath else (cache_root / name).resolve()
        if (target / "SKILL.md").is_file():
            found[name] = target
    return found


def sync_upstream_repos(home: Path, quiet: bool = False) -> list[str]:
    warnings: list[str] = []
    if not UPSTREAM_LOCK.is_file():
        return warnings
    lock = load_json_file(UPSTREAM_LOCK)
    cache_root = upstream_cache_for(home)
    cache_root.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o ConnectTimeout=3"

    for entry in lock.get("skills", []):
        name = entry.get("name")
        url = entry.get("repo_url")
        ref = entry.get("ref", "main")
        pinned_sha = entry.get("sha")
        if not name or not url:
            continue
        dest = cache_root / name
        try:
            if not dest.exists():
                subprocess.run(
                    ["git", "clone", "--depth", "1", "--branch", ref, url, str(dest)],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=20,
                    check=True,
                )
            elif (dest / ".git").exists():
                subprocess.run(
                    ["git", "-C", str(dest), "fetch", "--depth", "1", "origin", ref],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15,
                    check=True,
                )
                subprocess.run(
                    ["git", "-C", str(dest), "reset", "--hard", f"origin/{ref}"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10,
                    check=True,
                )
            if pinned_sha:
                subprocess.run(
                    ["git", "-C", str(dest), "checkout", "--quiet", pinned_sha],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10,
                    check=True,
                )
        except (subprocess.SubprocessError, OSError) as exc:
            msg = f"upstream sync skipped for {name}: {exc}"
            warnings.append(msg)
            if not quiet:
                print(f"[warn] {msg}", file=sys.stderr)
    return warnings


def cmd_backup(home: Path, quiet: bool = False) -> Path:
    broot = backup_root_for(home)
    broot.mkdir(parents=True, exist_ok=True)
    os.chmod(broot, 0o700)

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bdir = broot / ts
    suffix = 1
    while bdir.exists():
        bdir = broot / f"{ts}-{suffix}"
        suffix += 1
    bdir.mkdir(parents=True, mode=0o700)
    os.chmod(bdir, 0o700)

    specs = host_specs(home)
    tracked_files: list[Path] = []
    for spec in specs.values():
        tracked_files.append(spec["root_instruction"])
        tracked_files.extend(spec["retired_files"])
        tracked_files.append(spec["response_file"])
        tracked_files.append(spec["hooks_file"])
        tracked_files.extend(spec["extra_backup_files"])

    file_records: list[dict[str, Any]] = []
    for path in tracked_files:
        rel = path.relative_to(home).as_posix()
        if path.is_symlink():
            file_records.append(
                {
                    "relpath": rel,
                    "kind": "symlink",
                    "symlink_target": os.readlink(path),
                }
            )
        elif path.is_file():
            dst = bdir / "files" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dst)
            os.chmod(dst, 0o600)
            file_records.append(
                {
                    "relpath": rel,
                    "kind": "file",
                    "mode": stat.S_IMODE(path.stat().st_mode),
                    "backup_relpath": (Path("files") / rel).as_posix(),
                }
            )
        else:
            file_records.append({"relpath": rel, "kind": "absent"})

    dir_inventories: dict[str, list[dict[str, Any]]] = {}
    for spec in specs.values():
        for d in (spec["skills_dir"], spec["roles_dir"]):
            d_rel = d.relative_to(home).as_posix()
            entries: list[dict[str, Any]] = []
            if d.is_dir():
                for child in sorted(d.iterdir()):
                    if child.is_symlink():
                        entries.append(
                            {
                                "name": child.name,
                                "kind": "symlink",
                                "symlink_target": os.readlink(child),
                            }
                        )
                    elif child.is_dir():
                        entries.append({"name": child.name, "kind": "dir"})
                    elif child.is_file():
                        entries.append({"name": child.name, "kind": "file"})
            dir_inventories[d_rel] = entries

    manifest = {
        "schema_version": "1.0",
        "created_at": datetime.datetime.now().isoformat(),
        "home": str(home),
        "files": file_records,
        "directories": dir_inventories,
    }
    atomic_write_json(bdir / "manifest.json", manifest, mode=0o600)

    # Enforce retention limit
    existing_backups = sorted(
        [p for p in broot.iterdir() if p.is_dir() and (p / "manifest.json").is_file()],
        key=lambda p: p.name,
    )
    for old in existing_backups[:-MAX_BACKUPS]:
        shutil.rmtree(old, ignore_errors=True)

    if not quiet:
        print(f"[backup] created {bdir} ({len(file_records)} tracked paths)")
    return bdir


def cmd_restore(home: Path, target_ts: str, quiet: bool = False) -> Path:
    broot = backup_root_for(home)
    if not broot.is_dir():
        raise SystemExit(f"No backups directory found at {broot}")

    if target_ts == "latest":
        candidates = sorted(
            [p for p in broot.iterdir() if p.is_dir() and (p / "manifest.json").is_file()],
            key=lambda p: p.name,
        )
        if not candidates:
            raise SystemExit(f"No backups available in {broot}")
        bdir = candidates[-1]
    else:
        bdir = broot / target_ts
        if not (bdir / "manifest.json").is_file():
            raise SystemExit(f"Backup not found: {bdir}")

    manifest = load_json_file(bdir / "manifest.json")

    # 1. Remove newly created managed artifacts not present in original directory inventory
    state_manifest_path = state_dir_for(home) / "manifest.json"
    orig_dir_names: dict[str, set[str]] = {
        d_rel: {e["name"] for e in entries}
        for d_rel, entries in manifest.get("directories", {}).items()
    }
    if state_manifest_path.is_file():
        smanifest = load_json_file(state_manifest_path)
        for rel in smanifest.get("managed_symlinks", []):
            p = home / rel
            parent_rel = p.parent.relative_to(home).as_posix()
            if p.name not in orig_dir_names.get(parent_rel, set()) and (p.is_symlink() or p.is_file()):
                p.unlink(missing_ok=True)
        for rel in smanifest.get("managed_role_files", []):
            p = home / rel
            parent_rel = p.parent.relative_to(home).as_posix()
            if p.name not in orig_dir_names.get(parent_rel, set()) and p.is_file():
                p.unlink(missing_ok=True)
                if p.parent.is_dir() and not any(p.parent.iterdir()):
                    p.parent.rmdir()

    # 2. Restore original directory symlinks
    for d_rel, entries in manifest.get("directories", {}).items():
        d_path = home / d_rel
        for entry in entries:
            if entry["kind"] == "symlink":
                link_path = d_path / entry["name"]
                d_path.mkdir(parents=True, exist_ok=True)
                if link_path.is_symlink() or link_path.is_file():
                    link_path.unlink(missing_ok=True)
                if not link_path.exists():
                    os.symlink(entry["symlink_target"], link_path)

    # 3. Restore tracked files
    for rec in manifest.get("files", []):
        dst = home / rec["relpath"]
        kind = rec["kind"]
        if kind == "absent":
            if dst.is_symlink() or dst.is_file():
                dst.unlink(missing_ok=True)
        elif kind == "symlink":
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_symlink() or dst.is_file():
                dst.unlink(missing_ok=True)
            os.symlink(rec["symlink_target"], dst)
        elif kind == "file":
            src = bdir / rec["backup_relpath"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_symlink():
                dst.unlink(missing_ok=True)
            data = src.read_text(encoding="utf-8")
            atomic_write_text(dst, data, mode=rec.get("mode"))

    if not quiet:
        print(f"[restore] restored snapshot {bdir.name}")
    return bdir


def render_template(text: str, home: Path, host_roles_dir: Path) -> str:
    return (
        text.replace("{{HOME}}", str(home))
        .replace("{{REPO_DIR}}", str(REPO_ROOT))
        .replace("{{HOST_ROLES_DIR}}", str(host_roles_dir))
    )


def build_root_instruction(spec: dict[str, Any], home: Path) -> str:
    parts = [
        GENERATED_HEADER,
        (CORE_DIR / "AGENTS.md").read_text(encoding="utf-8").strip(),
        (CORE_DIR / "GUARDRAIL.md").read_text(encoding="utf-8").strip(),
        (CORE_DIR / "RESPONSE.md").read_text(encoding="utf-8").strip(),
        spec["override"].read_text(encoding="utf-8").strip(),
    ]
    combined = "\n\n---\n\n".join(parts) + "\n"
    return render_template(combined, home, spec["roles_dir"])


def merge_host_hook(spec: dict[str, Any], home: Path) -> None:
    hooks_file: Path = spec["hooks_file"]
    kind: str = spec["hooks_kind"]
    script_path = Path(__file__).resolve()
    data = load_json_file(hooks_file)

    if kind == "antigravity":
        cmd = f'python3 "{script_path}" hook-sync --json --home "{home}" {HOOK_MARKER}'
        data[ANTIGRAVITY_HOOK_KEY] = {
            "enabled": True,
            "SessionStart": [
                {
                    "type": "command",
                    "command": cmd,
                    "timeout": 5,
                }
            ],
        }
        atomic_write_json(hooks_file, data)
        return

    cmd = f'python3 "{script_path}" hook-sync --home "{home}" {HOOK_MARKER}'
    new_block = {
        "hooks": [
            {
                "type": "command",
                "command": cmd,
                "timeout": 5,
            }
        ]
    }
    hooks_obj = data.setdefault("hooks", {})
    if not isinstance(hooks_obj, dict):
        hooks_obj = {}
        data["hooks"] = hooks_obj
    session_start = hooks_obj.setdefault("SessionStart", [])
    if not isinstance(session_start, list):
        session_start = []
        hooks_obj["SessionStart"] = session_start

    replaced = False
    for idx, group in enumerate(session_start):
        if isinstance(group, dict):
            inner = group.get("hooks", [])
            if isinstance(inner, list) and any(
                isinstance(h, dict) and HOOK_MARKER in str(h.get("command", ""))
                for h in inner
            ):
                session_start[idx] = new_block
                replaced = True
                break
    if not replaced:
        session_start.append(new_block)

    atomic_write_json(hooks_file, data)


def cmd_sync(home: Path, skip_hooks: bool = False, quiet: bool = False) -> dict[str, Any]:
    sdir = state_dir_for(home)
    sdir.mkdir(parents=True, exist_ok=True)
    prev_manifest = load_json_file(sdir / "manifest.json")
    prev_symlinks = set(prev_manifest.get("managed_symlinks", []))
    prev_role_files = set(prev_manifest.get("managed_role_files", []))

    specs = host_specs(home)
    desired_skills = discover_local_skills(REPO_ROOT)
    for uname, upath in discover_upstream_skills(home).items():
        desired_skills.setdefault(uname, upath)

    role_sources: list[Path] = sorted(ROLES_DIR.glob("*.md")) + [
        CORE_DIR / "CONTRACTS.md",
        CORE_DIR / "ROUTING.md",
    ]

    new_managed_symlinks: set[str] = set()
    new_managed_role_files: set[str] = set()
    skipped_real_dirs: list[str] = []

    response_text = (CORE_DIR / "RESPONSE.md").read_text(encoding="utf-8")

    for host_name, spec in specs.items():
        spec["config_dir"].mkdir(parents=True, exist_ok=True)

        # 1. Compile root instruction file atomically
        compiled = build_root_instruction(spec, home)
        atomic_write_text(spec["root_instruction"], compiled)

        # 2. Write local copy of RESPONSE.md (sandbox-safe)
        atomic_write_text(spec["response_file"], GENERATED_HEADER + "\n" + response_text)

        # 3. Retire duplicate files (e.g. ~/.claude/AGENTS.md)
        for retired in spec["retired_files"]:
            if retired.is_symlink() or retired.is_file():
                retired.unlink(missing_ok=True)

        # 4. Copy managed roles/ + CONTRACTS.md + ROUTING.md into host directory
        roles_dst: Path = spec["roles_dir"]
        roles_dst.mkdir(parents=True, exist_ok=True)
        for src in role_sources:
            dst = roles_dst / src.name
            rendered = render_template(src.read_text(encoding="utf-8"), home, roles_dst)
            atomic_write_text(dst, GENERATED_HEADER + "\n" + rendered)
            new_managed_role_files.add(dst.relative_to(home).as_posix())

        # 5. Symlink skills cleanly without clobbering real local directories
        skills_dst: Path = spec["skills_dir"]
        skills_dst.mkdir(parents=True, exist_ok=True)
        for child in list(skills_dst.iterdir()):
            if child.is_symlink() and not child.exists():
                raw_target = Path(os.readlink(child))
                if str(raw_target).startswith(str(REPO_ROOT) + os.sep):
                    child.unlink(missing_ok=True)
        for skill_name, skill_src in sorted(desired_skills.items()):
            link_path = skills_dst / skill_name
            rel = link_path.relative_to(home).as_posix()
            if link_path.is_symlink():
                current_target = Path(os.readlink(link_path))
                if current_target != skill_src:
                    link_path.unlink()
                    os.symlink(skill_src, link_path)
                new_managed_symlinks.add(rel)
            elif link_path.exists():
                skipped_real_dirs.append(rel)
            else:
                os.symlink(skill_src, link_path)
                new_managed_symlinks.add(rel)

        # 6. Merge SessionStart hooks non-destructively
        if not skip_hooks:
            merge_host_hook(spec, home)

    # 7. Prune stale managed symlinks and role files
    for stale_rel in sorted(prev_symlinks - new_managed_symlinks):
        stale_path = home / stale_rel
        if stale_path.is_symlink():
            stale_path.unlink(missing_ok=True)
    for stale_rel in sorted(prev_role_files - new_managed_role_files):
        stale_path = home / stale_rel
        if stale_path.is_file():
            stale_path.unlink(missing_ok=True)

    new_manifest = {
        "schema_version": "1.0",
        "updated_at": datetime.datetime.now().isoformat(),
        "repo_root": str(REPO_ROOT),
        "managed_symlinks": sorted(new_managed_symlinks),
        "managed_role_files": sorted(new_managed_role_files),
        "skipped_real_dirs": sorted(skipped_real_dirs),
    }
    atomic_write_json(sdir / "manifest.json", new_manifest)

    if not quiet:
        print(
            f"[sync] updated 3 hosts | skills={len(desired_skills)} | "
            f"managed_links={len(new_managed_symlinks)} | skipped_real_dirs={len(skipped_real_dirs)}"
        )
    return new_manifest


def validate_public_repo() -> tuple[bool, str]:
    validator = REPO_ROOT / "scripts" / "validate_public_package.py"
    if not validator.is_file():
        return True, "validator not present"
    python_bin = REPO_ROOT / ".venv" / "bin" / "python"
    exe = str(python_bin) if python_bin.is_file() else sys.executable
    proc = subprocess.run(
        [exe, str(validator)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
    )
    return proc.returncode == 0, proc.stdout.strip()


def run_hook_sync_worker(home: Path) -> int:
    sdir = state_dir_for(home)
    sdir.mkdir(parents=True, exist_ok=True)
    lock_path = sdir / ".sync.lock"
    with open(lock_path, "w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0

        (sdir / ".last_sync").write_text(str(int(time.time())), encoding="utf-8")
        if not (REPO_ROOT / ".git").exists():
            return 0

        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o ConnectTimeout=2"

        try:
            branch = subprocess.check_output(
                ["git", "-C", str(REPO_ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
                env=env,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=3,
            ).strip()
            if branch not in ("main", "master"):
                return 0

            dirty = subprocess.check_output(
                ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
                env=env,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=3,
            ).strip()
            if dirty:
                return 0

            before_head = subprocess.check_output(
                ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
                env=env,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=3,
            ).strip()

            subprocess.run(
                ["git", "-C", str(REPO_ROOT), "pull", "--ff-only", "--quiet"],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
                check=False,
            )

            after_head = subprocess.check_output(
                ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
                env=env,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=3,
            ).strip()

            if after_head != before_head:
                ok, _ = validate_public_repo()
                if ok:
                    cmd_sync(home, skip_hooks=False, quiet=True)
        except (subprocess.SubprocessError, OSError):
            return 0
    return 0


def cmd_hook_sync(home: Path, emit_json: bool, ttl: int, worker: bool) -> int:
    if worker:
        return run_hook_sync_worker(home)

    # Consume stdin safely without blocking if attached to a tty
    if not sys.stdin.isatty():
        try:
            sys.stdin.read(65536)
        except OSError:
            pass

    if os.environ.get("AI_HARNESS_NO_SYNC") == "1":
        if emit_json:
            print("{}")
        return 0

    sdir = state_dir_for(home)
    sdir.mkdir(parents=True, exist_ok=True)
    last_sync_file = sdir / ".last_sync"
    now = int(time.time())
    should_sync = True
    if last_sync_file.is_file():
        try:
            last_ts = int(last_sync_file.read_text(encoding="utf-8").strip())
            if now - last_ts < ttl:
                should_sync = False
        except ValueError:
            should_sync = True

    if should_sync:
        lock_path = sdir / ".sync.lock"
        try:
            with open(lock_path, "w", encoding="utf-8") as lf:
                fcntl.flock(lf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
            subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "hook-sync", "--worker", "--home", str(home)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=True,
            )
        except (BlockingIOError, OSError):
            pass

    if emit_json:
        print("{}")
    return 0


def cmd_doctor(home: Path, skip_repo_validate: bool = False) -> int:
    errors: list[str] = []
    specs = host_specs(home)

    for name, spec in specs.items():
        root_file: Path = spec["root_instruction"]
        if not root_file.is_file():
            errors.append(f"[{name}] missing compiled root instruction: {root_file}")
        else:
            text = root_file.read_text(encoding="utf-8")
            if GENERATED_HEADER.strip() not in text:
                errors.append(f"[{name}] missing generated header in {root_file}")
            if "# 응답 형식" not in text:
                errors.append(f"[{name}] RESPONSE.md not inlined in {root_file}")
            if "READ-ONLY" not in text:
                errors.append(f"[{name}] GUARDRAIL.md READ-ONLY rule missing in {root_file}")

        for retired in spec["retired_files"]:
            if retired.exists() or retired.is_symlink():
                errors.append(f"[{name}] retired duplicate file still exists: {retired}")

        roles_dir: Path = spec["roles_dir"]
        for expected in ("orchestrator.md", "implementer.md", "reviewer.md", "scout.md", "CONTRACTS.md", "ROUTING.md"):
            if not (roles_dir / expected).is_file():
                errors.append(f"[{name}] missing managed role/protocol file: {roles_dir / expected}")

        hooks_file: Path = spec["hooks_file"]
        try:
            hdata = load_json_file(hooks_file)
            if spec["hooks_kind"] == "antigravity":
                if ANTIGRAVITY_HOOK_KEY not in hdata:
                    errors.append(f"[{name}] missing {ANTIGRAVITY_HOOK_KEY} hook in {hooks_file}")
            else:
                ss = hdata.get("hooks", {}).get("SessionStart", [])
                found = any(
                    isinstance(g, dict)
                    and any(
                        isinstance(h, dict) and HOOK_MARKER in str(h.get("command", ""))
                        for h in g.get("hooks", [])
                    )
                    for g in ss
                )
                if not found:
                    errors.append(f"[{name}] missing {HOOK_MARKER} SessionStart hook in {hooks_file}")
        except Exception as exc:
            errors.append(f"[{name}] invalid JSON in {hooks_file}: {exc}")

        skills_dir: Path = spec["skills_dir"]
        managed_set = set(load_json_file(state_dir_for(home) / "manifest.json").get("managed_symlinks", []))
        if skills_dir.is_dir():
            for child in skills_dir.iterdir():
                if child.is_symlink() and not child.exists():
                    target_str = os.readlink(child)
                    rel = child.relative_to(home).as_posix()
                    if rel in managed_set or target_str.startswith(str(REPO_ROOT) + os.sep):
                        errors.append(f"[{name}] broken managed symlink: {child} -> {target_str}")
                    else:
                        print(f"[warn] [{name}] external broken symlink (not managed): {child} -> {target_str}", file=sys.stderr)

    broot = backup_root_for(home)
    if broot.is_dir():
        mode = stat.S_IMODE(broot.stat().st_mode)
        if mode != 0o700:
            errors.append(f"[backup] {broot} permissions {oct(mode)} != 0o700")

    if not skip_repo_validate:
        ok, out = validate_public_repo()
        if not ok:
            errors.append(f"[repo] validate_public_package.py failed: {out}")

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    print(f"PASS: doctor verified 3 hosts (home={home})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Multi-model SSOT agent harness CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_home(p: argparse.ArgumentParser) -> None:
        p.add_argument("--home", default=str(Path.home()), help="Target home directory")

    p_install = sub.add_parser("install", help="Backup, sync upstream skills, sync hosts, and run doctor")
    add_home(p_install)
    p_install.add_argument("--skip-upstream", action="store_true", help="Skip cloning/updating upstream skills")
    p_install.add_argument("--skip-hooks", action="store_true", help="Skip merging SessionStart hooks")
    p_install.add_argument("--skip-repo-validate", action="store_true", help="Skip validate_public_package.py in doctor")

    p_backup = sub.add_parser("backup", help="Create chmod-hardened snapshot backup of host configs")
    add_home(p_backup)
    p_backup.add_argument("--quiet", action="store_true")

    p_restore = sub.add_parser("restore", help="Restore host configs from a backup snapshot")
    add_home(p_restore)
    p_restore.add_argument("timestamp", nargs="?", default="latest", help="Backup timestamp or 'latest'")
    p_restore.add_argument("--quiet", action="store_true")

    p_sync = sub.add_parser("sync", help="Compile host instructions, copy roles, link skills, merge hooks")
    add_home(p_sync)
    p_sync.add_argument("--skip-hooks", action="store_true")
    p_sync.add_argument("--quiet", action="store_true")

    p_doctor = sub.add_parser("doctor", help="Verify host configs, symlinks, hooks, and repo hygiene")
    add_home(p_doctor)
    p_doctor.add_argument("--skip-repo-validate", action="store_true")

    p_hook = sub.add_parser("hook-sync", help="Non-blocking SessionStart auto-sync hook")
    add_home(p_hook)
    p_hook.add_argument("--json", dest="emit_json", action="store_true", help="Print {} JSON on stdout")
    p_hook.add_argument(
        "--ttl",
        type=int,
        default=int(os.environ.get("AI_HARNESS_SYNC_TTL", str(DEFAULT_TTL_SECONDS))),
        help="Minimum seconds between background syncs",
    )
    p_hook.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args(argv)
    home = Path(args.home).expanduser().resolve()

    if args.command == "backup":
        cmd_backup(home, quiet=args.quiet)
        return 0
    if args.command == "restore":
        cmd_restore(home, args.timestamp, quiet=args.quiet)
        return 0
    if args.command == "sync":
        cmd_sync(home, skip_hooks=args.skip_hooks, quiet=args.quiet)
        return 0
    if args.command == "doctor":
        return cmd_doctor(home, skip_repo_validate=args.skip_repo_validate)
    if args.command == "hook-sync":
        return cmd_hook_sync(home, emit_json=args.emit_json, ttl=args.ttl, worker=args.worker)
    if args.command == "install":
        cmd_backup(home)
        if not args.skip_upstream:
            sync_upstream_repos(home)
        cmd_sync(home, skip_hooks=args.skip_hooks)
        return cmd_doctor(home, skip_repo_validate=args.skip_repo_validate)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
