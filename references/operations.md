# 操作命令模板

所有命令同时给出 PowerShell 与 bash 两种写法；路径用 `$CC_HOME`（默认 `~/.cc-switch`）和 `$S`（本技能脚本路径）表示。

```powershell
$CC_HOME = if ($env:CC_SWITCH_HOME) { $env:CC_SWITCH_HOME } else { Join-Path $HOME '.cc-switch' }
$S = Join-Path $PSScriptRoot 'scripts\ccs_db.py'   # 在技能目录内执行时
```

```bash
CC_HOME="${CC_SWITCH_HOME:-$HOME/.cc-switch}"
S="$(dirname "$0")/scripts/ccs_db.py"              # 在技能目录内执行时
```

## 备份

PowerShell：
```powershell
$stamp='yyyyMMdd-<slug>'
Copy-Item <文件> "<文件>.bak-$stamp" -Force
Copy-Item "$CC_HOME\cc-switch.db" "$CC_HOME\backups\db_backup_$stamp.db" -Force
```

bash：
```bash
stamp="$(date +%Y%m%d)-<slug>"
cp "$CC_HOME/cc-switch.db" "$CC_HOME/backups/db_backup_$stamp.db"
```

## 停 / 启 CCS

PowerShell：
```powershell
Get-Process -Name 'cc-switch' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Process -FilePath '<CC Switch executable path>' -WindowStyle Hidden
```

bash / macOS：
```bash
pkill -f cc-switch || true
open -a "CC Switch"   # macOS；Windows 上按安装位置启动
```

> CCS 启动路径因平台/安装方式而异；以实际安装位置为准。

## 常用 DB 操作（推荐：内置脚本）

```powershell
python $S doctor                 # 路径、schema、供应商、直连/路由/聚合与健康告警
python $S check                  # 检查全库中文是否出现可疑 '?'
```

```bash
python "$S" doctor
python "$S" check
```

### MCP 记录

JSON 用 `--config-file`（避免 shell 剥掉双引号），tags 用逗号列表，中文可内联：

```powershell
python $S mcp-upsert --name dashscope-websearch `
  --config-file server_config.json `
  --description "DashScope 网页搜索（经 mcp-remote 桥接）" --tags "stdio,websearch" `
  --enable-codex --enable-claude
```

```bash
python "$S" mcp-upsert --name dashscope-websearch \
  --config-file server_config.json \
  --description "DashScope 网页搜索（经 mcp-remote 桥接）" --tags "stdio,websearch" \
  --enable-codex --enable-claude
```

### 全局提示词

```powershell
python $S prompt-set --app-type codex --content-file prompts_codex.txt
```

`--app-type` 支持 14 个应用：`codex` / `claude` / `claude-desktop` / `gemini` / `grokbuild` / `opencode` / `openclaw` / `hermes` / `pi` / `mcode` / `kimi` / `agy` / `omp` / `dsh`（Kimi/OMP/Agy/mcode 的供应商编辑走 CCS 界面；DSH 使用专用命令）。

### skill 注册

```powershell
python $S skill-upsert --name my-skill --description "我的技能" --enable-codex
python $S skill-upsert --name my-skill --preserve-flags
```

编辑本地 skill 后必须重跑一次刷新 `content_hash`；已有记录使用 `--preserve-flags` 可避免未传的 `--enable-*` 把已启用应用置 0。工具按 CCS 4.0.27 的完整目录语义计算，并忽略隐藏文件、`__pycache__/`、`*.pyc`。技能技术名必须是小写 kebab-case，DSH 会静默跳过不合规的 frontmatter `name`；目录名可以与 `name` 不同。repo 安装的 skill（`repo_owner` 非空）不要手改；Pi 没有 DB 开关（存在即启用）。

### 供应商 config 文本

```powershell
python $S provider-block --section "[mcp_servers.foo]" --block-file block.toml `
  --insert-before "[mcp_servers.bar]"
python $S provider-block --section "[mcp_servers.foo]" --block-file block.toml --replace
```

