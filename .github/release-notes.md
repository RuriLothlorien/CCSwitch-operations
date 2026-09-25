# v1.2.0 增量更新

## 对齐 CC Switch 3.20.4（2026-09-22）

- **基线升级**：以 CC Switch **3.20.4** 为验证基线（数据库 schema **v19**）。3.20.4 首次启动执行 v18 → v19 迁移（`mcp_servers` 与 `skills` 各新增 `enabled_mcode`）；3.20.1–3.20.3（v18）与 3.20.0（v17）继续兼容，但迁移后旧版 CCS 会拒绝打开数据库，升级前请保留一份备份。mcode 相关命令需要 3.20.4+。
- **新增第十个受管应用 MiniMax Code（`mcode`）**：`prompt-set --app-type mcode`（单条提示词 ≤32 KiB，超限直接拒绝）、`mcp-upsert --enable-mcode`、`skill-upsert --enable-mcode`、`set-flags --mcode 1`，`doctor` 会列出 mcode 供应商。mcode 的供应商是 `~/.minimax/config.yaml` 里的 YAML `custom_provider`，`provider-block` / `provider-env` / `provider-set-key` 会明确拒绝并提示改用 CCS 界面，避免写坏结构。
- **新增 Codex 密钥恢复**：针对 3.20.4 修复的 #7434（编辑或切走供应商会清空已保存的 API Key，且旧值不会自动恢复）。`check --strict` / `doctor --audit` 会点名“auth 为空但 provider 表仍有 token”的可恢复形态；`repair --target provider --mode codex-key [--apply]` 从 provider 表回填 `auth.OPENAI_API_KEY`（默认 dry-run，apply 时自动备份；官方卡与代理托管 OAuth 卡按设计跳过）。
- **向 v18 老库兼容**：helper 会探测数据库实际存在的 `enabled_*` 列，v18 数据库（没有 `enabled_mcode`）上所有命令照常工作；对缺少 mcode 列的老库，`set-flags --mcode` 会明确报错而不是写入失败。
- **标志语义提示**：`mcp-upsert` / `skill-upsert` 的 `--enable-*` 是全量标志集——当这次更新会关掉原本启用的应用时，工具会打印警告并提示用 `set-flags` 单独切换（第十个应用加入后更容易踩到）。
- **文档更新**：`SKILL.md`、README（中英）与 `references/*` 全部对齐 3.20.4：schema v19、MiniMax Code 边界与数据目录、密钥恢复、3.20.4 升级复核清单，#6719 警告覆盖 3.20.0–3.20.4。

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

## v1.2.0 Incremental (English)

- Aligned with **CC Switch 3.20.4** (database schema **v19**). 3.20.4 migrates v18 → v19 on first start (`mcp_servers` and `skills` gain `enabled_mcode`); 3.20.1–3.20.3 (v18) and 3.20.0 (v17) remain compatible, but older CCS versions refuse to open the migrated database — keep a backup before upgrading. mcode commands need 3.20.4+.
- **Tenth managed app: MiniMax Code (`mcode`)**: `prompt-set --app-type mcode` (prompts capped at 32 KiB), `mcp-upsert --enable-mcode`, `skill-upsert --enable-mcode`, `set-flags --mcode 1`, and `doctor` lists mcode providers. mcode providers live in `~/.minimax/config.yaml` as YAML `custom_provider` entries — `provider-block` / `provider-env` / `provider-set-key` refuse them with guidance instead of writing a shape CCS cannot read.
- **New Codex key recovery**: covers #7434, fixed in 3.20.4 (editing or switching a provider used to wipe the saved API key, and lost keys are not restored automatically). `check --strict` / `doctor --audit` report the recoverable shape ("auth empty while the provider table still carries a token"), and `repair --target provider --mode codex-key [--apply]` restores `auth.OPENAI_API_KEY` from the provider table (dry-run by default, backup on apply; official and proxy-managed OAuth cards are skipped by design).
- **Backward compatible with v18 databases**: the helper detects which `enabled_*` columns exist, so every command keeps working on a v18 database without `enabled_mcode`; `set-flags --mcode` reports the missing column instead of failing mid-write.
- **Clearer flag semantics**: `mcp-upsert` / `skill-upsert` set the whole `--enable-*` flag set — the tool now warns when an update would disable an app that was enabled before and points to `set-flags` for single-app toggles (easier to hit with a tenth app).
- **Docs updated**: `SKILL.md`, both READMEs and `references/*` now cover 3.20.4 (schema v19, MiniMax Code boundaries and data dir, key recovery, the 3.20.4 upgrade checklist, and the #6719 warning extended to 3.20.0–3.20.4).

### Update / Install

1. Quit Codex.
2. Replace the `CCSwitch-operations/` folder in your agent's skills directory with the one from this zip (e.g. `~/.codex/skills/CCSwitch-operations/`).
3. Restart the agent, then run `check --strict` and `doctor --audit`.
