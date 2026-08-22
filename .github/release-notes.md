# v1.1.0 增量更新

## 新增能力（相对 v1.0.0）

- 结构安全审计：`check --strict`（空命令/缺失命令的 stdio MCP、url-only MCP 误写、标记配对、表头乱序/越权、live-only 混入）
- 三处一致性审计：`doctor --audit`（面板 MCP ↔ 供应商配置 ↔ config.toml）、`doctor --compare-backup`
- 写操作主动预检：配置已损坏时自动拒绝写入（`--force` 可显式跳过）
- 快照与对比：`snapshot` / `diff`
- 修复工具：`repair`（表头顺序 / live-only，默认 dry-run，`--apply` 写入并自动备份）
- 通用配置维护：`common-config get/check/status/set/set-key/remove-key/extract/enable/disable`（幂等审查、提取自动打勾；仅支持 codex/claude/gemini，其余 agent 自动忽略）
- `provider-block --check-semantics`
- 已知上游缺陷警示：CCS 3.20.0 编辑页“零改动保存”会破坏 Codex 配置，已在 README/SKILL 中明确并建议使用本技能

## 修复 / 改进

- 修复 `common-config set-key` 在 snippet 无 preamble 时无法新增顶层 key
- `check --strict` 增加 stdio MCP 缺失 command 检测
- `doctor` 默认输出结构健康摘要
- `repair` 改为最小修复：合法布局零改动
- 对不支持通用配置的 agent 直接忽略，保证兼容

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

## v1.1.0 Incremental (English)

- Structural safety: `check --strict`, `doctor --audit`, proactive write preflight, `snapshot` / `diff`, `repair` (dry-run + `--apply`)
- Common-config maintenance: `common-config ...` with idempotence checks (codex/claude/gemini only; other agents ignored)
- `provider-block --check-semantics`
- Fixes: `set-key` without preamble, stdio missing-command detection, `doctor` health summary, minimal repair

### Update / Install

1. Quit Codex.
2. Replace the `CCSwitch-operations/` folder in your agent's skills directory with the one from this zip (e.g. `~/.codex/skills/CCSwitch-operations/`).
3. Restart the agent, then run `check --strict` and `doctor --audit`.
