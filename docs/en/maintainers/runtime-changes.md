# Runtime Changes

Use this guide when changing installed Skills, route matching, always-loaded context, package declarations, or Hooks. Start with the contributor workflow in [CONTRIBUTING.md](../../../CONTRIBUTING.md) and classify the exact final diff under [Runtime Identity](../runtime-identity.md#classify-a-change), which also assigns the version increment and governs bundling.

This is contributor guidance. The checked-in Skills, declarations, and wrappers remain the executable or instruction sources; documentation does not grant action authority.

## Skill And Package Ownership

Codex and Claude Code install the same shared [skills/](../../../plugin/skills) source. Keep the [Codex manifest](../../../plugin/.codex-plugin/plugin.json) and the [Claude Code manifest](../../../plugin/.claude-plugin/plugin.json) pointed at `./skills/` and without a `version` field; the Release workflow stamps the released version into both on the `release` branch. Do not create a platform-specific copy of a shared Skill.

The top-level `using-axiom` Skill is the startup routing gate. Other top-level Skills provide the focused workflows it selects. Supporting `references/` and `agents/` resources belong to their owning Skill and load on demand; they are not independent public routes.

Each Skill opens with a short direction paragraph and an Invariants section of named rules that bind in every phase, including the references its active phase loads. Every prohibition a Skill or its references state, a never, only, or stop, also binds; everything else in the Skill is a default the model may adapt, saying so. The gate defines the shared terms, a Skill defines the terms it introduces where they first appear, and dated host facts live in the gate's `codex-host.md` and `claude-code-host.md` references. Keep an invariant only for a rule that protects authority, prevents an irreversible or duplicated effect, handles untrusted input, or rests on a session-observable fact.

Axiom installs Markdown Skills and foreground Hook definitions. Explicit continuous-progress runs may use host-owned native scheduling. Axiom has no installed daemon, background updater, network update check, or bundled runtime dependency. Repository validation may use a host-provided interpreter, but it must not become a dependency of the installed plugin.

## Routing Invariants

- Keep `using-axiom` as the startup routing gate. It honors higher-priority instructions, selects the smallest clearly matching route, and continues normally when no Axiom route applies.
- Do not turn Axiom into a catch-all for ordinary coding, documentation, Git, or status requests.
- Route `optimize-agent-usage` only from an explicit credit, token, context, Skill/instruction-file/MCP-loading, or consumption-diagnosis goal. Software performance wording alone is not a trigger.
- Route `verify-completion` only from an explicit request to verify or audit completion or from a completion claim that rests on recalled or summarized facts. The startup gate alone owns the compaction moment; status questions and routine continuation, including continuation after compaction, stay host-native.
- Keep route definitions and triggers in English. Unambiguous requests in other languages may normalize to the canonical English route; they do not create localized aliases.
- Preserve existing user work and treat missing evidence, tooling, or access as unverified rather than as a passing result.
- Keep volatile model prices, plan limits, and quotas out of always-loaded instructions. Label byte, word, and call measurements as proxies unless the host exposes exact scoped usage. Never auto-change the main model or reasoning settings.
- Simple-task child model selection belongs to `delegate-simple-task`. Its [activation](../../../plugin/skills/delegate-simple-task/SKILL.md#activation) requires an explicit invocation or a clear delegation request and the user's consent, which the one model-and-brief confirmation can supply; the startup gate's delivery is advisory context for ambiguity, and the host's reasoning level is not a condition. Preserve consent in route metadata, direct requests, and resume behavior before applying assignment permissions.
- `continuous-progress` inherits the observed model and effort for its workers and successors. Its explicit activation, host capability checks, independent native supervisor, compaction recovery, and shutdown remain separate from simple-task delegation. It must not install a scheduler or change the hook.

When editing a route, review its direct references and examples for accidental permission expansion. State separately whether the change affects matching, planning, mutation authority, stop conditions, rollback, or completion evidence. The repository does not measure installed behavior, so do not describe behavior you did not observe as observed.

## Always-Loaded Context

The always-loaded cost has two halves: the startup gate, and the bundled skill descriptions that each host lists on every turn. Every byte of either is paid in every session, routed or not, so add only what selection or a binding rule needs.

Keep at least 10% headroom below the 8,192-byte authoring boundary for the gate. This is an engineering reserve, not a platform limit. The publication aggregate rejects a gate over 7,372 UTF-8 bytes (`8192 * 90 // 100`). Each host also caps hook output on its own terms: Codex about 2,500 tokens per message by default, Claude Code 10,000 characters of stdout. Do not rewrite stable routing merely to preserve an earlier file size, and do not remove a safety, authorization, stop, or evidence rule or weaken quality merely to meet a size target. A passing size check does not replace review of the changed text.

## Hook Changes

Codex declares [plugin/hooks/codex-hooks.json](../../../plugin/hooks/codex-hooks.json) and Claude Code declares [plugin/hooks/claude-hooks.json](../../../plugin/hooks/claude-hooks.json). Both declare the same three host-documented events: `SessionStart`, including `compact` and `fork`, reads the [startup routing gate](../../../plugin/skills/using-axiom/SKILL.md); `UserPromptSubmit` prints one static statement; `Stop` runs the shared `plugin/hooks/stop-check.sh` script, which continues the turn at most once. Keep the conventional `plugin/hooks/hooks.json` absent. The [Hook Reference](../reference/hooks.md) renders the canonical declarations and packaged scripts for inspection.

Review any Hook change command by command. A Hook must remain foreground-only, locally inspectable, and limited to printing Axiom's own static text: the routing gate, one sentence, or one JSON object. It never reads session content into context, and a Stop handler must stay guarded by `stop_hook_active` so it continues a turn at most once. Do not add file writes, network calls, credential access, a daemon, watcher, scheduled task, or automatic update behavior. Keep the static texts stable: Codex requires every user to review a changed packaged script again, so a text edit is a release decision, not a wording tweak. Update the relevant manifest and public trust documentation whenever a declared Hook path, command, or script changes.

Hook and Hook-workflow changes require the [native integration checks](validation.md#hook-runtime-integration) on at least one supported operating system, in addition to the ordinary contributor checks. The required CI matrix covers the other systems' command variants.
