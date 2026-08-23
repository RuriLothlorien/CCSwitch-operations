---
name: CCSwitch-operations
description: "Operate CC Switch (CCS): safely modify and sync its managed configuration — global prompts, skills, MCP servers, providers, and the Codex model catalog — across Codex, Claude Code, Claude Desktop, and other managed apps via cc-switch.db and the managed config files. Use when the user asks to 同步/修改 CCS 或 CC Switch 配置、全局提示词、skill 同步/安装、MCP 配置、供应商配置、修复 CCS 乱码, or whenever CCS-managed files must be edited without being overwritten on the next sync."
---

# CC Switch Operations

Methodology for safely operating CC Switch (CCS): backup first, stop the app, edit, validate, restart, and re-check.

> **Version compatibility**: designed and tested with CC Switch **3.20.0** (database schema v17). Run `scripts/ccs_db.py doctor` to verify the installed schema; other versions may behave differently — see `references/migration.md` for official version behavior changes.

> **Iron rule**: when unsure, first carefully read this skill (SKILL.md and its references) — do not improvise or guess. If the request is genuinely outside this skill's scope, tell the user and propose concrete recommended actions instead.

## 1. Safety workflow (mandatory for any write)

1. Backup: config files become `*.bak-<yyyyMMdd>-<slug>`; the database is copied to `<cc-home>/backups/db_backup_<stamp>.db`.
2. Stop CCS (the `cc-switch` process) before editing its database; a running CCS can overwrite your edits from memory.
3. Edit (see the sections below; use `scripts/ccs_db.py` for database writes).
4. Validate: TOML with `tomllib`, JSON with `json.load`, database with `python scripts/ccs_db.py check`; inspect Chinese text with `repr()`/`ascii()`.
5. Restart CCS, wait 3–5 seconds.
6. Re-parse the config files and confirm CCS did not rewrite them.
7. Remind the user to restart target apps (config is loaded at startup).

## 2. Encoding safety

- Never pipe Chinese text into Python through a shell that can mangle encoding (Windows PowerShell 5.1 uses the console code page; Chinese can become `?` and corrupt the DB permanently).
- Use `scripts/ccs_db.py` for Chinese-containing DB writes; pass Chinese inline (wide argv) or via UTF-8 files (`--*-file`).
- On Windows PowerShell, save `.ps1` files as UTF-8 with BOM.
- After any write, run `scripts/ccs_db.py check`; it covers user-facing text and JSON/TOML blobs and reports `?` only when it looks like mojibake (not legitimate URL query strings).

## 3. Architecture (details: references/architecture.md)

- Database: `<cc-home>/cc-switch.db` (schema v17 as of CCS 3.20). Hand-maintained tables: `providers`, `prompts`, `skills`, `mcp_servers`, `settings`. CCS-managed tables (`model_pricing`, `profiles`, `proxy_*`, `session_usage_dedup`, `usage_daily_rollups`, `skill_repos`, ...) must not be edited by hand.
- `cc-home` discovery: `CC_SWITCH_HOME` env var, else `~/.cc-switch`. `scripts/ccs_db.py` resolves this automatically; `doctor` prints the resolved paths.
- Managed apps (9): codex, claude, claude-desktop, gemini, grokbuild, opencode, openclaw, hermes, pi. Switch-mode apps (claude/codex/gemini) write only the current provider; additive-mode apps (opencode/openclaw/hermes/pi) let providers coexist. Pi has no MCP registry and its skills are exists-equals-enabled; Claude Desktop is not synced by CCS.
- Official/bundled MCP servers (for example `openaiDeveloperDocs`) are intentionally absent from the `mcp_servers` table; do not add them.

## 4. Global prompts (prompts table)

- `prompts` stores `app_type` (9 values) and `name='全局'` content with `enabled=1`.
- Update via `scripts/ccs_db.py prompt-set --app-type codex|claude|... --content-file <utf8.txt>`.
- Keep codex and claude contents consistent unless the user explicitly asks otherwise.

## 5. Skills

- Source of truth: `<cc-home>/skills/<name>/SKILL.md`; `skills.enabled_*` flags control per-app enablement.
- Install to an app = copy/symlink/junction the skill folder into the app's skills directory (see references/apps.md for per-app paths). The exact link style is controlled by CCS `skillSyncMethod` (auto/symlink/copy).
- After editing a local SKILL.md, refresh its `content_hash` with `skill-upsert`.

