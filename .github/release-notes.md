# v1.7.0 增量更新

## 安全与兼容性

- **兼容基线升级**：对齐 CC Switch **4.0.38** / Codex 0.169 / 数据库 **schema v27**（4.0.34 的 v26→v27 只加 `skills.repo_host` 与 `skill_repos.host`，老行无需回填，`NULL` 按 `github.com` 读）。
- **【安全】`repair --mode live-only` 改为 provider 专用**：此前 `--target config.toml --mode live-only` 会直接把 live 的 Codex 配置当成"混进了 live-only 段落"来清理，实测会把 `[plugins]`（含 20 个插件子表）、`[marketplaces]`、`[projects]`、`[desktop]`、`[features]`、`[memories]`、`[windows]`、`[sandbox_workspace_write]`、`[shell_environment_policy]` 共 46 个段落（7197 → 3594 字节）全部删掉——和 2026-08-23 那次配置损毁同一类破坏面。现在该组合会直接拒绝并提示改用 `repair --target provider --provider-id <id> --mode live-only`；`--target config.toml --mode both` 不受影响。
- **DSH 思考档位规范化（对齐 4.0.38 #9785）**：`dsh-provider-set` 现在按上游 `normalize_reasoning_efforts` 处理 `reasoningEfforts`——把 YAML 工具写坏的 `false` 键改回 `off`，剔除 `off/minimal/low/medium/high/xhigh/max` 之外的档位，剔除值不是 string/null 的条目，清空后删除整个键。这正是 4.0.38 修复"DeepSeek Harness 第三方供应商全部消失"的根因：一个非法键会让 DSH 判定整段供应商配置无效。
- **`check --strict` / `doctor` 新增 DSH 坏档位检测**：逐 profile 扫描 `reasoningEfforts`，报告 `false` 键、非法档位、非 string/null 值与非块式（flow）写法，`dsh-provider-set` 前会先被 preflight 拦下。两个子命令新增 `--dsh-home`。
- **不可读条目不再静默跳过（对齐 4.0.37 #9767）**：供应商 `settings_config` 或 MCP `server_config` 解析失败时，`check --strict` 会报出该行，`doctor --audit` 新增 `unreadable entries: N` 明细段，三向对比遇到坏行改为跳过并说明原因。CCS 4.0.37+ 对这些条目是"原样保留、不可编辑/启用、可单独删除、故障转移跳过"，技能现在能把这些行指出来。
- **技能仓库多站点（对齐 4.0.34）**：`skill-upsert` 新增 `--repo-host`，写入 `skills.repo_host`（v27 之前自动跳过该列）；`doctor` 输出 `skills repo_host:` 与 `skill_repos host:` 分布，缺列时提示 `column absent (pre-4.0.34 schema)`。
- **测试**：新增 8 个用例（live-only 拒绝与 provider 卡仍可用、DSH 档位规范化、坏档位检测正反例、不可读条目审计、`repo_host` 写入与 v27 之前兼容），共 89 个用例全绿。

## 文档

- 补齐 **4.0.33–4.0.38** 六版行为变化：4.0.33 的"先复制后替换"、4.0.36 的插件页矩阵（6 个应用，Codex 停用插件只改 `[plugins."<插件>@<市场>"].enabled`）与私有仓库令牌（存系统凭据管理器、不随云同步）、4.0.37 的不可读条目与小写 `[1m]`、4.0.38 的 #9785。
- 版本基线统一刷到 4.0.38 / Codex 0.169 / schema v27（`SKILL.md`、`README.md`、`README.en.md`、`references/*`）。

## 更新安装方法

### Codex
1. 退出 Codex。
2. 用 zip 解压出的 `CCSwitch-operations/` 替换 `~/.codex/skills/CCSwitch-operations/`。
3. 重新打开 Codex 并新开会话。

### DeepSeek Harness / 其他 SKILL.md agent
用 zip 解压出的 `CCSwitch-operations/` 替换对应 agent skills 目录下的同名文件夹。若 CC Switch 已创建链接，则刷新其技能同步并重启应用或新开会话。技能在列表中的调用名是 `ccswitch-operations`。

