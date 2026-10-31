# v1.5.0 增量更新

## 对齐 CC Switch 4.0.23 / schema v24

- **新增 Oh My Pi（`omp`）支持**：MCP、Skills、Prompt 和 `enabled_omp`；兼容默认/命名 profile、目录覆盖和 Skills“存在即启用”语义。
- **新增 DeepSeek Harness（`dsh`）完整供应商支持**：新增 `dsh-provider-get/set/remove`，事务式更新 web/desktop 及已存在的 headless/acp `cordis.patch.yml`、`.credentials.yaml` 和数据库行。
- **DSH 安全保护**：拒绝 profile 副本不一致、home-level `llm-pi-ai` 覆盖、flow YAML、anchors/tags；通用 provider-* 命令不会误写 DSH。
- **数据库迁移对齐**：4.0.20 升至 v23（MCP `enabled_omp`），4.0.22 升至 v24（MCP/Skills `enabled_dsh` 与内部 `parser_state`）。
- **Codex MCP 审计扩展**：`check --strict` 和 `repair --mode mcp-type` 现在清理 Codex 拒绝的 `type`、`timeout`、`autoApprove`。
- **14 应用支持**：MCP/Skills/Prompt、启用标志和 `doctor` 全部覆盖新增应用；补充 4.0.20–4.0.23 行为变化、原生供应商编辑器、Claude 多账号和路由思考档位说明。

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

## v1.5.0 Incremental (English)

- **Oh My Pi (`omp`) support**: MCP, Skills, Prompts and `enabled_omp`, including default/named profiles, directory overrides, and exists-equals-enabled skill semantics.
- **Full DeepSeek Harness (`dsh`) provider support**: new `dsh-provider-get/set/remove` commands atomically update every profile patch, `.credentials.yaml`, and the database row.
- **DSH safety**: refuses inconsistent profile copies, home-level `llm-pi-ai` shadowing, flow YAML, anchors, tags and aliases; generic provider-* commands never write DSH.
- **Schema alignment**: CC Switch 4.0.20 moved to v23 (`enabled_omp`); 4.0.22 moved to v24 (`enabled_dsh` and internal `parser_state`).
- **Codex MCP audit**: `check --strict` and `repair --mode mcp-type` now clean the Codex-invalid `type`, `timeout`, and `autoApprove` keys.
- **14-app coverage**: MCP/Skills/Prompt flags and `doctor` now cover both new apps; docs include 4.0.20–4.0.23 behavior, native provider editors, Claude multi-account support, and expanded thinking levels.

### Update / Install

1. Quit the target agent.
2. Replace its existing `CCSwitch-operations/` skill folder with the one from this zip.
3. Restart the agent, then run `doctor`, `check --strict`, and `doctor --audit`.
