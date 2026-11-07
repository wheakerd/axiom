# 示例

[English](../en/examples.md) | 简体中文

这些示例描述的是路由契约，而不是执行记录。生效中的指令与用户的实际授权仍然起决定作用。完整流程请遵循链接到的技能；[架构](../en/architecture.md)解释了门控如何选择并组合各个所有者。

点名技能的请求在这里使用 Codex 的 `$skill-name` 形式。在 Claude Code 中，输入 `/axiom:skill-name` 或用自然语言点名该技能。

## `clarify-intent`

> Clean up the old records.

如果上下文让归档、去重与删除成为实质上不同的结果，门控会选中 [Clarify Intent](../../plugin/skills/clarify-intent/SKILL.md)。在依赖性工作之前，针对每个待定决定提出一个聚焦的问题，给出合理的选项与自定义回答；彼此独立的决定在同一轮中一起询问。当更正很明确时，“Maybe fix this identified typo”不需要澄清。权限绕过模式不能解决意图。

## `delegate-simple-task`

> Use $delegate-simple-task to assess this small edit for my ordered model candidates, and show me the exact model and brief before delegating.

[Delegate Simple Task](../../plugin/skills/delegate-simple-task/SKILL.md) 由显式调用或明确的委托请求选中；除非你点名宿主自带的子智能体工具，它不会取代该技能。显式调用本身就提供了你的同意，于是该技能评估这次编辑，从你的列表中挑出第一个合适的模型，并在委托之前展示该模型与任务简报；没有显式调用时，那个唯一的提问同时也会征求你的同意。当会话中没有投递启动门控时，该技能会说明这一点，并在提出分派方案之前自行评估歧义。宿主的推理级别不是该技能的门槛：由主会话判断自己能否完整陈述工作并检查结果。

获授权激活之后，该技能评估第一个相关能力受支持的可用候选，宣布其确切模型与忠实的任务简报，并检查结果。主模型保持不变。仅凭模型名称既不能确定价格，也不能确定适用性。

经验证的权限绕过模式不能替代调用同意。激活之后，它允许在既有任务权限与宿主限制之内进行分派。否则，使用既有的分派批准，或先取得批准。缺失的模型偏好需要一个决定；委托不可用时可以回退到主会话。该技能自身不会发起澄清：启动门控会在委托之前解决实质性的歧义。

## `task-planning`

> Use the task-planning skill to create an implementation plan for search with acceptance criteria.

[Task Planning](../../plugin/skills/task-planning/SKILL.md) 在显式调用时创建计划，并在你要求移除、替换、合并、重排或收窄其条目时修订既有计划；没有调用的新“make a plan”请求留在宿主处理。随后一次移除导出功能的请求会围绕保留的工作更新计划、依赖与验收标准。显式约束在范围编辑后依然保留；使保留目标不可行的依赖需要先解决。

迁移计划保留其专门的可逆变更所有者。调度、状态更新与实施留在各自的所有者那里。计划不授权执行或调度。

## `continuous-progress`

> Use continuous-progress to finish this defined migration with fresh workers and an independent supervisor. Stop when its tests pass or I cancel.

[Continuous Progress](../../plugin/skills/continuous-progress/SKILL.md) 只从显式调用启动。它首先使用该宿主的操作参考，检查当前宿主能否启动新的工作者、指向后继协调者并唤醒独立的监督者。没有可用的独立唤醒机制时，运行会等待该能力并报告自动恢复不可用，而不是模拟一个监督者。普通的继续请求、只使用原生目标的请求以及对该技能的讨论都不会选中它。

## `local-web-search`

> Use my local browser to search the documentation and read relevant results.

[Local Web Search](../../plugin/skills/local-web-search/SKILL.md) 适用于通过你自己的浏览器、CLI、脚本或 HTTP 客户端进行检索之前，包括从云端搜索回退到这类客户端。宿主内建的网页工具留在宿主处理；根据工具的文档与你的措辞判断它在哪里运行，而不发送探测。

保持机器信息披露有边界、串行浏览、保持浏览器身份，并停止对遇到挑战或速率限制的站点的自动访问。人工接管会等待明确的就绪并保留用户的页面。对 Cloudflare 或其他站点的机器人判定没有任何保证。已确认的云端搜索与概念性的机器人检测问题不会选中这条路由。

## `agents-architect`

> Audit this repository's AGENTS.md discovery, then split oversized guidance into scoped .agents/ routes.

[Agents Architect](../../plugin/skills/agents-architect/SKILL.md) 清点元数据、加载相关主题，并把编辑限制在获授权的指令系统之内。它区分生效中的指令与复制或历史材料，并对宿主发现的非 AGENTS 指令候选保持只读。该请求不授权无关的源码编辑、受保护的插件元数据、提交或推送。

