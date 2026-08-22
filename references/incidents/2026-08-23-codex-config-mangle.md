# 事故复盘：Codex 配置被重排/剥离/坏块写回（2026-08-23）

## 现象

- 在 CC Switch 3.20.0 的 Codex 供应商编辑页**零改动直接保存**后：
  - 供应商 `settings_config.config` 与 `~/.codex/config.toml` 块顺序重排（MCP 服务器块被移位）；
  - 通用配置块（plugins / marketplaces / projects / hooks 等）从供应商配置中被剥离；
  - 非通用内容（如新信任的 `[projects]`）被固化进供应商配置；
  - 标记注释错位（`# >>> ... begin/end <<<` 丢配对）；
  - url-only 远程 MCP（esp-cn-docs）被写成 `type = "stdio"` + `command = ""` + `url = ...`。
- “通用配置提取”同样产出混乱结果。

## 根因（源码级）

1. 前端编辑器用 smol-toml 做 parse→stringify 往返（`src/utils/tomlUtils.ts`），注释全丢、键序重排。
2. 保存路径 `ProviderService::update` → `normalize_provider_common_config_for_storage` / `remove_common_config_from_settings`（`src-tauri/src/services/provider/live.rs`）用 toml_edit 剥离通用 snippet 键并整文 `to_string()`；写 live 时再 `apply_common_config_to_settings` 合并重排。
3. `codex_config.rs::write_codex_live_config_atomic` 只做 TOML 语法校验后整文写入，空命令 stdio MCP 能通过。
4. 提取路径 `extract_codex_common_config`（`services/provider/mod.rs`）同样 parse→remove→to_string。

## 影响

- 零改动保存也会破坏用户配置；
- 含注释/标记/复杂 MCP 的配置易损坏；
- 远程 MCP（url-only）会被序列化成 `type="stdio" command=""` 坏块，Codex 无法启动该 MCP。

## 修复步骤（本机已执行）

1. 备份 DB 到 `backups/`；
2. 从事故前快照恢复 DeepSeek `settings_config`；
3. 用 `provider-block --replace` 修复 esp-cn-docs 为 url-only；
4. 以 `config.toml.bak` 为顺序模板重建 config.toml（保留当前运行路径与信任项）；
5. 修复通用配置 snippet 的标记配对（instructions/hooks begin/end、清除游离 mcp 标记）；
6. `check --strict` / `doctor --audit` / 重启后字节级复核。

## 预防（v1.1.0 起）

- 所有写操作自动 preflight：检测空命令 MCP、标记不配对、表头乱序/越权、live-only 混入；
- `repair` 提供 header-order / live-only 修复（dry-run + `--apply`）；
- `common-config` 维护 snippet 与勾选状态（幂等审查、提取自动打勾）；
- **不要使用 CCS 3.20.0 编辑页保存/提取 Codex 供应商配置**。

上游 issue：[#6719](https://github.com/farion1231/cc-switch/issues/6719)
