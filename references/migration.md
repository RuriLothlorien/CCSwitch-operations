# 官方版本行为变化

只记录 CC Switch 官方版本带来的行为变化；不包含任何用户/环境相关说明。

## 4.0（正式版 4.0.4，2026-10-06；含 4.0.5–4.0.15 修复）

- **数据库迁移 v19 → v20**：`mcp_servers` 新增 `enabled_pi`（MCP 同步到 Pi 1.0）。首次启动自动迁移并尝试备份到 `<cc-home>/backups/`；运行过 4.0 后 3.x 会以“数据库版本过新”拒绝打开。
- **配置写入重写（#6719 修复）**：供应商编辑页保存只替换地址、Key、模型等关键字段，其余内容（顶层键、`[plugins]`/`[projects]`/`[mcp_servers.*]`、注释、`# >>> … <<<` 标记）逐字节保留；零改动保存与保存前逐字节一致；不再剥离/合并通用配置；url-only 远程 MCP 不再写成空 `command`，Codex 的 `[mcp_servers.*]` 不再写 `type`。**已损坏的存量条目不会自动修**：在 MCP 面板把服务器关掉再打开重写，或用本技能 `check --strict` / `repair` / `mcp-upsert`。
- **通用配置片段功能移除**：共享设置直接留在客户端配置文件里并跨切换保留；DB 里旧的 `common_config_*` 与 `providers.meta.common_config_enabled` 成为惰性遗留（升级时会把片段合并进各供应商配置，记录在 `common_config_legacy_migrated_v1`）。临时在客户端选的模型/推理强度，切走再切回会恢复为供应商设定值。
- **三种模式：直连 / 路由 / 聚合（Stack）**：聚合把多家供应商的模型发布到同一个客户端模型列表并按所选模型分发；4.0.13 起支持 Claude Code、Codex 与 Claude Desktop，需要本地路由，**无故障转移**；状态在设备本地 `~/.cc-switch/live-state.json`（不跟随 `CC_SWITCH_HOME`、不同步），Claude Code 各家的发布模型在 `providers.meta.stackModels`。Claude Code 需 ≥2.1.243；Codex 聚合列表变化需重启（Claude Code 立即生效）；同会话换模型会重建提示词缓存，首轮更贵。Claude Desktop 只在启动时读配置，换模式、路由目标或成员后必须重启。跨供应商子 agent 在 4.0.13+ 使用 `settings.json: codexStackClassicTools`（默认 true）。
- **MCP**：可同步到 8 个应用（新增 Pi 1.0，`~/.pi/agent/mcp.json`）；只写连接字段，关同步=在目标里停用而不删条目；SSE 传输、名称含特殊字符的服务器会提示不支持。Codex 0.158+ 不接受 `[mcp_servers.*]` 里的 `type`（4.0 写入时剥离；卡片/面板里的 `type` 在 4.0 下是惰性遗留）。
- **Codex**：4.0.5 起可用 GitHub Copilot 账号（需开路由，按模型自动选择 Responses/Chat，也可在「上游格式」手选）；4.0.7 起可开关会话压缩（写 `config.toml` 的 `[features] local_thread_store_compression = true`，7 天以上会话压成 `.jsonl.zst`，第三方直接读 raw `.jsonl` 的工具可能读不到）；切换账号或模式会提示重启 Codex 后台服务。
- **其他**：Claude Code 新增「关闭 auto mode 服务端检查」快捷开关（新建第三方卡默认勾选）；Skills 支持一键全部更新；提示词 8 个应用同页管理；备份总览；预设更新只影响新建卡；移除的设置：供应商成本倍率、连通性检查高级设置、Claude 的 Teammates 与最大强度（已写入配置的变量不会被删除）。
- **4.0.9–4.0.12**：本地路由新增 WSL2 可用的「连接地址」；深链支持 `apiFormat`、Pi 供应商和受校验的 `iconUrl`，可执行/可展开值会被拒绝；应用页可安装、升级、卸载并处理多个安装；新增本地 Ollama / LM Studio / llama.cpp / vLLM 供应商，发往回环地址的请求绕过代理；后台会话扫描降为每 10 分钟、打开用量页会立即扫描。schema 始终为 v20。
- **4.0.13**：Claude Desktop 获得直连/路由/聚合模式和对应模式面板；Codex 新增自动审批模型、provider 卡内 `[agents] default_subagent_model` / `default_subagent_reasoning_effort`，聚合页可单独选择子代理模型；保存 Codex 配置时能识别双引号、单引号及带空格的 `[model_providers.*]` 表头；GPT 系列自动补全窗口封顶 272K，1M 模型预设默认声明。schema 仍为 v20。
- **4.0.14**：用量面板的币种、侧栏指标、请求日志列可配置；Skills 仓库压缩包上限提升到 512 MiB；Claude Desktop 的 1M 模型只显示一行；schema 仍为 v20。
- **4.0.15**：Windows 上 `settings.json` 改为原子替换，并可从 BOM、尾部垃圾或截断内容中恢复；损坏原文件保留为 `settings.json.broken-<time>.bak`。此前已被重置的设置不会找回。修复路由会话识别、Codex 坏工具调用历史、DeepSeek 工具历史、WebDAV/S3 慢速传输和 WSL Hermes 会话读取；schema 仍为 v20。
- **升级须知**：升级前建议手动再备份一次（自动备份失败只记日志）；Codex 模型目录/会话分组的修复要等下一次写入（升级后切换一次供应商）；已有 MCP 配置重新同步一次以清掉旧 `type`；时间 MCP 预设改用 `uvx mcp-server-time`（存量需手改命令）；MiniMax Code 可在「应用」页安装与升级。使用带引号的 provider 表头时，确认本技能版本至少为 v1.3.1。

