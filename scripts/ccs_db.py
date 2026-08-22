#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ccs_db.py - portable, UTF-8-safe CC Switch DB operations helper.

No machine-specific paths or credentials. The CC Switch home directory is
resolved in this order:
  1. --cc-home
  2. CC_SWITCH_HOME environment variable
  3. ~/.cc-switch

Subcommands:
  mcp-upsert      upsert a row in mcp_servers (JSON server_config)
  prompt-set      set a global prompt for an app_type
  skill-upsert    register a local skill and refresh its content_hash
  provider-block  append/replace/insert a TOML block in a provider's config
  provider-env    set/remove environment variables on a provider
  set-flags       toggle enabled_* flags without touching other fields
  check           scan for likely mojibake '?' in text/JSON/TOML fields
  doctor          print resolved paths, schema, and per-app provider status

Chinese values can be passed inline (wide argv survives Windows PowerShell) or
via UTF-8 files (--*-file) for large/sensitive content.
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

APP_TYPES = (
    "codex",
    "claude",
    "claude-desktop",
    "gemini",
    "grokbuild",
    "opencode",
    "openclaw",
    "hermes",
    "pi",
)


def default_cc_home() -> Path:
    env = os.environ.get("CC_SWITCH_HOME")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".cc-switch"


def resolve_paths(args) -> tuple:
    cc_home = Path(args.cc_home).expanduser() if args.cc_home else default_cc_home()
    db_path = Path(args.db).expanduser() if args.db else cc_home / "cc-switch.db"
    return cc_home, db_path


