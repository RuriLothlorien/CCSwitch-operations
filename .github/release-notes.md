# v1.5.2 增量更新

## 对齐 CC Switch 4.0.28 / Codex 0.167 / schema v24

- **Codex 0.167 废弃键修复**：`check --strict` 检测 `disable_response_storage`；新增 `repair --mode codex-0167`，支持 live 配置和 provider 卡。
- **4.0.28 本地路由识别**：路由模式合法的内置 `openai` + 本地 `openai_base_url` 不再被当作旧误路由，`codex-0149` 会识别并保持不变。
- **Codex 会话诊断**：`doctor` 显示统一历史、旧会话迁移、暂停官方登录和额度保护有效状态；direct + split 会提示异组会话只读风险。
- **模式冲突提示**：`codexProxyWithoutOfficialLogin` 在 direct 模式开启时明确提示无效；额度保护迁移未落盘时显示 `pending default-on`。
- **文档更新**：补充 4.0.28 会话分桶、路由契约、官方登录暂停、额度保护迁移和 Codex 0.167 配置移除。

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

## v1.5.2 Incremental (English)

- **Codex 0.167 obsolete-key repair**: `check --strict` detects `disable_response_storage`; the new `repair --mode codex-0167` cleans live config and provider cards.
- **4.0.28 local-route recognition**: the valid route-mode shape with the built-in `openai` provider and a local `openai_base_url` is preserved rather than mistaken for a legacy misroute.
- **Codex session diagnostics**: `doctor` shows unified-history, legacy-migration, pause-official-login and effective quota-protection state, and warns that direct + split makes the inactive session group read-only.
- **Mode conflict warnings**: `codexProxyWithoutOfficialLogin` in direct mode is reported as ineffective; quota protection appears as `pending default-on` until its one-time migration is persisted.
- **Documentation**: covers 4.0.28 session buckets, route contracts, official-login pause, quota migration and Codex 0.167 config removal.

### Update / Install

1. Quit the target agent.
2. Replace its existing `CCSwitch-operations/` skill folder with the one from this zip.
3. Restart the agent, then run `doctor`, `check --strict`, and `doctor --audit`.
