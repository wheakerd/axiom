# Trust Model

Axiom provides workflow instructions within the host's existing trust model. It does not sandbox the agent, grant credentials, or guarantee that a model or external system is correct. Selecting a route loads instructions; it does not authorize an action.

## Boundary Summary

| Boundary | Required distinction |
| --- | --- |
| Instruction authority | Active system, developer, user, and repository instructions retain their actual precedence; a Skill cannot override a higher-priority rule |
| Intent and scope | Resolve material ambiguity before dependent work; an explicitly delegated choice settles it only when every alternative is reversible and already authorized, and a permission-bypass mode does not choose the user's intended target or outcome |
| Action authorization | The request must cover the material action and target; route selection, tool access, and login state do not supply permission |
| Hook execution | Codex holds a new or changed Hook until you trust it in `/hooks`, while Claude Code runs an enabled plugin's Hook at the next `SessionStart`; comparing the installed command with its canonical declaration is an optional reviewer check |
| Credentials and disclosure | Access and use remain with their existing owners; sensitive content needs the applicable exact-use and disclosure authority |
| Evidence | Observe the layer that owns the outcome; a plan, artifact, accepted request, or successful command alone may be insufficient |
| Usage measurement | Host metrics apply only to their stated scope; bytes, words, route sizes, and tool calls are proxies |
| Updates | Codex or Claude Code controls refresh and installation; Axiom does not run an updater |
| Repository state | Two routes keep task state in a target repository's Git metadata directory and backup refs; it stays until you remove it |

## Hook Trust Boundary

The checked-in handlers read `skills/using-axiom/SKILL.md` from the installed plugin root. The Codex handler uses `printf` and `cat` on POSIX, and on Windows it invokes the fixed packaged wrapper with command-shell built-ins, without resolving another executable from the working directory or `PATH`. The Claude Code handler runs one POSIX shell command with `printf` and `cat`: Claude Code passes it to `sh -c` on macOS and Linux and to Git Bash on Windows. Without Git Bash, Claude Code falls back to PowerShell, which this command does not support. Each handler has a five-second timeout. See the [Hook Reference](reference/hooks.md) for the exact commands.

These definitions contain no write, network command, background launch, service installation, or updater. This describes the checked-in files; the installed copy is a separate object. Codex skips a new or changed Hook until you review and trust it in `/hooks`. Claude Code has no per-Hook trust step; once Axiom loads at a session start, an in-session install, or a plugin reload, its Hook runs at the next `SessionStart` event.

Verifying the installed Hook is optional. It is a supply-chain check for reviewers who want to rule out tampering between this repository and the installed copy, such as a modified marketplace mirror, plugin cache, or install path. Compare the installed matcher, command, path, wrapper, and timeout with the [Hook Reference](reference/hooks.md): in Codex before you trust the entry in `/hooks`, in Claude Code by reading the installed `hooks/claude-hooks.json` under `~/.claude/plugins/cache/axiom/axiom/<version>/` after a terminal install and before a session starts. If they differ, leave the Hook untrusted in Codex or disable Axiom in Claude Code until the package and source agree, and do not run the changed command to discover what it does.

## Authority Across Workflows