供应商 ID 解析顺序：`--provider-id` → `settings.json` 的 `currentProvider*` → `providers.is_current=1`；解析失败会明确报错。`provider-block` 只适用于有 `config` TOML 文本的供应商（如 codex/gemini）；claude/claude-desktop 用 `provider-env`。Kimi 的 `{provider, models}`、OMP/mcode 的 YAML、Agy 的启动终端卡会明确拒绝并提示 UI；DSH 必须使用 `dsh-provider-*`。

### 供应商环境变量

```powershell
python $S provider-env --app-type claude `
  --set ANTHROPIC_BASE_URL=https://api.example.com/anthropic --remove ENABLE_TOOL_SEARCH
```

### 供应商顶层/段内键（provider-set-key）

```bash
python scripts/ccs_db.py provider-set-key --app-type codex --key model_reasoning_summary --value '"none"'
python scripts/ccs_db.py provider-set-key --app-type codex --key mcp_servers.foo.startup_timeout_sec --value 30
python scripts/ccs_db.py provider-set-key --app-type codex --key web_search --remove
```

`--value` 是 TOML 字面量（字符串需带引号，PowerShell 下用单引号包裹整个参数）。该命令会自动跑 preflight 并校验 TOML。`[agents].max_threads` 是 CCS 4.0.25+ 的 Codex 全局设置，不属于 provider card；`check --strict` 会拦截，应该在 Codex live 配置或 CCS 供应商表单里设置。

### 只切启用标志

```powershell
python $S set-flags --table mcp_servers --name my-server --claude 1 --codex 1
python $S set-flags --table skills --name my-skill --claude 0
```

支持的开关：`--codex` `--claude` `--gemini` `--opencode` `--hermes` `--grokbuild` `--mcode`（3.20.4+）`--pi`（MCP，4.0+）`--agy`（4.0.18+）`--kimi`（4.0.19+）`--omp`（MCP，4.0.20+）`--dsh`（MCP/Skills，4.0.22+）。Pi/OMP 的 Skills 都按存在判定，没有数据库开关。

## 安装技能到各应用（复制/链接）

PowerShell（Junction，无需管理员）：
```powershell
New-Item -ItemType Junction -Path "$HOME\.codex\skills\<name>" -Target "$CC_HOME\skills\<name>"
```

bash（符号链接）：
```bash
ln -s "$CC_HOME/skills/<name>" "$HOME/.codex/skills/<name>"
```

删除只删链接本身，不要递归删除目标内容。

## MCP 三处同步（以远程 HTTP 为例）

仅适用于用户自建 / CCS 管理的 MCP；官方/内置服务器（如 `openaiDeveloperDocs`）不在 `mcp_servers` 表，属正常。

`~/.codex/config.toml`（Codex 实际生效）：
```toml
[mcp_servers.dashscope-websearch]
command = "npx"
args = ["-y", "mcp-remote", "https://example.com/WebSearch/mcp", "--header", "Authorization:${DASHSCOPE_AUTH}", "--transport", "http-first"]
startup_timeout_sec = 120

[mcp_servers.dashscope-websearch.env]
DASHSCOPE_AUTH = "Bearer <key>"
```

`mcp_servers` 表 `server_config`（CCS 面板）：
```json
{"command":"npx","args":["-y","mcp-remote","https://example.com/WebSearch/mcp","--header","Authorization:${DASHSCOPE_AUTH}","--transport","http-first"],"type":"stdio","env":{"DASHSCOPE_AUTH":"Bearer <key>"}}
```

> 面板 JSON 里的 `type` 由 CCS 按应用翻译；**Codex 不接受 `[mcp_servers.*]` 里的 `type`、`timeout`、`autoApprove`**（4.0.21 起写入时剥离客户端专用字段）。手写 Codex provider/live config 时不要带这三项，旧值用 `repair --mode mcp-type` 清理。

codex provider 的 `settings_config.config` 文本：追加与 config.toml 相同的 TOML 块。

## 校验

```python
import json

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # Python 3.8-3.10: pip install tomli