def read_text(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def parse_tags(s):
    """Accept a JSON array string or a comma-separated list."""
    s = (s or "").strip()
    if not s:
        return "[]"
    if s.startswith("["):
        return json.dumps(json.loads(s), ensure_ascii=False)
    return json.dumps([t.strip() for t in s.split(",") if t.strip()], ensure_ascii=False)


def _is_sub_section(section, header):
    base = section.strip().lstrip("[").rstrip("]").strip()
    h = header.strip().lstrip("[").rstrip("]").strip()
    return h == base or h.startswith(base + ".")


def connect(db_path):
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    return con


def verify_no_q(label, values):
    bad = [v for v in values if isinstance(v, str) and "?" in v]
    if bad:
        raise SystemExit(f"[FAIL] {label}: '?' found: {bad!r}")
    print(f"[OK] {label}: no '?' in text values")


def load_settings_provider_ids(cc_home: Path) -> dict:
    settings_file = cc_home / "settings.json"
    try:
        with open(settings_file, "r", encoding="utf-8-sig") as f:
            s = json.load(f)
    except Exception:
        return {}
    return {
        "codex": s.get("currentProviderCodex"),
        "claude": s.get("currentProviderClaude"),
        "claude-desktop": s.get("currentProviderClaudeDesktop"),
        "gemini": s.get("currentProviderGemini"),
    }


def resolve_provider_id(con, cc_home: Path, app_type, explicit_id=None):
    """Explicit id > settings.json currentProvider* > providers.is_current=1."""
    if explicit_id:
        return explicit_id
    settings_ids = load_settings_provider_ids(cc_home)
    if settings_ids.get(app_type):
        return settings_ids[app_type]
    row = con.execute(
        "SELECT id FROM providers WHERE app_type=? AND is_current=1", (app_type,)
    ).fetchone()
    if row:
        return row["id"]
    raise SystemExit(
        f"cannot resolve provider for app_type={app_type!r}: "
        "no --provider-id, no currentProvider* in settings.json, "
        "and no providers.is_current=1 row"
    )


def cmd_mcp_upsert(args):
    cfg = read_text(args.config_file) if args.config_file else args.config
    json.loads(cfg)
    desc = read_text(args.description_file) if args.description_file else (args.description or "")
    tags = read_text(args.tags_file) if args.tags_file else parse_tags(args.tags)

    _, db_path = resolve_paths(args)
    con = connect(db_path)
    cur = con.cursor()
    flags = (
        int(args.enable_claude), int(args.enable_codex), int(args.enable_gemini),
        int(args.enable_opencode), int(args.enable_hermes), int(args.enable_grokbuild),
    )
    existing = cur.execute("SELECT id FROM mcp_servers WHERE name=?", (args.name,)).fetchone()
    if existing:
        cur.execute(
            "UPDATE mcp_servers SET server_config=?, description=?, tags=?, "
            "enabled_claude=?, enabled_codex=?, enabled_gemini=?, enabled_opencode=?, "
            "enabled_hermes=?, enabled_grokbuild=? WHERE name=?",
            (cfg, desc, tags, *flags, args.name),
        )
        action = "UPDATED"
    else:
        cur.execute(
            "INSERT INTO mcp_servers (id, name, server_config, description, homepage, docs, tags, "
            "enabled_claude, enabled_codex, enabled_gemini, enabled_opencode, enabled_hermes, enabled_grokbuild) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (args.name, args.name, cfg, desc, "", "", tags, *flags),
        )
        action = "INSERTED"
    con.commit()
    row = cur.execute("SELECT name, description, enabled_codex, enabled_claude FROM mcp_servers WHERE name=?", (args.name,)).fetchone()
    print(f"[{action}] mcp_servers: {row['name']} codex={row['enabled_codex']} claude={row['enabled_claude']}")
    verify_no_q("mcp_servers.description", [row["description"]])
    con.close()


def cmd_prompt_set(args):
    content = read_text(args.content_file) if args.content_file else (args.content or "")
    name = args.name or "全局"
    now_ms = int(time.time() * 1000)
    _, db_path = resolve_paths(args)
    con = connect(db_path)
    cur = con.cursor()
    existing = cur.execute(
        "SELECT id FROM prompts WHERE app_type=? AND name=?", (args.app_type, name)
    ).fetchone()
    if existing:
        cur.execute(
            "UPDATE prompts SET content=?, updated_at=? WHERE app_type=? AND name=?",
            (content, now_ms, args.app_type, name),
        )
        action = "UPDATED"
    else:
        cur.execute(
            "INSERT INTO prompts (id, app_type, name, content, description, enabled, created_at, updated_at) "
            "VALUES (?,?,?,?,?,1,?,?)",
            (f"prompt-{now_ms}", args.app_type, name, content, None, now_ms, now_ms),
        )
        action = "INSERTED"
    con.commit()
    row = cur.execute(
        "SELECT app_type, name, length(content) AS n FROM prompts WHERE app_type=? AND name=?",
        (args.app_type, name),
    ).fetchone()
    print(f"[{action}] prompts: {row['app_type']}/{row['name']} content_len={row['n']}")
    verify_no_q("prompts.content", [content])
    con.close()


def cmd_skill_upsert(args):
    desc = read_text(args.description_file) if args.description_file else (args.description or "")
    directory = args.directory or args.name
    cc_home, db_path = resolve_paths(args)
    source = cc_home / "skills" / directory / "SKILL.md"
    content_hash = args.content_hash or ""
    if source.exists():
        content_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    now = int(time.time())
    skill_id = f"local:{args.name}"
    con = connect(db_path)
    cur = con.cursor()
    existing = cur.execute("SELECT id FROM skills WHERE id=?", (skill_id,)).fetchone()
    if existing:
        cur.execute(
            "UPDATE skills SET name=?, description=?, directory=?, enabled_claude=?, enabled_codex=?, "
            "enabled_gemini=?, enabled_opencode=?, enabled_hermes=?, enabled_grokbuild=?, "
            "content_hash=?, updated_at=? WHERE id=?",
            (args.name, desc, directory, int(args.enable_claude), int(args.enable_codex),
             int(args.enable_gemini), int(args.enable_opencode), int(args.enable_hermes),
             int(args.enable_grokbuild), content_hash, now, skill_id),
        )
        action = "UPDATED"
    else:
        cur.execute(
            "INSERT INTO skills (id, name, description, directory, repo_owner, repo_name, repo_branch, "
            "readme_url, enabled_claude, enabled_codex, enabled_gemini, enabled_opencode, enabled_hermes, "
            "installed_at, content_hash, updated_at, enabled_grokbuild) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (skill_id, args.name, desc, directory, None, None, None, None,
             int(args.enable_claude), int(args.enable_codex), int(args.enable_gemini),
             int(args.enable_opencode), int(args.enable_hermes), now, content_hash, now,
             int(args.enable_grokbuild)),
        )
        action = "INSERTED"
    con.commit()
    row = cur.execute(
        "SELECT id, name, enabled_codex, enabled_claude, content_hash FROM skills WHERE id=?",
        (skill_id,),
    ).fetchone()
    print(f"[{action}] skills: {row['name']} codex={row['enabled_codex']} claude={row['enabled_claude']} hash={row['content_hash'][:16]}...")
    verify_no_q("skills.description", [desc])
    con.close()