## 3.20.4（2026-09-22）

- **数据库迁移 v18 → v19**：`mcp_servers` 与 `skills` 各新增 `enabled_mcode`（默认 0）。首次启动自动迁移；CCS 会尝试自动备份到 `<cc-home>/backups/`，但备份失败只记日志、不中止升级。运行过本版后 3.20.3 及更早版本会以“数据库版本过新”拒绝打开，降级需恢复升级前备份。
- **第十个受管应用：MiniMax Code（app_type `mcode`）**：累加模式；供应商写入 `~/.minimax/config.yaml` 的 `custom_provider`（DB 里 `settings_config` 是 `name/kind/enabled/api/options/models` 的 JSON）；MCP ↔ `~/.minimax/mcp.json`；Skills → `~/.minimax/skills/`（Pi 式归属检查，不动非 CCS 所有的同名 skill）；提示词 → `~/.minimax/AGENTS.md`（单条 ≤32 KiB UTF-8 字节；停用最后一个提示词会清空文件；切换前会把 live 外部修改写回当前提示词）。数据目录：`MINIMAX_DATA_DIR` → `MAVIS_DATA_DIR` → `~/.minimax`（设置里不可覆盖）。默认模型、登录、云端功能、会话删除归 MiniMax 自己；无本地代理接管、故障转移、托盘、通用配置与 Profiles。存量 MCP/Skills 对 mcode 默认关闭，手动开启前 CCS 不写 `~/.minimax`。
- **Codex 经 Chat 网关的修复**：Codex 0.154+ 的 `additional_tools` 不再生成 `content: null` 的 system 消息（#7454）；`detail: "original"` 截图不再让会话此后每轮 400（#7476）；无描述工具不再发 `"description": null`（#7319/#7378）。升级后相关请求有一次前缀缓存未命中，之后稳定。
- **Codex 密钥不再被清空，但已丢的不恢复**：编辑或切走供应商不再用 live 的空 auth 覆盖已保存的 API Key（#7434）；之前被清空的密钥需重填，用量脚本若被重置也要重配。本技能 `check --strict` / `doctor --audit` 会报告“auth 为空但 provider 表仍有 token”的可恢复形态，`repair --target provider --mode codex-key --apply` 可回填。
- **已删除 ChatGPT 账号的绑定**：绑定旧账号的 Codex 卡不再卡死切换/编辑，但需手动重绑；重绑前无法开启接管，若上次退出时接管开着，启动恢复会关闭 Codex 接管（`~/.codex/auth.json` 不动）（#7395）。
- **Claude Code**：GitHub Copilot 下 auto mode 恢复（#5404）；`/effort` 的 `xhigh`、映射到 Grok 4.6 模型的推理强度、GPT-5.6/GPT-6 Astra 的 `max` 按所选档位发送（#7318/#7531）。
- **Skills 安装**：skills.sh 的 id 与目录名不一致、超过 1 万个文件的仓库修复（#6381/#7489）。
- **提示词读回**：打开提示词列表时，会用 live 文件（`CLAUDE.md`/`AGENTS.md` 等）的外部修改覆盖 DB 中“启用中”的内容；非启用模板不受影响，Pi 不在此列（#7194）。
- **「隐藏 AI 署名」**：现在要求 `attribution.sessionUrl = false` 才算开启；旧格式 `{commit:"", pr:""}` 升级后显示未勾选，需重新勾选一次（不自动改写）（#7053）。
- **预设/定价**：国内 Codex 预设按厂商 Responses 文档对齐（Kimi For Coding → K2.8 Preview、1M 窗口；DeepSeek 默认 `deepseek-flash`）；MiniMax 国内站与百灵迁到新官方域名；AICodeWith 的 Codex 端点改为 `/v1`（存量卡需手改）；DeepSeek V4 Pro 撤回调价、恢复高峰档；`Ling-2.6-1T` 按纯文本处理。
- **其他**（不影响本技能操作方式）：Claude Desktop 第三方配置支持 Linux、请求日志显示每秒输出 token 数、OpenCode 供应商表单批量添加模型、Windows 任务栏与关于页版本探测修复。
- **#6719 仍未修复**：编辑页零改动保存破坏 Codex 配置的缺陷不在 3.20.4 修复列表内，警告覆盖 3.20.0–3.20.4。