### CC Switch
在 CC Switch 中从 zip 导入/安装（zip 顶层为 `CCSwitch-operations/`，根目录含 `SKILL.md`），或使用 README 中的 `ccswitch://` 深链加入仓库后安装。

---

## v1.7.0 Incremental (English)

- **Compatibility baseline**: now targets CC Switch **4.0.38**, Codex 0.169 and database **schema v27** (the 4.0.34 v26→v27 migration only adds `skills.repo_host` and `skill_repos.host`; existing rows need no backfill and `NULL` reads as `github.com`).
- **[Safety] `repair --mode live-only` is now provider-only**: `--target config.toml --mode live-only` used to treat the live Codex config itself as "sections that leaked in from a live config" and strip them — measured on a real machine it deleted 46 sections (20 `[plugins."…"…]`, `[marketplaces]`, `[projects]`, `[desktop]`, `[features]`, `[memories]`, `[windows]`, `[sandbox_workspace_write]`, `[shell_environment_policy]`, 7197 → 3594 bytes), the same blast radius as the 2026-08-23 config-corruption incident. That combination is now refused with a pointer to `repair --target provider --provider-id <id> --mode live-only`; `--target config.toml --mode both` still works.
- **DSH reasoning-level normalization (aligns with 4.0.38 #9785)**: `dsh-provider-set` now applies the upstream `normalize_reasoning_efforts` rules — a `false` key written by a YAML tool is rewritten to `off`, levels outside `off/minimal/low/medium/high/xhigh/max` are dropped, entries whose value is not a string or null are dropped, and an empty result removes the whole key. This is the exact root cause the 4.0.38 release fixed for "every DeepSeek Harness third-party provider disappeared": one invalid key makes DSH reject the entire provider block.
- **New bad-level detection in `check --strict` / `doctor`**: every profile's `reasoningEfforts` is scanned for the `false` key, unknown levels, non-string/null values and flow-style mappings, and preflight blocks `dsh-provider-set` while they exist. Both subcommands accept `--dsh-home`.
- **Unreadable entries are no longer swallowed (aligns with 4.0.37 #9767)**: when a provider `settings_config` or MCP `server_config` fails to parse, `check --strict` reports the row and `doctor --audit` prints an `unreadable entries: N` section with per-row detail; the three-way audit skips such rows with an explanation instead of raising. CC Switch 4.0.37+ keeps these entries as-is (not editable or enableable, deletable on their own, skipped by failover) and the skill can now point them out.
- **Multi-host skill repositories (aligns with 4.0.34)**: `skill-upsert` gained `--repo-host` and writes `skills.repo_host` (skipped automatically on pre-v27 schemas); `doctor` prints the `skills repo_host:` and `skill_repos host:` distributions and reports `column absent (pre-4.0.34 schema)` when missing.
- **Tests**: 8 new cases (live-only refusal plus provider cards still working, DSH level normalization, bad-level detection in both directions, unreadable-entry audit, `repo_host` on v27 and graceful degradation before it) for a total of 89 green tests.

### Documentation

- Adds the full **4.0.33–4.0.38** behavior changes: 4.0.33's copy-then-replace skill updates, 4.0.36's Plugins page matrix (6 apps; disabling a Codex plugin only flips `[plugins."<plugin>@<marketplace>"]` `enabled`) and private skill repositories (tokens in the OS credential manager, never part of cloud sync), 4.0.37's unreadable entries and lowercase `[1m]`, and 4.0.38's #9785.
- Version baselines bumped to 4.0.38 / Codex 0.169 / schema v27 across `SKILL.md`, `README.md`, `README.en.md` and `references/*`.

### Update / Install

1. Quit the target agent.
2. Replace its existing `CCSwitch-operations/` skill folder with the one from this zip.
3. Restart the agent or start a new session. The skill is exposed as `ccswitch-operations`.
