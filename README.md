# CCSwitch Operations

![License](https://img.shields.io/github/license/RuriLothlorien/CCSwitch-operations)
![Release](https://img.shields.io/github/v/release/RuriLothlorien/CCSwitch-operations)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Stars](https://img.shields.io/github/stars/RuriLothlorien/CCSwitch-operations?style=social)

> [English](README.en.md) | 简体中文

可移植、可发布的 **CC Switch（CCS）** 操作技能：安全地维护全局提示词、Skills、MCP 服务器、供应商与 Codex 模型目录，覆盖 CCS 管理的十二个应用。

本包自包含：**没有安装脚本，也不依赖任何外部辅助脚本**。安装方式只有两种——把技能目录解压/复制到 agent 的 skills 目录，或在 CC Switch 中从 zip 导入。

如果这个技能对你有帮助，欢迎点个 Star ⭐。

> [!NOTE]
> **曾经的 3.20.x 手动编辑缺陷已在 CCS 4.0.4 修复（#6719 已关闭）**：3.20.0–3.20.3 的 Codex 供应商编辑页在零改动保存时可能重排 `config.toml`、剥离通用配置、写入 `type="stdio"` + 空 `command` 的坏块。4.0.4 起写入改为“只替换关键字段”，零改动保存与保存前逐字节一致。**已经写坏的条目不会自动恢复**：可在 MCP 面板把服务器关掉再打开一次重写，或用本技能的 `check --strict` / `repair` / `mcp-upsert` 修复。

> [!WARNING]
> **Codex 桌面版需要 `~/.codex/auth.json`**：CC Switch 3.20.1 起的 Codex 第三方切换是 config-only（密钥写进 `[model_providers.*]` 的 `experimental_bearer_token`），但部分 Codex 构建（尤其桌面版）以 `auth.json` 是否存在判定登录态——只写 token 并删除 `auth.json` 会让 Codex 回到默认登录页。3.20.2 只修了**接管**路径，**直切**第三方仍会删除 `auth.json`。请保留 `auth.json`，并在 CCS 设置中打开“非接管切换时保留官方登录”（`preserveCodexOfficialAuthOnSwitch=true`）。

## 为什么需要这个技能？

CC Switch 的配置分散在数据库、`settings.json` 和多个应用的 live 配置文件里。手动维护的痛点是：位置多、容易忘，改完还要去 Codex、Claude Code、Claude Desktop、Gemini 等每个 agent 里**逐个确认**是否生效，稍不留神漏一处，下次切换供应商时配置就被覆盖、工具就失效。更麻烦的是，**AI 在自我维护时往往只顾自己的 agent 配置，不会顾及你本机安装的 CC Switch**——它自己写的 `config.toml` / `settings.json` 可能和 CCS 的管理状态冲突，下一次切换就被回写覆盖。更糟的是，**CCS 自己也可能误操作你的配置**——3.20.0–3.20.3 的 Codex 供应商编辑页曾在零改动保存时重排 `config.toml`、剥离通用配置、写入空命令 MCP 坏块（4.0.4 已修复，存量坏块仍需重同步或用本技能修复）。用户不应该费时费力地手动维护 CCS 与你的 agents 的一致性。

这个技能把“安全维护”沉淀成一套方法论和工具：

- **不用碰数据库**：`mcp-upsert`、`prompt-set`、`skill-upsert`、`provider-block`、`provider-env`、`set-flags` 覆盖日常操作，全部由工具代劳
- **按需维护，十二个 agent 都覆盖**：Codex、Claude Code、Claude Desktop、Gemini、Grok Build、OpenCode、OpenClaw、Hermes、Pi、MiniMax Code、Kimi Code、Antigravity CLI 的配置边界一次讲清；只改某一个 agent 或批量同步都可以，不用再逐个手工确认
- **先备份、后修改、再校验**：备份 → 停止 CCS → 修改 → 校验 → 重启 → 复核，照着流程走就不会漏
- **自动发现路径、跨平台**：支持 `CC_SWITCH_HOME` / `~/.cc-switch`，Windows / macOS / Linux 通用
- **中文内容安全**：UTF-8 安全读写，不再担心乱码
- **先看后改**：`doctor` / `check` 只读检查环境与配置健康度，动手前先看清现状
- **主动防御误操作**：`check --strict` / `doctor --audit` / `repair` 在写入前拦截异常、写入后校验、一键修复 CCS 造成的损坏

## 版本兼容

- 本技能基于 **CC Switch 4.0.19**（数据库 schema v22）设计与测试。4.0.18 把 v20 升到 v21，为 MCP/Skills 增加 `enabled_agy`；4.0.19 把 v21 升到 v22，增加 `enabled_kimi`。迁移后旧版 CCS 会以“数据库版本过新”拒绝打开——升级前请保留自动备份。
- 历史库仍按列兼容读取：v17（3.20.0）、v18（3.20.1–3.20.3）、v19（3.20.4）、v20（4.0.16–4.0.17）、v21（4.0.18）；一旦升级到 v22，旧版 CCS 将无法直接打开数据库。
- CCS 4.0 行为变化：**通用配置片段功能已移除**（共享设置直接留在客户端配置文件里并跨切换保留；临时在客户端选的模型/推理强度，切走再切回会恢复为供应商设定值）；新增**聚合（Stack）模式**（Claude Code、Codex，以及 4.0.13 起的 Claude Desktop；按所选模型分发、不提供故障转移，状态在设备本地 `~/.cc-switch/live-state.json`，Claude Code 的发布模型在 `providers.meta.stackModels`）；配置写入改为“只替换关键字段”；MCP 支持 Pi（`~/.pi/agent/mcp.json`，v20 的 `enabled_pi`）；Codex 0.158+ 的 MCP `type` 字段问题已修（CCS 4.0 写入时剥离）；可选压缩 Codex 历史会话（写 `[features] local_thread_store_compression`）。
- **`common-config` 命令只适用于 CCS ≤ 3.20.4（schema ≤ v19）**；在 v20 上所有 `common-config` 子命令都会被明确拒绝并提示新做法：共享键写客户端 live 配置，供应商专属字段写卡片（`provider-block` / `provider-set-key` / `provider-env`）。
- mcode 相关命令需要 3.20.4+；Pi MCP（`--enable-pi`）需要 4.0+；Antigravity（`--enable-agy`）需要 4.0.18+；Kimi Code（`--enable-kimi`）需要 4.0.19+。Kimi 的结构化供应商、Agy 的启动终端供应商和 mcode 的 YAML 供应商都由 CCS 界面管理；本技能的 provider-* 命令会明确拒绝这些格式。
- 3.20.x 遗留行为（Codex `model_provider` 缺省卡的接管路由、统一同步的子卡设置、代理重试/超时串写、Kimi/DeepSeek 预设等）与 4.0 的完整变化见 `references/migration.md`。
- 操作前可运行 `python scripts/ccs_db.py doctor` 查看 schema、各应用当前模式（直连/路由/聚合）与关键安全告警。
- 其他版本可能略有差异，详见 `references/migration.md` 的官方版本行为变化。

## 功能特性

- 安全写入流程：备份 → 停止 CCS → 修改 → 校验 → 重启 → 复核。
- 面向中文内容安全的数据库辅助脚本（`scripts/ccs_db.py`），支持 UTF-8 文件与内联中文参数。
- 覆盖全部 12 个受管应用：codex、claude、claude-desktop、gemini、grokbuild、opencode、openclaw、hermes、pi、mcode、kimi、agy。
- 跨平台：自动发现 `CC_SWITCH_HOME` / `~/.cc-switch`，文档同时给出 PowerShell 与 bash 示例。
- `doctor` 子命令输出解析到的路径、数据库 schema、12 个应用及其供应商状态、MCP/Skills 标志列和当前模式（直连/路由/聚合，读 `live-state.json`）；它还会提示 `settings.json` / `live-state.json` 损坏，以及 Codex 官方登录保留开关是否关闭。

## 工作原理

CC Switch 的托管配置存放在 SQLite 数据库（`~/.cc-switch/cc-switch.db`）、`settings.json` 以及各应用的 live 配置文件中。本技能不做猜测：通过一个零依赖的 Python 辅助脚本（`scripts/ccs_db.py`）直接读写这些文件。

每次写入都遵循安全、可验证的流程：

1. **先备份**数据库与配置文件。
2. **停止** CC Switch，避免其内存状态覆盖你的修改。
3. **通过 `ccs_db.py` 修改**（UTF-8 安全，中文内容不会被损坏）。
4. **校验** TOML/JSON 语法并扫描编码损坏。
5. **重启** CC Switch，并确认它没有回写覆盖你的更改。

### 安全性分析

- **完全本地运行**：只读写 `~/.cc-switch`（或 `CC_SWITCH_HOME`）下的数据库与配置文件；无网络请求、无遥测、无外部服务。
- **最小占用与权限**：仅用 Python 标准库——零第三方依赖、无需安装任何包；常规操作不需要管理员权限，不触碰系统目录。
- **写入默认安全**：备份 → 停止 CCS → 修改 → 校验 → 重启 → 复核，防止运行中的 CCS 用内存状态覆盖你的修改。
- **编码安全**：UTF-8 安全读写，中文内容不会被损坏成 `?`；`check` 会在改动前后扫描疑似乱码。
- **只读先行**：`doctor` 与 `check` 不会修改任何内容，动手前先看清环境。
- **不处理密钥**：工具不读取也不上传任何凭据，只操作你指定的 CCS 本地配置。
- **透明可审计**：MIT 开源、零第三方依赖、无隐藏行为，完整源码就在本仓库。


## 仓库结构

```text
CCSwitch-operations/
├─ SKILL.md                    # 技能入口（frontmatter + 方法论）
├─ README.md                   # 中文说明（默认）
├─ README.en.md                # 英文说明
├─ LICENSE                     # MIT 许可证
├─ agents/openai.yaml          # OpenAI/Codex 的 UI 元数据
├─ assets/ccswitch-operations-banner.png  # 社交预览图（仅仓库内）
├─ references/
│  ├─ architecture.md          # 架构速查
│  ├─ apps.md                  # 十二大受管应用矩阵
│  ├─ operations.md            # 操作模板（PowerShell + bash）
│  ├─ pitfalls.md              # 已踩过的坑
│  ├─ migration.md             # 官方版本行为变化
│  ├─ examples/                # 示例 TOML/JSON/提示词
│  └─ incidents/               # 事故复盘（仅仓库内）
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

或用深链把它加入 CC Switch 的 Skill 仓库列表（已安装 CC Switch 时点击即可；之后在 CC Switch -> Skills -> Browse GitHub repos 中安装到你想用的应用）：

```text
ccswitch://v1/import?resource=skill&repo=RuriLothlorien/CCSwitch-operations&branch=main
```

## 使用

要求 **Python 3.11+**（自带 `tomllib`，推荐）；Python 3.8–3.10 需要先安装 [tomli](https://pypi.org/project/tomli/)（唯一的可选第三方依赖，其余全部使用标准库）。

```bash
# 查看环境（路径、schema、各应用供应商与当前模式：直连/路由/聚合）
python scripts/ccs_db.py doctor

# 安全校验
python scripts/ccs_db.py check
python scripts/ccs_db.py check --strict      # 结构安全（MCP 语义/标记/表头顺序/live-only/Codex 路由与密钥/MCP type）
python scripts/ccs_db.py doctor --audit      # 三处一致性审计 + 各应用模式

# 写操作会自动 preflight；配置已损坏时会被拦截（--force 放在子命令前可显式跳过）
python scripts/ccs_db.py repair --target config.toml --mode header-order   # dry-run
python scripts/ccs_db.py repair --target provider --mode codex-0149        # dry-run：迁移旧 openai_base_url 误路由
python scripts/ccs_db.py repair --target provider --mode codex-key         # dry-run：恢复被 CCS #7434 清空的 Codex 密钥
python scripts/ccs_db.py repair --target provider --mode mcp-type         # dry-run：清理 Codex 不接受的 MCP `type` 键

# 示例（完整命令见 references/operations.md）
python scripts/ccs_db.py mcp-upsert --name my-server --config-file server_config.json --enable-codex --enable-claude
python scripts/ccs_db.py mcp-upsert --name my-server --config-file server_config.json --enable-pi   # Pi 1.0（CCS 4.0+）
python scripts/ccs_db.py mcp-upsert --name my-server --config-file server_config.json --enable-agy --enable-kimi  # CCS 4.0.19+
python scripts/ccs_db.py prompt-set --app-type codex --content-file prompt.txt
python scripts/ccs_db.py prompt-set --app-type mcode --content-file mcode-prompt.txt  # MiniMax Code（≤32 KiB）
python scripts/ccs_db.py skill-upsert --name my-skill --description "我的技能" --enable-codex
python scripts/ccs_db.py set-flags --table skills --name my-skill --mcode 1
```

设置 `CC_SWITCH_HOME` 环境变量可覆盖 CC Switch 主目录（默认 `~/.cc-switch`）。

> CCS 4.0 已移除“通用配置片段”，因此 `common-config` 子命令只在 schema ≤ v19（CCS ≤ 3.20.4）上可用；v20 上会被明确拒绝并提示把共享键写进客户端 live 配置。

## 构建 zip

如需手动打包为可分发的 zip（例如导入 CC Switch 或手动分享）：

```bash
python scripts/build-zip.py --version 1.4.0
```

输出：`dist/CCSwitch-operations-v1.4.0.zip`。

## 文档

- `references/architecture.md` — 架构速查（表结构、生效链路）
- `references/apps.md` — 十二大受管应用矩阵
- `references/operations.md` — 操作命令模板（PowerShell + bash）
- `references/pitfalls.md` — 已踩过的坑
- `references/migration.md` — 官方版本行为变化
- `references/examples/` — 示例 TOML/JSON/提示词文件

## License

MIT — 见 [LICENSE](LICENSE)。