## 3.20.3（2026-09-11）

- **无数据库迁移**：schema 保持 v18；Codex 的字节游标复用 `session_log_sync.last_byte_offset`。升级后首轮会重新解析一次 rollout（只耗 CPU，按行偏移跳过已导入事件，不会重复计数）。
- **Codex 缺 `model_provider` 的卡接管时改走本地代理**：缺失的选择器现在视为内置 `openai` 供应商，代理地址先写 `openai_base_url`，再由共享规范化步骤改写为 `[model_providers.cc-switch(-N)]`（`model_provider` 指向该表、`name`、`base_url`、`wire_api = "responses"`、`PROXY_MANAGED` bearer）——与其他第三方接管同形。旧行为把地址写到 Codex 不读的顶层 `base_url`，请求会静默直连 `api.openai.com`。直切（非接管）仍按卡片原样；该规范化对切换、接管备份与恢复的每次 live 写入都生效。
- **统一供应商同步保留子卡设置**：此前同步会把子卡的 `meta`（用量脚本、通用配置 opt-out、端点自动选择）清空并把排序位置归零；3.20.3 起保留。**被旧版清掉的设置不会自动恢复**，需要重填一次——通用配置勾选可用 `common-config status` 复核后重新 `enable`。
- **每应用代理重试/超时串写停止**：此前退出时会把 Claude 的代理重试/超时抄给 Codex、Gemini、Grok Build；3.20.3 止住串写，但**已被覆盖的旧值不会恢复**，需逐应用到代理设置复核。
- **Chat 上游转换修复**：commentary 与紧随的工具调用合并进同一条 assistant 消息（#7280），修掉 Codex 长任务在一句进度汇报后停止；同一根因的 DeepSeek 无限复读也一并修复。升级后 Chat 上游卡会经历一次前缀缓存未命中（请求字节变了，之后逐轮稳定）。
- **Claude Code 空 Thought 块修复**（#7227）：GLM、Qwen、DeepSeek 等每个 chunk 带空 `reasoning_content` 占位的上游不再刷屏。
- **Claude Desktop 探针 `max_tokens` 1–15 夹到 16**（#7287）：Responses 上游下不再误报“模型不可用”。
- **预设/目录/定价**：Kimi 开放平台与 Kimi For Coding 两条 Codex 预设由 `openai_chat` 改为 `openai_responses`（存量卡仍是 Chat 路由，可改“上游格式”或重新导入；注意开放平台 Tier 0 限 3 次/分钟）；千问AI平台改名并升到 Qwen 3.8（含 Pi 的 QwenCloud Token Plan 协议切换）；MiniMax 默认 M3；火山豆包显示名更新；千帆/腾讯 Token Plan 的 DeepSeek 行显式声明纯文本；DeepSeek 官方目录 `deepseek-flash` 支持视觉输入（切换供应商时重建 catalog，切走再切回生效）；DeepSeek V4 家族定价按 V4.1 Flash 档修正（历史费用不重算）。
- **Claude Code 新增“禁用 Artifact 工具”快捷开关**：写 `settings_config.config.env.CLAUDE_CODE_DISABLE_ARTIFACT = "1"`，避免严格校验工具 schema 的网关对每个请求返回 400。
- **#6719 仍未修复**：3.20.3 的修复列表与提交均不含“编辑页零改动保存破坏配置”，上游 issue 仍为 open；警告覆盖 3.20.0–3.20.3。
- **代理与用量层修复**（不影响本技能的操作方式）：Windows 上正在增长的 Codex 会话用量按文件大小判定、托盘显示托管账号额度、Claude Fable 的 `limits[]` 周限额解析等。

