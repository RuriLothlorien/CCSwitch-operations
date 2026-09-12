# v1.1.5 增量更新

## 对齐 CC Switch 3.20.3（2026-09-11）

- **基线升级**：以 CC Switch **3.20.3** 为验证基线（schema 仍为 v18，**本版无数据库迁移**）；3.20.1–3.20.2（schema v18）与 3.20.0（schema v17）继续兼容。
- **修复 `repair --mode codex-0149` 的迁移产物**：此前迁移顶层 `openai_base_url` 时只建表，没有改写 `model_provider`、也没有写 `wire_api`，迁移出的表实际不参与路由（`check --strict` 还会误报已修好）。现在迁移结果与 CC Switch 3.20.3 自身的规范化完全一致：`model_provider = <新 id>` + `[model_providers.cc-switch(-N)]`（`name` / `base_url` / `wire_api = "responses"` / `experimental_bearer_token`）。用户已存在的 `cc-switch` 表不会被覆盖，顺延 `cc-switch-2`…；活跃路由的保留表改名后，`model_provider` 会跟着改名。
- **收敛 `check --strict` 的误报**：顶层 `openai_base_url` 只在该键真正改路由（选择器缺省或 `openai`）时报告；选择器指向自带表的惰性残留不再误报，也不会被错误迁移。
- **补上 `check --strict` 的漏报**：`model_provider` 指向缺失的 `[model_providers.<id>]` 表会被点名——该形态下顶层 token 不被 Codex 0.149 读取，路由会回落到内置 openai/auth.json。
- **识别内联 `model_providers = { ... }`**：不再被误判为“空第三方卡”；单行内联表可就地完成迁移，多行内联表只提示、不写坏 TOML。
- **3.20.3 升级要点已写入文档**：Codex 缺 `model_provider` 的卡在接管时改走本地代理；统一供应商同步不再清空子卡设置（旧版已清掉的用量脚本/通用配置勾选/端点自动选择/排序需重填一次，可用 `common-config status` 复核）；每应用代理重试/超时串写已停止但旧值不恢复；Kimi 两条 Codex 预设改原生 Responses；DeepSeek `deepseek-flash` 目录新增视觉支持（切走再切回生效）；Claude Code 新增“禁用 Artifact 工具”开关。**#6719 编辑页缺陷在 3.20.3 仍未修复**，警告覆盖 3.20.0–3.20.3。

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

## v1.1.5 Incremental (English)

- Aligned with **CC Switch 3.20.3** (schema stays v18; no database migration); 3.20.1–3.20.2 (v18) and 3.20.0 (v17) remain compatible.
- **Fixed the `repair --mode codex-0149` migration output**: it used to create the table without rewriting `model_provider` or writing `wire_api`, so the migrated table never carried the route (`check --strict` even reported the config as clean). The result now matches CC Switch 3.20.3's own normalization: `model_provider = <new id>` plus `[model_providers.cc-switch(-N)]` with `name`, `base_url`, `wire_api = "responses"` and `experimental_bearer_token`. An existing user-authored `cc-switch` table is preserved (the next free `cc-switch-2`… id is used), and a renamed reserved table follows with `model_provider`.
- **Fewer false positives in `check --strict`**: a top-level `openai_base_url` is only reported when it actually reroutes (selector absent or `openai`); inert leftovers on custom-routed cards are left alone.
- **New detection in `check --strict`**: a `model_provider` selector whose `[model_providers.<id>]` table is missing is flagged — top-level tokens are ignored by Codex 0.149 there, so the route falls back to the built-in openai/auth.json path.
- **Inline `model_providers = { ... }` is recognized**: no more "empty third-party card" false positive; single-line inline tables are migrated in place, multi-line ones are reported instead of producing broken TOML.
- **3.20.3 upgrade notes are documented**: cards without `model_provider` route through the local proxy under takeover; universal-provider sync keeps child settings, but anything an earlier sync erased must be re-entered (check `common-config status`); the per-app proxy retry/timeout cross-write is stopped but old values are not restored; Kimi's two Codex presets moved to native Responses; DeepSeek's `deepseek-flash` catalog entry gained vision (switch away and back); Claude Code has a new "disable Artifact tool" toggle. **#6719 is still unfixed in 3.20.3**, so the warning now covers 3.20.0–3.20.3.

### Update / Install

1. Quit Codex.
2. Replace the `CCSwitch-operations/` folder in your agent's skills directory with the one from this zip (e.g. `~/.codex/skills/CCSwitch-operations/`).
3. Restart the agent, then run `check --strict` and `doctor --audit`.
