# CCSwitch Operations

> [中文文档](README.zh-CN.md) | English

A portable, publishable skill for operating **CC Switch (CCS)** safely: global prompts, skills, MCP servers, providers, and the Codex model catalog, across the nine apps CCS manages.

The package is self-contained: no installer script, no external helper dependencies. Installation is just copying/unzipping the skill folder into an agent's skills directory (or importing the zip from CC Switch).

## Features

- Safe write workflow: backup → stop CCS → edit → validate → restart → re-check.
- UTF-8-safe database helper (`scripts/ccs_db.py`) for Chinese content.
- Covers all 9 managed apps: codex, claude, claude-desktop, gemini, grokbuild, opencode, openclaw, hermes, pi.
- Cross-platform: `CC_SWITCH_HOME` / `~/.cc-switch` discovery, PowerShell and bash examples.
- `doctor` subcommand prints resolved paths, schema version, and per-app provider availability.

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