## 3.20.2（2026-09-07）

- **无数据库迁移**：schema 保持 v18，不产生迁移备份；`doctor` 读数与 3.20.1 相同。
- **`requires_openai_auth` 新矩阵**：代理逐请求注入令牌的 OAuth 卡（`providers.meta.provider_type` = `xai_oauth` / `github_copilot`）在活跃自定义表上被强制 `requires_openai_auth = false`（预设源头同步输出 false，存量卡在下一次切换时自愈）；**Codex OAuth 刻意排除**——官方登录就是它的凭据。v3.20.1 的无密钥安全闸曾把这类无密钥卡误判为“会回落到官方登录”而拒绝切换。
- **接管按登录状态覆盖该标志**：接管写入器先解析 Codex 的鉴权模式（显式 `auth_mode` > 个人访问令牌 > Bedrock API key > Bedrock 访问密钥 > `OPENAI_API_KEY` > ChatGPT），再按凭据存储判定——`file` 跟随 `auth.json` 是否持有官方登录；`ephemeral` 视为未登录（写 `false`）；`keyring` / `auto` 无法从磁盘判定，保留卡上原值；`auth.json` 缺失、不可读或损坏一律视为未登录，且不再让接管写入失败。这修掉了“直切删掉 `auth.json` 后再开接管，Codex 停在登录屏”的坑。
- **catalog 类修复在下一次切换供应商时生效**（切换时重建 catalog）：DeepSeek 预设改为 `supports_search_tool = false`（MCP 工具不再被隐藏）、`supports_parallel_tool_calls` 加入必填回填清单、DeepSeek 未匹配型号按注册表解析输入模态、`glm-5.3` 加入已确认纯文本清单。
- **预设 = 创建时的快照，改动只影响新建卡**：本版涉及智谱 GLM（改指官方 Responses 端点 `/api/v1`、默认 `glm-5.3`）、`grok-4.5` 的 `xhigh` 档、腾讯 Pi 预设的思考控制、腾讯预设里 `minimax-m2.5` 的移除——**存量智谱 Codex 卡仍指向 Chat 端点，直连依旧失败，需重新导入预设**。例外：PPIO、JieKou、Novita 的模型列表地址按卡片 Base URL 反查预设，仍在默认地址上的存量卡无需改动。
- **Codex OAuth 接管自报版本升到 0.153.4**：GPT-6 经 Codex OAuth 不再被后端以“需要更新 Codex”拒绝；若绕过 CCS 直接用 Codex CLI，需本机 Codex ≥ 0.153.0。
- **#6719 仍未修复**：3.20.2 的修复列表不含“编辑页零改动保存破坏配置”，故该缺陷在 3.20.0–3.20.2 均存在，编辑页维护 Codex 供应商/通用配置的警告继续有效。
- **代理与用量层修复**（不影响本技能的操作方式）：Grok 经 xAI 原生 Responses 跑通、Codex 内置图片生成走本地路由、Moonshot `$ref` 兄弟键改写、Claude Code 在 Codex OAuth 上并行工具调用、中途 system 消息原位转发恢复前缀缓存、resume 后用量补记、九月定价刷新与七个新模型定价行。

