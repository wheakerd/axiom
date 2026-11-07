# Axiom 文档

[English](README.md) | 简体中文

使用本索引找到负责你所需任务或事实的文档。下面的位置是当前的公开规范结构。

当前指南描述的是与文档同一份源码快照。比较源码树、已发布版本与已安装包时，参见[源码与版本范围](maintainers/documentation-policy.md#source-and-version-scope)。

## 按任务开始

| 我想要 | 从这里开始 | 读者 |
| --- | --- | --- |
| 安装 Axiom 并尝试一个路由请求 | [快速开始](guides/getting-started.zh-CN.md) | 用户 |
| 更新、禁用、移除或排查 Axiom | [管理安装](guides/managing-installation.zh-CN.md) | 用户 |
| 检查确切的 Hook 命令 | [Hook 参考](reference/hooks.md) | 用户与审计者 |
| 理解 Axiom 做什么 | [架构](architecture.md) | 用户与审阅者 |
| 审阅权限与信任边界 | [信任模型](trust-model.zh-CN.md) | 用户与安全审阅者 |
| 查看当前的宿主支持 | [兼容性](compatibility.md) | 用户与审计者 |
| 查看路由示例 | [示例](examples.zh-CN.md) | 用户与审阅者 |
| 解决一个不明确的请求 | [Clarify Intent 示例](examples.zh-CN.md#clarify-intent) | 用户 |
| 在不更换主模型的情况下委托简单工作 | [Delegate Simple Task 示例](examples.zh-CN.md#delegate-simple-task) | 用户 |
| 创建或修订任务计划 | [Task Planning 示例](examples.zh-CN.md#task-planning) | 用户 |
| 显式地跨会话延续一项任务 | [Continuous Progress](../plugin/skills/continuous-progress/SKILL.md) | 用户 |
| 通过本地浏览器或客户端做检索 | [Local Web Search 示例](examples.zh-CN.md#local-web-search) | 用户 |
| 报告宿主结果 | [报告兼容性结果](compatibility.md#report-a-compatibility-result) | 测试者与审计者 |
| 理解包身份 | [运行时身份](runtime-identity.md) | 维护者与审计者 |
| 决定某项变更的版本增量或打包方式 | [版本增量](runtime-identity.md#version-increment) | 维护者 |
| 审阅仓库控制 | [仓库治理](repository-governance.md) | 维护者 |
| 贡献文档 | [文档策略](maintainers/documentation-policy.md) | 贡献者 |
| 准备发布文档与证据 | [发布文档与证据](maintainers/release-documentation.md) | 维护者与审计者 |
| 决定 Axiom 在哪里上架并记录提交 | [分发渠道](maintainers/distribution-channels.md) | 维护者 |
| 做出贡献 | [贡献指南](../CONTRIBUTING.md) | 贡献者 |
| 更改技能、路由或 Hook | [运行时变更](maintainers/runtime-changes.md) | 贡献者 |
| 运行仓库检查并解读结果 | [贡献者验证](maintainers/validation.md) | 贡献者 |

在 [GitHub Discussions](https://github.com/wheakerd/axiom/discussions) 提问，并通过 [GitHub Issues](https://github.com/wheakerd/axiom/issues/new/choose) 表单提交可处理的报告。安全问题请按 [SECURITY.md](../SECURITY.md) 中的流程报告；社区期望见[行为准则](../CODE_OF_CONDUCT.md)。

## 发布历史

发布事实请查阅[已发布的 Releases](https://github.com/wheakerd/axiom/releases)。仅有发布并不能确立已安装宿主上的行为。

- [更新日志](../CHANGELOG.md)记录每个版本的用户可见变更及需要的操作。
- [运行时身份](../.ci/runtime-identity.json)记录当前版本与已安装文件的摘要。
- [早期记录](compatibility.md#earlier-records)指明保留版本说明、路由评估与宿主观测记录的发布标签。

## 当前结构

| 位置 | 职责 |
| --- | --- |
| `plugin/` | 两个宿主共用的已安装插件根目录；仓库的其余部分支持开发、验证与发布 |
| 根目录 `README.md` | 产品介绍、安装与更新快速入门以及首次使用 |
| 根目录 `CONTRIBUTING.md` | 贡献入口、仓库地图与审阅清单 |
| 根目录 `SECURITY.md` | 支持的安全范围与私下漏洞报告 |
| 根目录 `CODE_OF_CONDUCT.md` | 社区行为期望与执行联系人 |
| 根目录 `CHANGELOG.md` | 用户可见的变更、影响与需要的操作 |
| `docs/guides/` | 首次使用以及由宿主管理的安装生命周期 |
| `docs/` 下的主题文档 | 架构、示例、信任、兼容性、身份以及仓库治理 |
| `docs/reference/` | 确切的公开技术参考：技能参考与经校验的 Hook 渲染 |
| `docs/maintainers/` | 运行时编写、验证、文档与发布流程 |
| `.ci/` | 仓库检查、发布脚本与机器可读的运行时身份 |
| 英文文档旁的 `<name>.zh-CN.md` | 该文档的简体中文翻译；英文为规范版本，翻译与其源文档在同一次变更中更新 |

完整的仓库地图见[贡献指南](../CONTRIBUTING.md#repository-layout)。

文档类别、规范所有者、迁移规则与验证要求见[文档策略](maintainers/documentation-policy.md)。
