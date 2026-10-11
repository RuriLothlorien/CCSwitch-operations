# v1.3.0 增量更新

## 对齐 CC Switch 4.0.8（含 4.0.4 正式版重写，2026-10-06 ~ 10-10）

- **基线升级**：以 **CC Switch 4.0.8 / schema v20** 为验证基线；3.20.4（v19）、3.20.1–3.20.3（v18）、3.20.0（v17）仍可读取，但 v19→v20 迁移后旧版 CCS 会拒绝打开数据库（升级前保留自动备份）。mcode 命令需 3.20.4+，Pi MCP（`--enable-pi`）需 4.0+。
- **#6719 已修复**：4.0.4 重写配置写入——只替换地址/Key/模型等关键字段，零改动保存与保存前逐字节一致，url-only MCP 不再写成空 `command`，Codex 的 `[mcp_servers.*]` 不再写 `type`。文档里的“不要用编辑页”警告改为“3.20.0–3.20.3 受影响，4.0.4+ 已修复”；**已损坏的存量条目不会自动修**，可面板关/开重写或用本技能修复。
- **`common-config` 在 v20 上全量拒绝**：CCS 4.0 移除了通用配置片段。schema ≥ v20 上所有 `common-config` 子命令（含只读）都会明确拒绝并提示新做法——共享键写客户端 live 配置，供应商专属字段写卡片（`provider-block` / `provider-set-key` / `provider-env`）；写前 preflight 与审计不再检查惰性 snippet。
- **新增 Pi MCP 支持**：`mcp-upsert --enable-pi`、`set-flags --table mcp_servers --pi 1`；老库（没有 `enabled_pi` 列）会给出明确警告而不是静默丢弃；skills 的 `--enable-pi` 会说明 Pi 技能是“存在即启用”。
- **新增 MCP `type` 存量检测与修复**：Codex 0.158+ 拒绝 `[mcp_servers.*]` 里的 `type`；`check --strict` 审计 live config（schema ≤ v19 时也审计供应商卡片），`repair --target config.toml|provider --mode mcp-type [--apply]` 清理。
- **doctor 增强**：打印 schema、`common-config` 是否已移除、以及各应用当前模式（读取设备本地 `~/.cc-switch/live-state.json`：直连 / 路由 / 聚合）。
- **文档**：全面对齐 4.0——三种模式与聚合限制、配置归属变化、Codex 会话压缩、GitHub Copilot 账号、Pi MCP、被移除的设置、时间 MCP 预设改 `uvx`、升级复核清单；`references/migration.md` 新增 4.0 章节。

## 更新安装方法

### Codex
1. 退出 Codex
2. 用本 zip 解压出的 `CCSwitch-operations/` 替换 `~/.codex/skills/CCSwitch-operations/`（直接覆盖旧版）
3. 重新打开 Codex 并新开会话

### Claude Code / 其他 SKILL.md agent
用 zip 解压出的 `CCSwitch-operations/` 替换对应 agent skills 目录下的同名文件夹。

### CC Switch
在 CC Switch 中从 zip 导入/安装（zip 顶层为 `CCSwitch-operations/`，根目录含 `SKILL.md`），或使用 README 中的 `ccswitch://` 深链加入仓库后安装。

### 升级后建议
```bash
python scripts/ccs_db.py snapshot
python scripts/ccs_db.py check --strict
python scripts/ccs_db.py doctor --audit
```

---

## v1.3.0 Incremental (English)

- Aligned with **CC Switch 4.0.8 / schema v20**; 3.20.4 (v19), 3.20.1–3.20.3 (v18) and 3.20.0 (v17) remain readable, but after the v19 → v20 migration older CCS versions refuse the database (keep the automatic backup). mcode needs 3.20.4+, Pi MCP (`--enable-pi`) needs 4.0+.
- **#6719 is fixed**: 4.0.4 rewrote config writing to key-field replacement (zero-change saves are byte-identical; url-only MCPs no longer get an empty `command`; Codex `[mcp_servers.*]` no longer gets `type`). The docs now say "3.20.0–3.20.3 affected, fixed in 4.0.4"; **already-damaged entries are not auto-fixed** — re-sync in the MCP panel or use this skill's repairs.
- **`common-config` is refused on v20**: CCS 4.0 removed the common-config snippet. Every `common-config` subcommand (including read-only ones) now refuses with guidance — shared keys belong in the client live config, provider-specific fields in the card (`provider-block` / `provider-set-key` / `provider-env`); preflight and audits skip the inert snippet.
- **Pi MCP support**: `mcp-upsert --enable-pi`, `set-flags --table mcp_servers --pi 1`; older databases (no `enabled_pi` column) get a clear warning instead of a silent drop; `--enable-pi` on skills explains that Pi skills are enabled by existence.
- **MCP `type` detection and repair**: Codex 0.158+ rejects `type` inside `[mcp_servers.*]`; `check --strict` audits the live config (and provider cards on schema ≤ v19) and `repair --target config.toml|provider --mode mcp-type [--apply]` cleans it.
- **doctor improvements**: prints the schema, whether common-config has been removed, and each app's current mode (read from the device-local `~/.cc-switch/live-state.json`: direct / route / stack).
- **Docs**: fully aligned with 4.0 — the three modes and stack limitations, config ownership changes, Codex session compression, GitHub Copilot on Codex, Pi MCP, removed settings, the `uvx` time-MCP change, and a 4.0 upgrade checklist; `references/migration.md` has a new 4.0 section.

### Update / Install

1. Quit Codex.
2. Replace the `CCSwitch-operations/` folder in your agent's skills directory with the one from this zip (e.g. `~/.codex/skills/CCSwitch-operations/`).
3. Restart the agent, then run `check --strict` and `doctor --audit`.
