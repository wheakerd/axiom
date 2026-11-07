# 管理 Axiom 安装

[English](managing-installation.md) | 简体中文

本指南负责 Axiom 当前的更新、禁用、移除与非破坏性排障流程。插件生命周期由宿主负责；Axiom 自身不会检查、下载、安装或宣布更新。

## 更新

对于 Codex，请求一次市场升级：

```bash
codex plugin marketplace upgrade axiom
```

在受支持的 Codex 工作区插件界面中，使用 **Refresh**。更新后开启新会话，并在 `/hooks` 中信任已更改的 Hook；Codex 会保留它直到你这样做。

对于 Claude Code，刷新市场并更新 Axiom：

```bash
claude plugin marketplace update axiom
claude plugin update axiom@axiom
```

Claude Code 运行更新后的 Hook 不需要单独的信任步骤，会在插件加载后的下一次 `SessionStart` 事件时运行。执行这些命令后请开启新会话；验证已安装的 Hook 是可选的，见[信任模型](../trust-model.zh-CN.md#hook-信任边界)。在运行中的会话内，运行 `/plugin marketplace update axiom`，然后在 `/plugin` 的 **Installed** 标签页中选择 Axiom 并选择 **Update now**。关闭面板后一旦插件重新加载，更新后的 Hook 会在该会话的下一次 `SessionStart` 事件时运行，例如 `/clear`、`/resume`、`/branch`，或一次自动或手动的压缩。新会话的 `SessionStart` Hook 会投递更新后的路由门控；`/reload-plugins` 不会重新运行它。启用市场自动更新时，Claude Code 可能在后台更新插件文件；对 `axiom` 这类第三方市场，该选项默认关闭；开启后，已安装的 Hook 可能在你没有执行任何命令的情况下，在两次会话之间发生变化。运行中的会话会一直使用其加载时的版本，直到 `/reload-plugins`。

是否自动检查或安装更新以及其时机，由你的设置以及原生客户端或工作区策略控制。Axiom 提供带版本的源元数据，没有更新调度器。

## 版本选择

[市场条目](../../.agents/plugins/marketplace.json)使用 Codex 官方的 `git-subdir` 源：仓库 `url`、作为其 `path` 的已安装插件根目录 `./plugin`，以及一个不可变的发布标签 `ref`。默认市场仍可从仓库的默认分支发现，而该条目独立地选定插件的已发布源。一次普通的 `main` 提交不会改变该选择。

`.claude-plugin/marketplace.json` 中的 Claude Code 目录通过其 `git-subdir` 源使用同一仓库与发布标签 `ref`，`path` 为 `plugin`。两个目录一起推进。

稳定版本成为 GitHub Latest 后，维护者通过既有的签名 PR 流程发布匹配的目录引用。在该目录变更合并之前，客户端继续解析到前一个选择。GitHub Release、其 Latest 标记以及字面名为 `latest` 的 Git 标签是不同的对象；客户端不会从其中一个推断另一个。

对于已有的默认分支注册，先使用上面的原生市场升级，再检查已安装的版本。在 Codex 中运行：

```bash
codex plugin list --marketplace axiom --json
```

在 Claude Code 中，`claude plugin list` 会打印每个已安装插件的 `Version`、`Scope` 与 `Status` 行。

保留有意为之的用户固定。目录固定锁定的是**目录快照**，并不覆盖插件条目自身的 `source.ref`。在 Codex 中使用市场的 `--ref` 选项。在 Claude Code 中，添加市场时加上 `#ref` 后缀，例如 `wheakerd/axiom#<tag>`；以标签或分支添加的市场只会更新到该引用的最新提交。要锁定某个特定的插件版本，请用客户端支持的源控制手段，选择一个其条目解析到该版本的不可变目录快照。在假定目录标签与插件版本一致之前，先检查该条目。对于由工作区管理的安装，工作区管理员负责所配置的仓库、路径、引用与原生同步策略。

Codex 源格式最后一次核对于 2026-10-25，生命周期语义最后一次核对于 2026-10-13，依据官方的[市场格式](https://developers.openai.com/plugins/build/plugins#marketplace-metadata)、[市场配置](https://learn.chatgpt.com/docs/config-file/config-reference)与[工作区同步文档](https://learn.chatgpt.com/docs/enterprise/plugin-management)。工作区同步时机不是对个人 Codex 安装的承诺。Claude Code 源格式最后一次核对于 2026-10-25，依据官方的[市场参考](https://code.claude.com/docs/en/plugins/marketplace-reference#plugin-sources)；其他 Claude Code 陈述最后一次核对于 2026-10-22，依据官方的[插件安装指南](https://code.claude.com/docs/en/discover-plugins)与[插件命令参考](https://code.claude.com/docs/en/plugins/cli-reference)。

## 市场克隆超时

在 Codex 中，包含 `git clone marketplace source timed out after 30s` 的错误表示下载市场目录失败。Codex 支持对 Git 市场使用 `--sparse` 以缩减目录检出。Axiom 当前的目录只需要 `.agents/plugins`：其插件条目使用一个带不可变发布引用的独立 `git-subdir` 源。下面的步骤适用于 Codex；[Claude Code](#claude-code-克隆超时) 有自己的步骤。

### 检查注册信息

在更改注册之前，记录市场与已安装插件的列表：

```bash
codex plugin marketplace list --json
codex plugin list --marketplace axiom --json
```

同时检查原始注册设置中是否有显式的目录引用、自定义来源或额外的稀疏路径。下面的迁移适用于跟随默认分支的个人 `wheakerd/axiom` Git 注册。对于已固定的目录，重新添加时保留其原有的 `--ref`。检查该快照的条目：如果它们使用本地插件路径，用另一个 `--sparse` 选项把每条路径加进去。指向本地插件文件的目录除了 `.agents/plugins` 之外还需要这些文件。自定义来源与工作区管理的控制留给其现有所有者。

### 使用稀疏检出重新注册

当已有注册拒绝更改源选项时，移除该市场注册，再用受支持的稀疏选项重新添加：

```bash
codex plugin marketplace remove axiom
codex plugin marketplace add wheakerd/axiom --sparse .agents/plugins
codex plugin marketplace upgrade axiom
```

任何命令失败时请停止。如果移除后重新注册失败，用上面记录的设置通过 `codex plugin marketplace add` 恢复先前的来源与引用。不要为了更改市场注册而移除插件或删除其缓存。

稀疏检出改变的是获取哪些目录文件。它保留默认分支的目录选择以及条目独立的插件版本选择。它不添加更新调度器，也不覆盖客户端或用户的更新设置。

### 验证结果

再次运行那两条列表命令。对照预期的目录条目与你记录的设置，检查已注册的来源、已安装版本、插件源引用与启用状态。按[更新检查](#更新)开启新会话并检查 Hook。

这次注册迁移于 2026-10-13 在 Linux 上使用 Codex CLI `0.162.1`，在一个隔离的 Axiom `v0.14.0` 安装中得到验证。既有的插件缓存与启用设置被保留，完整的原生升级成功。这并不确立另一台安装上的桌面刷新、Hook 信任或自动更新时机。

克隆超时时限适用于目录下载。一次完整刷新还可能下载插件源，耗时可能超过 30 秒。稀疏检出不会改变客户端的超时，也不保证在缓慢或不可用的网络上完成。如果错误持续，请记录确切的失败阶段、CLI 版本、退出状态以及脱敏后的错误，用于[问题报告](#报告问题)。

受支持的 CLI 选项与稀疏路径要求最后一次核对于 2026-10-13，依据官方的[市场 CLI 文档](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli)与[配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)。

### Claude Code 克隆超时

在 Claude Code 中，`Git clone timed out after 120s` 表示克隆或重新克隆市场超过了默认时限。在运行命令的 shell 中以毫秒为单位提高时限，然后重试：

```bash
export CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=300000
claude plugin marketplace update axiom
```

在 PowerShell 中改为设置 `$env:CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS = "300000"`。对于新的注册，`claude plugin marketplace add wheakerd/axiom --sparse .claude-plugin` 只获取目录，因为其插件条目使用独立的 `git-subdir` 源。移除市场会同时卸载其插件，所以不要仅为了添加稀疏检出而重新注册一个已有安装。这些选项最后一次核对于 2026-10-22，依据官方的[插件排障](https://code.claude.com/docs/en/plugins/troubleshooting)与[插件命令](https://code.claude.com/docs/en/plugins/cli-reference)参考。

## 禁用或移除

对于受信任的项目，在该项目的 `.codex/config.toml` 中禁用 Axiom：

```toml
[plugins."axiom@axiom"]
enabled = false
```

设置 `enabled = true` 可再次启用。该键由插件名与市场名组合而成。项目配置仅对受信任的项目加载，并且仍受托管要求约束。禁用会保留安装；市场刷新仍可能更新其文件。在 Codex 中，安装或启用插件并不会自动信任其 Hook；使用前请在 `/hooks` 中审阅当前定义。

该项目设置适用于本地市场安装，而不是工作区管理插件的启用状态。这些配置语义最后一次核对于 2026-09-16，依据官方的[项目插件设置](https://developers.openai.com/plugins/build/plugins#enable-or-disable-a-plugin-for-a-repo)与 [Hook 信任要求](https://learn.chatgpt.com/docs/hooks#plugin-bundled-hooks)。

从 `axiom` 市场移除确切的 Codex 安装：

```bash
codex plugin remove axiom@axiom
```

在 Claude Code 中，可以在保留 Axiom 的同时禁用它、再次启用它，或将其卸载：

```bash
claude plugin disable axiom@axiom
claude plugin enable axiom@axiom
claude plugin uninstall axiom@axiom
```

不带 `--scope` 时，`disable` 与 `enable` 作用于 local、project、user 三个范围中第一个在设置里提到 Axiom 的范围。那通常是 `user`，因此禁用会在所有项目中关闭 Axiom。要只在当前项目中关闭它，为你自己加上 `--scope local`，或加上 `--scope project` 通过项目设置共享该覆盖。一旦 Axiom 被启用并再次加载，无论是在会话开始还是插件重新加载时，其 Hook 都会在下一次 `SessionStart` 事件时运行，不需要单独的信任步骤。这些 Claude Code 命令最后一次核对于 2026-10-24，依据官方的[插件命令参考](https://code.claude.com/docs/en/plugins/cli-reference)。

在任一宿主上做出更改后，请开启新会话。在 Claude Code 中，`/reload-plugins` 会从运行中的会话卸载插件，但已经投递的路由门控仍留在该会话的上下文中。在把 Axiom 视为未激活之前，确认它在宿主的插件列表中不存在或已禁用，并且其 Hook 不在 `/hooks` 中。不要编辑已安装的文件或删除宿主缓存来替代由宿主管理的生命周期。禁用或移除 Axiom 会把路由写入你各个仓库 Git 元数据中的任务状态原样留下；[信任模型](../trust-model.zh-CN.md#路由写入的仓库状态)列出了这些位置以及如何移除它们。

## 非破坏性排障

如果预期的 Axiom 能力不可用，或某个请求被错误地路由：

1. 确认 Axiom 已安装并在宿主的插件列表中启用。
2. 打开 `/hooks`，确认 `SessionStart` Hook 存在且与[签入的参考](../reference/hooks.md)一致；在 Codex 中，还要确认它已被信任。
3. 确认已安装的 Axiom 版本就是你打算测试的版本。
4. 在任一宿主中开启一个新会话。
5. 重试[快速开始](getting-started.zh-CN.md)中的一个只读路由请求与一个无路由对照请求。

如果在任一宿主中压缩或分叉之后路由缺失，确认 `compact` 与 `fork` 仍在已安装的 `SessionStart` 匹配器中。在 Windows 上，确认 Claude Code 可以使用 Git Bash；没有它，Claude Code 会在 PowerShell 中运行 Hook，而 PowerShell 不支持该命令。

不要为了让路由出现而删除宿主数据、清理缓存、编辑已安装的插件、更改全局配置、安装专有验证器或创建第二个 Hook。说明该工具不可用，不要把它报告为通过。

## 报告问题

报告之前，记录宿主及其确切版本、操作系统、Axiom 版本或提交、安装方式、生命周期来源、已安装的 Hook 定义、请求、选中的路由、澄清次数，以及是否尝试过任何变更。不要包含凭证、私人对话文本或敏感的仓库内容。

- 安装或宿主观测使用[兼容性报告](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml)。
- 意外的路由行为使用[路由用例报告](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml)。
- 漏洞使用 [SECURITY.md](../../SECURITY.md) 中的私下报告流程。
