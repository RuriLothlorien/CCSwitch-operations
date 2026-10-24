# CCSwitch Operations

![License](https://img.shields.io/github/license/RuriLothlorien/CCSwitch-operations)
![Release](https://img.shields.io/github/v/release/RuriLothlorien/CCSwitch-operations)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Stars](https://img.shields.io/github/stars/RuriLothlorien/CCSwitch-operations?style=social)

> [简体中文](README.md) | English

A portable, publishable skill for operating **CC Switch (CCS)** safely: global prompts, skills, MCP servers, providers, and the Codex model catalog, across the twelve apps CCS manages.

The package is self-contained: no installer script, no external helper dependencies. Installation is just copying/unzipping the skill folder into an agent's skills directory (or importing the zip from CC Switch).

If this skill helps you, please give it a ⭐.

> [!NOTE]
> **The old 3.20.x manual-edit bug was fixed in CC Switch 4.0.4 (#6719 is closed)**: in 3.20.0–3.20.3, saving the Codex provider page without changes could reorder `config.toml`, strip common-config blocks, and write `type="stdio"` + an empty `command`. From 4.0.4 the writer replaces only key fields — a zero-change save is byte-identical. **Already-damaged entries are not auto-fixed**: toggle the MCP server off/on in the panel to re-sync it, or use this skill's `check --strict` / `repair` / `mcp-upsert`.

> [!WARNING]
> **Codex desktop app requires `~/.codex/auth.json`**: CC Switch 3.20.1+ switches Codex third-party providers config-only (key goes into `[model_providers.*]` as `experimental_bearer_token`), but some Codex builds (especially the desktop app) decide login state by the *presence* of `auth.json` — writing the token and deleting `auth.json` can send Codex back to the default login screen. 3.20.2 fixed only the **takeover** path; a **direct** third-party switch still deletes `auth.json`. Keep `auth.json`, and enable “Preserve official Codex auth on switch” (`preserveCodexOfficialAuthOnSwitch=true`) in CCS settings.

## Why this skill?

CC Switch spreads its configuration across a database, `settings.json`, and each app's live config files. Maintaining it by hand means remembering a dozen locations, then checking **every agent one by one** — Codex, Claude Code, Claude Desktop, Gemini, and the rest — to see whether a change actually took effect. Miss one spot and the next provider switch overwrites your work, or a tool silently stops working. Worse, **AI agents maintaining their own configuration rarely know about your CC Switch installation** — their edits to `config.toml` / `settings.json` can conflict with what CCS manages and get overwritten on the next switch. Even worse, **CC Switch itself can misoperate your configuration** — in 3.20.0–3.20.3, saving the Codex provider edit page without changing anything could reorder `config.toml`, strip common config, and write an empty-command MCP block (fixed in 4.0.4; already-damaged entries still need a re-sync or this skill's repair). You should not have to spend time and effort manually keeping CCS and your agents consistent.

This skill turns safe maintenance into one repeatable workflow:

- **No database access required**: `mcp-upsert`, `prompt-set`, `skill-upsert`, `provider-block`, `provider-env`, and `set-flags` cover everyday tasks
- **Maintain per agent or in bulk, all twelve covered**: Codex, Claude Code, Claude Desktop, Gemini, Grok Build, OpenCode, OpenClaw, Hermes, Pi, MiniMax Code, Kimi Code, and Antigravity CLI — update just one agent or several at once, no more checking each one by hand
- **Backup first, verify after**: backup → stop CCS → edit → validate → restart → re-check
- **Automatic path discovery, cross-platform**: honors `CC_SWITCH_HOME` / `~/.cc-switch` on Windows, macOS, and Linux
- **Chinese-safe by design**: UTF-8-safe reads and writes
- **Inspect before you change**: read-only `doctor` / `check` commands show the current state first
- **Proactive defense against misoperations**: `check --strict` / `doctor --audit` / `repair` block broken writes, verify after writes, and fix damage caused by CCS

## Compatibility

- Designed and tested with **CC Switch 4.0.19** (database schema v22). 4.0.18 moved v20 to v21 and added `enabled_agy` to MCP/Skills; 4.0.19 moved v21 to v22 and added `enabled_kimi`. After those migrations, older CCS versions refuse to open the database — keep the automatic backup.
- Historical databases remain readable where the required columns exist: v17 (3.20.0), v18 (3.20.1–3.20.3), v19 (3.20.4), v20 (4.0.16–4.0.17), and v21 (4.0.18). Once migrated to v22, older CCS releases cannot open the database directly.
- What 4.0 changes: **the common-config snippet feature is gone** (shared settings now live in the client config file and survive provider switches; a model or effort picked inside the client reverts to the provider's value on switch); a third mode, **stack/aggregation** (Claude Code and Codex, plus Claude Desktop since 4.0.13; per-model dispatch, no failover; state in the device-local `~/.cc-switch/live-state.json`, Claude Code models in `providers.meta.stackModels`); config writing replaces only key fields (the #6719 fix); MCP syncs to Pi (`~/.pi/agent/mcp.json`, `enabled_pi`); Codex 0.158+'s MCP `type` rejection is fixed (CCS 4.0 strips it on write); optional Codex session compression writes `[features] local_thread_store_compression`; GitHub Copilot accounts work on Codex (router on).
- **`common-config` only works on CCS ≤ 3.20.4 (schema ≤ v19)**; on v20 every `common-config` subcommand is refused with guidance: shared keys belong in the client live config, provider-specific fields in the card (`provider-block` / `provider-set-key` / `provider-env`).
- mcode needs 3.20.4+; Pi MCP (`--enable-pi`) needs 4.0+; Antigravity (`--enable-agy`) needs 4.0.18+; Kimi Code (`--enable-kimi`) needs 4.0.19+. Kimi's structured provider data, Agy's terminal-launch cards, and mcode's YAML providers are managed in the CC Switch UI; the provider-* commands explicitly refuse those shapes.
- Legacy 3.20.x behavior (missing-`model_provider` takeover routing, universal-sync child settings, proxy retry/timeout cross-writes, Kimi/DeepSeek presets) and the full 4.0 change list are in `references/migration.md`.
- Proxy-managed OAuth cards (xAI OAuth / GitHub Copilot) are forced to `requires_openai_auth = false` (the local proxy injects the token); `check --strict` flags the wrong value, and `repair --mode codex-0149` fixes it early.
- Run `python scripts/ccs_db.py doctor` to check the schema, each app's current mode (direct/route/stack), malformed state files, and the Codex auth-preservation guard before operating.
- Other versions may behave differently; see `references/migration.md` for official version behavior changes.

## Features

- Safe write workflow: backup → stop CCS → edit → validate → restart → re-check.
- UTF-8-safe database helper (`scripts/ccs_db.py`) for Chinese content.
- Covers all 12 managed apps: codex, claude, claude-desktop, gemini, grokbuild, opencode, openclaw, hermes, pi, mcode, kimi, agy.
- Cross-platform: `CC_SWITCH_HOME` / `~/.cc-switch` discovery, PowerShell and bash examples.
- `doctor` prints resolved paths, the schema, all 12 apps and provider counts, MCP/Skills flag availability, and each app's current mode (direct/route/stack from `live-state.json`); it also warns about malformed `settings.json` / `live-state.json` and a disabled Codex official-auth preservation guard.

## How it works

CC Switch stores its managed configuration in an SQLite database (`~/.cc-switch/cc-switch.db`), `settings.json`, and the per-app live config files. This skill does not guess: it reads and writes those files directly with a small, dependency-free Python helper (`scripts/ccs_db.py`).

Every write follows a safe, verifiable flow:

1. **Backup** the database and config files first.
2. **Stop** CC Switch so its in-memory state cannot overwrite your edit.
3. **Edit** through `ccs_db.py` (UTF-8-safe, so Chinese content is never corrupted).
4. **Validate** TOML/JSON syntax and scan for encoding damage.
5. **Restart** CC Switch and confirm it did not rewrite your changes.

### Security analysis

- **Runs fully locally**: reads and writes only files under `~/.cc-switch` (or `CC_SWITCH_HOME`); no network calls, no telemetry, no external services.
- **Minimal footprint and permissions**: standard-library Python only — zero third-party dependencies, nothing to install; normal operations need no admin rights and never touch system directories.
- **Safe-by-default writes**: backup → stop CCS → edit → validate → restart → re-check, so a running CCS cannot overwrite your changes from memory.
- **Encoding-safe**: UTF-8-safe reads and writes prevent Chinese content from being corrupted into `?`; `check` scans for likely mojibake before and after changes.
- **Read-only first**: `doctor` and `check` never modify anything — inspect the environment before changing it.
- **No secrets handling**: the helper never reads or uploads credentials; it only manages the local CCS configuration you point it at.
- **Transparent and auditable**: MIT-licensed, zero third-party dependencies, no hidden behavior — the full source is in this repository.


## Repository structure

```text
CCSwitch-operations/
├─ SKILL.md                    # Skill entrypoint (frontmatter + methodology)
├─ README.md                   # Chinese readme (default)
├─ README.en.md                # English readme
├─ LICENSE                     # MIT license
├─ agents/openai.yaml          # UI metadata for OpenAI/Codex
├─ assets/ccswitch-operations-banner.png  # Social preview banner (repo only)
├─ references/
│  ├─ architecture.md          # Architecture quick reference
│  ├─ apps.md                  # The 12 managed apps matrix
│  ├─ operations.md            # Command templates (PowerShell + bash)
│  ├─ pitfalls.md              # Known pitfalls
│  ├─ migration.md             # Official CCS version behavior changes
│  ├─ examples/                # Sample TOML/JSON/prompt files
│  └─ incidents/               # Incident retrospectives (repo only)
├─ scripts/
│  ├─ ccs_db.py                # Dependency-free DB helper (the only runtime script)
│  └─ build-zip.py             # Manual zip packaging helper (repo only)
└─ .github/workflows/release.yml  # Release build workflow (repo only)
```

The release zip contains only what the skill needs at runtime: `SKILL.md`, `agents/`, `references/`, `scripts/ccs_db.py`, the READMEs, and `LICENSE`.

## Install

### Codex

Copy or symlink the `CCSwitch-operations` folder into `~/.codex/skills/`, then start a new session.

### Claude Code

Copy or symlink the `CCSwitch-operations` folder into `~/.claude/skills/`, then restart Claude Code.

### Other SKILL.md agents

Place the `CCSwitch-operations` folder into the agent's skills directory (for example `~/.gemini/skills`, `~/.config/opencode/skills`, `~/.openclaw/skills`, `~/.pi/agent/skills`). Most agents load `SKILL.md` from the folder root.

### CC Switch

Use the release zip: in CC Switch, import/install the skill from the zip. The zip contains a top-level `CCSwitch-operations/` folder with `SKILL.md` at its root.

Or add it to CC Switch's skill repository list with the deep link (click it with CC Switch installed; then open CC Switch -> Skills -> Browse GitHub repos to install the skill to the apps you want):

```text
ccswitch://v1/import?resource=skill&repo=RuriLothlorien/CCSwitch-operations&branch=main
```

## Usage

Requires **Python 3.11+** (bundled `tomllib`, recommended); Python 3.8–3.10 needs [tomli](https://pypi.org/project/tomli/) installed first (the only optional third-party dependency — everything else is standard library).

```bash
# Discover the environment (paths, schema, per-app mode: direct/route/stack)
python scripts/ccs_db.py doctor

# Safe checks
python scripts/ccs_db.py check
python scripts/ccs_db.py check --strict      # structural safety (MCP semantics / markers / header order / live-only / Codex routing & keys / MCP type)
python scripts/ccs_db.py doctor --audit      # three-way consistency audit + per-app modes

# Write commands run an automatic preflight; broken configs are refused
# (put --force before the subcommand to override)
python scripts/ccs_db.py repair --target config.toml --mode header-order   # dry-run
python scripts/ccs_db.py repair --target provider --mode codex-0149        # dry-run: migrate legacy openai_base_url misroutes
python scripts/ccs_db.py repair --target provider --mode codex-key         # dry-run: restore a key wiped by CCS #7434
python scripts/ccs_db.py repair --target provider --mode mcp-type         # dry-run: strip MCP `type` keys Codex rejects

# Examples (see references/operations.md for the full set)
python scripts/ccs_db.py mcp-upsert --name my-server --config-file server_config.json --enable-codex --enable-claude
python scripts/ccs_db.py mcp-upsert --name my-server --config-file server_config.json --enable-pi  # Pi 1.0 (CCS 4.0+)
python scripts/ccs_db.py mcp-upsert --name my-server --config-file server_config.json --enable-agy --enable-kimi  # CCS 4.0.19+
python scripts/ccs_db.py prompt-set --app-type codex --content-file prompt.txt
python scripts/ccs_db.py prompt-set --app-type mcode --content-file mcode-prompt.txt  # MiniMax Code (32 KiB limit)
python scripts/ccs_db.py skill-upsert --name my-skill --description "My skill" --enable-codex
python scripts/ccs_db.py set-flags --table skills --name my-skill --mcode 1
```

Set `CC_SWITCH_HOME` to override the CC Switch home directory (default: `~/.cc-switch`).

> CCS 4.0 removed the common-config snippet, so `common-config` subcommands only work on schema ≤ v19 (CCS ≤ 3.20.4); on v20 they are refused with guidance to put shared keys into the client live config.

## Build the zip

To package the skill into a distributable zip (for example to install it in CC Switch or share it manually):

```bash
python scripts/build-zip.py --version 1.4.0
```

Output: `dist/CCSwitch-operations-v1.4.0.zip`.

## License

MIT — see [LICENSE](LICENSE).
