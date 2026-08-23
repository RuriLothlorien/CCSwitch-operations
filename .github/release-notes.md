# v1.1.2 增量更新

## 新增能力（相对 v1.1.1）

- 新增 `provider-set-key`：安全设置/删除 provider 配置的顶层或段内键（TOML 字面量），自动 preflight 与 TOML 校验，替代手写临时脚本直改 DB
- 铁律更新：不确定时先认真读本技能（SKILL.md 与 references/），不得自由发挥；“同步”必须先确认对象（配置 / 技能 / 模板）再行动
- 配置同步语义：未明确范围时默认 provider-first（`provider-set-key`），改完后询问是否提取到通用配置模板（`common-config extract`）；只有用户明示“通用配置 / common-config / 模板”才直接操作 snippet
- 同步对象识别：由 AI 自行判断识别变更对象（配置 / 技能 / 模板），没有问题不轻易问用户；识别范围含配置时落到配置变更铁律（provider-first + 提取询问 + 安全流程）
- 文档同步：operations / SKILL / pitfalls 补充上述规则与命令

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

## v1.1.2 Incremental (English)

- New `provider-set-key`: safely set/remove top-level or dotted keys in a provider's config TOML (with preflight + TOML validation)
- Iron rules: read the skill first when unsure; "sync" requires confirming the object (config / skill / template) before acting
- Config sync semantics: provider-first by default (`provider-set-key`), then ask whether to `common-config extract`; only touch the snippet when the user explicitly mentions "common config" / "模板"
- Sync object is inferred by the AI (config / skill / template) from context; don't ask unless truly unresolvable; if config is in scope, apply the config-change iron rules (provider-first + extract question + safety flow)

### Update / Install

1. Quit Codex.
2. Replace the `CCSwitch-operations/` folder in your agent's skills directory with the one from this zip (e.g. `~/.codex/skills/CCSwitch-operations/`).
3. Restart the agent, then run `check --strict` and `doctor --audit`.
