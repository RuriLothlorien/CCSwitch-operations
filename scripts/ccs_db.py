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
  check --strict  also run structural safety checks (MCP semantics, markers,
                  header order, live-only sections)
  doctor          print resolved paths, schema, and per-app provider status
  doctor --audit  read-only three-way consistency audit
  doctor --compare-backup <db>  diff current DB against a backup
  snapshot        save a point-in-time snapshot (DB + config.toml + settings)
  diff            show changes since a snapshot
  repair          dry-run/apply fixes for header order / live-only sections
  common-config   get/set/check/extract/set-key/remove-key/status/enable/disable

Safety model:
- Every mutating command runs a read-only structural preflight first. If the
  configuration is already broken (empty-command stdio MCP, unpaired markers,
  misplaced table headers, live-only sections in provider config), the write
  is refused unless --force is passed.
- Common-config snippet is only modified by explicit common-config subcommands.
- Enabling the per-provider "use common config" flag requires an idempotence
  check: stripping the snippet from the provider config and merging it back
  must be semantically equivalent, otherwise enable is refused.

Chinese values can be passed inline (wide argv survives Windows PowerShell) or
via UTF-8 files (--*-file) for large/sensitive content.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import time
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python 3.8-3.10
    import tomli as tomllib

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

# Only these app types have a common-config snippet and the per-provider
# "use common config" checkbox. Other agents are ignored for compatibility.
COMMON_CONFIG_APP_TYPES = ("codex", "claude", "gemini")


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
    cc_home, db_path = resolve_paths(args)
    run_preflight(args, cc_home, db_path)
    cfg = read_text(args.config_file) if args.config_file else args.config
    json.loads(cfg)
    desc = read_text(args.description_file) if args.description_file else (args.description or "")
    tags = read_text(args.tags_file) if args.tags_file else parse_tags(args.tags)

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
    cc_home, db_path = resolve_paths(args)
    run_preflight(args, cc_home, db_path)
    content = read_text(args.content_file) if args.content_file else (args.content or "")
    name = args.name or "全局"
    now_ms = int(time.time() * 1000)
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
    run_preflight(args, cc_home, db_path)
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
    run_preflight(args, cc_home, db_path)
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
    if getattr(args, "check_semantics", False):
        issues = find_header_issues("".join(lines), is_provider_config=True)
        if issues:
            print("[CHECK-SEMANTICS] issues in resulting provider config:")
            for iss in issues[:30]:
                print("  -", iss)
            raise SystemExit(2)
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
    run_preflight(args, cc_home, db_path)
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
    cc_home, db_path = resolve_paths(args)
    run_preflight(args, cc_home, db_path)
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
    if getattr(args, "strict", False):
        cc_home, db_path = resolve_paths(args)
        issues = collect_structural_issues(cc_home, db_path)
        if issues:
            print("[STRICT] structural issues:")
            for iss in issues[:80]:
                print("  -", iss)
            raise SystemExit(2)
        print("[OK] strict structural checks passed")


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

    if getattr(args, "audit", False):
        print("== audit ==")
        issues = collect_structural_issues(cc_home, db_path, ("providers", "config", "common"))
        if issues:
            for iss in issues[:80]:
                print("  -", iss)
        else:
            print("  no structural issues")
        con = connect(db_path)
        for r in con.execute(
            "SELECT id, name, settings_config FROM providers WHERE app_type='codex'"
        ):
            cfg = json.loads(r["settings_config"] or "{}").get("config", "")
            names = [
                h for h, path, _, _ in parse_sections(cfg)
                if path and path[0] == "mcp_servers" and len(path) == 1
            ]
            print(f"  provider[{r['name']}] mcp sections: {len(names)}")
        con.close()

    if getattr(args, "compare_backup", None):
        print(f"== compare backup {args.compare_backup} ==")
        _compare_db(db_path, Path(args.compare_backup))


# ================= structural safety =================

LIVE_ONLY_HEADERS = (
    "[projects", "[plugins", "[marketplaces", "[desktop", "[features",
    "[memories", "[windows", "[shell_environment_policy",
    "[sandbox_workspace_write", "[hooks.state",
)

MARKER_TAGS = ("instructions", "hooks", "mcp")


