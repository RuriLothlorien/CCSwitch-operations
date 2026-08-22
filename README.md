# CCSwitch Operations

![License](https://img.shields.io/github/license/RuriLothlorien/CCSwitch-operations)
![Release](https://img.shields.io/github/v/release/RuriLothlorien/CCSwitch-operations)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Stars](https://img.shields.io/github/stars/RuriLothlorien/CCSwitch-operations?style=social)

> [中文文档](README.zh-CN.md) | English

A portable, publishable skill for operating **CC Switch (CCS)** safely: global prompts, skills, MCP servers, providers, and the Codex model catalog, across the nine apps CCS manages.

The package is self-contained: no installer script, no external helper dependencies. Installation is just copying/unzipping the skill folder into an agent's skills directory (or importing the zip from CC Switch).

If this skill helps you, please give it a ⭐.

## Why this skill?

CC Switch spreads its configuration across a database, `settings.json`, and each app's live config files. Maintaining it by hand means remembering a dozen locations, then checking **every agent one by one** — Codex, Claude Code, Claude Desktop, Gemini, and the rest — to see whether a change actually took effect. Miss one spot and the next provider switch overwrites your work, or a tool silently stops working. Worse, **AI agents maintaining their own configuration rarely know about your CC Switch installation** — their edits to `config.toml` / `settings.json` can conflict with what CCS manages and get overwritten on the next switch. You should not have to spend time and effort manually keeping CCS and your agents consistent.

This skill turns safe maintenance into one repeatable workflow:

- **No database access required**: `mcp-upsert`, `prompt-set`, `skill-upsert`, `provider-block`, `provider-env`, and `set-flags` cover everyday tasks
- **Maintain once, consistent across all nine agents**: Codex, Claude Code, Claude Desktop, Gemini, Grok Build, OpenCode, OpenClaw, Hermes, and Pi — no more checking each one individually
- **Backup first, verify after**: backup → stop CCS → edit → validate → restart → re-check
- **Automatic path discovery, cross-platform**: honors `CC_SWITCH_HOME` / `~/.cc-switch` on Windows, macOS, and Linux
- **Chinese-safe by design**: UTF-8-safe reads and writes
- **Inspect before you change**: read-only `doctor` / `check` commands show the current state first

## Features

- Safe write workflow: backup → stop CCS → edit → validate → restart → re-check.
- UTF-8-safe database helper (`scripts/ccs_db.py`) for Chinese content.
- Covers all 9 managed apps: codex, claude, claude-desktop, gemini, grokbuild, opencode, openclaw, hermes, pi.
- Cross-platform: `CC_SWITCH_HOME` / `~/.cc-switch` discovery, PowerShell and bash examples.
- `doctor` subcommand prints resolved paths, schema version, and per-app provider availability.

## How it works

CC Switch stores its managed configuration in an SQLite database (`~/.cc-switch/cc-switch.db`), `settings.json`, and the per-app live config files. This skill does not guess: it reads and writes those files directly with a small, dependency-free Python helper (`scripts/ccs_db.py`).

Every write follows a safe, verifiable flow:

1. **Backup** the database and config files first.
2. **Stop** CC Switch so its in-memory state cannot overwrite your edit.
3. **Edit** through `ccs_db.py` (UTF-8-safe, so Chinese content is never corrupted).
4. **Validate** TOML/JSON syntax and scan for encoding damage.
5. **Restart** CC Switch and confirm it did not rewrite your changes.

Everything runs locally: no telemetry, no network calls, no hidden behavior. All code is open source under MIT.

## Repository structure

```text
CCSwitch-operations/
├─ SKILL.md                    # Skill entrypoint (frontmatter + methodology)
├─ README.md                   # English readme
├─ README.zh-CN.md             # Chinese readme
├─ LICENSE                     # MIT license
├─ agents/openai.yaml          # UI metadata for OpenAI/Codex
├─ references/
│  ├─ architecture.md          # Architecture quick reference
│  ├─ apps.md                  # The 9 managed apps matrix
│  ├─ operations.md            # Command templates (PowerShell + bash)
│  ├─ pitfalls.md              # Known pitfalls
│  ├─ migration.md             # Official CCS version behavior changes
│  └─ examples/                # Sample TOML/JSON/prompt files
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

## Usage

Requires **Python 3.11+** (recommended).

```bash
# Discover the environment
python scripts/ccs_db.py doctor

# Safe checks
python scripts/ccs_db.py check

# Examples (see references/operations.md for the full set)
python scripts/ccs_db.py mcp-upsert --name my-server --config-file server_config.json --enable-codex --enable-claude
python scripts/ccs_db.py prompt-set --app-type codex --content-file prompt.txt
python scripts/ccs_db.py skill-upsert --name my-skill --description "My skill" --enable-codex
```

Set `CC_SWITCH_HOME` to override the CC Switch home directory (default: `~/.cc-switch`).

## Build the zip

To package the skill into a distributable zip (for example to install it in CC Switch or share it manually):

```bash
python scripts/build-zip.py --version 1.0.0
```

Output: `dist/CCSwitch-operations-v1.0.0.zip`.

## License

MIT — see [LICENSE](LICENSE).
