# 十四大受管应用矩阵（CCS 4.0.28）

路径均使用可移植写法：`~` 在 Windows 上等同于 `%USERPROFILE%`；macOS/Linux 为 `$HOME`。

| 应用 | 模式 | 主要配置 | skills 目录 | prompts | MCP | 本地代理/故障转移 |
| --- | --- | --- | --- | --- | --- | --- |
| codex | 切换（直连/路由/聚合） | `~/.codex/config.toml` | `~/.codex/skills` | DB(prompts) | config.toml + mcp_servers + provider config 三处一致 | 支持；聚合无故障转移 |
| claude | 切换（直连/路由/聚合） | `~/.claude/settings.json` | `~/.claude/skills` | DB(prompts) | settings.json + provider env | 支持；聚合无故障转移 |
| claude-desktop | 切换（直连/路由/聚合，4.0.13+） | 1P `<roaming-app-data>\Claude\claude_desktop_config.json`；3P `<local-app-data>\Claude-3p\...` | 不走 CCS skill 同步（3P 手动 manifest） | DB(prompts) | 手动 JSON | 路由/聚合支持，无故障转移 |
| gemini | 切换（直连/路由） | `~/.gemini/` | `~/.gemini/skills` | DB(prompts) | provider config | 支持 |
| grokbuild | 切换（直连/路由） | `~/.grok/` | `~/.grok/skills` | DB(prompts) | provider config | 支持 |
| opencode | 累加 | `~/.config/opencode/` | `~/.config/opencode/skills` | DB(prompts) | provider config | 无 |
| openclaw | 累加 | `~/.openclaw/openclaw.json` | `~/.openclaw/skills` | DB(prompts) | provider config | 无 |
| hermes | 累加 | hermes 配置目录 | hermes 配置目录/skills | DB(prompts) | provider config | 无 |
| pi | 累加 | `~/.pi/agent/models.json` | `~/.pi/agent/skills` | AGENTS.md / SYSTEM.md / APPEND_SYSTEM.md | `~/.pi/agent/mcp.json`（CCS 4.0+，`enabled_pi`；只写连接字段） | 无 |
| mcode | 累加 | `~/.minimax/config.yaml`（`custom_provider`） | `~/.minimax/skills` | `~/.minimax/AGENTS.md`（单条 ≤32 KiB） | `~/.minimax/mcp.json` | 无 |
| kimi | 累加 | `~/.kimi-code/config.toml`（`KIMI_CODE_HOME` 可覆盖） | `~/.kimi-code/skills` | `~/.kimi-code/AGENTS.md` | `~/.kimi-code/mcp.json`（stdio/HTTP/SSE，`enabled_kimi`） | 无 |
| agy | 终端启动时指定供应商 | `~/.gemini/antigravity-cli/settings.json` 为只读现状；卡片 Key/URL 只在 CCS 打开的终端生效 | `~/.gemini/config/skills` | `~/.gemini/config/AGENTS.md` | `~/.gemini/config/mcp_config.json`（stdio/HTTP，无 SSE，`enabled_agy`） | 无 |
| omp | 累加 | `~/.omp/agent` 或 profile 下的 `models.yml` / `config.yml` | `<omp agent>/skills`（存在即启用） | `<omp agent>/AGENTS.md` | `<omp agent>/mcp.json`（`enabled_omp`） | 无 |
| dsh | 累加 | CCS `dshConfigDir`、`DSH_HOME` 或 `~/.dsh`；profiles 下的 `cordis.patch.yml`、`.credentials.yaml` | `<dsh-home>/skills`（`enabled_dsh`） | `<dsh-home>/AGENTS.md` | web/desktop/headless/acp profile patches（stdio/HTTP，`enabled_dsh`） | 无 |

## 模式说明