def cmd_provider_block(args):
    block = read_text(args.block_file) if args.block_file else (args.block or "")
    cc_home, db_path = resolve_paths(args)
    con = connect(db_path)
    cur = con.cursor()
    provider_id = resolve_provider_id(cur, cc_home, args.app_type, args.provider_id)
    section = args.section.strip()
    row = cur.execute("SELECT settings_config FROM providers WHERE id=?", (provider_id,)).fetchone()
    if not row:
        raise SystemExit(f"provider not found: {provider_id}")
    obj = json.loads(row["settings_config"])
    if "config" not in obj or not isinstance(obj.get("config"), str):
        raise SystemExit(
            f"provider {provider_id} has no 'config' TOML text "
            "(claude/claude-desktop providers store env instead); use 'provider-env'"
        )
    cfg = obj.get("config", "")
    lines = cfg.splitlines(keepends=True)

    def line_strip(line):
        return line.rstrip("\r\n")

    start = next((i for i, line in enumerate(lines) if line_strip(line) == section), None)
    if start is not None:
        if not args.replace:
            raise SystemExit(f"section already exists: {section} (use --replace)")
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if lines[j].lstrip().startswith("[") and not _is_sub_section(section, line_strip(lines[j])):
                end = j
                break
        lines = lines[:start] + [block] + lines[end:]
        action = "REPLACED"
    else:
        if args.insert_before:
            target = args.insert_before.strip()
            pos = next((i for i, line in enumerate(lines) if line_strip(line) == target), None)
            if pos is None:
                raise SystemExit(f"--insert-before section not found: {target}")
            lines.insert(pos, block)
            action = f"INSERTED_BEFORE {target}"
        else:
            cfg = cfg.rstrip() + "\n\n" + block.rstrip() + "\n"
            lines = cfg.splitlines(keepends=True)
            action = "APPENDED"
    obj["config"] = "".join(lines)
    cur.execute(
        "UPDATE providers SET settings_config=? WHERE id=?",
        (json.dumps(obj, ensure_ascii=False), provider_id),
    )
    con.commit()
    cfg2 = json.loads(cur.execute("SELECT settings_config FROM providers WHERE id=?", (provider_id,)).fetchone()["settings_config"])["config"]
    print(f"[{action}] provider config: section present={section in cfg2}")
    con.close()


def cmd_provider_env(args):
    cc_home, db_path = resolve_paths(args)
    con = connect(db_path)
    cur = con.cursor()
    provider_id = resolve_provider_id(cur, cc_home, args.app_type, args.provider_id)
    row = cur.execute("SELECT settings_config FROM providers WHERE id=?", (provider_id,)).fetchone()
    if not row:
        raise SystemExit(f"provider not found: {provider_id}")
    obj = json.loads(row["settings_config"])
    env = obj.get("env")
    if not isinstance(env, dict):
        env = {}
    for kv in args.set or []:
        k, sep, v = kv.partition("=")
        if not sep or not k.strip():
            raise SystemExit(f"--set expects KEY=VALUE, got: {kv}")
        env[k.strip()] = v
    for k in args.remove or []:
        env.pop(k, None)
    obj["env"] = env
    cur.execute(
        "UPDATE providers SET settings_config=? WHERE id=?",
        (json.dumps(obj, ensure_ascii=False), provider_id),
    )
    con.commit()
    row = cur.execute("SELECT settings_config FROM providers WHERE id=?", (provider_id,)).fetchone()
    env2 = json.loads(row["settings_config"]).get("env", {})
    print(f"[UPDATED] provider {provider_id} env keys: {sorted(env2.keys())}")
    verify_no_q("provider.env values", list(env2.values()))
    con.close()


