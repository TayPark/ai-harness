from __future__ import annotations

import fcntl
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_SCRIPT = REPO_ROOT / "harness" / "scripts" / "harness.py"
sys.path.insert(0, str(HARNESS_SCRIPT.parent))
import harness  # noqa: E402


class HarnessLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name) / "fake-home"
        self.home.mkdir(parents=True)

        # Seed realistic pre-existing host configs with existing hooks and a local real skill dir
        (self.home / ".gemini" / "config" / "skills" / "local-only-skill").mkdir(parents=True)
        (self.home / ".gemini" / "config" / "skills" / "local-only-skill" / "SKILL.md").write_text("local\n", encoding="utf-8")
        os.symlink(
            str(REPO_ROOT / "skills" / "deprecated-removed-skill"),
            self.home / ".gemini" / "config" / "skills" / "deprecated-removed-skill",
        )
        (self.home / ".gemini" / "config" / "AGENTS.md").write_text("old gemini agents\n", encoding="utf-8")
        (self.home / ".gemini" / "config" / "RESPONSE.md").write_text("old gemini response\n", encoding="utf-8")
        (self.home / ".gemini" / "config" / "mcp_config.json").write_text('{"mcpServers":{"aside":{"command":"aside"}}}\n', encoding="utf-8")
        (self.home / ".gemini" / "config" / "hooks.json").write_text(
            json.dumps({"moshi-hook": {"enabled": True, "Stop": []}, "orca-status": {"PreInvocation": []}}, indent=2) + "\n",
            encoding="utf-8",
        )

        (self.home / ".claude" / "skills").mkdir(parents=True)
        (self.home / ".claude" / "CLAUDE.md").write_text("@AGENTS.md\nold claude\n", encoding="utf-8")
        (self.home / ".claude" / "AGENTS.md").write_text("old claude agents\n", encoding="utf-8")
        (self.home / ".claude" / "RESPONSE.md").write_text("old claude response\n", encoding="utf-8")
        (self.home / ".claude" / "settings.json").write_text(
            json.dumps(
                {
                    "model": "opus",
                    "hooks": {
                        "SessionStart": [
                            {"hooks": [{"type": "command", "command": "echo existing-gsd"}]},
                            {"hooks": [{"type": "command", "command": "echo existing-orca"}]},
                        ]
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        (self.home / ".codex" / "skills").mkdir(parents=True)
        (self.home / ".codex" / "AGENTS.md").write_text("old codex agents\n", encoding="utf-8")
        (self.home / ".codex" / "RESPONSE.md").write_text("old codex response\n", encoding="utf-8")
        (self.home / ".codex" / "config.toml").write_text('model = "gpt-6.2-sol"\n', encoding="utf-8")
        (self.home / ".codex" / "hooks.json").write_text(
            json.dumps(
                {
                    "hooks": {
                        "SessionStart": [
                            {"hooks": [{"type": "command", "command": "echo existing-lpm"}]}
                        ]
                    }
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_full_lifecycle_idempotency_and_exact_rollback(self) -> None:
        orig_gemini_agents = (self.home / ".gemini" / "config" / "AGENTS.md").read_text(encoding="utf-8")
        orig_claude_md = (self.home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        orig_claude_agents = (self.home / ".claude" / "AGENTS.md").read_text(encoding="utf-8")
        orig_claude_settings = (self.home / ".claude" / "settings.json").read_text(encoding="utf-8")
        orig_codex_hooks = (self.home / ".codex" / "hooks.json").read_text(encoding="utf-8")

        # 1. Backup -> verify hardened permissions
        bdir = harness.cmd_backup(self.home, quiet=True)
        self.assertEqual(stat.S_IMODE(harness.backup_root_for(self.home).stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(bdir.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((bdir / "manifest.json").stat().st_mode), 0o600)
        self.assertEqual(
            stat.S_IMODE((bdir / "files" / ".gemini" / "config" / "mcp_config.json").stat().st_mode),
            0o600,
        )

        # 2. Sync -> verify compiled instructions, retired duplicate, roles copies, preserved hooks, real dir untouched
        harness.cmd_sync(self.home, skip_hooks=False, quiet=True)
        self.assertEqual(harness.cmd_doctor(self.home, skip_repo_validate=True), 0)

        self.assertFalse((self.home / ".claude" / "AGENTS.md").exists())
        self.assertTrue((self.home / ".gemini" / "config" / "skills" / "local-only-skill" / "SKILL.md").is_file())
        self.assertTrue((self.home / ".codex" / "roles" / "reviewer.md").is_file())
        self.assertFalse((self.home / ".codex" / "roles" / "reviewer.md").is_symlink())

        claude_settings = json.loads((self.home / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(len(claude_settings["hooks"]["SessionStart"]), 3)
        gemini_hooks = json.loads((self.home / ".gemini" / "config" / "hooks.json").read_text(encoding="utf-8"))
        self.assertIn("moshi-hook", gemini_hooks)
        self.assertIn("orca-status", gemini_hooks)
        self.assertIn(harness.ANTIGRAVITY_HOOK_KEY, gemini_hooks)

        # 3. Second sync -> idempotency (zero duplicate hooks)
        harness.cmd_sync(self.home, skip_hooks=False, quiet=True)
        claude_settings_2 = json.loads((self.home / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(len(claude_settings_2["hooks"]["SessionStart"]), 3)
        codex_hooks_2 = json.loads((self.home / ".codex" / "hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(len(codex_hooks_2["hooks"]["SessionStart"]), 2)

        # 4. Restore latest -> byte-for-byte equality + managed artifacts cleaned up
        harness.cmd_restore(self.home, "latest", quiet=True)
        self.assertEqual((self.home / ".gemini" / "config" / "AGENTS.md").read_text(encoding="utf-8"), orig_gemini_agents)
        self.assertEqual((self.home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8"), orig_claude_md)
        self.assertEqual((self.home / ".claude" / "AGENTS.md").read_text(encoding="utf-8"), orig_claude_agents)
        self.assertEqual((self.home / ".claude" / "settings.json").read_text(encoding="utf-8"), orig_claude_settings)
        self.assertEqual((self.home / ".codex" / "hooks.json").read_text(encoding="utf-8"), orig_codex_hooks)
        self.assertFalse((self.home / ".codex" / "roles" / "reviewer.md").exists())
        self.assertFalse((self.home / ".codex" / "skills" / "anti-slop").exists())
        self.assertTrue((self.home / ".gemini" / "config" / "skills" / "local-only-skill" / "SKILL.md").is_file())

    def test_hook_sync_json_fast_and_no_sync_guard(self) -> None:
        env = os.environ.copy()
        env["AI_HARNESS_NO_SYNC"] = "1"
        start = time.monotonic()
        proc = subprocess.run(
            [sys.executable, str(HARNESS_SCRIPT), "hook-sync", "--json", "--home", str(self.home)],
            input='{"hookEventName":"SessionStart"}\n',
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
            check=True,
        )
        elapsed = time.monotonic() - start
        self.assertEqual(proc.stdout.strip(), "{}")
        self.assertLess(elapsed, 1.5)

    def test_hook_sync_lock_contention_skips_cleanly(self) -> None:
        sdir = harness.state_dir_for(self.home)
        sdir.mkdir(parents=True, exist_ok=True)
        lock_path = sdir / ".sync.lock"
        with open(lock_path, "w", encoding="utf-8") as lf:
            fcntl.flock(lf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            rc = harness.run_hook_sync_worker(self.home)
            self.assertEqual(rc, 0)
            self.assertFalse((sdir / ".last_sync").exists())

    def test_jsonc_stripping(self) -> None:
        raw = '// header comment\n{\n  /* block */ "a": "http://example.com", "b": 1\n}\n'
        parsed = json.loads(harness.strip_jsonc(raw))
        self.assertEqual(parsed, {"a": "http://example.com", "b": 1})


if __name__ == "__main__":
    unittest.main()