tomllib.load(open("config.toml", "rb"))          # TOML
json.load(open("claude_desktop_config.json", encoding="utf-8-sig"))  # JSON
```

`python scripts/ccs_db.py check` 覆盖 `providers`（name/notes/settings_config）、`settings.value`、`model_pricing.display_name`（JSON 内只报含 CJK 或 `??` 的可疑 `?`，URL 查询串不误报）。`codex mcp list` 检查 MCP 是否按预期注册；CCS 重启后复查 config 未被回写；`settings.json` 的 `currentProvider*` 与 `providers.is_current` 一致。

## 结构安全（v1.1.0+）

所有写操作都会自动运行只读 preflight，配置已损坏时拒绝写入（`--force` 放在子命令前可显式跳过）：

```bash
# 结构审计（独立只读命令）
python scripts/ccs_db.py check --strict
python scripts/ccs_db.py doctor --audit
python scripts/ccs_db.py doctor --compare-backup backups/db_backup_xxx.db

# 写操作前快照 / 之后对比（快照含 DB、config.toml、settings.json、live-state.json）
python scripts/ccs_db.py snapshot
python scripts/ccs_db.py diff <snapshot-dir>

# 修复（默认 dry-run，--apply 写入并自动备份）
python scripts/ccs_db.py repair --target config.toml --mode header-order
python scripts/ccs_db.py repair --target config.toml --mode codex-catalog-path
python scripts/ccs_db.py repair --target config.toml --mode codex-0167
python scripts/ccs_db.py repair --target provider --provider-id <id> --mode live-only --apply
python scripts/ccs_db.py repair --target common --mode both --apply

# provider-block 替换后自动做语义校验
python scripts/ccs_db.py provider-block --app-type codex \
  --section "[mcp_servers.foo]" --block-file block.toml --replace --check-semantics
```

`check --strict` 也会检测**顶层键被挪进表内**（如 `notify = [...]` 出现在某个 `[table]` 之后/内部）；`repair --mode header-order` 会自动把这类顶层键移回 preamble（所有 `[table]` 之前）。它还会检测 provider card 中违规出现的 `[agents].max_threads`，以及原生 Codex 配置目录中的相对 `model_catalog_json`；后者的 dry-run 与写入模板为：

```bash
python scripts/ccs_db.py repair --target config.toml --mode codex-catalog-path
python scripts/ccs_db.py repair --target config.toml --mode codex-catalog-path --apply
```

嵌套修复会遵守 CCS 4.0.27 规则：普通本地配置目录写绝对路径；WSL/UNC 配置目录保留 `cc-switch-model-catalog.json` 裸文件名。

Codex 0.167 不再识别 `disable_response_storage`。provider 或 live 配置中存在该键时，`check --strict` 会失败；修复模板：

```bash
python scripts/ccs_db.py repair --target config.toml --mode codex-0167
python scripts/ccs_db.py repair --target provider --provider-id <id> --mode codex-0167 --apply
```

### Codex 0.149 config-only 兼容（3.20.1+，含 3.20.2 flag 规则与 3.20.3 路由语义）

```bash
# 检测 0.149 拒绝/误路由形态（遗留保留表 / 缺 name / 真正生效的顶层 openai_base_url /
# 选择器指向缺失的表 / 空卡 / 无凭据 requires_openai_auth；内联 model_providers 会被识别）
python scripts/ccs_db.py check --strict

