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
Start-Process -FilePath (Join-Path $env:LOCALAPPDATA 'Programs\CC Switch\cc-switch.exe') -WindowStyle Hidden
```

bash / macOS：
```bash
pkill -f cc-switch || true
open -a "CC Switch"   # macOS；Windows 上按安装位置启动
```

> CCS 启动路径因平台/安装方式而异；以实际安装位置为准。

## 常用 DB 操作（推荐：内置脚本）

```powershell
python $S doctor                 # 打印解析出的路径、schema、各应用供应商
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

`--app-type` 支持 9 个应用：`codex` / `claude` / `claude-desktop` / `gemini` / `grokbuild` / `opencode` / `openclaw` / `hermes` / `pi`。

### skill 注册

```powershell
python $S skill-upsert --name my-skill --description "我的技能" --enable-codex
```

编辑本地 `SKILL.md` 后必须重跑一次刷新 `content_hash`；repo 安装的 skill（`repo_owner` 非空）不要手改；Pi 没有 DB 开关（存在即启用）。

### 供应商 config 文本

```powershell
python $S provider-block --section "[mcp_servers.foo]" --block-file block.toml `
  --insert-before "[mcp_servers.bar]"
python $S provider-block --section "[mcp_servers.foo]" --block-file block.toml --replace
```

供应商 ID 解析顺序：`--provider-id` → `settings.json` 的 `currentProvider*` → `providers.is_current=1`；解析失败会明确报错。`provider-block` 只适用于有 `config` TOML 文本的供应商（如 codex/gemini）；claude/claude-desktop 用 `provider-env`。

### 供应商环境变量

```powershell
python $S provider-env --app-type claude `
  --set ANTHROPIC_BASE_URL=https://api.example.com/anthropic --remove ENABLE_TOOL_SEARCH
```

### 只切启用标志

```powershell
python $S set-flags --table mcp_servers --name my-server --claude 1 --codex 1
python $S set-flags --table skills --name my-skill --claude 0
```

支持的开关：`--codex` `--claude` `--gemini` `--opencode` `--hermes` `--grokbuild`。

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

# 写操作前快照 / 之后对比
python scripts/ccs_db.py snapshot
python scripts/ccs_db.py diff <snapshot-dir>

# 修复（默认 dry-run，--apply 写入并自动备份）
python scripts/ccs_db.py repair --target config.toml --mode header-order
python scripts/ccs_db.py repair --target provider --provider-id <id> --mode live-only --apply
python scripts/ccs_db.py repair --target common --mode both --apply

# provider-block 替换后自动做语义校验
python scripts/ccs_db.py provider-block --app-type codex \
  --section "[mcp_servers.foo]" --block-file block.toml --replace --check-semantics
```

`check --strict` 也会检测**顶层键被挪进表内**（如 `notify = [...]` 出现在某个 `[table]` 之后/内部）；`repair --mode header-order` 会自动把这类顶层键移回 preamble（所有 `[table]` 之前）。

## 通用配置维护（v1.1.0+）

```bash
# 只读
python scripts/ccs_db.py common-config get --app-type codex
python scripts/ccs_db.py common-config check --app-type codex
python scripts/ccs_db.py common-config status --app-type codex

# 修改（必须显式调用；默认 dry-run，--apply 写入并自动备份）
python scripts/ccs_db.py common-config set --app-type codex --content-file snippet.toml --apply
python scripts/ccs_db.py common-config set-key --app-type codex --key model_reasoning_effort --value '"max"' --apply
python scripts/ccs_db.py common-config remove-key --app-type codex --key web_search --apply

# 提取（用户显式调用；执行后自动打勾）
python scripts/ccs_db.py common-config extract --app-type codex --provider-id <id> --apply

# 打勾 / 取消打勾（enable 前自动做幂等审查）
python scripts/ccs_db.py common-config enable --app-type codex --provider-id <id> --apply
python scripts/ccs_db.py common-config disable --app-type codex --provider-id <id> --apply
```

交互说明：`set*` 写完后在 TTY 下询问“是否同步当前配置并打勾”；非交互默认不同步，可用 `--sync-and-enable` 显式要求（同样先过幂等审查）。

### 两边一起改（canonical workflow）

当需要“配置和通用配置都要更新”时，唯一推荐姿势：

```bash
# 单键
python scripts/ccs_db.py common-config set-key --app-type codex --key <key> --value '<value>' --apply --sync-and-enable
# 整体
python scripts/ccs_db.py common-config set --app-type codex --content-file snippet.toml --apply --sync-and-enable
```

它会：① 写 snippet；② 从当前 provider config 剥离与 snippet 重复的键；③ 显式打勾（`commonConfigEnabled=true`）；④ 自动校验。

**禁止**手写临时脚本直接 `UPDATE providers` / 直改 `cc-switch.db`；DB 写入一律走 `ccs_db.py` 子命令。规范终态：snippet 持有这些键，provider config 不重复持有。