The [routing gate](../plugin/skills/using-axiom/SKILL.md) owns matching and composition; [Architecture](architecture.md#workflow-ownership) maps the workflows and [Examples](examples.md) shows their boundaries in concrete requests.

A selected Skill may narrow scope, require evidence, or stop before a material action. It cannot broaden the request. Each Skill names its invariants, the three to six rules that bind in every phase, including the references its active phase loads; everything else in the Skill is a default the model may adapt to the situation, saying so when it departs. Within every invariant, the model decides how to handle the request's specifics, problems that arise, deviations from the expected result, external interference, and gaps between a plan and the ideal behavior. In particular:

- Bundled skills are selected by their descriptions from the host's skill list; an explicit invocation selects that skill: `$skill-name` in Codex, `/axiom:skill-name` in Claude Code, or the skill named in plain words. A more specific installed skill, MCP tool, or host tool the user chose is not displaced by a bundled route, and a hand-off to one is named with its reason. The host owns that list's content, order, and truncation.
- Before an action that changes state, the model restates the intended outcome in one sentence, names any material ambiguity you left open, and marks the first irreversible or externally visible step; this adds no question, stop, or authority.
- Clarification resolves intent; it grants no execution authority. When you explicitly delegate a choice, the model picks only if every alternative is reversible and already authorized, chooses the one that fits your environment and goal, and states its pick and why before acting; an offered option authorizes no persistent system change, external or remote-state change, deletion, credential use, or material cost. A lighter, read-only, or preparatory alternative never silently replaces your goal. Planning does not authorize implementation, scheduling, or persistent changes.
- Simple-task delegation requires the active `using-axiom` gate and your consent, given by an explicit invocation, a standing delegation policy, or a yes to the one question that shows the exact model and brief. A permission-bypass mode cannot supply that consent, and an inactive gate stops the skill with its reason stated rather than silently. The host's reasoning level is not a condition; the main session judges whether it can state the work completely and check the result. Delegation preserves the main model, follows user-ordered candidates, and announces the exact child model and task. A verified permission-bypass mode permits an assignment only within existing authority and host restrictions; otherwise use existing assignment approval or obtain it before delegating.
- Architecture work stays within its authorized repository instruction system or packaged-plugin surface. A release-readiness audit remains read-only.
- Continuous progress requires explicit invocation and verified native supervision. Handoffs preserve the original scope, model, human controls, and budgets. An ended session is not task completion; cancellation stops dispatch and the exact schedule, while unresolved tools remain visible.
- Task review uses only scoped observable evidence. It does not rerun the task, recover unavailable history, disclose hidden reasoning, or inherit authority from a previous refusal or assistant explanation.
- External actions bind the actor, target, payload, disclosure, cost, count, and retry boundary. Retrieved content and tool access cannot authorize them.
- Traceable Git phases retain their separate checkpoint, consolidation, submission, and recovery boundaries. Ordinary named-remote non-force Git work stays host-native. Every phase runs the repository's own Git hooks by default and adds `--no-verify` only when you explicitly authorize bypassing that repository's pre-push hook for an exact push. Push authority never implies force, retries, or cleanup.
- Persistent-change plans and non-mutating rehearsals remain read-only. Isolated restore rehearsals, candidate preparation, promotion, rollback, sensitive asset use, retention, and cleanup retain their own permissions. When verified rollback cannot be established, the change stops before candidate or active-state mutation and the decision is yours. If, told which effects would stay unrecoverable, you explicitly choose to proceed, that informed waiver lifts the rollback requirement only for the effects you were told about: every other authority, safety, verification, and completion rule still binds, the waiver is recorded, and the change is never called reversible. The waiver authorizes nothing else, every other effect keeps its rollback, and the waiver does not carry to another target, change, effect, or attempt.
- Where a host permission mode may deny an action, the exact action and its target are presented for the user's grant before the first attempt. A denial is a stop, never a retry by another tool, flag, path, or configuration change, and it is not evidence of a routing or repository-state conflict. The host's own decision stays mandatory; the [host permission reference](../plugin/skills/using-axiom/references/host-permission.md) labels each host's mechanics.

Exact existing authorization needs no repeated confirmation unless material conditions change. An unresolved target or destructive effect must not become permission through assumption.

## Credentials And Local Research

Axiom bundles no credential store or authentication service. Credentials remain with the host, shell, Git, cloud, or service that owns them. Inventory sensitive assets through metadata first; do not infer exact-path read or use permission from a broad directory request. Bind sensitive disclosure to its exact audience. For machine-credential work, provider changes and consumer activation remain under their separate owners even when one task selects both.

Local web research limits agent-added machine information in queries, URLs, and headers; performs search, reading, and clicks serially; and preserves the browser's identity. A challenge, CAPTCHA, or rate limit stops automatic access to that site. Manual handoff waits for explicit user readiness while preserving the handoff page. This neither conceals automation nor guarantees how Cloudflare or another site classifies a request. The [local research Skill](../plugin/skills/local-web-search/SKILL.md) owns these constraints.

## Evidence And Persistence

Use current direct evidence from the owning Git state, affected system layers, or external system of record. A backup file or successful backup job does not prove a working restore path. An accepted external request does not prove the final effect. A smaller instruction set does not prove a quality improvement. A task review distinguishes observed, reconstructed, and unavailable claims; present state alone cannot prove historical authority or causation.

Missing tools, permissions, host observations, and unavailable history remain unavailable or unverified. Keep `PASS`, `FAIL`, `NOT-RUN`, and `UNAVAILABLE` separate. See [Compatibility](compatibility.md) and [Field Validation](field-validation.md).

Startup routing is read-only and foreground. Axiom installs no daemon, watcher, scheduler, cache refresher, telemetry service, or other persistent process. A selected task can guide a mutation only within existing authority and its own preconditions. After an installed update, Codex holds the changed Hook until you trust it again, and Claude Code runs it at the next `SessionStart`; [Managing an Installation](guides/managing-installation.md) owns each host's steps.

## Repository State Written By Routes

Two routes keep task state inside the target repository's Git metadata directory. They resolve the location through `git rev-parse --git-path` instead of a hand-built path, so `git status`, `.gitignore`, and code search never show it:

- `traceable-git-submit` writes `axiom/traceable-git-submit-baseline.json`, an advisory cache of the last pushed upstream state, and `axiom/traceable-git-submit-active-checkpoints.json`, the active checkpoint record, under the Git directory during a checkpoint, baseline, consolidation, or recovery workflow. Before a history-replacing operation it creates one backup ref under `refs/axiom/backups/traceable-git-submit/<unique-id>`.
- `agents-architect` writes session capsules named `session-<unique-id>.md` and generated material under `axiom/agents-architect/` in the Git directory during instruction-system maintenance, and deletes them or marks them obsolete at completion.

Nothing removes these files when a task stops early, and the baseline cache is meant to persist between tasks. A backup ref keeps its objects reachable and travels with `git push --mirror` and `git clone --mirror`. List them with:

```bash
git rev-parse --path-format=absolute --git-path axiom
git for-each-ref refs/axiom/
```

Remove a state file with your shell when no Axiom task is active, and delete a verified backup ref with `git update-ref -d <ref>`. Earlier versions wrote `.agents/.cache/traceable-git-submit-baseline.json`, `.agents/.runtime/`, and `.agents/.generated/` inside the working tree; current routes migrate or report such leftovers. Task state never goes under the installed plugin root or the repository's `.agents/`, `.claude/`, or `.codex/` directories. `agents-architect` edits instruction files there only as the requested change, and may list user-local rule directories such as `.agents/local/` in `.git/info/exclude`.