## 6. MCP

- Three places must stay consistent for user-managed MCP servers: `~/.codex/config.toml` (live), the `mcp_servers` table (panel), and the current codex provider's `settings_config.config` text. Use `mcp-upsert` + `provider-block`.
- Claude Desktop MCP configs are separate JSON files (see references/operations.md).
- Codex does not support SSE transport; bridge via `npx -y mcp-remote <url> --transport sse-only` where needed.

## 7. Verification checklist

- `python scripts/ccs_db.py check` passes.
- `python scripts/ccs_db.py check --strict` and `doctor --audit` pass (structural safety + three-way consistency).
- `codex mcp list` shows the expected command/args/env; official/bundled servers may appear without `mcp_servers` rows.
- `settings.json` `currentProvider*` matches `providers.is_current`.
- After CCS restart, config files are unchanged.
- Target apps are fully restarted before judging visibility.
- After any write, confirm the config text did not change beyond the intended edit (byte-level re-check).

## 8. Proactive preflight and known upstream defect (3.20.0)

- **Proactive preflight**: every mutating command (`provider-block` / `provider-env` / `mcp-upsert` / `prompt-set` / `skill-upsert` / `set-flags` / `common-config set|set-key|remove-key|extract` / `repair --apply`) runs a read-only structural audit first. If it finds empty-command stdio MCP servers, unpaired markers, misplaced/out-of-place table headers, or live-only sections, the write is refused with repair hints (`--force` overrides).
- **Known upstream defect**: CC Switch 3.20.0's provider edit page — even when saved without any changes — can reorder `config.toml`, strip common-config blocks, misplace markers, and serialize a url-only remote MCP as `type="stdio"` + `command=""` (frontend smol-toml round-trip plus backend toml_edit strip/merge). **Do not use the edit page to save or extract Codex provider config**; use this skill's commands instead.
  - Common symptoms: top-level `notify = [...]` displaced, `[plugins]` / `[marketplaces]` blocks stripped, `[mcp_servers]` / `[mcp_servers.node_repl(.env)]` blocks or keys rewritten or reordered.
- **Common-config maintenance**: `common-config` only modifies the snippet when explicitly invoked; `enable` requires an idempotence check (stripping the snippet and re-merging must stay semantically equivalent); `extract` auto-enables after success; `set*` asks whether to sync the current config and enable (non-interactive defaults to no sync unless `--sync-and-enable`).
- **Canonical "update both provider and common config" flow**: use `common-config set-key|set --apply --sync-and-enable` — it updates the snippet, strips duplicate snippet keys from the current provider config, and enables the flag in one step. Never hand-write temporary scripts to edit the CCS DB directly; DB writes go through `ccs_db.py`. Canonical state: the snippet owns the keys, the provider config does not duplicate them.
- **Scope disambiguation**: "sync" / "同步" is ambiguous about BOTH the object and the target. First confirm WHAT is being synced — configuration, skill files, or template — before acting. If it is a configuration sync and the scope is not explicit, default to the **provider config** (provider-first), then ask whether to extract to the common-config template (`common-config extract`). Only touch the `common-config` snippet directly when the user explicitly says "common config" / "通用配置" / "模板"; never unilaterally change only the common-config, and never treat a "sync the skill" request as a configuration sync.
- **Provider-first sync**: a config "sync" without an explicit scope updates the provider config via `provider-set-key`; after that, ask whether to `common-config extract` to the template.
- **Uncertainty handling**: when unsure, first re-read this skill (SKILL.md and its references) — do not improvise. If the request is outside this skill's scope, tell the user and propose recommended actions.

## References

- references/architecture.md — paths, tables, effect chain
- references/apps.md — the 9 managed apps matrix
- references/operations.md — copy-paste command templates (PowerShell + bash)
- references/pitfalls.md — known pitfalls
- references/migration.md — official CCS version behavior changes
- references/examples/ — sample TOML/JSON/prompt files

## Helper script

- scripts/ccs_db.py — portable CCS DB operations (UTF-8 safe). Subcommands: `mcp-upsert`, `prompt-set`, `skill-upsert`, `provider-block`, `provider-env`, `provider-set-key`, `set-flags`, `check` (`--strict`), `doctor` (`--audit` / `--compare-backup`), `snapshot`, `diff`, `repair`, `common-config`.
