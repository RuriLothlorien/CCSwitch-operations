# v1.5.1 增量更新

## 对齐 CC Switch 4.0.27 / schema v24

- **DSH 对齐 4.0.24/4.0.26**：模型输入只保留 `text`/`image`；解析 `settings.json:dshConfigDir`（含 WSL 路径）；已有 headless profile 在需要时恢复 credentials store。
- **软链接安全写入（4.0.27）**：原子写入会更新链接目标，不再把配置文件软链接替换成普通文件，也避免 Windows 原子替换报错。
- **Skill 哈希对齐（4.0.27）**：`skill-upsert` 改为完整目录哈希，忽略隐藏文件、`__pycache__/` 和 `*.pyc`，运行 Skill 不再制造“可更新”假阳性。
- **Codex 结构审计增强**：检测 provider card 中违规的 `[agents].max_threads`；检测原生配置目录中的相对 `model_catalog_json`，新增 `repair --mode codex-catalog-path`。
- **文档更新**：补充 4.0.24–4.0.27 的 MCP 连通性、本地路由来源限制、DSH 目录/凭据、Codex Fast 与全局设置行为。

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

## v1.5.1 Incremental (English)

- **DSH aligned with 4.0.24/4.0.26**: model inputs are limited to `text`/`image`, `settings.json:dshConfigDir` (including WSL paths) is honored, and existing headless profiles restore the managed credentials store when needed.
- **Symlink-safe writes (4.0.27)**: atomic writes update the link target instead of replacing a config symlink with a regular file or failing on Windows.
- **Skill hash alignment (4.0.27)**: `skill-upsert` now hashes the complete directory while ignoring hidden files, `__pycache__/`, and `*.pyc`, preventing false update detection after running a skill.
- **Codex audit improvements**: detects provider-card misuse of `[agents].max_threads` and relative `model_catalog_json` pointers in native config dirs; adds `repair --mode codex-catalog-path`.
- **Documentation**: covers 4.0.24–4.0.27 MCP connectivity, local-router origin protection, DSH directory/credentials behavior, Codex Fast, and global settings.

### Update / Install

1. Quit the target agent.
2. Replace its existing `CCSwitch-operations/` skill folder with the one from this zip.
3. Restart the agent, then run `doctor`, `check --strict`, and `doctor --audit`.
