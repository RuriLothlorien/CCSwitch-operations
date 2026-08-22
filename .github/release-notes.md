# v1.1.1 增量更新

## 新增能力（相对 v1.1.0）

- 顶层键顺序异常检测与修复：`check --strict` 检测 `notify = [...]` 等顶层键被挪进 `[table]` 内部；`repair --mode header-order --apply` 自动移回 preamble（所有 `[table]` 之前）
- 文档补充：README / SKILL / pitfalls 增加“CCS 3.20.0 可能误操作配置”的痛点，以及 `[plugins]` / `[marketplaces]` / `[mcp_servers.node_repl(.env)]` / `notify =` 等具体表头/键级现象与对策

## 更新安装方法

### Codex
1. 退出 Codex
2. 用本 zip 解压出的 `CCSwitch-operations/` **替换** `~/.codex/skills/CCSwitch-operations/`（直接覆盖旧版）
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

## v1.1.1 Incremental (English)

- New: `check --strict` detects top-level keys (e.g. `notify = [...]`) misplaced inside `[table]` blocks; `repair --mode header-order --apply` moves them back to the preamble
- Docs: README / SKILL / pitfalls now cover the "CCS 3.20.0 may misoperate your config" pain point and concrete symptoms (`[plugins]`, `[marketplaces]`, `[mcp_servers.node_repl(.env)]`, `notify =`)

### Update / Install

1. Quit Codex.
2. Replace the `CCSwitch-operations/` folder in your agent's skills directory with the one from this zip (e.g. `~/.codex/skills/CCSwitch-operations/`).
3. Restart the agent, then run `check --strict` and `doctor --audit`.