# 自动迁移（默认 dry-run，--apply 写入并自动备份）
python scripts/ccs_db.py repair --target provider --app-type codex --mode codex-0149
python scripts/ccs_db.py repair --target provider --app-type codex --mode codex-0149 --apply
python scripts/ccs_db.py repair --target config.toml --mode codex-0149 --apply
```

说明：`codex-0149` 会改名遗留保留表（活跃路由且自带密钥时同步改写 `model_provider`）、回填缺失的 `name`、把选择器缺省/`openai` 时真正生效的顶层 `openai_base_url` 迁移为 `[model_providers.cc-switch(-N)]`，并写入 `model_provider` + `wire_api = "responses"` + `base_url` + `experimental_bearer_token`——与 CCS 3.20.3 自身的规范化形态一致；用户已有的 `cc-switch` 表不会被覆盖（顺延 `cc-switch-2`…）。单行内联 `model_providers = { ... }` 会就地扩展，多行内联表只提示、不写坏 TOML。选择器指向自带表时，顶层 `openai_base_url` 是惰性残留，保持原样。对代理托管 OAuth 卡（`providers.meta.provider_type` = `xai_oauth` / `github_copilot`）还会把活跃表上的 `requires_openai_auth` 改为 `false`（与 CCS 3.20.2 一致）。空卡/无凭据/缺表的普通第三方卡仍然只提示，不会自动造表。

CC Switch 4.0.13+ 接受双引号、单引号及带空格的 provider 表头（如 `[model_providers."my provider"]`）。本技能 v1.3.1+ 在比较和修复前会解码表头键，回填 `name` 时重新生成合法 TOML 字符串；修复后仍应运行 `check --strict` 与 `tomllib` 复核。

### Codex 密钥恢复（3.20.4，#7434）

```bash
# 只读：check --strict / doctor --audit 会点名「auth 为空但 provider 表仍有 token」的卡
python scripts/ccs_db.py check --strict

# 恢复（默认 dry-run；--apply 写入并自动备份）
python scripts/ccs_db.py repair --target provider --app-type codex --mode codex-key
python scripts/ccs_db.py repair --target provider --provider-id <id> --mode codex-key --apply
```

说明：只处理可恢复形态（provider 文本里仍有 `experimental_bearer_token` / `api_key`）；官方卡与代理托管 OAuth 卡按设计跳过；两处都没有 token 时需要在 CCS 里重填密钥，并检查用量脚本是否被重置。

### MiniMax Code（mcode，3.20.4+）

```bash
# 提示词（单条 ≤32 KiB UTF-8；超出会被本工具拒绝）
python scripts/ccs_db.py prompt-set --app-type mcode --content-file mcode-prompt.txt

