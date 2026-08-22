# CCSwitch Operations

![License](https://img.shields.io/github/license/RuriLothlorien/CCSwitch-operations)
![Release](https://img.shields.io/github/v/release/RuriLothlorien/CCSwitch-operations)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Stars](https://img.shields.io/github/stars/RuriLothlorien/CCSwitch-operations?style=social)

可移植、可发布的 **CC Switch（CCS）** 操作技能：安全地维护全局提示词、Skills、MCP 服务器、供应商与 Codex 模型目录，覆盖 CCS 管理的九个应用。

本包自包含：**没有安装脚本，也不依赖任何外部辅助脚本**。安装方式只有两种——把技能目录解压/复制到 agent 的 skills 目录，或在 CC Switch 中从 zip 导入。

如果这个技能对你有帮助，欢迎点个 Star ⭐。

## 为什么需要这个技能？

CC Switch 的配置分散在数据库、`settings.json` 和多个应用的 live 配置文件里。手动维护的痛点是：位置多、容易忘，改完还要去 Codex、Claude Code、Claude Desktop、Gemini 等每个 agent 里**逐个确认**是否生效，稍不留神漏一处，下次切换供应商时配置就被覆盖、工具就失效。更麻烦的是，**AI 在自我维护时往往只顾自己的 agent 配置，不会顾及你本机安装的 CC Switch**——它自己写的 `config.toml` / `settings.json` 可能和 CCS 的管理状态冲突，下一次切换就被回写覆盖。用户不应该费时费力地手动维护 CCS 与你的 agents 的一致性。

这个技能把“安全维护”沉淀成一套方法论和工具：

- **不用碰数据库**：`mcp-upsert`、`prompt-set`、`skill-upsert`、`provider-block`、`provider-env`、`set-flags` 覆盖日常操作，全部由工具代劳
- **按需维护，九个 agent 都覆盖**：Codex、Claude Code、Claude Desktop、Gemini、Grok Build、OpenCode、OpenClaw、Hermes、Pi 的配置边界一次讲清；只改某一个 agent 或批量同步都可以，不用再逐个手工确认
- **先备份、后修改、再校验**：备份 → 停止 CCS → 修改 → 校验 → 重启 → 复核，照着流程走就不会漏
- **自动发现路径、跨平台**：支持 `CC_SWITCH_HOME` / `~/.cc-switch`，Windows / macOS / Linux 通用
- **中文内容安全**：UTF-8 安全读写，不再担心乱码
- **先看后改**：`doctor` / `check` 只读检查环境与配置健康度，动手前先看清现状

## 版本兼容

- 本技能基于 **CC Switch 3.20.0**（数据库 schema v17）设计与测试。
- 操作前可运行 `python scripts/ccs_db.py doctor` 查看本机版本与 schema。
- 其他版本可能略有差异，详见 `references/migration.md` 的官方版本行为变化。

## 功能特性

- 安全写入流程：备份 → 停止 CCS → 修改 → 校验 → 重启 → 复核。
- 面向中文内容安全的数据库辅助脚本（`scripts/ccs_db.py`），支持 UTF-8 文件与内联中文参数。
- 覆盖全部 9 个受管应用：codex、claude、claude-desktop、gemini、grokbuild、opencode、openclaw、hermes、pi。
- 跨平台：自动发现 `CC_SWITCH_HOME` / `~/.cc-switch`，文档同时给出 PowerShell 与 bash 示例。
- `doctor` 子命令输出解析到的路径、数据库 schema 版本与各应用供应商状态。

## 工作原理

CC Switch 的托管配置存放在 SQLite 数据库（`~/.cc-switch/cc-switch.db`）、`settings.json` 以及各应用的 live 配置文件中。本技能不做猜测：通过一个零依赖的 Python 辅助脚本（`scripts/ccs_db.py`）直接读写这些文件。

每次写入都遵循安全、可验证的流程：

1. **先备份**数据库与配置文件。
2. **停止** CC Switch，避免其内存状态覆盖你的修改。
3. **通过 `ccs_db.py` 修改**（UTF-8 安全，中文内容不会被损坏）。
4. **校验** TOML/JSON 语法并扫描编码损坏。
5. **重启** CC Switch，并确认它没有回写覆盖你的更改。

一切都在本地完成：无遥测、无网络请求、无隐藏行为；全部代码 MIT 开源。

## 仓库结构

```text
CCSwitch-operations/
├─ SKILL.md                    # 技能入口（frontmatter + 方法论）
├─ README.md                   # 英文说明
├─ README.zh-CN.md             # 中文说明
├─ LICENSE                     # MIT 许可证
├─ agents/openai.yaml          # OpenAI/Codex 的 UI 元数据
├─ references/
│  ├─ architecture.md          # 架构速查
│  ├─ apps.md                  # 九大受管应用矩阵
│  ├─ operations.md            # 操作模板（PowerShell + bash）
│  ├─ pitfalls.md              # 已踩过的坑
│  ├─ migration.md             # 官方版本行为变化
│  └─ examples/                # 示例 TOML/JSON/提示词
├─ scripts/
│  ├─ ccs_db.py                # 零依赖数据库辅助脚本（唯一运行时脚本）
│  └─ build-zip.py             # 手动打包 zip 的辅助脚本（仅仓库内）
└─ .github/workflows/release.yml  # Release 构建工作流（仅仓库内）
```

发布 zip 只包含技能运行所需内容：`SKILL.md`、`agents/`、`references/`、`scripts/ccs_db.py`、README 与 `LICENSE`。

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

## License

MIT — 见 [LICENSE](LICENSE)。
