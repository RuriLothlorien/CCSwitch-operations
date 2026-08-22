#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke and regression tests for the publishable CCSwitch-operations skill.

Run from the repository root:
    python -m unittest discover -s tests -v

These tests never touch a real CC Switch installation: they use a synthetic
SQLite database in a temporary directory.
"""

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CCS_DB = REPO / "scripts" / "ccs_db.py"
BUILD_ZIP = REPO / "scripts" / "build-zip.py"


def make_synthetic_home() -> Path:
    home = Path(tempfile.mkdtemp(prefix="ccs-test-home-"))
    (home / "skills" / "test-skill").mkdir(parents=True)
    (home / "skills" / "test-skill" / "SKILL.md").write_text("# test skill\n", encoding="utf-8")

    db = home / "cc-switch.db"
    con = sqlite3.connect(db)
    con.executescript(
        """
        CREATE TABLE providers (
            id TEXT PRIMARY KEY, app_type TEXT, name TEXT,
            settings_config TEXT, notes TEXT, is_current INTEGER
        );
        CREATE TABLE mcp_servers (
            id TEXT PRIMARY KEY, name TEXT, server_config TEXT, description TEXT,
            homepage TEXT, docs TEXT, tags TEXT,
            enabled_claude INTEGER, enabled_codex INTEGER, enabled_gemini INTEGER,
            enabled_opencode INTEGER, enabled_hermes INTEGER, enabled_grokbuild INTEGER
        );
        CREATE TABLE prompts (
            id TEXT PRIMARY KEY, app_type TEXT, name TEXT, content TEXT,
            description TEXT, enabled INTEGER, created_at INTEGER, updated_at INTEGER
        );
        CREATE TABLE skills (
            id TEXT PRIMARY KEY, name TEXT, description TEXT, directory TEXT,
            repo_owner TEXT, repo_name TEXT, repo_branch TEXT, readme_url TEXT,
            enabled_claude INTEGER, enabled_codex INTEGER, enabled_gemini INTEGER,
            enabled_opencode INTEGER, enabled_hermes INTEGER, installed_at INTEGER,
            content_hash TEXT, updated_at INTEGER, enabled_grokbuild INTEGER
        );
        CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE model_pricing (display_name TEXT);
        """
    )
    seed_config = (
        '[mcp_servers.existing]\ncommand = "echo"\n\n'
        '[mcp_servers.existing.env]\nK = "v"\n'
    )
    con.execute(
        "INSERT INTO providers (id, app_type, name, settings_config, notes, is_current) "
        "VALUES (?, ?, ?, ?, ?, 1)",
        ("p-codex", "codex", "Test Provider",
         json.dumps({"config": seed_config, "env": {"A": "1"}}), ""),
    )
    con.commit()
    con.close()
    return home


class CcsDbCliTest(unittest.TestCase):
    def setUp(self):
        self.home = make_synthetic_home()
        self.maxDiff = None

    def run_cli(self, *args, expect_ok=True, env=None):
        cmd = [sys.executable, str(CCS_DB), "--cc-home", str(self.home), *args]
        run_env = dict(os.environ)
        if env:
            run_env.update(env)
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", env=run_env
        )
        if expect_ok:
            self.assertEqual(
                proc.returncode, 0,
                msg=f"command failed: {cmd}\nstdout={proc.stdout}\nstderr={proc.stderr}",
            )
        return proc

    def db_rows(self, sql, params=()):
        con = sqlite3.connect(self.home / "cc-switch.db")
        con.row_factory = sqlite3.Row
        rows = [dict(r) for r in con.execute(sql, params)]
        con.close()
        return rows

    def test_help_lists_all_subcommands(self):
        proc = self.run_cli("--help")
        for sub in ("mcp-upsert", "prompt-set", "skill-upsert", "provider-block",
                    "provider-env", "set-flags", "check", "doctor"):
            self.assertIn(sub, proc.stdout)

    def test_doctor_reports_paths_and_providers(self):
        proc = self.run_cli("doctor")
        self.assertIn("cc_home:", proc.stdout)
        self.assertIn("exists=True", proc.stdout)
        self.assertIn("codex: total=1 current=1", proc.stdout)

    def test_doctor_missing_db_is_non_fatal(self):
        empty_home = Path(tempfile.mkdtemp(prefix="ccs-test-empty-"))
        proc = subprocess.run(
            [sys.executable, str(CCS_DB), "--cc-home", str(empty_home), "doctor"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("[warn] database not found", proc.stdout)

    def test_cc_home_env_var_is_respected(self):
        other = Path(tempfile.mkdtemp(prefix="ccs-test-env-"))
        proc = self.run_cli("doctor", expect_ok=True, env={"CC_SWITCH_HOME": str(other)})
        # --cc-home wins over the env var, so use no --cc-home for this test.
        proc = subprocess.run(
            [sys.executable, str(CCS_DB), "doctor"],
            capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "CC_SWITCH_HOME": str(other)},
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn(str(other), proc.stdout)

    def test_db_override_is_respected(self):
        other_home = Path(tempfile.mkdtemp(prefix="ccs-test-db-"))
        proc = subprocess.run(
            [sys.executable, str(CCS_DB), "--cc-home", str(other_home),
             "--db", str(self.home / "cc-switch.db"), "check"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("[OK]", proc.stdout)

    def test_mcp_upsert_insert_and_update(self):
        self.run_cli("mcp-upsert", "--name", "test-server",
                     "--config", '{"command":"npx"}',
                     "--description", "测试中文描述", "--tags", "stdio,test",
                     "--enable-codex", "--enable-claude")
        rows = self.db_rows("SELECT * FROM mcp_servers WHERE name='test-server'")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["description"], "测试中文描述")
        self.assertEqual(rows[0]["enabled_codex"], 1)
        self.assertEqual(rows[0]["enabled_claude"], 1)

        self.run_cli("mcp-upsert", "--name", "test-server",
                     "--config", '{"command":"python"}',
                     "--description", "更新描述", "--tags", "stdio",
                     "--enable-codex")
        rows = self.db_rows("SELECT * FROM mcp_servers WHERE name='test-server'")
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0]["server_config"])["command"], "python")
        self.assertEqual(rows[0]["description"], "更新描述")
        self.assertEqual(rows[0]["enabled_claude"], 0)

    def test_mcp_upsert_rejects_invalid_json(self):
        proc = self.run_cli("mcp-upsert", "--name", "bad", "--config", "{not json}",
                            expect_ok=False)
        self.assertNotEqual(proc.returncode, 0)

    def test_prompt_set_insert_and_update(self):
        self.run_cli("prompt-set", "--app-type", "codex", "--content", "全局提示词一")
        rows = self.db_rows("SELECT * FROM prompts WHERE app_type='codex' AND name='全局'")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["content"], "全局提示词一")

        self.run_cli("prompt-set", "--app-type", "codex", "--content", "全局提示词二")
        rows = self.db_rows("SELECT * FROM prompts WHERE app_type='codex' AND name='全局'")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["content"], "全局提示词二")

    def test_skill_upsert_computes_hash(self):
        self.run_cli("skill-upsert", "--name", "test-skill",
                     "--description", "测试技能", "--enable-codex")
        rows = self.db_rows("SELECT * FROM skills WHERE id='local:test-skill'")
        self.assertEqual(len(rows), 1)
        expected = hashlib.sha256(
            (self.home / "skills" / "test-skill" / "SKILL.md").read_bytes()
        ).hexdigest()
        self.assertEqual(rows[0]["content_hash"], expected)
        self.assertEqual(rows[0]["enabled_codex"], 1)
        self.assertEqual(rows[0]["enabled_claude"], 0)

    def test_set_flags_only_touches_requested_flags(self):
        self.run_cli("mcp-upsert", "--name", "flag-server", "--config", "{}",
                     "--enable-codex", "--enable-claude")
        self.run_cli("set-flags", "--table", "mcp_servers", "--name", "flag-server",
                     "--gemini", "1")
        rows = self.db_rows("SELECT * FROM mcp_servers WHERE name='flag-server'")
        self.assertEqual(rows[0]["enabled_codex"], 1)
        self.assertEqual(rows[0]["enabled_claude"], 1)
        self.assertEqual(rows[0]["enabled_gemini"], 1)

    def test_provider_block_append_replace_insert(self):
        self.run_cli("provider-block", "--app-type", "codex",
                     "--section", "[mcp_servers.new]",
                     "--block", '[mcp_servers.new]\ncommand = "x"\n')
        cfg = self.db_rows("SELECT settings_config FROM providers WHERE id='p-codex'")[0]["settings_config"]
        self.assertIn("[mcp_servers.new]", json.loads(cfg)["config"])

        self.run_cli("provider-block", "--app-type", "codex",
                     "--section", "[mcp_servers.existing]",
                     "--block", '[mcp_servers.existing]\ncommand = "y"\n\n[mcp_servers.existing.env]\nK = "z"\n',
                     "--replace")
        cfg = self.db_rows("SELECT settings_config FROM providers WHERE id='p-codex'")[0]["settings_config"]
        text = json.loads(cfg)["config"]
        self.assertEqual(text.count("[mcp_servers.existing.env]"), 1)
        self.assertIn('command = "y"', text)

        self.run_cli("provider-block", "--app-type", "codex",
                     "--section", "[mcp_servers.before]",
                     "--block", '[mcp_servers.before]\ncommand = "b"\n',
                     "--insert-before", "[mcp_servers.existing]")
        cfg = self.db_rows("SELECT settings_config FROM providers WHERE id='p-codex'")[0]["settings_config"]
        text = json.loads(cfg)["config"]
        self.assertLess(text.index("[mcp_servers.before]"), text.index("[mcp_servers.existing]"))

    def test_provider_block_duplicate_section_without_replace_fails(self):
        proc = self.run_cli("provider-block", "--app-type", "codex",
                            "--section", "[mcp_servers.existing]",
                            "--block", '[mcp_servers.existing]\ncommand = "x"\n',
                            expect_ok=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("already exists", proc.stderr)

    def test_provider_env_set_and_remove(self):
        self.run_cli("provider-env", "--app-type", "codex",
                     "--set", "NEW_KEY=value1")
        cfg = self.db_rows("SELECT settings_config FROM providers WHERE id='p-codex'")[0]["settings_config"]
        self.assertEqual(json.loads(cfg)["env"]["NEW_KEY"], "value1")

        self.run_cli("provider-env", "--app-type", "codex", "--remove", "NEW_KEY")
        cfg = self.db_rows("SELECT settings_config FROM providers WHERE id='p-codex'")[0]["settings_config"]
        self.assertNotIn("NEW_KEY", json.loads(cfg)["env"])

    def test_provider_resolution_error_without_current(self):
        proc = self.run_cli("provider-env", "--app-type", "gemini",
                            "--set", "K=v", expect_ok=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("cannot resolve provider", proc.stderr)

    def test_check_passes_for_clean_and_url_question_marks(self):
        self.run_cli("prompt-set", "--app-type", "codex", "--content", "中文内容")
        con = sqlite3.connect(self.home / "cc-switch.db")
        con.execute("INSERT INTO settings (key, value) VALUES ('url', ?)",
                    ('{"url":"https://example.com/x?a=1&b=2"}',))
        con.commit()
        con.close()
        self.run_cli("check")

    def test_check_fails_for_mojibake(self):
        con = sqlite3.connect(self.home / "cc-switch.db")
        con.execute("INSERT INTO prompts (id, app_type, name, content, enabled) "
                    "VALUES ('bad', 'codex', '全局', '中文??损坏', 1)")
        con.commit()
        con.close()
        proc = self.run_cli("check", expect_ok=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("[FAIL]", proc.stderr)


class PackageTest(unittest.TestCase):
    def test_build_zip_is_clean_and_standalone(self):
        with tempfile.TemporaryDirectory(prefix="ccs-test-pkg-") as tmp:
            out_dir = Path(tmp) / "out"
            proc = subprocess.run(
                [sys.executable, str(BUILD_ZIP), "--repo", str(REPO),
                 "--out-dir", str(out_dir), "--version", "1.0.0"],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            zip_path = out_dir / "CCSwitch-operations-v1.0.0.zip"
            self.assertTrue(zip_path.exists())

            with zipfile.ZipFile(zip_path) as zf:
                names = zf.namelist()
            self.assertTrue(names)
            for name in names:
                self.assertTrue(name.startswith("CCSwitch-operations/"), name)
                self.assertNotIn("__pycache__", name)
                self.assertNotIn("/.git", name)
                self.assertNotIn("/.github", name)
                self.assertNotIn("tests", name)
                self.assertNotIn("build-zip.py", name)
                self.assertNotIn(".gitignore", name)
            self.assertIn("CCSwitch-operations/SKILL.md", names)
            self.assertIn("CCSwitch-operations/scripts/ccs_db.py", names)
            self.assertIn("CCSwitch-operations/README.zh-CN.md", names)

            # The extracted package must be usable standalone.
            extract_dir = Path(tmp) / "extract"
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)
            help_proc = subprocess.run(
                [sys.executable, str(extract_dir / "CCSwitch-operations" / "scripts" / "ccs_db.py"),
                 "--help"],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(help_proc.returncode, 0)
            self.assertIn("doctor", help_proc.stdout)

    def test_readmes_are_user_facing_without_build_release_instructions(self):
        readme_en = (REPO / "README.md").read_text(encoding="utf-8")
        readme_zh = (REPO / "README.zh-CN.md").read_text(encoding="utf-8")
        for text in (readme_en, readme_zh):
            self.assertNotIn("gh release", text)
            self.assertNotIn("GitHub Actions", text)
            self.assertNotIn("git tag", text)
        self.assertIn("build-zip", readme_en)
        self.assertIn("build-zip", readme_zh)
        self.assertIn("3.11", readme_en)
        self.assertIn("3.11", readme_zh)
        self.assertIn("How it works", readme_en)
        self.assertIn("工作原理", readme_zh)
        self.assertNotIn("发布 GitHub Release", readme_zh)


if __name__ == "__main__":
    unittest.main(verbosity=2)
