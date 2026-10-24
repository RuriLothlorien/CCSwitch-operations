# v1.4.0 增量更新

## 对齐 CC Switch 4.0.19 / schema v22

- **新增 Kimi Code（`kimi`）支持**：可用于 MCP、Skills、Prompt 和对应启用标志；支持 `KIMI_CODE_HOME`、多供应商共存、`~/.kimi-code/mcp.json`、`~/.kimi-code/skills` 与 `~/.kimi-code/AGENTS.md`。
- **新增 Antigravity CLI（`agy`）支持**：可用于 MCP、Skills、Prompt 和 `enabled_agy`；MCP/Skills/Prompt 同步到共享的 `~/.gemini/config`，MCP 支持 stdio/HTTP，不支持 SSE。
- **数据库迁移对齐**：4.0.18 从 schema v20 升到 v21（`enabled_agy`），4.0.19 升到 v22（`enabled_kimi`）；迁移后旧版 CCS 会拒绝打开数据库。
- **供应商安全边界**：Kimi 的结构化 `{provider, models}`、Agy 的启动终端供应商以及 mcode 的 YAML 供应商不会被 provider-* 命令误写；工具会明确拒绝并提示使用 CCS UI/卡片。
- **`doctor` 增强**：显示 12 个受管应用、每个应用的 provider 数量、MCP/Skills 新标志列是否可用，以及原有模式、JSON 和 Codex auth 安全告警。
- **文档与示例**：更新中英 README、12 应用矩阵、架构、操作模板、迁移说明和已知坑，覆盖 4.0.16–4.0.19 的相关行为变化。

## 更新安装方法

### Codex
1. 退出 Codex
2. 用 zip 解压出的 `CCSwitch-operations/` 替换 `~/.codex/skills/CCSwitch-operations/`
3. 重新打开 Codex 并新开会话

### Claude Code / 其他 SKILL.md agent
用 zip 解压出的 `CCSwitch-operations/` 替换对应 agent skills 目录下的同名文件夹。

### CC Switch
在 CC Switch 中从 zip 导入/安装（zip 顶层为 `CCSwitch-operations/`，根目录含 `SKILL.md`），或使用 README 中的 `ccswitch://` 深链加入仓库后安装。

### 升级后建议
```bash
python scripts/ccs_db.py doctor
python scripts/ccs_db.py check --strict
python scripts/ccs_db.py doctor --audit
```

---

## v1.4.0 Incremental (English)

- **Kimi Code (`kimi`) support**: MCP, Skills, Prompts and enable flags; supports `KIMI_CODE_HOME`, additive providers, `~/.kimi-code/mcp.json`, `~/.kimi-code/skills`, and `~/.kimi-code/AGENTS.md`.
- **Antigravity CLI (`agy`) support**: MCP, Skills, Prompts and `enabled_agy`; shared customizations live under `~/.gemini/config`; MCP supports stdio/HTTP but not SSE.
- **Schema alignment**: CC Switch 4.0.18 moved schema v20 to v21 (`enabled_agy`), and 4.0.19 moved v21 to v22 (`enabled_kimi`). Older CCS releases cannot open the migrated database.
- **Provider safety boundaries**: Kimi's structured `{provider, models}`, Agy's terminal-launch cards, and mcode's YAML provider shape are refused by provider-* commands instead of being written in an incompatible format.
- **`doctor` improvements**: reports all 12 managed apps, provider counts, availability of the new MCP/Skills flags, plus the existing mode/JSON/Codex-auth health warnings.
- **Documentation**: updated READMEs, the 12-app matrix, architecture, operations, migration history, and pitfalls for the relevant 4.0.16–4.0.19 changes.

### Update / Install

1. Quit the target agent.
2. Replace its existing `CCSwitch-operations/` skill folder with the one from this zip.
3. Restart the agent, then run `doctor`, `check --strict`, and `doctor --audit`.
