# v1.3.1 增量更新

## 对齐 CC Switch 4.0.15

- **quoted provider 表头修复**：CC Switch 4.0.13+ 接受 `[model_providers."custom"]`、带空格以及单引号表头。技能现在先解码 TOML 表头键再审计/修复，不再把缺失的 `name` 回填成非法的 `name = ""custom""`；`repair --mode codex-0149` 生成的配置会通过 `tomllib` 校验。
- **`doctor` 模式显示修正**：`live-state.json` 的内部值 `proxy` 现在按 CCS 用户界面映射为 `route`；Claude Desktop 的聚合状态显示为 `stack`。
- **主动健康告警**：`doctor` 会提示损坏的 `settings.json` / `live-state.json`，并在 `preserveCodexOfficialAuthOnSwitch` 未开启时提醒 Codex 桌面版可能因为缺少 `auth.json` 回到登录页。
- **快照完整性**：`snapshot` 和 `diff` 现在包含设备本地 `live-state.json`，可一起核对模式与聚合成员状态。
- **4.0.15 文档对齐**：聚合支持 Claude Code、Codex 和 Claude Desktop（4.0.13+）；Codex 子代理兼容开关更新为 `codexStackClassicTools`；补充 4.0.9–4.0.15 的深链、本地供应商、应用管理、`settings.json` 原子写入等行为变化。
- **兼容基线**：CC Switch **4.0.15 / schema v20**；4.0.9–4.0.15 无数据库迁移，旧版 3.20.x 数据库仍按原规则读取。

## 更新安装方法

### Codex
1. 退出 Codex
2. 用 zip 解压出的 `CCSwitch-operations/` 替换 `~/.codex/skills/CCSwitch-operations/`（直接覆盖旧版）
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

## v1.3.1 Incremental (English)

- **Quoted provider headers fixed**: CC Switch 4.0.13+ accepts `[model_providers."custom"]`, spaced keys, and single-quoted headers. The skill now decodes TOML key parts before auditing/repairing, so a missing `name` is never emitted as invalid `name = ""custom""`; `repair --mode codex-0149` output is validated with `tomllib`.
- **Correct user-facing modes**: `doctor` maps the internal `live-state.json` value `proxy` to `route`, and reports Claude Desktop aggregation as `stack`.
- **Proactive health warnings**: `doctor` flags malformed `settings.json` / `live-state.json` and warns when `preserveCodexOfficialAuthOnSwitch` is off, which can leave Codex desktop at the login screen after a third-party switch.
- **Complete snapshots**: `snapshot` and `diff` now include the device-local `live-state.json`, covering mode and aggregation-member state.
- **Aligned with 4.0.15**: stack/aggregation covers Claude Code, Codex, and Claude Desktop (4.0.13+); the Codex sub-agent compatibility key is now `codexStackClassicTools`; docs cover deep-link/import, local providers, app management, and atomic `settings.json` writes from 4.0.9–4.0.15.
- **Compatibility baseline**: CC Switch **4.0.15 / schema v20**. Releases 4.0.9–4.0.15 made no database migration; legacy 3.20.x databases remain readable under the documented rules.

### Update / Install

1. Quit the target agent.
2. Replace its existing `CCSwitch-operations/` skill folder with the one from this zip (for Codex, `~/.codex/skills/CCSwitch-operations/`).
3. Restart the agent, then run `check --strict` and `doctor --audit`.
