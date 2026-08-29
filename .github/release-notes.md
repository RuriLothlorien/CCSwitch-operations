# v1.1.3 增量更新

## 新增能力（相对 v1.1.2）

- 对齐 **CC Switch 3.20.1（schema v18）**：`doctor` 可识别 v18；兼容基线更新（3.20.0 = v17 仍兼容）
- 新增 **Codex 0.149 config-only 兼容检测与修复**：
  - `check --strict` 检测 0.149 拒绝形态（遗留 `[model_providers.openai|ollama|lmstudio]`、缺 `name`、顶层 `openai_base_url`、空第三方卡、`requires_openai_auth=true` 无凭据）
  - `repair --mode codex-0149` 自动迁移可修形态（改名保留表、回填 `name`、迁移 `openai_base_url`+密钥到 `[model_providers.cc-switch]`）
- 文档更新：3.20.1 迁移说明（v17→v18、config-only 切换、`auth.json` 语义与保留开关）、#6719 在 3.20.1 仍未修复的警告保留

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

## v1.1.3 Incremental (English)

- Aligned with CC Switch 3.20.1 (schema v18; 3.20.0/v17 still compatible)
- New Codex 0.149 config-only compatibility: `check --strict` detects rejected shapes; `repair --mode codex-0149` migrates fixable ones
- Docs: v17→v18 migration, config-only switching, `auth.json` semantics; #6719 warning kept (not fixed in 3.20.1)

### Update / Install

1. Quit Codex.
2. Replace the `CCSwitch-operations/` folder in your agent's skills directory with the one from this zip (e.g. `~/.codex/skills/CCSwitch-operations/`).
3. Restart the agent, then run `check --strict` and `doctor --audit`.