# MCP / Skills 的 mcode 启用标志（v19 的 enabled_mcode 列）
python scripts/ccs_db.py mcp-upsert --name my-server --config-file server_config.json --enable-mcode
python scripts/ccs_db.py skill-upsert --name my-skill --enable-mcode
python scripts/ccs_db.py set-flags --table skills --name my-skill --mcode 1
```

边界：mcode 供应商是 `~/.minimax/config.yaml` 的 YAML `custom_provider`，`provider-block` / `provider-env` / `provider-set-key` 会明确拒绝（请走 CCS 界面）；数据目录按 `MINIMAX_DATA_DIR` → `MAVIS_DATA_DIR` → `~/.minimax` 解析；MCP/Skills 默认对 mcode 关闭，开启后 CCS 才写 `~/.minimax`。注意 `mcp-upsert` / `skill-upsert` 的 `--enable-*` 是**全量标志集**（未传的会被置 0，关掉已启用项时工具会给出警告），单个开关请用 `set-flags`。

### Kimi Code（kimi，4.0.19+）

```bash
python scripts/ccs_db.py prompt-set --app-type kimi --content-file kimi-prompt.txt
python scripts/ccs_db.py mcp-upsert --name my-server --config-file server_config.json --enable-kimi
python scripts/ccs_db.py skill-upsert --name my-skill --enable-kimi
python scripts/ccs_db.py set-flags --table mcp_servers --name my-server --kimi 1
```

边界：数据目录按 `KIMI_CODE_HOME` → `~/.kimi-code`；MCP 写 `mcp.json`（stdio/HTTP/SSE），Skills 写 `skills/`，Prompt 写 `AGENTS.md`。供应商在 DB 中是结构化 `{provider, models}`，`provider-block` / `provider-env` / `provider-set-key` / provider repair 会明确拒绝；CLI 和桌面版共享这份配置，Kimi 不走本地代理或聚合。

### Antigravity CLI（agy，4.0.18+）

```bash
python scripts/ccs_db.py prompt-set --app-type agy --content-file agy-prompt.txt
python scripts/ccs_db.py mcp-upsert --name my-server --config-file server_config.json --enable-agy
python scripts/ccs_db.py skill-upsert --name my-skill --enable-agy
python scripts/ccs_db.py set-flags --table mcp_servers --name my-server --agy 1
```

边界：MCP/Skills/Prompt 都写 `~/.gemini/config`（MCP 为 `mcp_config.json`、Prompt 为 `AGENTS.md`），该目录可能和 Antigravity IDE 共用。MCP 支持 stdio 和流式 HTTP，**不支持 SSE**。供应商卡只对 CCS 卡片“使用此供应商打开终端”启动的 agy 生效；直接运行 agy 仍使用官方 Google 登录，因此 provider-* 命令会拒绝 Agy。

### Oh My Pi（omp，4.0.20+）

```bash
python scripts/ccs_db.py prompt-set --app-type omp --content-file omp-prompt.txt
python scripts/ccs_db.py mcp-upsert --name my-server --config-file server_config.json --enable-omp
python scripts/ccs_db.py skill-upsert --name my-skill --enable-omp  # 提示存在即启用
python scripts/ccs_db.py set-flags --table mcp_servers --name my-server --omp 1
```

边界：agent 目录可通过命名 profile、`PI_CONFIG_DIR`、`PI_CODING_AGENT_DIR` 或 CCS 设置改变；MCP 写 `mcp.json`，Skills/Prompt 位于同一 agent 目录。OMP 可能发现项目和外部技能/MCP，原生数量可高于 CCS 列表。供应商 `models.yml` 可能使用 YAML profile、anchors/tags，通用 provider-* 命令会拒绝。

### DeepSeek Harness（dsh，4.0.22+）

```bash
python scripts/ccs_db.py dsh-provider-get --provider-id <id>
python scripts/ccs_db.py dsh-provider-set --provider-id <id> --config-file dsh-provider.json
python scripts/ccs_db.py dsh-provider-set --provider-id <id> --config-file dsh-provider.json --apply
python scripts/ccs_db.py dsh-provider-remove --provider-id <id> --apply
python scripts/ccs_db.py mcp-upsert --name my-server --config-file server_config.json --enable-dsh
python scripts/ccs_db.py skill-upsert --name my-skill --enable-dsh
```

`dsh-provider-set` 的 JSON 使用 CCS 编辑器形态：`name`、`api`（`openai-completions` / `openai-responses` / `anthropic-messages`）、`options.baseURL`、`options.apiKey`/`apiKeyEnv`、`models`。命令会拒绝 profile 副本不一致、flow YAML、anchors/tags，并以事务方式更新 web/desktop 与已存在的 headless/acp `cordis.patch.yml`、`.credentials.yaml` 和 DB 行。

DSH 目录解析顺序：`--dsh-home` → CCS 4.0.26+ `settings.json:dshConfigDir` → `DSH_HOME` → `~/.dsh`。模型 `modalities.input` 只保留 `text`/`image`，其他值会打印告警并过滤。headless profile 使用 `.credentials.yaml` 中的 Key 时，会自动补 `- id: credentials` / `disabled: false`；若用户已显式写 `credentials` 条目则原样保留。profile 解析错误会带具体文件路径。

可直接从 `references/examples/dsh-provider.json` 复制模板；示例中不含真实凭据。

### CC Switch 4.0.28 升级后复核

```bash
python scripts/ccs_db.py doctor                                    # schema v24 + 14 应用 + 标志列 + 模式/安全告警
python scripts/ccs_db.py check --strict
python scripts/ccs_db.py doctor --audit
python scripts/ccs_db.py repair --target config.toml --mode mcp-type    # dry-run：清 type/timeout/autoApprove
python scripts/ccs_db.py repair --target config.toml --mode codex-catalog-path  # dry-run：相对目录指针
python scripts/ccs_db.py repair --target config.toml --mode codex-0167  # dry-run：Codex 0.167 废弃键
```

要点：4.0.24–4.0.28 无 schema 迁移，仍为 v24；4.0.20 升 v23（`enabled_omp`），4.0.22 升 v24（`enabled_dsh` + `parser_state`）。Codex MCP 旧 live 配置可用 `repair --mode mcp-type` 清理 `type`、`timeout`、`autoApprove`。`common-config` 已移除。Claude Desktop 从 4.0.13 起支持直连/路由/聚合；跨供应商 Codex 子代理开关是 `codexStackClassicTools`。`doctor` 警告 `preserveCodexOfficialAuthOnSwitch` 未开启时，若使用依赖 `auth.json` 的 Codex 构建，应在 CCS 设置中打开。

4.0.25+ 的 MCP 连通性检查会实际握手或启动本地命令，和 `doctor --audit` 的结构一致性不是一回事；本技能不会为了“验证”而执行未知 MCP。4.0.27+ 配置和 Skill 写入支持软链接；本技能的事务写入同样保留链接。

4.0.28 重点：

- **会话组**：Codex 0.167+ 的官方与第三方会话按 provider id 分组。直连且 `unifyCodexSessionHistory=false` 时，切换后另一组只读；路由/聚合通常保留在 `openai` 组。`doctor` 会打印并告警。
- **暂停官方登录**：`codexProxyWithoutOfficialLogin` 只在路由/聚合生效，切换后需彻底重启 Codex；直连下开启无效。
- **额度保护**：`codexQuotaProtection.enabled` 在 4.0.28 读入时默认开启一次；在迁移标记 `codexQuotaProtectionDefaultOnV1` 落盘前，旧文件里的 false 不是最终有效值。
- **本地路由形态**：top-level `openai_base_url=http://127.0.0.1:<port>/v1` 且无 bearer 时，可能是 4.0.28 的合法会话分组契约；`codex-0149` 会识别并保持，不要强行迁成 custom 表。

