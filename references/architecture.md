# CC Switch 架构速查

## 数据库 `<cc-home>/cc-switch.db`（CCS 3.20 = schema v17）

`cc-home` 解析顺序：`CC_SWITCH_HOME` 环境变量 → `~/.cc-switch`。

### 手工维护的表

| 表 | 作用 | 关键列 |
| --- | --- | --- |
| providers | 各应用下的供应商 | app_type(9 个应用), settings_config(JSON：`config` TOML 文本 / `env` / `modelCatalog`), provider_type, is_current, in_failover_queue, cost_multiplier, limit_daily_usd, limit_monthly_usd, meta |
| prompts | 全局提示词 | app_type(codex/claude/claude-desktop/gemini/grokbuild/opencode/openclaw/hermes/pi), name(`全局`), content, enabled |
| skills | skill 管理 | id(`local:<name>`), name, directory, repo_owner/repo_name/repo_branch/readme_url, enabled_codex/claude/gemini/opencode/hermes/grokbuild, installed_at, content_hash |
| mcp_servers | MCP 面板 | id(slug), name, server_config(JSON), description, tags, enabled_codex/claude/gemini/opencode/hermes/grokbuild。只放用户自建/CCS 管理的服务器；官方/内置 MCP 故意不在此表 |
| settings | 通用配置 | key(common_config_codex/common_config_claude/claude_desktop_gateway_token/official_providers_seeded/...), value |

### CCS 自管表（不要手改）

`model_pricing`、`profiles`、`provider_endpoints`、`provider_health`、`proxy_config`、`proxy_live_backup`、`proxy_request_logs`、`session_log_sync`、`session_usage_dedup`（v17 新增）、`skill_repos`、`stream_check_logs`、`usage_daily_rollups` —— 用量、代理、故障转移、Profile、repo skill 安装都在这里，改坏会被 CCS 回写或导致面板异常。

## settings.json（`<cc-home>/settings.json`）

- `currentProviderCodex` / `currentProviderClaude` / `currentProviderClaudeDesktop`（启用 Gemini 后还有 `currentProviderGemini`）——`ccs_db.py` 从这里 + `providers.is_current` 动态解析供应商 ID。
- `skillSyncMethod`: `auto`（默认，优先 symlink、失败回退 copy）/ `symlink` / `copy`；`skillStorageLocation`: `cc_switch`（默认，源在 `<cc-home>/skills`）/ `unified`。
- 其他：`visibleApps`、`enableLocalProxy`、`enableFailoverToggle`、`preserveCodexOfficialAuthOnSwitch`、`unifyCodexSessionHistory`、`enableClaudePluginIntegration`、`preferredTerminal` 等。

## 生效链路

- **Codex config.toml** ← CCS 从当前 codex provider 的 `settings_config.config` 文本生成。直接改 config.toml 后，必须同步改 provider 的 config 文本，否则 CCS 下次切换供应商会回写覆盖。
- **Claude Code settings.json** ← claude provider 的 `settings_config.env` + `settings.common_config_claude`。
- **Claude Desktop 3P**：`%LOCALAPPDATA%\Claude-3p\claude_desktop_config.json`（MCP/偏好）+ `configLibrary\...157210.json`（网关/模型/toolSearchEnabled）。CCS 会自动维护这些文件，但不负责 MCP/Skills 内容（3.20 源码仍显式跳过 Claude Desktop）。
- **Claude Desktop 1P**：`%APPDATA%\Claude\claude_desktop_config.json`。
- **模型目录**：`~/.codex/cc-switch-model-catalog.json`（CCS 从供应商模板生成；DeepSeek 模板需保持 `supports_search_tool:false` 以规避工具不可见问题）。3.20 的目录支持逐模型思考档位；`model_catalog_json` 指针只在缺失或已是 CCS 自有文件名时才被认领。
- **恢复 `.db` 备份（3.20 行为变化）**：恢复后会按新库**重写所有受管应用的 live 配置（Pi 除外）**，而旧版只改数据库——恢复后仍需复核 MCP 三处一致。

## 受管应用（CCS 3.20 共 9 个）与 Skills 目录

见 references/apps.md 的完整矩阵。

## Skills 目录

- 源：`<cc-home>/skills/<name>`（`skillStorageLocation=cc_switch` 时）
- 各受管应用：`~/.<app>/skills/<name>`，形态由 `skillSyncMethod` 决定（`auto` 优先 symlink、失败或已有普通目录时回退 copy；`symlink` 恒为链接；`copy` 恒为复制）
- Claude Desktop 3P：`%LOCALAPPDATA%\Claude-3p\local-agent-mode-sessions\skills-plugin\{org}\{account}\skills\<name>`（Junction）+ manifest.json 条目（`creatorType:"user"`, `syncManaged:false`, `enabled:true`）+ `cc-switch-managed.json`（管理标记）