## 3.20.0（2026-08-18）

- **数据库迁移 v16 → v17**：新增 `session_usage_dedup`（会话用量持久去重账本）。升级前自动创建备份（`<cc-home>/backups/`）；运行过 3.20 后旧版会拒绝打开数据库，降级需还原该备份。
- **Pi 成为第九个受管应用**：供应商、提示词（AGENTS.md / SYSTEM.md / APPEND_SYSTEM.md）、Skills（存在即启用）、会话用量接入；无代理/故障转移。（3.20 时 Pi 无 MCP 注册表；4.0 起支持 MCP，见上方 4.0 章节。）
- **Codex 多 ChatGPT 账号**：官方供应商卡可绑定认证中心的账号；切换绑定卡会写入 `~/.codex/auth.json`；官方卡退出自动故障转移。
- **Codex 模型目录**：支持逐模型思考档位；`model_catalog_json` 指针只在缺失或已是 CCS 自有文件名时才被认领（被早期版本改写过的指针需手动指回一次）。
- **备份/恢复**：SQL 备份逐值保真、截断文件导入被拒绝；恢复 `.db` 备份会重写所有受管应用的 live 配置（Pi 除外），恢复后需复核 MCP 三处一致。
- **Skills 一致性**：同步、恢复与 Skills 操作全局串行；本地 skill 编辑后需刷新 `content_hash`；文件缺失的 repo skill 会显示为“可更新”。
- **输入法（IME）修复**：修复了表单输入的字符损坏问题，但已损坏的旧值仍保留在库/配置里，需重新编辑。
- **DeepSeek 定价**：按厂商新峰值牌价重定价，看板成本读数会显著上升（历史不重算，个别别名行回填）。

## 3.20.1（2026-08-28）

- **数据库迁移 v17 → v18**：`session_log_sync` 新增字节游标与尾部指纹两列（会话日志增量扫描）。升级前自动备份；运行过 3.20.1 后旧版会拒绝打开数据库，降级需还原备份。
- **Codex 第三方切换改为 config-only**：密钥写入该供应商 `[model_providers.*]` 表的 `experimental_bearer_token`，不再写 `auth.json`；`auth.json` 仅存官方 ChatGPT 登录。Codex <0.48 不读取该字段，需升级 Codex。
- **注意（桌面版兼容）**：部分 Codex 构建（尤其桌面版 / patched CLI）以 `~/.codex/auth.json` 是否存在判定登录态；仅写入 `experimental_bearer_token` 而删除 `auth.json` 会回到默认登录页。请保留 `auth.json`，并在 `~/.cc-switch/settings.json` 打开 `preserveCodexOfficialAuthOnSwitch=true`，防止切换第三方时被删除。
- **Codex 0.149 兼容**：遗留 `[model_providers.openai|ollama|lmstudio]` 表、缺 `name` 的表、顶层 `openai_base_url` 旧路由会在切换/接管时被自动修复或预检拒绝；空卡/无凭据卡会在切换时被点名拒绝。
- **保留开关**：“非接管切换时保留官方登录”关闭（默认）时，切换第三方会**删除 `auth.json`**；找回官方登录请切到绑定账号的官方卡或 `codex login`。
- **上游修复（技能无需变化）**：供应商编辑必达 live 配置（#6779）、Codex 编辑框不再串染密钥（#6534）、恢复备份不再清空非受管 prompt 文件（#6810）、会话扫描自动/手动开关与字节游标增量扫描。
- **#6719 未修复**：3.20.1 的修复列表不含“编辑页零改动保存破坏配置”，该缺陷在 3.20.0/3.20.1 均存在，技能仍建议不要用编辑页保存/提取 Codex 供应商配置。

## 更早版本

- v3.19.2：修复了 WSL 路径上无法更新/切换已有配置的问题；受影响用户应升级到 3.20。
- v3.16 前后：引入 `profiles` 表（项目 Profile）；引入本地代理、用量统计与故障转移相关表（`proxy_*`、`usage_*`、`provider_health` 等），这些表由 CCS 自管，不要手改。