def codex_config_path() -> Path:
    env = os.environ.get("CODEX_HOME")
    if env:
        return Path(env).expanduser() / "config.toml"
    return Path.home() / ".codex" / "config.toml"


def _split_header(header):
    s = header.strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()
    parts = []
    buf = ""
    quote = None
    for ch in s:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            buf += ch
        elif ch == ".":
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf:
        parts.append(buf)
    return tuple(parts)


def parse_sections(text):
    lines = text.splitlines()
    sections = []
    cur = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]") and not stripped.startswith("[["):
            if cur is not None:
                sections.append(cur)
            cur = [stripped, _split_header(stripped), i, []]
        else:
            if cur is None:
                if sections and sections[-1][0] is None:
                    sections[-1][3].append(line)
                else:
                    sections.append([None, None, i, [line]])
            else:
                cur[3].append(line)
    if cur is not None:
        sections.append(cur)
    return sections


def marker_issues(text):
    openers = len(re.findall(
        r"#\s*>>>\s*codex-deepseek-routing-suite\s+(?:instructions|hooks|mcp)\s*:\s*begin\s*>>>",
        text, re.I,
    ))
    closers = len(re.findall(
        r"#\s*>>>\s*codex-deepseek-routing-suite\s+(?:instructions|hooks|mcp)\s*:\s*end\s*<<<",
        text, re.I,
    ))
    if openers != closers:
        return [f"routing-suite begin/end markers unbalanced: begin={openers} end={closers}"]
    return []


def _body_map(body):
    m = {}
    for line in body:
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            k, _, v = s.partition("=")
            m[k.strip()] = v.strip()
    return m


def mcp_semantic_issues(text):
    issues = []
    for header, path, _, body in parse_sections(text):
        if path and len(path) >= 2 and path[0] == "mcp_servers":
            m = _body_map(body)
            if m.get("type") == '"stdio"' and m.get("command") == '""':
                issues.append(f"{header}: stdio MCP with empty command")
            if "url" in m and m.get("command") == '""':
                issues.append(f"{header}: url-only remote MCP written with empty stdio command")
    return issues


def header_order_issues(text):
    issues = []
    sections = parse_sections(text)
    seen = {}
    for header, path, i, _ in sections:
        if path is None:
            continue
        if path in seen:
            issues.append(f"duplicate table header {header} (line {i + 1})")
        seen.setdefault(path, i)
    for header, path, i, _ in sections:
        if path is None:
            continue
        for anc in [path[:k] for k in range(1, len(path))]:
            for h2, p2, j, _ in sections:
                if p2 == anc and j > i:
                    issues.append(
                        f"{header} (line {i + 1}): parent [{' . '.join(anc)}] appears after child (line {j + 1})"
                    )
    for header, path, i, body in sections:
        if path is None:
            continue
        # Empty container parents ([mcp_servers], [plugins], ...) may legally have
        # children spread across the file in CC Switch's layout; only flag
        # interleaving when the parent table carries actual key/value content.
        if not _body_map(body):
            continue
        for hc, pc, k, _ in sections:
            if pc and len(pc) == len(path) + 1 and pc[:-1] == path and k > i:
                for hb, pb, j, _ in sections:
                    if i < j < k and not (pb and pb[:len(path)] == path):
                        issues.append(f"{hb} (line {j + 1}) interleaved between {header} and {hc}")
    return issues


def live_only_issues(text):
    issues = []
    for header, path, i, _ in parse_sections(text):
        if header and header.startswith(LIVE_ONLY_HEADERS):
            issues.append(f"{header} (line {i + 1}): live-only section in provider config")
    return issues


def find_header_issues(text, is_provider_config=False):
    issues = []
    issues += marker_issues(text)
    issues += mcp_semantic_issues(text)
    issues += header_order_issues(text)
    if is_provider_config:
        issues += live_only_issues(text)
    return issues


def _join_sections(sections):
    out = []
    for idx, (header, path, _, body) in enumerate(sections):
        if idx > 0:
            out.append("")
        if header is not None:
            out.append(header)
        out.extend(body)
    return "\n".join(out).rstrip("\n") + "\n"


def repair_header_order(text):
    """Minimal header-order repair: only move sections that actually violate
    parent/child ordering. Legal layouts (e.g. CC Switch's empty container
    headers like [mcp_servers] with children spread across the file) stay
    untouched."""
    moved = []
    original = text
    text = text.rstrip("\n") + "\n"
    while True:
        sections = parse_sections(text)
        action = None
        # 1) unrelated section interleaved between a non-empty parent and its child
        for idx_p, (header, path, i, body) in enumerate(sections):
            if path is None or not _body_map(body):
                continue
            for idx_c, (hc, pc, k, _) in enumerate(sections):
                if pc and len(pc) == len(path) + 1 and pc[:-1] == path and idx_c > idx_p:
                    for idx_b, (hb, pb, j, _) in enumerate(sections):
                        if idx_p < idx_b < idx_c and not (pb and pb[:len(path)] == path):
                            action = ("after", sections[idx_b], sections[idx_c])
                            break
                    if action:
                        break
            if action:
                break
        # 2) parent table appearing after its child
        if not action:
            for idx_c, (header, path, i, _) in enumerate(sections):
                if path is None:
                    continue
                for anc in [path[:n] for n in range(1, len(path))]:
                    for idx_p, (h2, p2, j, _) in enumerate(sections):
                        if p2 == anc and idx_p > idx_c:
                            action = ("before", sections[idx_p], sections[idx_c])
                            break
                    if action:
                        break
                if action:
                    break
        if not action:
            break
        kind, sec, anchor = action
        rest = [s for s in sections if s is not sec]
        ref_idx = next(n for n, s in enumerate(rest) if s is anchor)
        if kind == "after":
            rest.insert(ref_idx + 1, sec)
        else:
            rest.insert(ref_idx, sec)
        moved.append(sec[0])
        text = _join_sections(rest)
    if not moved:
        return original, []
    return text, moved


def strip_live_only_sections(text):
    kept = []
    removed = []
    for header, path, i, body in parse_sections(text):
        if header and header.startswith(LIVE_ONLY_HEADERS):
            removed.append(header)
        else:
            kept.append([header, path, i, body])
    if not removed:
        return text, []
    return _join_sections(kept), removed


def toml_to_map(text):
    out = {}
    for header, path, _, body in parse_sections(text):
        if path is None:
            out[()] = _body_map(body)
        else:
            out[path] = _body_map(body)
    return out


def is_idempotent(provider_text, snippet_text):
    pm = toml_to_map(provider_text)
    sm = toml_to_map(snippet_text)
    conflicts = []
    for path, keys in sm.items():
        target = pm.get(path, {})
        for k, v in keys.items():
            if k in target and target[k] != v:
                label = ".".join(path) if path else "<top>"
                conflicts.append(f"{label}.{k}: provider={target[k]} snippet={v}")
    return (not conflicts), conflicts


def _is_top_key_line(line, top_keys):
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        return False
    return s.partition("=")[0].strip() in top_keys


def strip_snippet_from_config(provider_text, snippet_text):
    sections = parse_sections(provider_text)
    sm = toml_to_map(snippet_text)
    snippet_tables = {p for p in sm if p}
    top_keys = set(sm.get((), {}))
    kept = []
    for header, path, i, body in sections:
        if path is None:
            body = [line for line in body if not _is_top_key_line(line, top_keys)]
            kept.append([None, None, i, body])
        elif path in snippet_tables:
            continue
        else:
            kept.append([header, path, i, body])
    return _join_sections(kept)


def extract_common_config_from_provider(text):
    sections = parse_sections(text)
    drop_top = {"model", "model_provider", "base_url", "wire_api",
                "experimental_bearer_token", "model_catalog_json"}
    kept = []
    for header, path, i, body in sections:
        if path is None:
            body = [line for line in body if not _is_top_key_line(line, drop_top)]
            body = [
                line for line in body
                if not (line.strip().startswith("web_search")
                        and '"disabled"' in line)
            ]
            kept.append([None, None, i, body])
        elif path[0] in ("model_providers", "mcp_servers", "mcp"):
            continue
        elif path[0] == "hooks" and len(path) > 1 and path[1] == "state":
            continue
        else:
            kept.append([header, path, i, body])
    return _join_sections(kept)


def _pair_instructions_markers(text):
    if "model_instructions_file" not in text:
        return text
    if "instructions: begin" not in text:
        text = text.replace(
            'model_instructions_file = "',
            '# >>> codex-deepseek-routing-suite instructions: begin >>>\nmodel_instructions_file = "',
            1,
        )
    if "instructions: end" not in text:
        idx = text.find("model_instructions_file")
        if idx != -1:
            end = text.find("\n", idx)
            if end == -1:
                end = len(text)
            text = text[:end + 1] + "# >>> codex-deepseek-routing-suite instructions: end <<<\n" + text[end + 1:]
    return text


def collect_structural_issues(cc_home, db_path, targets=("providers", "config", "common")):
    issues = []
    con = None
    try:
        con = connect(db_path)
        cur = con.cursor()
        if "providers" in targets:
            for r in cur.execute(
                "SELECT id, app_type, name, settings_config FROM providers"
            ):
                try:
                    obj = json.loads(r["settings_config"] or "{}")
                except Exception:
                    continue
                cfg = obj.get("config")
                if isinstance(cfg, str) and cfg.strip():
                    for iss in find_header_issues(cfg, is_provider_config=(r["app_type"] == "codex")):
                        issues.append(f"provider[{r['name']}]: {iss}")
        if "common" in targets:
            for app in ("codex", "claude", "gemini"):
                row = cur.execute(
                    "SELECT value FROM settings WHERE key=?",
                    (f"common_config_{app}",),
                ).fetchone()
                if row and row["value"]:
                    for iss in find_header_issues(row["value"], is_provider_config=False):
                        issues.append(f"common_config_{app}: {iss}")
    finally:
        if con:
            con.close()
    if "config" in targets:
        cfg = codex_config_path()
        if cfg.exists():
            try:
                text = cfg.read_text(encoding="utf-8")
            except Exception:
                text = ""
            for iss in find_header_issues(text, is_provider_config=False):
                issues.append(f"config.toml: {iss}")
    return issues


def run_preflight(args, cc_home, db_path, targets=("providers", "config", "common")):
    if getattr(args, "force", False):
        return []
    issues = collect_structural_issues(cc_home, db_path, targets)
    if issues:
        print("[PREFLIGHT] structural issues found; run 'repair' or pass --force to override:")
        for iss in issues[:50]:
            print("  -", iss)
        raise SystemExit(2)
    return issues


def backup_db(cc_home, db_path, slug):
    backups = cc_home / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    dst = backups / f"db_backup_{time.strftime('%Y%m%d-%H%M%S')}-{slug}.db"
    shutil.copy2(db_path, dst)
    return dst


def backup_file(path, slug):
    dst = Path(str(path) + f".bak-{time.strftime('%Y%m%d-%H%M%S')}-{slug}")
    shutil.copy2(path, dst)
    return dst


def get_snippet(con, app_type):
    row = con.execute(
        "SELECT value FROM settings WHERE key=?",
        (f"common_config_{app_type}",),
    ).fetchone()
    return row["value"] if row else ""


def set_snippet(con, app_type, value):
    con.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (f"common_config_{app_type}", value),
    )


def _validate_snippet(app_type, content):
    if app_type == "codex":
        tomllib.loads(content)
    else:
        json.loads(content)


def set_common_config_enabled(con, provider_id, enabled):
    row = con.execute("SELECT meta FROM providers WHERE id=?", (provider_id,)).fetchone()
    if not row:
        raise SystemExit(f"provider not found: {provider_id}")
    try:
        meta = json.loads(row["meta"]) if row["meta"] else {}
    except Exception:
        meta = {}
    meta["common_config_enabled"] = enabled
    con.execute(
        "UPDATE providers SET meta=? WHERE id=?",
        (json.dumps(meta, ensure_ascii=False), provider_id),
    )


def _sync_and_enable_current(con, cc_home, app_type):
    provider_id = resolve_provider_id(con, cc_home, app_type, None)
    row = con.execute("SELECT settings_config FROM providers WHERE id=?", (provider_id,)).fetchone()
    obj = json.loads(row["settings_config"])
    cfg = obj.get("config", "")
    snippet = get_snippet(con, app_type)
    ok, conflicts = is_idempotent(cfg, snippet)
    if not ok:
        print("[SKIP] sync-and-enable refused; idempotence conflicts:")
        for c in conflicts[:20]:
            print("  -", c)
        return
    obj["config"] = strip_snippet_from_config(cfg, snippet)
    con.execute(
        "UPDATE providers SET settings_config=? WHERE id=?",
        (json.dumps(obj, ensure_ascii=False), provider_id),
    )
    set_common_config_enabled(con, provider_id, True)
    con.commit()
    print(f"[SYNC] provider {provider_id} config stripped of snippet keys and commonConfigEnabled=true")


def _maybe_sync_and_enable(args, con, cc_home, app_type):
    if getattr(args, "sync_and_enable", False):
        _sync_and_enable_current(con, cc_home, app_type)
        return
    if sys.stdin.isatty():
        try:
            ans = input("是否同步当前配置并打勾？[y/N] ").strip().lower()
        except EOFError:
            return
        if ans in ("y", "yes"):
            _sync_and_enable_current(con, cc_home, app_type)


def edit_snippet_key(app_type, content, key, value, remove):
    if app_type == "codex":
        parts = key.split(".")
        sections = parse_sections(content)
        if len(parts) == 1:
            # top-level key
            new_lines = []
            found = False
            for header, path, i, body in sections:
                if path is None:
                    for line in body:
                        if _is_top_key_line(line, {key}):
                            found = True
                            if not remove:
                                new_lines.append(f"{key} = {value}")
                            continue
                        new_lines.append(line)
                    if not found and not remove:
                        new_lines.append(f"{key} = {value}")
                else:
                    new_lines.extend(body)
                if header is not None:
                    # body already copied; no need to re-add header
                    pass
            # rebuild: sections order lost; rebuild manually below
            return _rebuild_from_lines(sections, key, value, remove, parts)
        else:
            sec_name = "[" + ".".join(parts[:-1]) + "]"
            target_key = parts[-1]
            sections = parse_sections(content)
            found_sec = False
            changed = False
            out = []
            for idx, (header, path, i, body) in enumerate(sections):
                if idx > 0:
                    out.append("")
                if header is not None:
                    out.append(header)
                if header == sec_name:
                    found_sec = True
                    new_body = []
                    for line in body:
                        if _is_top_key_line(line, {target_key}):
                            changed = True
                            if not remove:
                                new_body.append(f"{target_key} = {value}")
                            continue
                        new_body.append(line)
                    if not remove and not any(_is_top_key_line(l, {target_key}) for l in new_body):
                        new_body.append(f"{target_key} = {value}")
                        changed = True
                    out.extend(new_body)
                else:
                    out.extend(body)
            if not found_sec and not remove:
                out.append("")
                out.append(sec_name)
                out.append(f"{target_key} = {value}")
                changed = True
            return "\n".join(out).rstrip("\n") + "\n"
    else:
        obj = json.loads(content)
        node = obj
        parts = key.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        if remove:
            node.pop(parts[-1], None)
        else:
            node[parts[-1]] = json.loads(value)
        return json.dumps(obj, ensure_ascii=False, indent=2)


def _rebuild_from_lines(sections, key, value, remove, parts):
    out = []
    changed = False
    for idx, (header, path, i, body) in enumerate(sections):
        if idx > 0:
            out.append("")
        if header is not None:
            out.append(header)
        if path is None:
            new_body = []
            for line in body:
                if _is_top_key_line(line, {key}):
                    changed = True
                    if not remove:
                        new_body.append(f"{key} = {value}")
                    continue
                new_body.append(line)
            if not remove and not any(_is_top_key_line(l, {key}) for l in new_body):
                new_body.append(f"{key} = {value}")
                changed = True
            out.extend(new_body)
        else:
            out.extend(body)
    return "\n".join(out).rstrip("\n") + "\n"


def _compare_db(cur_db, snap_db):
    import difflib

    def dump(db, tables):
        if not Path(db).exists():
            return {t: [] for t in tables}
        c = sqlite3.connect(str(db))
        c.row_factory = sqlite3.Row
        out = {}
        for t in tables:
            try:
                out[t] = [dict(r) for r in c.execute(f"SELECT * FROM {t}")]
            except Exception:
                out[t] = []
        c.close()
        return out

    tables = ("providers", "settings", "mcp_servers", "skills", "prompts")
    a = dump(snap_db, tables)
    b = dump(cur_db, tables)
    for t in tables:
        if a[t] == b[t]:
            continue
        key_of = lambda r: str(r.get("id") or r.get("key") or r.get("name") or r.get("app_type"))
        am = {key_of(r): r for r in a[t]}
        bm = {key_of(r): r for r in b[t]}
        print(f"== {t}: {len(am)} -> {len(bm)} ==")
        for k in sorted(set(am) | set(bm)):
            if am.get(k) != bm.get(k):
                print(f"  row {k}: changed")
    cfg_a = Path(str(snap_db.parent / "config.toml"))
    cfg_b = codex_config_path()
    if cfg_a.exists() and cfg_b.exists():
        d = list(difflib.unified_diff(
            cfg_a.read_text(encoding="utf-8").splitlines(),
            cfg_b.read_text(encoding="utf-8").splitlines(),
            "snapshot", "current", lineterm="",
        ))
        print("== config.toml ==")
        print("\n".join(d) if d else "  (unchanged)")


def cmd_snapshot(args):
    cc_home, db_path = resolve_paths(args)
    snap = cc_home / "snapshots" / time.strftime("%Y%m%d-%H%M%S")
    snap.mkdir(parents=True, exist_ok=True)
    shutil.copy2(db_path, snap / "cc-switch.db")
    cfg = codex_config_path()
    if cfg.exists():
        shutil.copy2(cfg, snap / "config.toml")
    st = cc_home / "settings.json"
    if st.exists():
        shutil.copy2(st, snap / "settings.json")
    print(snap)


def cmd_diff(args):
    cc_home, db_path = resolve_paths(args)
    snap = Path(args.snapshot)
    if not (snap / "cc-switch.db").exists():
        raise SystemExit(f"snapshot db not found: {snap / 'cc-switch.db'}")
    _compare_db(db_path, snap / "cc-switch.db")


def cmd_repair(args):
    cc_home, db_path = resolve_paths(args)
    apply = args.apply
    mode = args.mode
    target = args.target

    if target == "config.toml":
        path = codex_config_path()
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        new_text = text
        moved = []
        removed = []
        if mode in ("header-order", "both"):
            new_text, moved = repair_header_order(new_text)
        if mode == "live-only":
            new_text, removed = strip_live_only_sections(new_text)
        changed = new_text != text
        print(f"[{'APPLY' if apply else 'DRY-RUN'}] config.toml changed={changed}")
        if moved:
            print("  moved:", ", ".join(moved[:30]))
        if removed:
            print("  removed:", ", ".join(removed[:30]))
        if changed and apply:
            backup_file(path, "repair")
            path.write_text(new_text, encoding="utf-8")
            print("  backup + applied")
        return

    con = connect(db_path)
    try:
        if target == "provider":
            provider_id = args.provider_id or resolve_provider_id(
                con, cc_home, args.app_type, None
            )
            row = con.execute(
                "SELECT settings_config FROM providers WHERE id=?", (provider_id,)
            ).fetchone()
            if not row:
                raise SystemExit(f"provider not found: {provider_id}")
            obj = json.loads(row["settings_config"])
            cfg = obj.get("config", "")
            new_cfg = cfg
            moved = []
            removed = []
            if mode in ("header-order", "both"):
                new_cfg, moved = repair_header_order(new_cfg)
            if mode in ("live-only", "both"):
                new_cfg, removed = strip_live_only_sections(new_cfg)
            changed = new_cfg != cfg
            print(f"[{'APPLY' if apply else 'DRY-RUN'}] provider {provider_id} changed={changed}")
            if moved:
                print("  moved:", ", ".join(moved[:30]))
            if removed:
                print("  removed:", ", ".join(removed[:30]))
            if changed and apply:
                backup_db(cc_home, db_path, "repair-provider")
                obj["config"] = new_cfg
                con.execute(
                    "UPDATE providers SET settings_config=? WHERE id=?",
                    (json.dumps(obj, ensure_ascii=False), provider_id),
                )
                con.commit()
                print("  backup + applied")
        elif target == "common":
            app_type = args.app_type
            value = get_snippet(con, app_type)
            new_value = value
            moved = []
            removed = []
            if mode in ("header-order", "both"):
                new_value, moved = repair_header_order(new_value)
            if mode == "live-only":
                new_value, removed = strip_live_only_sections(new_value)
            new_value = _pair_instructions_markers(new_value)
            changed = new_value != value
            print(f"[{'APPLY' if apply else 'DRY-RUN'}] common_config_{app_type} changed={changed}")
            if moved:
                print("  moved:", ", ".join(moved[:30]))
            if removed:
                print("  removed:", ", ".join(removed[:30]))
            if changed and apply:
                backup_db(cc_home, db_path, "repair-common")
                set_snippet(con, app_type, new_value)
                con.commit()
                print("  backup + applied")
        else:
            raise SystemExit("--target must be config.toml | provider | common")
    finally:
        con.close()


def cmd_common_config(args):
    cc_home, db_path = resolve_paths(args)
    app_type = args.app_type
    sub = args.cc_cmd
    if app_type not in COMMON_CONFIG_APP_TYPES:
        print(f"[SKIP] app_type '{app_type}' does not use common config; ignored")
        return
    if sub in ("set", "set-key", "remove-key", "extract"):
        run_preflight(args, cc_home, db_path)
    con = connect(db_path)
    try:
        if sub == "get":
            print(get_snippet(con, app_type) or "(empty)")
        elif sub == "check":
            value = get_snippet(con, app_type)
            if not value.strip():
                print(f"[OK] common_config_{app_type} is empty")
                return
            issues = find_header_issues(value)
            if issues:
                for iss in issues:
                    print("  -", iss)
                raise SystemExit(2)
            print(f"[OK] common_config_{app_type} structurally clean")
        elif sub == "set":
            content = read_text(args.content_file) if args.content_file else args.content
            _validate_snippet(app_type, content)
            if not args.apply:
                print(f"[DRY-RUN] would update common_config_{app_type}")
                return
            backup_db(cc_home, db_path, f"common-{app_type}-set")
            set_snippet(con, app_type, content)
            con.commit()
            print(f"[SET] common_config_{app_type} updated ({len(content)} chars)")
            _maybe_sync_and_enable(args, con, cc_home, app_type)
        elif sub == "extract":
            if app_type != "codex":
                raise SystemExit("extract is only supported for codex")
            provider_id = args.provider_id or resolve_provider_id(con, cc_home, app_type, None)
            row = con.execute(
                "SELECT settings_config FROM providers WHERE id=?", (provider_id,)
            ).fetchone()
            obj = json.loads(row["settings_config"])
            cfg = obj.get("config", "")
            extracted = extract_common_config_from_provider(cfg)
            _validate_snippet("codex", extracted)
            ok, conflicts = is_idempotent(cfg, extracted)
            if not ok:
                raise SystemExit("extract conflicts with provider config: " + "; ".join(conflicts[:20]))
            if not args.apply:
                print(f"[DRY-RUN] would extract common_config_codex from provider {provider_id} and enable it")
                return
            backup_db(cc_home, db_path, f"common-{app_type}-extract")
            set_snippet(con, app_type, extracted)
            set_common_config_enabled(con, provider_id, True)
            con.commit()
            print(f"[EXTRACT] common_config_codex updated; provider {provider_id} commonConfigEnabled=true")
        elif sub in ("set-key", "remove-key"):
            value = get_snippet(con, app_type)
            new_value = edit_snippet_key(
                app_type, value, args.key,
                getattr(args, "value", None), sub == "remove-key",
            )
            _validate_snippet(app_type, new_value)
            if not args.apply:
                print(f"[DRY-RUN] would {sub} key '{args.key}' in common_config_{app_type}")
                return
            backup_db(cc_home, db_path, f"common-{app_type}-{sub}")
            set_snippet(con, app_type, new_value)
            con.commit()
            print(f"[{sub.upper()}] common_config_{app_type} key '{args.key}' updated")
            _maybe_sync_and_enable(args, con, cc_home, app_type)
        elif sub == "status":
            for r in con.execute(
                "SELECT id, app_type, name, is_current, meta FROM providers "
                "WHERE app_type=? ORDER BY name",
                (app_type,),
            ):
                try:
                    meta = json.loads(r["meta"]) if r["meta"] else {}
                except Exception:
                    meta = {}
                flag = meta.get("common_config_enabled")
                state = {True: "enabled", False: "disabled", None: "auto"}[flag]
                print(f"  {r['app_type']}/{r['name']}: common_config_enabled={state}")
        elif sub == "enable":
            provider_id = args.provider_id or resolve_provider_id(con, cc_home, app_type, None)
            row = con.execute(
                "SELECT settings_config FROM providers WHERE id=?", (provider_id,)
            ).fetchone()
            cfg = json.loads(row["settings_config"]).get("config", "")
            snippet = get_snippet(con, app_type)
            ok, conflicts = is_idempotent(cfg, snippet)
            if not ok:
                print("[REFUSED] idempotence check failed; conflicts:")
                for c in conflicts[:30]:
                    print("  -", c)
                print(f"suggest: repair --target provider --provider-id {provider_id} --mode live-only")
                raise SystemExit(2)
            if not args.apply:
                print(f"[DRY-RUN] would enable commonConfigEnabled for {provider_id}")
                return
            backup_db(cc_home, db_path, f"common-{app_type}-enable")
            set_common_config_enabled(con, provider_id, True)
            con.commit()
            print(f"[ENABLE] provider {provider_id} commonConfigEnabled=true")
        elif sub == "disable":
            provider_id = args.provider_id or resolve_provider_id(con, cc_home, app_type, None)
            if not args.apply:
                print(f"[DRY-RUN] would disable commonConfigEnabled for {provider_id}")
                return
            backup_db(cc_home, db_path, f"common-{app_type}-disable")
            set_common_config_enabled(con, provider_id, False)
            con.commit()
            print(f"[DISABLE] provider {provider_id} commonConfigEnabled=false")
    finally:
        con.close()


def build_parser():
    p = argparse.ArgumentParser(description="CCS DB operations (portable, UTF-8 safe)")
    p.add_argument("--cc-home", help="CC Switch home dir (default: CC_SWITCH_HOME or ~/.cc-switch)")
    p.add_argument("--db", help="sqlite db path (default: <cc-home>/cc-switch.db)")
    p.add_argument("--force", action="store_true", help="skip preflight structural checks")
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
    b.add_argument("--check-semantics", action="store_true",
                   help="validate the resulting config for MCP/marker/header issues")
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
    c.add_argument("--strict", action="store_true", help="also run structural safety checks")
    c.set_defaults(func=cmd_check)

    d = sub.add_parser("doctor")
    d.add_argument("--audit", action="store_true", help="run three-way consistency audit")
    d.add_argument("--compare-backup", metavar="DB", help="diff current DB against a backup DB")
    d.set_defaults(func=cmd_doctor)

    sn = sub.add_parser("snapshot", help="save point-in-time snapshot (DB + config.toml + settings)")
    sn.set_defaults(func=cmd_snapshot)

    df = sub.add_parser("diff", help="show changes since a snapshot")
    df.add_argument("snapshot", help="snapshot directory")
    df.set_defaults(func=cmd_diff)

    rp = sub.add_parser("repair", help="fix header order / live-only sections (dry-run by default)")
    rp.add_argument("--target", required=True, choices=("config.toml", "provider", "common"))
    rp.add_argument("--mode", choices=("header-order", "live-only", "both"), default="both")
    rp.add_argument("--apply", action="store_true", help="write changes (with automatic backup)")
    rp.add_argument("--provider-id")
    rp.add_argument("--app-type", choices=APP_TYPES, default="codex")
    rp.set_defaults(func=cmd_repair)

    cc = sub.add_parser("common-config", help="maintain the common-config snippet")
    cc_sub = cc.add_subparsers(dest="cc_cmd", required=True)
    cc_parent = argparse.ArgumentParser(add_help=False)
    cc_parent.add_argument("--app-type", choices=APP_TYPES, default="codex")
    cc_parent.add_argument("--provider-id", help="explicit provider id (enable/disable/extract)")
    cc_parent.add_argument("--apply", action="store_true", help="write changes (with automatic backup)")
    cc_parent.add_argument("--sync-and-enable", action="store_true",
                           help="after set*, also sync current provider config and enable the flag")
    cc_parent.add_argument("--content", default="")
    cc_parent.add_argument("--content-file")
    cc_parent.add_argument("--key", default="")
    cc_parent.add_argument("--value", default="")
    for name in ("get", "check", "set", "extract", "set-key", "remove-key",
                 "status", "enable", "disable"):
        cc_sub.add_parser(name, parents=[cc_parent])
    cc.set_defaults(func=cmd_common_config)
    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
