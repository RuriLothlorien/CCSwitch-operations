# CCSwitch Operations

可移植、可发布的 **CC Switch（CCS）** 操作技能：安全地维护全局提示词、Skills、MCP 服务器、供应商与 Codex 模型目录，覆盖 CCS 管理的九个应用。

本包自包含：**没有安装脚本，也不依赖任何外部辅助脚本**。安装方式只有两种——把技能目录解压/复制到 agent 的 skills 目录，或在 CC Switch 中从 zip 导入。

## 功能特性

- 安全写入流程：备份 → 停止 CCS → 修改 → 校验 → 重启 → 复核。
- 面向中文内容安全的数据库辅助脚本（`scripts/ccs_db.py`），支持 UTF-8 文件与内联中文参数。
- 覆盖全部 9 个受管应用：codex、claude、claude-desktop、gemini、grokbuild、opencode、openclaw、hermes、pi。
- 跨平台：自动发现 `CC_SWITCH_HOME` / `~/.cc-switch`，文档同时给出 PowerShell 与 bash 示例。
- `doctor` 子命令输出解析到的路径、数据库 schema 版本与各应用供应商状态。

## 安装

### Codex

把 `CCSwitch-operations` 文件夹复制或软链接到 `~/.codex/skills/`，然后新开一个 Codex 会话。

### Claude Code

把 `CCSwitch-operations` 文件夹复制或软链接到 `~/.claude/skills/`，然后重启 Claude Code。

### 其他 SKILL.md agent

把 `CCSwitch-operations` 文件夹放到对应 agent 的 skills 目录（例如 `~/.gemini/skills`、`~/.config/opencode/skills`、`~/.openclaw/skills`、`~/.pi/agent/skills`）。大多数 agent 从文件夹根目录的 `SKILL.md` 加载技能。

### CC Switch

使用 Release zip：在 CC Switch 中从 zip 导入/安装技能。zip 顶层为 `CCSwitch-operations/`，其根目录含 `SKILL.md`。

## 使用

要求 **Python 3.11+**（推荐）。

```bash
# 查看环境（路径、schema、各应用供应商）
python scripts/ccs_db.py doctor

# 安全校验
python scripts/ccs_db.py check

# 示例（完整命令见 references/operations.md）
python scripts/ccs_db.py mcp-upsert --name my-server --config-file server_config.json --enable-codex --enable-claude
python scripts/ccs_db.py prompt-set --app-type codex --content-file prompt.txt
python scripts/ccs_db.py skill-upsert --name my-skill --description "我的技能" --enable-codex
```

设置 `CC_SWITCH_HOME` 环境变量可覆盖 CC Switch 主目录（默认 `~/.cc-switch`）。

## 构建 zip

如需手动打包为可分发的 zip（例如导入 CC Switch 或手动分享）：

```bash
python scripts/build-zip.py --version 1.0.0
```

输出：`dist/CCSwitch-operations-v1.0.0.zip`。

## 文档

- `references/architecture.md` — 架构速查（表结构、生效链路）
- `references/apps.md` — 九大受管应用矩阵
- `references/operations.md` — 操作命令模板（PowerShell + bash）
- `references/pitfalls.md` — 已踩过的坑
- `references/migration.md` — 官方版本行为变化
- `references/examples/` — 示例 TOML/JSON/提示词文件

## 测试

```bash
python -m unittest discover -s tests -v
```

## License

MIT — 见 [LICENSE](LICENSE)。
