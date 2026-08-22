# CCSwitch Operations

可移植、可发布的 **CC Switch（CCS）** 操作技能：安全地维护全局提示词、Skills、MCP 服务器、供应商与 Codex 模型目录，覆盖 CCS 管理的九个应用。

本包自包含：**没有安装脚本，也不依赖任何外部辅助脚本**。安装方式只有两种——把技能目录解压/复制到 agent 的 skills 目录，或在 CC Switch 中从 zip 导入。

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
