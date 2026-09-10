# v1.1.4 增量更新

## 对齐 CC Switch 3.20.2（2026-09-07）

- **基线升级**：以 CC Switch **3.20.2** 为验证基线（schema v18；**本版无数据库迁移**）；3.20.1（schema v18）与 3.20.0（schema v17）继续兼容。
- **`requires_openai_auth` 新矩阵**：代理托管 OAuth 卡（`providers.meta.provider_type` = `xai_oauth` / `github_copilot`）的活跃表必须为 `false`（令牌由本地代理逐请求注入），**Codex OAuth 例外**（官方登录即其凭据）。
  - `check --strict` 不再把这类卡误报为 “switch will be refused”，改为点名错误的标志值；
  - `repair --target provider --mode codex-0149 --apply` 会提前把该标志改成 `false`（与 CCS 3.20.2“下次切换自愈”一致）；普通无凭据卡仍只提示、不自动改；
  - 顺带修复：`provider-block --check-semantics` 不再把官方卡误判为“空第三方卡”。
- **桌面版 `auth.json` 警告更新**：3.20.2 只修了**接管**路径（接管按 Codex 观察到的登录状态覆盖该标志）；**直切**第三方在“保留官方登录”关闭时仍会删除 `auth.json` → 桌面版继续保留 `auth.json` 并打开 `preserveCodexOfficialAuthOnSwitch=true`。
- **catalog 修复需“切走再切回”**：DeepSeek 的 MCP 可见性（`supports_search_tool=false`）、`supports_parallel_tool_calls` 回填、未知型号视觉模态、`glm-5.3` 纯文本均在切换供应商重建 catalog 后才生效。
- **预设改动只影响新建卡**：智谱 GLM 改指官方 Responses 端点 `/api/v1`（存量卡需重新导入）；`grok-4.5` 的 `xhigh`、腾讯 Pi 思考控制、`minimax-m2.5` 移除同理；PPIO / JieKou / Novita 的模型列表地址按卡片 Base URL 反查，存量卡免改。
- **#6719 仍未修复**：编辑页零改动保存破坏 Codex 配置的缺陷不在 3.20.2 修复列表内，警告对 3.20.0–3.20.2 继续有效。
- 回归测试：新增 3 条用例（代理 OAuth 标志检测/修复、普通卡不改标志、官方卡 `--check-semantics` 不误报），共 **42** 条全部通过。

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

## v1.1.4 Incremental (English)

- Aligned with **CC Switch 3.20.2** (schema v18; no database migration in this release); 3.20.1 (v18) and 3.20.0 (v17) remain compatible.
- **`requires_openai_auth` matrix**: proxy-managed OAuth cards (`meta.provider_type` = `xai_oauth` / `github_copilot`) must use `false` — the local proxy injects the token per request; Codex OAuth is excluded because the official login is its credential. `check --strict` now names the wrong value instead of reporting "no own credentials", and `repair --mode codex-0149 --apply` fixes it early. `provider-block --check-semantics` no longer misjudges official cards as empty third-party cards.
- **Desktop `auth.json` warning updated**: 3.20.2 fixed only the takeover path; a direct third-party switch still deletes `auth.json`, so keep the file and enable “Preserve official Codex auth on switch”.
- **Catalog fixes apply after switching away and back**: DeepSeek MCP visibility, `supports_parallel_tool_calls` backfill, vision modality, `glm-5.3` plain text.
- **Preset changes only affect newly created providers** — re-import the GLM preset to get the official Responses endpoint `/api/v1`; PPIO / JieKou / Novita model-list URLs are resolved from the card's base URL, so existing cards need no change.
- **#6719** (edit-page config mangling) is still not in the 3.20.2 fix list.

### Update / Install

1. Quit Codex.
2. Replace the `CCSwitch-operations/` folder in your agent's skills directory with the one from this zip (e.g. `~/.codex/skills/CCSwitch-operations/`).
3. Restart the agent, then run `check --strict` and `doctor --audit`.