### MCP `type` 与 Pi 同步（4.0）

```bash
# Codex 不接受 [mcp_servers.*] 里的 type/timeout/autoApprove；旧 live 值直接清掉
python scripts/ccs_db.py repair --target config.toml --mode mcp-type
python scripts/ccs_db.py repair --target provider --provider-id <id> --mode mcp-type --apply

# Pi MCP（CCS 4.0+；只写连接字段，关同步=在 Pi 里停用不删条目）
python scripts/ccs_db.py mcp-upsert --name <name> --config-file server_config.json --enable-pi
python scripts/ccs_db.py set-flags --table mcp_servers --name <name> --pi 1

# Kimi / Antigravity / Oh My Pi / DeepSeek Harness
python scripts/ccs_db.py mcp-upsert --name <name> --config-file server_config.json --enable-kimi --enable-agy --enable-omp --enable-dsh
python scripts/ccs_db.py set-flags --table mcp_servers --name <name> --kimi 1 --agy 1 --omp 1 --dsh 1
```

### CC Switch 3.20.4 升级后复核（历史）

```bash
python scripts/ccs_db.py doctor --audit
python scripts/ccs_db.py check --strict          # 含 #7434 密钥清空检测
python scripts/ccs_db.py repair --target provider --app-type codex --mode codex-key   # dry-run
```

另外：绑定已删除 ChatGPT 账号的卡需手动重绑（重绑前无法开启接管）；「隐藏 AI 署名」需重新勾选；AICodeWith 的 Codex 端点需改成 `/v1`；DeepSeek V4 Pro 价格回到高峰档、`Ling-2.6-1T` 按纯文本处理。v18→v19 迁移后旧版 CCS 会拒绝打开数据库，确认升级前的备份还在。

### CC Switch 3.20.3 升级后复核（历史）

```bash
python scripts/ccs_db.py doctor --audit
python scripts/ccs_db.py check --strict
python scripts/ccs_db.py common-config status --app-type codex    # 旧版统一同步可能抹掉勾选
python scripts/ccs_db.py repair --target provider --app-type codex --mode codex-0149   # dry-run：旧 openai_base_url 误路由
```

