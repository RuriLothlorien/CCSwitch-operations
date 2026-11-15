# v1.6.0 增量更新

## 兼容性修复

- **兼容基线升级**：对齐 CC Switch **4.0.32** / Codex 0.167 / 数据库 **schema v26**。
- **新增两个受管应用**：GitHub Copilot CLI（`copilot`，4.0.29+，schema v25 增加 `enabled_copilot`）与腾讯 WorkBuddy（`workbuddy`，4.0.31+，schema v26 增加 `enabled_workbuddy`）；`--app-type`、`--enable-*`、`--copilot`/`--workbuddy` 与 `doctor` 一并覆盖 16 个应用。
- **拒绝结构化编辑**：Copilot 的 `providers.json` 与 WorkBuddy 的 `models.json` 由 CCS 整份校验，`provider-block`/`provider-env`/`provider-set-key`/`repair --target provider` 会明确拒绝并指引改用 CCS 界面。
- **目录解析**：`doctor` 新增 `copilot_home`（`COPILOT_HOME` → `~/.copilot`，含 providers.json 位置）与 `workbuddy_home`（`WORKBUDDY_CONFIG_DIR` → `~/.workbuddy`，含 models.json 与账号级 MEMORY.md 目录）。
- **Codex 模型目录指针（修正 v1.5.1 回归）**：CCS 4.0.29 起，若 `[desktop] runCodexInWindowsSubsystemForLinux = true`，指针必须保持裸文件名（Windows 绝对路径在 WSL 里的 Codex 中会导致启动报 `os error 2`，上游 #9375）。`check --strict` 与 `repair --mode codex-catalog-path` 现在双向处理。
- **测试**：新增 schema v26 列、两个新应用的 MCP/Skills/prompts/flags、供应商编辑拒绝、WSL 目录指针正向与反向用例。

## 更新安装方法

### Codex
1. 退出 Codex。
2. 用 zip 解压出的 `CCSwitch-operations/` 替换 `~/.codex/skills/CCSwitch-operations/`。
3. 重新打开 Codex 并新开会话。

### DeepSeek Harness / 其他 SKILL.md agent
用 zip 解压出的 `CCSwitch-operations/` 替换对应 agent skills 目录下的同名文件夹。若 CC Switch 已创建链接，则刷新其技能同步并重启应用或新开会话。技能在列表中的调用名是 `ccswitch-operations`。

### CC Switch
在 CC Switch 中从 zip 导入/安装（zip 顶层为 `CCSwitch-operations/`，根目录含 `SKILL.md`），或使用 README 中的 `ccswitch://` 深链加入仓库后安装。

---

## v1.6.0 Incremental (English)

- **Compatibility baseline**: now targets CC Switch **4.0.32**, Codex 0.167 and database **schema v26**.
- **Two new managed apps**: GitHub Copilot CLI (`copilot`, 4.0.29+, schema v25 adds `enabled_copilot`) and Tencent WorkBuddy (`workbuddy`, 4.0.31+, schema v26 adds `enabled_workbuddy`). `--app-type`, `--enable-*`, `--copilot`/`--workbuddy` and `doctor` now cover all 16 apps.
- **Structured edits refused**: Copilot's `providers.json` and WorkBuddy's `models.json` are validated as whole documents by CC Switch, so `provider-block`, `provider-env`, `provider-set-key` and `repair --target provider` refuse them and point at the CC Switch UI.
- **Directory resolution**: `doctor` now prints `copilot_home` (`COPILOT_HOME` → `~/.copilot`, plus the providers.json location) and `workbuddy_home` (`WORKBUDDY_CONFIG_DIR` → `~/.workbuddy`, plus models.json and the account-scoped MEMORY.md directory).
- **Codex model-catalog pointer (fixes a v1.5.1 regression)**: since CCS 4.0.29, when `[desktop] runCodexInWindowsSubsystemForLinux = true` the pointer must stay a bare filename — a Windows absolute path makes WSL-hosted Codex fail at startup with `os error 2` (upstream #9375). `check --strict` and `repair --mode codex-catalog-path` now handle both directions.
- **Tests**: schema v26 columns, MCP/Skills/prompts/flags for both new apps, refusal of structured provider edits, and WSL catalog pointers in both directions.

### Update / Install

1. Quit the target agent.
2. Replace its existing `CCSwitch-operations/` skill folder with the one from this zip.
3. Restart the agent or start a new session. The skill is exposed as `ccswitch-operations`.
