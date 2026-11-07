# 快速开始

[English](../../en/guides/getting-started.md) | 简体中文

本指南负责 Axiom 的安装、首次使用，以及一个路由请求与一个普通对照请求之间的首次安全比较。Axiom 通过各自独立的宿主清单、市场与 Hook，在同一套签入的技能之上支持 Codex 与 Claude Code。

## 安装前

先查看当前的[兼容性边界](../../en/compatibility.md)，并记住：已签入或经静态验证的支持并不是对你宿主的一次新鲜观测。路由门控是只读的，因此在任何仓库中的首次尝试都不会改变任何东西，除非你提出变更请求。

## 为 Codex 安装

添加 Git 市场并从中安装 Axiom：

```bash
codex plugin marketplace add wheakerd/axiom --sparse .agents/plugins
codex plugin add axiom@axiom
```

[市场条目](../../../.agents/plugins/marketplace.json)通过其 Git 源的 `ref` 选定一个已发布版本。从默认分支获取市场并不会安装该分支上的开发中插件文件。固定来源与既有安装见[版本选择](managing-installation.md#版本选择)。

官方的 `--sparse` 选项把市场检出限制在存放市场目录的子目录中。目录的 `git-subdir` 源会单独获取插件，因此插件的技能与 Hook 不需要额外的市场稀疏路径。该 CLI 选项依据官方的[市场注册文档](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli)。如果 `axiom` 已在没有稀疏检出的情况下注册，请按[迁移流程](managing-installation.md#市场克隆超时)操作。

开启一个新的 Codex 聊天或 CLI 会话。已有会话可能仍保留较旧的 Hook 或技能快照。

## 为 Claude Code 安装

在终端中添加市场并安装 Axiom：

```bash
claude plugin marketplace add wheakerd/axiom
claude plugin install axiom@axiom
```

在运行中的会话内，使用 `/plugin marketplace add wheakerd/axiom`，再用 `/plugin install axiom@axiom` 打开 Axiom 的详情并选择安装范围；安装摘要会说明是否需要重新加载。立即生效或触发重新加载的安装会把 Hook 载入该会话，并在下一次 `SessionStart` 事件时运行，例如 `/clear`、`/resume`、`/branch`，或一次自动或手动的压缩。`.claude-plugin/marketplace.json` 中的 Claude Code 目录通过 Git 源的 `ref` 选定与 Codex 目录相同的已发布版本；`main` 上的开发提交不会改变它。

开启一个新的 Claude Code 会话，使其 `SessionStart` Hook 投递路由门控；`/reload-plugins` 会把插件变更应用到运行中的会话，但不会重新运行该 Hook。在 Windows 上，启动 Hook 需要 Git Bash。

Claude Code 插件加载同一套技能与路由。用自然语言或 `/axiom:<skill-name>` 的形式调用任意技能。

## 信任 Hook

Codex 会跳过新的或已更改的 Hook，直到你审阅并信任其确切定义：在新会话中打开 `/hooks`，阅读 Axiom 条目并信任它。Axiom 的路由在这一步之后才开始。Claude Code 没有单独的 Hook 信任步骤：插件加载后，其 Hook 会在下一次 `SessionStart` 事件时运行，例如新会话、`/clear`、`/resume`、分叉或压缩，而 `/hooks` 会显示已加载的条目。将已安装的定义与 [Hook 参考](../../en/reference/hooks.md)比对是审阅者的可选检查；[信任模型](../trust-model.md#hook-信任边界)说明了它在何时重要，以及定义不一致时该怎么做。

## 尝试一个路由请求

使用这个只读请求：

> Audit this repository's AGENTS.md instruction system. Report findings only; do not modify files.

预期契约是选中 `agents-architect`、给出只读的证据报告，且不改动任何文件。路由选择不是修改仓库的许可。在 `using-axiom` 生效时，模型与宿主可以按你的输出详细程度偏好说明这次调用。例如：

`axiom:agents-architect` Review the repository's instruction structure.

整个 Axiom 技能标记是行内代码。外部或仓库本地的技能、插件或 MCP 能力保留其自身的行内代码名称和简短原因，不加 `axiom:` 前缀。模型自行决定是否说明调用以及如何安排周围的输出。

这项可选指引属于 `using-axiom`：它通过已启用的启动门控或对该技能的显式调用生效。门控被禁用时，单独调用另一个 Axiom 技能并不会激活通知指引。

## 尝试一个对照请求

使用这个普通请求：

> Summarize the purpose of this README. Do not modify files.

预期契约是宿主正常执行，不附加任何 Axiom 路由。启动与无路由结果都不会收到通知。无路由结果不是安全认证；宿主权限与仓库指令仍然有效。激活与命名边界见[通知指引](../../../plugin/skills/using-axiom/SKILL.md#invocation-notes)。

## 解读并报告结果

上面的预期结果是契约，而不是你的安装已经复现它们的断言。请记录宿主名称与版本、操作系统、Axiom 版本或不可变提交、安装方式、生命周期来源、确切请求、选中的路由、澄清次数，以及是否尝试过任何变更。

报告中不要包含凭证、私人对话文本或敏感的仓库内容。如果某个结果可能暴露漏洞或未经授权的操作，在公开分享细节之前，先使用 [SECURITY.md](../../../SECURITY.md) 中的私下报告流程。

- 有边界的宿主结果使用[兼容性报告](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml)。
- 误报、漏报或意外的澄清使用[路由用例报告](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml)。
- 非破坏性观测流程遵循[报告兼容性结果](../../en/compatibility.md#report-a-compatibility-result)。

更新、移除、禁用或排障流程，请继续阅读[管理安装](managing-installation.md)。
