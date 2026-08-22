## 简介

CCSwitch-operations 是一个可移植、可发布的 **CC Switch（CCS）** 操作技能：安全地维护全局提示词、Skills、MCP 服务器、供应商与 Codex 模型目录，覆盖 CCS 管理的九个应用。

- 零第三方 Python 依赖，推荐 Python 3.11+
- 安全写入流程：备份 → 停止 CCS → 修改 → 校验 → 重启 → 复核
- 跨平台（Windows / macOS / Linux），文档同时提供 PowerShell 与 bash 示例
- 内置 UTF-8 安全的数据库辅助脚本（`ccs_db.py`）与 `doctor` / `check` 校验
- MIT 开源，全本地运行，无遥测、无网络请求

## 安装

- **Codex**：把 `CCSwitch-operations` 文件夹复制或软链接到 `~/.codex/skills/`
- **Claude Code**：复制或软链接到 `~/.claude/skills/`
- **其他 SKILL.md agent**：放入对应 agent 的 skills 目录
- **CC Switch**：直接导入本 Release 的 zip（顶层为 `CCSwitch-operations/`）

## 文档

仓库内 `README.md` / `README.zh-CN.md` 与 `references/` 提供完整说明（架构、九大受管应用矩阵、操作模板、坑位记录、版本行为变化）。

## 资源

- 技能包：发布附件中的 `CCSwitch-operations-*.zip`（也可在仓库内手动打包）
