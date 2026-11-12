# v1.5.3 增量更新

## 兼容性修复

- **兼容基线不变**：继续支持并对齐 CC Switch 4.0.28 / Codex 0.167 / schema v24。
- **DSH 技能加载**：技术名称改为小写 kebab-case `ccswitch-operations`，避免 DSH 因名称不合规而跳过整个技能；仓库、ZIP 目录和界面展示名称保持不变。
- **安全刷新哈希**：`skill-upsert --preserve-flags` 在更新已有技能时保留所有 `enabled_*`，不会因省略开关而关闭 Codex、DSH 等已启用应用。
- **发布包校验**：手动打包和 Release 构建会校验 frontmatter 名称及描述，不合规时拒绝生成 ZIP。
- **安装文档**：补充 DSH 导入目录、CCS 已建链接和技能技术名称的区别。

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

## v1.5.3 Incremental (English)

- **Compatibility baseline unchanged**: continues to target CC Switch 4.0.28, Codex 0.167 and schema v24.
- **DSH skill loading**: the technical name is now the lowercase kebab-case `ccswitch-operations`, so DSH no longer skips the skill. The repository, zip folder and display name remain unchanged.
- **Safe hash refresh**: `skill-upsert --preserve-flags` keeps every existing `enabled_*` value when updating a skill.
- **Package validation**: manual and Release builds reject invalid frontmatter names or missing descriptions.
- **Installation guidance**: documents DSH directory import, existing CC Switch links, and the difference between the technical and display names.

### Update / Install

1. Quit the target agent.
2. Replace its existing `CCSwitch-operations/` skill folder with the one from this zip.
3. Restart the agent or start a new session. The skill is exposed as `ccswitch-operations`.
