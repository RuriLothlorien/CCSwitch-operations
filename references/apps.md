# 九大受管应用矩阵（CCS 3.20）

路径均使用可移植写法：`~` 在 Windows 上等同于 `%USERPROFILE%`；macOS/Linux 为 `$HOME`。

| 应用 | 模式 | 主要配置 | skills 目录 | prompts | MCP | 本地代理/故障转移 |
| --- | --- | --- | --- | --- | --- | --- |
| codex | 切换 | `~/.codex/config.toml` | `~/.codex/skills` | DB(prompts) | config.toml + mcp_servers + provider config 三处一致 | 支持 |
| claude | 切换 | `~/.claude/settings.json` | `~/.claude/skills` | DB(prompts) | settings.json + provider env | 支持 |
| claude-desktop | 切换 | 1P `%APPDATA%\Claude\claude_desktop_config.json`；3P `%LOCALAPPDATA%\Claude-3p\...` | 不走 CCS skill 同步（3P 手动 manifest） | DB(prompts) | 手动 JSON | 3P 支持 |
| gemini | 切换 | `~/.gemini/` | `~/.gemini/skills` | DB(prompts) | provider config | 支持 |
| grokbuild | 切换 | `~/.grok/` | `~/.grok/skills` | DB(prompts) | provider config | 支持 |
| opencode | 累加 | `~/.config/opencode/` | `~/.config/opencode/skills` | DB(prompts) | provider config | 无 |
| openclaw | 累加 | `~/.openclaw/openclaw.json` | `~/.openclaw/skills` | DB(prompts) | provider config | 无 |
| hermes | 累加 | hermes 配置目录 | hermes 配置目录/skills | DB(prompts) | provider config | 无 |
| pi | 累加 | `~/.pi/agent/models.json` | `~/.pi/agent/skills` | AGENTS.md / SYSTEM.md / APPEND_SYSTEM.md | 无 MCP 注册表，不参与 MCP 同步 | 无 |

## 模式说明

- **切换模式**（claude / codex / gemini / claude-desktop / grokbuild）：只把当前供应商写入 live 配置，切换供应商会重写对应配置文件。
- **累加模式**（opencode / openclaw / hermes / pi）：多个供应商共存于原生配置，供应商“启用”等于其配置键存在于原生文件。

## 各应用要点

- **Pi**：CCS 绝不读写 `~/.pi/agent/auth.json`、`defaultProvider`、`defaultModel`；Skills 按“存在即启用”，CCS 不覆盖/删除同名但非它所有的 skill。
- **Claude Desktop 3P**：CCS 设计上不同步 MCP/Skills；MCP 手写 3P config，skills 走 `manifest.json`（`syncManaged:false`）+ `cc-switch-managed.json` 手动同步。
- **Codex**：官方/内置 MCP（如 `openaiDeveloperDocs`）在 `mcp_servers` 表中没有行属正常，不要补录。