def cmd_set_flags(args):
    colmap = {
        "codex": "enabled_codex",
        "claude": "enabled_claude",
        "gemini": "enabled_gemini",
        "opencode": "enabled_opencode",
        "hermes": "enabled_hermes",
        "grokbuild": "enabled_grokbuild",
    }
    updates = {}
    for key, col in colmap.items():
        val = getattr(args, key, None)
        if val is not None:
            updates[col] = int(val)
    if not updates:
        raise SystemExit("provide at least one flag with 0 or 1 (e.g. --claude 1 --codex 0)")
    _, db_path = resolve_paths(args)
    con = connect(db_path)
    cur = con.cursor()
    row = cur.execute(f"SELECT name FROM {args.table} WHERE name=?", (args.name,)).fetchone()
    if not row:
        raise SystemExit(f"{args.table} row not found: {args.name}")
    sets = ", ".join(f"{col}=?" for col in updates)
    cur.execute(f"UPDATE {args.table} SET {sets} WHERE name=?", (*updates.values(), args.name))
    con.commit()
    row = cur.execute(
        f"SELECT name, enabled_codex, enabled_claude, enabled_gemini, enabled_opencode, "
        f"enabled_hermes, enabled_grokbuild FROM {args.table} WHERE name=?",
        (args.name,),
    ).fetchone()
    print(
        f"[UPDATED] {args.table}/{row['name']}: codex={row['enabled_codex']} claude={row['enabled_claude']} "
        f"gemini={row['enabled_gemini']} opencode={row['enabled_opencode']} "
        f"hermes={row['enabled_hermes']} grokbuild={row['enabled_grokbuild']}"
    )
    con.close()


def cmd_check(args):
    _, db_path = resolve_paths(args)
    con = connect(db_path)
    cur = con.cursor()
    hits = []

    def text_scan(table, cols):
        for col in cols:
            try:
                rows = cur.execute(
                    f"SELECT rowid, CAST({col} AS TEXT) AS v FROM {table} "
                    f"WHERE CAST({col} AS TEXT) LIKE '%?%'"
                )
            except sqlite3.OperationalError:
                # Older or trimmed schemas may lack a column; skip it.
                continue
            for row in rows:
                hits.append((table, col, row["rowid"], row["v"][:80]))

    for table, cols in (
        ("mcp_servers", ("name", "description", "tags", "server_config")),
        ("skills", ("name", "description", "directory")),
        ("prompts", ("name", "content")),
        ("providers", ("name", "notes")),
        ("model_pricing", ("display_name",)),
    ):
        text_scan(table, cols)

    def suspicious(value):
        if not isinstance(value, str) or "?" not in value:
            return False
        cjk = any("\u4e00" <= ch <= "\u9fff" for ch in value)
        return cjk or "??" in value

    def scan_json_blob(table, col, rowid, raw):
        try:
            obj = json.loads(raw)
        except Exception:
            if suspicious(raw):
                hits.append((table, col, rowid, raw[:80]))
            return
        stack = [obj]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
            elif suspicious(item):
                hits.append((table, col, rowid, item[:80]))

    for table, col in (
        ("providers", "settings_config"),
        ("settings", "value"),
    ):
        try:
            rows = cur.execute(
                f"SELECT rowid, CAST({col} AS TEXT) AS v FROM {table} WHERE CAST({col} AS TEXT) LIKE '%?%'"
            )
        except sqlite3.OperationalError:
            continue
        for row in rows:
            scan_json_blob(table, col, row["rowid"], row["v"])
    con.close()
    if hits:
        for h in hits:
            print("HIT:", h)
        raise SystemExit(f"[FAIL] {len(hits)} field(s) contain '?'")
    print("[OK] no mojibake '?' in CCS DB text fields")