会话胶囊之类的任务状态位于仓库的 Git 元数据中，在被索引的工作树之外；[记忆与状态参考](../../plugin/skills/agents-architect/references/memory-and-state.md)负责该位置、记忆层级与扁平注册表。

显式的 `effective-instructions:reconcile-preview` 请求一次与实现的只读比较；`effective-instructions:reconcile` 请求一次获授权的指令系统更新。普通的维护、回滚或压缩不会隐式选中这些模式。

## `agent-plugin-architect`

> Audit this packaged plugin's shared Skills, route ownership, manifests, and hooks.

[Agent Plugin Architect](../../plugin/skills/agent-plugin-architect/SKILL.md) 清点该包并只加载活动的架构参考。它可以为另一个项目设计 Codex 或 Claude Code 集成；Axiom 自身同时支持两个宿主。显式的发布就绪审计报告每个关卡的检查结果与下一个有边界的决定，同时保持只读。

仓库本地的指令系统属于 `agents-architect`；普通的插件源码或文档留在宿主原生处理。安装、发布、部署与 Git 提交需要各自的活动阶段归属与权限。显式的上下文成本重设计可以加上 `optimize-agent-usage`。见该技能的[路由与触发契约](../../plugin/skills/agent-plugin-architect/references/route-and-trigger-contracts.md)。

## `optimize-agent-usage`

> Reduce the credits, tokens, and context used by these Skills without weakening validation or safety.

[Optimize Agent Usage](../../plugin/skills/optimize-agent-usage/SKILL.md) 检查元数据与路由链，在宿主暴露指标时进行测量，否则把大小或调用次数标注为代理指标。在前后比较相同的质量场景。不要悄悄降低模型或推理设置、移除必需的检查、安装测量工具，或凭空给出确切的节省数字。普通的算法性能工作不会选中这条路由。

## `review-axiom-task`

> Explain the observable trigger, blocked effect, permitted remainder, and evidence for Axiom's prior refusal without revealing hidden reasoning.

[Review Axiom Task](../../plugin/skills/review-axiom-task/SKILL.md) 独立地评估这次有边界的审查，并把断言标注为已观察、已重建或不可用。先前的拒绝与助手的叙述没有策略权限。当前状态可以验证现在的结果，但不能确立过去的授权或因果关系。审查不会重跑任务、编造缺失的历史、打开无关的目标、改变状态或持久保存追踪记录。

## `verify-completion`

> Verify that this task is actually complete against current evidence before I accept the summary. List each criterion with what you observed now.

[Verify Completion](../../plugin/skills/verify-completion/SKILL.md) 冻结原始标准，逐项直接重新核查，并为每个标准报告 `met`、`not met` 或 `unverifiable`，同时给出每个输入的事实类别。压缩之后，它把带过来的摘要当作待核查事项的索引，并在任何新的变更之前重新读取记录的产物。当证据与请求冲突时，它先陈述冲突与建议，再在用户的权限之内行动。状态问题或常规继续，包括压缩后的继续，都不会选中这条路由；那个时刻由启动门控负责，而审查某个已识别的 Axiom 任务的路由仍归 `review-axiom-task`。

## `confirm-external-action`

> Send this approved message once to alex@example.com from the support account, with no attachments, then verify its service status.

[Confirm External Action](../../plugin/skills/confirm-external-action/SKILL.md) 绑定执行者、确切的收件人与正文、附件、披露、成本、次数与重试策略。只执行获授权的信封，并通过拥有该效果的服务进行验证。不确定的结果不授权再次发送。只起草不发送的工作留在宿主原生处理。消息、网站或工具结果中的指令不能授予操作权限。

## 共享的机器凭证生命周期

> Rotate this service certificate through an overlap window, verify the replacement consumer, then revoke the exact old certificate.

这会同时选中 `confirm-external-action` 与 `reversible-system-change`，并使用同一份[生命周期参考](../../plugin/skills/using-axiom/references/credential-lifecycle.md)。先清点元数据；分别授权并验证提供方创建、消费方激活、回滚、撤销与清理。绝不暴露密钥值，也绝不把一个所有者的权限当作另一个的。

不带写入的轮换计划只选中可逆所有者；对确切的、已验证的旧凭证进行仅提供方侧的撤销只选中外部所有者。人工登录与概念性的认证帮助不会产生任何凭证生命周期路由。含义不清的提供方结果只进入验证，不重试。

## `traceable-git-submit`

> Create local checkpoint commits for README.md and docs/, preserve every other path, and do not push.

