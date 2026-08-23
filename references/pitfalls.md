# 已踩过的坑

| 症状 | 根因 | 处理 |
| --- | --- | --- |
| CCS 面板中文显示 `???` | PowerShell 5.1 管道把中文按 GBK 传给 `python -` | 用 `scripts/ccs_db.py`（内联 argv 或 `--*-file`），禁止管道传中文 |
| `.ps1` 中文乱码 / 解析报错 | 无 BOM UTF-8 被 PS 5.1 按 GBK 解码 | 存为 UTF-8 with BOM |
| Codex 里 MCP 工具全部不可见 | 模型目录 `supports_search_tool:true` + `tool_mode:null` | 改目录为 `supports_search_tool:false` |
| Codex 远程 MCP 带静态头不生效 | 配置键写成了 `headers` | Codex 用 `http_headers`（Claude Desktop JSON 才用 `headers`） |
| DashScope 等远程 MCP 原生连接 403 | 网关拦截特定客户端（TLS/UA 指纹） | 走 `npx -y mcp-remote <url>` 桥接 |
| Codex 无法连 SSE 端点 | Codex 不支持 SSE 传输 | `npx -y mcp-remote <url> --transport sse-only` 桥接 |
| Windows 下 mcp-remote header 带空格被 npx 弄坏 | 原生程序调用不转义空格参数 | header 写 `Authorization:${ENV}`，值放 `env` 变量 |
| PowerShell 内联参数里的双引号被剥掉 | PS 调原生程序不保留内嵌双引号 | JSON/TOML 值一律用 `--*-file` 读 UTF-8 文件；tags 可用逗号列表 |
| `provider-block --replace` 后 config 出现重复的 `[x.env]` 子表 | 旧版 replace 把子表头当节边界 | 使用当前脚本（连同子表一起替换）；历史损坏需手工去重 |
| CCS 重启后 config.toml 修改丢失 | 只改了文件，没改 provider 的 `settings_config.config` | 两处同步；改完重启 CCS 并复核 |
| Claude Desktop 3P 看不到 MCP/Skills | CCS 设计上不同步 3P 的 MCP/Skills | MCP 手写 3P config；skills 走 manifest 手动同步 |
| 改了配置但桌面不生效 | 配置只在启动时加载 | 完全退出（含托盘）后重启目标应用 |
| 升级后旧版 CCS 拒绝打开数据库 | schema 迁移（如 v16→v17） | 用迁移前自动备份还原（`<cc-home>/backups/`） |
| 旧版 IME 缺陷写坏的文本仍乱码 | 修复只防新增，旧值保留 | 重新编辑受影响字段；`ccs_db.py check` 覆盖 providers |
| skill 目录从 Junction 变成普通目录 | `skillSyncMethod=auto` 遇到目标已有普通目录时改用 copy 覆盖 | 需要稳定链接就设 `symlink`，或删除目标后让 CCS 重建 |
| 恢复 `.db` 备份后各应用 live 配置被改写 | 3.20 恢复会重建所有受管应用配置（Pi 除外） | 恢复后按“MCP 三处同步”复核 |
| Pi 同名 skill 无法覆盖/删除 | CCS 只管理它自己拥有的 skill | 先确认归属，再手动处理 `~/.pi/agent/skills` |
| 控制台显示 `��`/乱码 | 控制台按非 UTF-8 解码 Python 输出 | 用 `ascii()` / `repr()` 核对；DB 内文本通常完好 |
| 官方 MCP 不在 `mcp_servers` 表 | 官方/内置服务器不归用户管理 | 属正常，不要补录；三处一致只针对用户自建 MCP |
| CCS 3.20.0 编辑页零改动保存即破坏 Codex 配置 | 前端 smol-toml 重排 + 后端剥离/合并通用配置，空命令 stdio MCP 落盘；现象含 `notify = [...]` 错位、`[plugins]`/`[marketplaces]` 被剥离、`[mcp_servers]` 与 `[mcp_servers.node_repl(.env)]` 块/键被改写或重排 | 不要用编辑页保存/提取；用本技能 `check --strict` / `doctor --audit` / `repair` / `common-config` 维护；保存后与 `config.toml.bak` 或 `snapshot`/`diff` 做字节级对比；详见 references/incidents/2026-08-23-codex-config-mangle.md |
| AI 手写临时脚本直改 DB，provider 与 snippet 持有重复键 | 绕过技能命令、没有幂等/剥离逻辑 | 用 `common-config set-key/set --apply --sync-and-enable` 规范化：snippet 持有、provider 剥离、显式打勾；禁止临时脚本直改 DB |
| 用户只说“同步 CCS”，AI 擅自只改 common-config | 范围推断错误，把“CCS”脑补成“通用配置” | “同步”默认降级为 provider 配置；改完后询问是否提取到通用配置模板（`common-config extract`）；只有用户明确提到“通用配置/common-config/模板”才直接碰 snippet |
| 用户说“同步”，AI 未确认对象直接按配置同步执行（实为同步 skill） | 对象推断错误 | 由 AI 自行识别变更对象（结合上下文/待同步差异），没问题不轻易问；识别含配置才落配置铁律（provider-first + 提取询问） |
| AI 不确定时自由发挥 / 自己猜 | 没有先读本技能就直接行动 | 不确定时先读 SKILL.md 与 references/；确属技能范围之外时明确告知用户并提供建议行动 |