def cmd_doctor(args):
    cc_home, db_path = resolve_paths(args)
    skills_root = cc_home / "skills"
    settings_file = cc_home / "settings.json"
    print(f"cc_home:    {cc_home}")
    print(f"db:         {db_path}  exists={db_path.exists()}")
    print(f"skills_dir: {skills_root}  exists={skills_root.exists()}")
    print(f"settings:   {settings_file}  exists={settings_file.exists()}")

    if not db_path.exists():
        print("[warn] database not found; run doctor after installing CC Switch")
        return
    con = connect(db_path)
    cur = con.cursor()
    try:
        version = cur.execute("PRAGMA user_version").fetchone()[0]
    except Exception:
        version = None
    print(f"db schema user_version: {version}")
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print(f"tables ({len(tables)}): {', '.join(tables)}")
    print("providers per app:")
    for row in cur.execute(
        "SELECT app_type, COUNT(*) AS n, SUM(is_current) AS current_n "
        "FROM providers GROUP BY app_type ORDER BY app_type"
    ):
        print(f"  {row['app_type']}: total={row['n']} current={row['current_n'] or 0}")
    con.close()

    settings_ids = load_settings_provider_ids(cc_home)
    print("settings currentProvider*:", {k: v for k, v in settings_ids.items() if v})


def build_parser():
    p = argparse.ArgumentParser(description="CCS DB operations (portable, UTF-8 safe)")
    p.add_argument("--cc-home", help="CC Switch home dir (default: CC_SWITCH_HOME or ~/.cc-switch)")
    p.add_argument("--db", help="sqlite db path (default: <cc-home>/cc-switch.db)")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_bool_flags(sp):
        for flag in ("enable_codex", "enable_claude", "enable_gemini", "enable_opencode", "enable_hermes", "enable_grokbuild"):
            sp.add_argument(f"--{flag.replace('_', '-')}", dest=flag, action="store_true", default=False)

    m = sub.add_parser("mcp-upsert")
    m.add_argument("--name", required=True)
    m.add_argument("--config", help="server_config JSON string")
    m.add_argument("--config-file", help="UTF-8 file containing server_config JSON")
    m.add_argument("--description", default="")
    m.add_argument("--description-file")
    m.add_argument("--tags", default="[]")
    m.add_argument("--tags-file")
    add_bool_flags(m)
    m.set_defaults(func=cmd_mcp_upsert)

    s = sub.add_parser("prompt-set")
    s.add_argument("--app-type", required=True, choices=APP_TYPES)
    s.add_argument("--name", default="全局")
    s.add_argument("--content", default="")
    s.add_argument("--content-file")
    s.set_defaults(func=cmd_prompt_set)

    k = sub.add_parser("skill-upsert")
    k.add_argument("--name", required=True)
    k.add_argument("--directory")
    k.add_argument("--description", default="")
    k.add_argument("--description-file")
    k.add_argument("--content-hash")
    add_bool_flags(k)
    k.set_defaults(func=cmd_skill_upsert)

    b = sub.add_parser("provider-block")
    b.add_argument("--provider-id")
    b.add_argument("--app-type", choices=APP_TYPES)
    b.add_argument("--section", required=True, help="exact TOML section header, e.g. [mcp_servers.foo]")
    b.add_argument("--block", default="")
    b.add_argument("--block-file", help="UTF-8 file containing the TOML block")
    b.add_argument("--insert-before", help="insert before this exact section header")
    b.add_argument("--replace", action="store_true", help="replace existing section")
    b.set_defaults(func=cmd_provider_block)

    e = sub.add_parser("provider-env")
    e.add_argument("--provider-id")
    e.add_argument("--app-type", choices=APP_TYPES)
    e.add_argument("--set", action="append", metavar="KEY=VALUE", help="set env var (repeatable)")
    e.add_argument("--remove", action="append", metavar="KEY", help="remove env var (repeatable)")
    e.set_defaults(func=cmd_provider_env)

    f = sub.add_parser("set-flags", description="Toggle enabled_* flags for an existing mcp_servers/skills row without touching other fields")
    f.add_argument("--table", required=True, choices=("mcp_servers", "skills"))
    f.add_argument("--name", required=True)
    for key in ("codex", "claude", "gemini", "opencode", "hermes", "grokbuild"):
        f.add_argument(f"--{key}", type=int, choices=(0, 1), default=None, help="1 = enable, 0 = disable")
    f.set_defaults(func=cmd_set_flags)

    c = sub.add_parser("check")
    c.set_defaults(func=cmd_check)

    d = sub.add_parser("doctor")
    d.set_defaults(func=cmd_doctor)
    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