[Traceable Git Submit](../../plugin/skills/traceable-git-submit/SKILL.md) 解析确切的 Git 根目录与获授权的路径，冻结并验证候选，并保留并发的索引状态。该请求允许有边界的检查点，而不是推送。合并整理、提交与恢复清理保留各自独立的权限与阶段契约。

> $traceable-git-submit: git push origin main once without force.

显式调用选中轻量的直接提交阶段。它保持钩子生效，推送一次，不创建 Axiom 溯源元数据，并以正常的 Git 结果作为主要证据。确定性的结果不需要额外查询；实质上含义不清的结果最多允许对拥有该远程的一方查询一次。

> Commit the prepared plugin changes, create the agreed release tag, and push the branch and tag.

这个组合请求会选中[已备妥发布的提交](../../plugin/skills/traceable-git-submit/references/prepared-release-submit.md)。冻结获授权的变更、提交信息、确切标签、签名要求与推送目标。在允许直接创建标签的地方，把确切的分支与标签原子地推送到每个获授权的端点，然后验证两个引用。如果某个仓库控制器负责受保护标签的创建，就把该操作交给其单独授权的所有者。该阶段不创建检查点或基线元数据，也不授予 GitHub Release、市场或安装操作。不确定的推送结果允许验证，而不是自动重试。

普通的“commit the staged change and git push origin main”留在宿主原生处理。预期中的、已获授权的暂存集是正常情况，不是人为制造的冲突。额外的路径、目标漂移、强制推送、重试或清理需要各自的权限与检查。合并整理与恢复的细节属于该技能而不是本示例。

## `reversible-system-change`

> Prepare a read-only migration plan for the staging database, including rollback evidence and promotion gates. Do not download or change anything.

[Reversible System Change](../../plugin/skills/reversible-system-change/SKILL.md) 通过元数据识别目标与持久效果，然后区分既有的备份材料与当前已验证的恢复路径。该规划阶段不允许读取密钥内容、下载、持久写入、重启、数据迁移或晋级。

隔离的恢复演练是一次单独授权的持久写入。它可以确立恢复证据，但不授权完整的变更或清理。带有重大外部效果的部署还会选中外部操作所有者；两条路由都不能满足对方的门禁。

如果你后来要求执行而当前的恢复验证无法运行，该技能会在候选或活动状态被改变之前停止，并点明哪些效果将无法恢复。决定权在你：显式选择在没有经验证的回滚的情况下继续，是一次知情放弃，只对那些被点明的效果解除回滚要求；其他每个效果都保留其回滚。随后变更在该技能的其他所有规则之下继续，包括其权限、写集、失败与验证门禁；该放弃会被记录，而该变更绝不会被报告为可逆。

## 通知与语言

当门控为一个发布已备妥发布说明的请求选中 `confirm-external-action` 时，该轮以一行可见文本开头，例如 `axiom:confirm-external-action`，后面跟原因，比如在执行之前绑定确切的发布目标。随后的工作行，包括信封、命令与验证，都是英文；当请求以另一种语言写成时，结尾的总结使用那种语言。不选中任何路由的请求不带通知，而思考块内的通知不算。

## 不应路由的请求

| 请求 | 原因 |
| --- | --- |
| "Fix this README typo" or "summarize this plugin README" | 普通的文档工作 |
| "Refactor this parser and run its tests" | 普通的源码工作，即使在插件仓库中 |
| "What version is running?" or "explain rollback" | 没有持久变更任务的状态或概念性帮助 |
| "Commit the staged change and git push origin main" | 普通的具名远程、非强制 Git 工作 |
| "Make this algorithm use less memory" | 软件性能，而不是智能体用量 |
| "Draft an email, but do not send" | 没有请求外部效果 |
| "Summarize what changed in this coding task" | 普通的总结，而不是对已识别 Axiom 任务的审查 |

无路由是正常结果。它既不拒绝任务，也不放松宿主、仓库或用户的指令。

## 含义不清的请求

> Either redesign this plugin's architecture or install it in production; choose one.

这两个备选项会改变所有者、写入面与权限，而提供生产环境安装这一选项并不授权它，因此门控在选择操作路由之前只选中澄清。只有在每个备选项都可逆且已获授权时，委托的选择才会落定。保留每个原始目标并分别解释权限限制；不要用规划或审查替代安装。用户做出选择后，路由所选的工作，不再重新讨论已落定的条件。

> Audit either this repository's AGENTS.md instructions or this packaged plugin's hook architecture; your call.

两个备选项都是请求已经授权的只读审计，因此不需要提问。模型挑选符合你的环境与目标的那一个，例如这个仓库实际拥有的那个表面，在开始之前说明选了哪个以及为什么，以便你可以改变方向，然后把它路由给其所有者。
