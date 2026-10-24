# 已踩过的坑

| 症状 | 根因 | 处理 |
| --- | --- | --- |
| CCS 面板中文显示 `???` | PowerShell 5.1 管道把中文按 GBK 传给 `python -` | 用 `scripts/ccs_db.py`（内联 argv 或 `--*-file`），禁止管道传中文 |
| `.ps1` 中文乱码 / 解析报错 | 无 BOM UTF-8 被 PS 5.1 按 GBK 解码 | 存为 UTF-8 with BOM |
| Codex 里 MCP 工具全部不可见 | 模型目录 `supports_search_tool:true` + `tool_mode:null`（DeepSeek 的 Responses API 不提供 `tool_search`，Codex 因此把 MCP 工具全部延迟隐藏） | 改目录为 `supports_search_tool:false`；DeepSeek 内置预设自 3.20.2 起已声明 false，存量卡**切走再切回**刷新 catalog 即恢复 |
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
| CCS 3.20.0–3.20.3 编辑页零改动保存即破坏 Codex 配置（4.0.4 已修复，#6719 已关闭） | 前端 smol-toml 重排 + 后端剥离/合并通用配置，空命令 stdio MCP 落盘；现象含 `notify = [...]` 错位、`[plugins]`/`[marketplaces]` 被剥离、`[mcp_servers]` 与 `[mcp_servers.node_repl(.env)]` 块/键被改写或重排 | 4.0.4 起写入改为“只替换关键字段”，零改动保存逐字节一致，编辑页可安全使用；**存量坏块不会自动修**——用本技能 `check --strict` / `doctor --audit` / `repair` 修复，或在 MCP 面板把条目关掉再打开重写；详见 references/incidents/2026-08-23-codex-config-mangle.md |
| AI 手写临时脚本直改 DB，provider 与 snippet 持有重复键 | 绕过技能命令、没有幂等/剥离逻辑 | 用 `common-config set-key/set --apply --sync-and-enable` 规范化：snippet 持有、provider 剥离、显式打勾；禁止临时脚本直改 DB |
| 用户只说“同步 CCS”，AI 擅自只改 common-config | 范围推断错误，把“CCS”脑补成“通用配置” | “同步”默认降级为 provider 配置；改完后询问是否提取到通用配置模板（`common-config extract`）；只有用户明确提到“通用配置/common-config/模板”才直接碰 snippet |
| 用户说“同步”，AI 把对象 A 的同步当成对象 B 的同步（如把同步 skill 当成配置同步） | 对象推断错误 | 由 AI 自行识别变更对象（结合上下文/待同步差异），没问题不轻易问；不要把对象 A 的同步当作对象 B 的同步（技能 ≠ 配置 ≠ 模板）；识别含配置才落配置铁律（provider-first + 提取询问） |
| AI 不确定时自由发挥 / 自己猜 | 没有先读本技能就直接行动 | 不确定时先读 SKILL.md 与 references/；确属技能范围之外时明确告知用户并提供建议行动 |
| Codex 3.20.1 切换第三方后 `auth.json` 消失（桌面版回默认登录页） | 保留开关关闭（默认）时切换第三方会删除 `auth.json`；部分 Codex 构建（桌面版）以 auth.json 是否存在判定登录态 | 打开“非接管切换时保留官方登录”（`preserveCodexOfficialAuthOnSwitch=true`）；桌面版必须保留 `auth.json`（仅写 `experimental_bearer_token` 不够） |
| Codex 0.149 切换被拒（空卡/无凭据卡） | 无 `[model_providers.*]` 表或无自有密钥、`requires_openai_auth=true` 无凭据、`model_provider` 指向缺失的表 | 用 `check --strict` 检测（会点名缺失表），`repair --mode codex-0149` 迁移可修形态；空卡/无凭据/缺表需补 `[model_providers.<id>]` 表（base_url + `experimental_bearer_token`）或修正选择器 |
| Codex 走内置 openai 却没到第三方端点（顶层 `openai_base_url` 误路由） | Codex 0.149 不读顶层 `experimental_bearer_token`；选择器缺省/`openai` 时顶层 `openai_base_url` 只能把内置 openai 指向第三方，密钥缺槽时会回落到 `auth.json` 的官方登录 | `check --strict` 只在该形态真正路由内置 openai 时报错；`repair --mode codex-0149 --apply` 迁移为 `[model_providers.cc-switch(-N)]` 并写 `model_provider` + `wire_api="responses"`；CCS 3.20.3 接管自身也会做同样的规范化（直切仍按卡面） |
| 顶层 `openai_base_url` 残留在 custom 路由卡里 | 选择器指向自带表时，该键对内置 openai 才生效，属惰性残留（上游 `normalize` 同样跳过） | 不要把对象弄混：`check --strict` 对这类卡不报错；只有选择器缺省/`openai` 时才需要迁移 |
| 密钥位置变化：现在在 provider 表而非 auth.json | 3.20.1 config-only 切换 | `[model_providers.*]` 内 `experimental_bearer_token` 为正常形态；`auth.json` 仅官方登录；`extract_common_config` 会自动剥离该字段，不入模板 |
| 按 3.20.1 config-only 迁移（删 auth.json）后 Codex 回默认登录页 | 桌面版/部分构建以 `~/.codex/auth.json` 是否存在判定登录态；删掉后即使 `config.toml` 有 `experimental_bearer_token` 也无效（手动注释掉等同未生效）；3.20.3 未改变直切行为 | 恢复/保留 `auth.json`（`OPENAI_API_KEY`）；`~/.cc-switch/settings.json` 设 `preserveCodexOfficialAuthOnSwitch=true`；live config 中的 token 可保留或注释，DB 模板仍按 3.20.1 形态保存 |
| 统一供应商同步后子卡的用量脚本/通用配置勾选/排序丢失 | 3.20.3 之前的同步用统一供应商生成的 `meta`/`sort_index` 覆盖子卡（`{}` + NULL）；3.20.3 起保留，但**已丢的值不会自动恢复** | 升级到 3.20.3 后重填一次；通用配置勾选先用 `common-config status` 查看（未勾选/自动推断），需要时 `common-config enable`（先过幂等审查） |
| Codex/Gemini/Grok Build 的代理重试/超时与 Claude 不一致 | 3.20.3 之前退出时把 Claude 的每应用代理设置串写给其它应用；本版只止住新串写 | 到各应用代理设置里复核一次，把不符合预期的重试/超时改回来（旧值不会自动恢复） |
| Codex 长任务在一句进度汇报后停止 / DeepSeek 无限复读 | Chat 上游的 Responses→Chat 转换把 commentary 与紧随的工具调用拆成两条 assistant 消息，上游提前 `stop`（#7280 / #5860 同根因） | 升级到 3.20.3；升级后 Chat 上游卡首次请求会经历一次前缀缓存未命中（请求字节变化，之后稳定） |
| Claude Code 每个 token 刷出空 Thought 块 | 上游每个 chunk 带空 `reasoning_content` 占位（#7227） | 升级到 3.20.3（代理层修复，无需改配置） |
| Claude Code 请求 400（工具 schema 校验） | Artifact 工具灰度正则不被严格网关接受 | 在 CCS 供应商快捷开关里打开“禁用 Artifact 工具”（写 `env.CLAUDE_CODE_DISABLE_ARTIFACT = "1"`） |
| Codex 把图片替换成 `[Unsupported Image]` | 3.20.3 之前 DeepSeek 官方目录按纯文本确认表处理 `deepseek-flash` | 升级到 3.20.3 并在 DeepSeek 卡上**切走再切回**重建 catalog（该目录现支持视觉输入） |
| 代理托管 OAuth 卡（xAI OAuth / GitHub Copilot）切换被拒 | 这类卡本身无密钥（本地代理逐请求注入令牌），而卡上仍带 0.149 之前模板的 `requires_openai_auth = true`，v3.20.1 的无密钥安全闸把它当成“会回落到官方登录” | 3.20.2 起对 `providers.meta.provider_type` = `xai_oauth` / `github_copilot` 的活跃表强制 `requires_openai_auth = false`（预设源头同步，存量卡下次切换自愈）；本技能 `check --strict` 会点名该标志，`repair --target provider --mode codex-0149 --apply` 可提前改 false；**Codex OAuth 不适用**（官方登录即其凭据） |
| 接管后 Codex 停在登录屏（旧版） | 直切第三方删掉了 `~/.codex/auth.json`，而卡上仍是 0.149 之前的 `requires_openai_auth = true` | 3.20.2 已修：接管按 Codex 会观察到的登录状态覆盖该标志（`file` 跟随 auth.json、`ephemeral` 记未登录、`keyring`/`auto` 保留原值、auth.json 缺失/损坏视为未登录且不再写入失败）；旧版可手动改 false 或打开保留开关 |
| catalog 类修复看不到效果 | catalog 只在**切换供应商**时重建 | 在受影响的卡上切走再切回一次即可（DeepSeek MCP 可见性、`supports_parallel_tool_calls` 回填、`deepseek-flash` 视觉模态、`glm-5.3` 纯文本均属此类） |
| 重新导入预设才算生效（例：GLM 直连报 400 unknown variant custom；Kimi 想走原生 Responses） | 预设改动只影响**新建**供应商，存量卡保存的是创建时的快照 | 按需重新导入该预设（智谱 GLM 自 3.20.2 起改指官方 Responses 端点 `/api/v1`；Kimi 自 3.20.3 起改 `openai_responses`，也可只在编辑页把“上游格式”改成 Responses——注意 Kimi 开放平台 Tier 0 限 3 次/分钟）；例外：PPIO、JieKou、Novita 的模型列表地址按卡片 Base URL 反查，存量卡无需改动 |
| 编辑或切走 Codex 供应商后已保存的 API Key 消失 | 3.20.4 之前 CCS 用 live 的空 auth 覆盖了 DB 里的 `auth.OPENAI_API_KEY`（#7434）；修复只防新增 | 升级到 3.20.4；若 provider 表里仍有 `experimental_bearer_token`，`check --strict` 会点名，`repair --target provider --mode codex-key --apply` 可回填；两处都没有时在 CCS 里重填，并检查用量脚本是否被重置 |
| 绑定了已删除 ChatGPT 账号的 Codex 卡切不走/改不了 | 账号被删后绑定检查失败（#7395） | 升级到 3.20.4，在卡片上“选择账号”重绑；重绑前无法开启接管，启动恢复会关闭 Codex 接管（`~/.codex/auth.json` 不动） |
| Codex 0.154+ 经 Chat 网关整轮 400 / 一张截图后会话每轮都失败 | `additional_tools` 被当成消息生成 `content: null`（#7454）；`detail:"original"` 只在 Responses 合法（#7476）；无描述工具发 `description: null`（#7319/#7378） | 升级到 3.20.4（已坏会话自动恢复）；升级后相关请求有一次前缀缓存未命中，之后稳定 |
| 打开 CCS 提示词列表后 DB 里的提示词被 live 文件覆盖 | 3.20.4 起打开列表会读回 live 文件（`CLAUDE.md`/`AGENTS.md` 等）的外部修改（#7194，Pi 除外） | 维护提示词时用 `prompt-set` 写 DB；先确认 live 文件内容就是要保留的内容，再打开列表 |
| 升级 3.20.4 后“隐藏 AI 署名”显示未勾选 | 新判定额外要求 `attribution.sessionUrl = false`，旧格式不带该字段（#7053） | 重新勾选一次（会自动补 `sessionUrl:false`） |
| 3.20.4 升级后部分预设/端点/计价与预期不同 | AICodeWith 的 Codex 端点改为 `/v1`（存量卡是创建时快照）；DeepSeek V4 Pro 撤回调价、回到高峰档；`Ling-2.6-1T` 转纯文本 | 存量 AICodeWith 卡手动改端点或重新导入预设；其余是官方行为，无需本机操作 |
| MiniMax Code（mcode）提示词写入失败 / CCS 找不到数据目录 | 提示词按 UTF-8 字节限 32 KiB；数据目录只认 `MINIMAX_DATA_DIR`/`MAVIS_DATA_DIR` 环境变量（都没有时用 `~/.minimax`） | 用 `prompt-set --app-type mcode`（本技能会先校验 32 KiB）；自定义目录时启动 CCS 也要带同一个环境变量；删除被 `defaultModel` 引用的供应商前先在 MiniMax Code 里换默认模型 |
| CCS 4.0 里 `common-config` 改了没效果 | 4.0 移除了“通用配置片段”：DB 里的 `common_config_*` 与 `providers.meta.common_config_enabled` 只是升级遗留 | 本技能在 schema v20 上会拒绝所有 `common-config` 命令；共享键写进客户端 live 配置（如 `~/.codex/config.toml`），供应商专属字段写卡片（`provider-block` / `provider-set-key` / `provider-env`） |
| Codex 0.158+ 因 MCP `type` 字段报错/起不来 | 旧版 CCS/手动配置把 `type = "stdio"` 写进了 `[mcp_servers.*]`；4.0 写入时会剥离，但 live 里可能残留旧值 | 先看 `check --strict`（live config 会被审计）；`repair --target config.toml --mode mcp-type [--apply]` 或面板关/开重写；不要在 Codex 的 provider config / live config 里手写 `type` |
| Codex 聚合模式下子 agent 读不到任务 | 新版子 agent 工具把任务加密给主 agent 的供应商，跨供应商解不开 | 在聚合设置里打开「聚合模式下子 agent 用经典工具」（`settings.json: codexStackClassicTools`，4.0.13 起默认 true），改完重启 Codex；代价是没有 `followup_task` 等新工具 |
| Windows 更新 CCS 后，隐藏应用、配置目录覆盖等设置回到默认值 | 4.0.15 之前 `settings.json` 直接覆盖写；新内容更短时旧尾部残留，随后整份解析失败并回落默认值 | 升级 4.0.15+；若首启出现 `settings.json.broken-<time>.bak`，从备份核对并重设；已丢失的旧设置不会自动找回 |
| Claude Desktop 切换直连/路由/聚合后没有变化 | Desktop 只在启动时读取配置 | 完全退出并重启 Claude Desktop；路由/聚合模式还需保持 CC Switch 运行 |
| 升级 4.0.18 / 4.0.19 后旧版 CCS 打不开数据库 | 4.0.18 将 schema 升到 v21 并加入 `enabled_agy`；4.0.19 升到 v22 并加入 `enabled_kimi` | 升级前保留自动备份；降级必须恢复迁移前数据库，不能用旧版直接打开 v21/v22 |
| Kimi Code 的 MCP/Skills 已在面板勾选但原生文件没有 | 技能只改 DB 标志，CCS 负责投影到 `~/.kimi-code`；也可能 `KIMI_CODE_HOME` 指向了另一目录 | 重启 CCS 触发同步；确认启动 CCS 的 `KIMI_CODE_HOME` 与 Kimi 实际使用目录一致 |
| 直接运行 agy 没有使用 CCS 里的第三方供应商 | Agy 卡片是启动时注入，只对“使用此供应商打开终端”启动的进程生效；直接运行 agy 仍是官方 Google 登录 | 从对应卡片打开终端；不要试图用 provider-* 改全局 agy |
| Agy 的 MCP 勾选后报 SSE 不支持 | Agy 只支持 stdio 和流式 HTTP | 改用 HTTP 或 `npx -y mcp-remote <url> --transport sse-only` 桥接为 stdio；不要手改共享目录绕过校验 |
| 修改 Agy 定制后 Antigravity IDE 也受影响 | CLI、桌面版和 IDE 可能共用 `~/.gemini/config` | 操作前明确要影响哪个应用；只改指定用户所需的 MCP/Skills/Prompt，并在重启 IDE/agy 后复核 |
| Kimi 多供应商中某些卡不能删除 | 默认模型或子代理仍引用该供应商 | 先在 Kimi Code 里把默认模型/子代理换掉，再从 CCS 移除；官方多账号由授权中心管理 |
| 打开「压缩 Codex 历史会话」后别的工具读不到会话 | 7 天以上会话被压成 `.jsonl.zst`，直接读 raw `.jsonl` 的工具看不到 | 属于预期行为：压缩会话在 CCS 里照常可读，Codex 继续时会自动解压；需要被第三方读取时不要开该开关 |
| 升级 4.0 后旧触发的问题还在 | 部分修复（Codex 模型目录、会话分组、MCP `type`）要等 CCS 下一次写入才生效 | 升级后切换一次供应商；已有 MCP 配置重新同步一次；时间 MCP 预设改为 `uvx mcp-server-time`（存量需手改） |
| 4.0 里找不到设置项 | 4.0 移除了供应商成本倍率、连通性检查高级设置、Claude 的 Teammates 与最大强度 | 已写入配置的环境变量不会被自动删除；需要时用官方端点的默认值或在会话里用 `/effort max` |
| Claude Code 聚合模型在 `/model` 里看不到 | Claude Code < 2.1.243 不支持 `modelPicker` | `claude --version` 检查并 `claude update`；Codex 聚合列表变化后按提示重启 |
