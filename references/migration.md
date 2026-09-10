# 官方版本行为变化

只记录 CC Switch 官方版本带来的行为变化；不包含任何用户/环境相关说明。

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
- **Pi 成为第九个受管应用**：供应商、提示词（AGENTS.md / SYSTEM.md / APPEND_SYSTEM.md）、Skills（存在即启用）、会话用量接入；Pi 无 MCP 注册表，不参与 MCP 同步；无代理/故障转移。
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