另外到 CCS 的代理设置里逐应用复核重试/超时（3.20.3 之前会被 Claude 串写覆盖，旧值不会自动恢复）；Kimi 卡想走原生 Responses 需改“上游格式”或重新导入预设，DeepSeek 视觉目录需切走再切回。

```bash
# 代理托管 OAuth 卡：检查标志 + 修正（Codex OAuth 卡不适用，其官方登录即凭据）
python scripts/ccs_db.py doctor --audit          # 只读：列出结构问题与三处 MCP 一致性
python scripts/ccs_db.py check --strict          # 只读：点名 requires_openai_auth=true 的代理 OAuth 卡
python scripts/ccs_db.py repair --target provider --provider-id <id> --mode codex-0149 --apply
# 修的是 DB 模板；live config.toml 上的旧值要等下一次切换（或手动重切一次）才被重写
```

> [!IMPORTANT]
> **Codex 桌面版依赖 `~/.codex/auth.json`**：不要按“config-only 理想态”删除 auth.json，否则桌面版会回默认登录页（即使 `config.toml` 已写 `experimental_bearer_token`，手动注释掉等同未生效）。请保留 auth.json，并在 `~/.cc-switch/settings.json` 打开 `preserveCodexOfficialAuthOnSwitch=true`；切换后复核 auth.json 仍存在：
> ```bash
> python -c "import os; print(os.path.exists(os.path.expanduser('~/.codex/auth.json')))"
> ```

## 通用配置维护（仅 CCS ≤ 3.20.4）

**CC Switch 4.0 已移除“通用配置片段”**：共享设置直接留在客户端配置文件里并跨切换保留，`settings.common_config_*` 与 `providers.meta.common_config_enabled` 只是升级遗留。本技能在 schema ≥ v20 上会**拒绝所有 `common-config` 子命令**并提示新做法：

```bash
# 共享键（所有供应商都生效）：写客户端 live 配置，例如 ~/.codex/config.toml 的顶层键/表
# 供应商专属字段：写卡片
python scripts/ccs_db.py provider-set-key --app-type codex --provider-id <id> --key <key> --value '<value>'
python scripts/ccs_db.py provider-block --app-type codex --provider-id <id> --section "[mcp_servers.foo]" --block-file block.toml --replace
```

写 live 配置前按安全流程停 CCS；4.0 的写入器只替换关键字段，其余 live 内容会保留。临时在客户端里选的模型/推理强度，切走再切回会恢复为供应商设定值。

### CCS ≤ 3.20.4 的旧用法（历史）

```bash
python scripts/ccs_db.py common-config get --app-type codex
python scripts/ccs_db.py common-config status --app-type codex
python scripts/ccs_db.py common-config set-key --app-type codex --key <key> --value '<value>' --apply --sync-and-enable
python scripts/ccs_db.py common-config extract --app-type codex --provider-id <id> --apply
python scripts/ccs_db.py common-config enable --app-type codex --provider-id <id> --apply
```

交互说明：`set*` 写完后在 TTY 下询问“是否同步当前配置并打勾”；非交互默认不同步，可用 `--sync-and-enable` 显式要求（同样先过幂等审查）。**禁止**手写临时脚本直改 `cc-switch.db`；DB 写入一律走 `ccs_db.py`。

### 范围确认（重要）

“同步”由 AI **自行判断识别变更对象**（配置 / 技能 / 模板，结合上下文与待同步差异），没有问题不要轻易问用户；只有确无法识别时才询问。识别结果若包含配置，则落到“配置变更铁律”：未明确范围时默认 provider-first（`provider-set-key`）；CCS ≤ 3.20.4 改完再询问是否 `common-config extract` 到模板，4.0+ 改为提示共享键写客户端 live 配置。只有用户明确提到“通用配置 / common-config / 模板”（且 CCS ≤ 3.20.4）才直接操作 snippet。**不要把对象 A 的同步当作对象 B 的同步**（技能 ≠ 配置 ≠ 模板，双向适用）。

任何不确定处，先认真阅读本技能（SKILL.md 与 references/）再行动，**不要自由发挥**；若请求确实超出本技能范围，明确告知用户并给出建议行动。