- **切换模式**（claude / codex / gemini / claude-desktop / grokbuild）：只把当前供应商写入 live 配置，切换供应商会重写对应配置文件。
- **累加模式**（opencode / openclaw / hermes / pi / mcode / kimi / omp / dsh）：多个供应商共存于原生配置，供应商“启用”等于其配置键存在于原生文件。
- **Antigravity CLI**：不是普通的全局切换应用。供应商只注入由 CCS 卡片“使用此供应商打开终端”启动的 `agy` 进程；直接在别处运行 `agy` 仍使用它自己的 Google 登录。
- **聚合（Stack）模式**（CCS 4.0；4.0.13 起支持 claude / codex / claude-desktop）：多家供应商的模型一起出现在客户端模型选择器里，经本地路由按所选模型分发，不提供故障转移；成员和模式状态在设备本地 `~/.cc-switch/live-state.json`，Claude Code 的发布模型在 `providers.meta.stackModels`。内部状态值 `proxy` 在界面和 `doctor` 中显示为 `route`。

## 各应用要点

- **Pi**：CCS 绝不读写 `~/.pi/agent/auth.json`、`defaultProvider`、`defaultModel`；Skills 按“存在即启用”，CCS 不覆盖/删除同名但非它所有的 skill；CCS 4.0 起 MCP 同步到 `~/.pi/agent/mcp.json`（`enabled_pi`，只写连接字段，关同步=停用不删条目）。
- **Claude Desktop**：4.0.13 起可直接使用直连/路由/聚合三种模式；需要模型映射的卡不能直连，路由和聚合都要求 CC Switch 保持运行。Desktop 只在启动时读取配置，切换模式、路由目标或聚合成员后必须重启 Desktop。3P 的 MCP/Skills 仍不由 CCS 同步：MCP 手写 3P config，skills 走 `manifest.json`（`syncManaged:false`）+ `cc-switch-managed.json` 手动同步。
- **Codex**：官方/内置 MCP（如 `openaiDeveloperDocs`）在 `mcp_servers` 表中没有行属正常，不要补录。4.0.25+ 的 `[agents].max_threads` 是客户端全局键并跨供应商保留，应写在 live `config.toml`，不要放进 provider card。Codex 0.167+ 按 provider id 分会话组；直连模式未统一历史时，官方/第三方切换后另一组只读。路由/聚合可保留在 `openai` 桶；统一历史或暂停官方登录会使用 `custom`。`disable_response_storage` 已废弃，不可再加入卡片或 live。
- **Kimi Code（4.0.19+，`kimi`）**：CLI 与桌面版共享 `~/.kimi-code`；多供应商共存，默认模型和子代理引用的供应商不能移除。供应商在 DB 中是结构化 `{provider, models}`，不是本技能 provider-* 命令支持的 TOML/env 形态。
- **Antigravity（4.0.18+，`agy`）**：`~/.gemini/config` 可能和 Antigravity IDE 共用；修改 MCP/Skills/提示词前确认影响范围。SSE MCP 不支持，应该桥接到 stdio 或流式 HTTP。
- **Oh My Pi（4.0.20+，`omp`）**：agent 目录可能是默认目录或 `OMP_PROFILE`/`PI_PROFILE` 选中的 profile，也受 `PI_CONFIG_DIR`、`PI_CODING_AGENT_DIR` 和 CCS 目录覆盖影响。供应商是 `models.yml`，可能含 anchors/tags/flow YAML；provider-* 命令必须拒绝。
- **DeepSeek Harness（4.0.22+，`dsh`）**：数据根优先使用 CCS 4.0.26+ 的 `dshConfigDir`，其次 `DSH_HOME`，最后 `~/.dsh`。Web/Desktop/已初始化的 headless/acp 共用同一供应商和 MCP 集合；每个 profile 分别写 `cordis.patch.yml`，凭据只在 `.credentials.yaml`。模型输入只写 `text`/`image`，其他模态会被过滤；headless 使用存放的 Key 时会自动恢复 credentials store，但保留用户显式配置。使用 `dsh-provider-get/set/remove`，不要直接写 YAML 或 DB。
- **MiniMax Code（mcode，3.20.4+）**：数据目录按 `MINIMAX_DATA_DIR` → `MAVIS_DATA_DIR` → `~/.minimax` 解析；默认模型、登录、云端功能与会话删除都归 MiniMax 自己，CCS 不参与本地代理、故障转移、托盘、通用配置与 Profiles。MCP/Skills 对 mcode 默认关闭（`enabled_mcode=0`），手动打开前 CCS 不写 `~/.minimax`；供应商是 YAML `custom_provider` 条目（本技能不支持编辑，请走 CCS 界面），本技能只管理它的提示词、Skills 与 MCP 启用标志。
