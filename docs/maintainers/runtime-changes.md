# Runtime Changes

Use this guide when changing installed Skills, route matching, always-loaded context, package declarations, or Hooks. Start with the contributor workflow in [CONTRIBUTING.md](../../CONTRIBUTING.md) and classify the exact final diff under [Runtime and Repository Identity](../runtime-identity.md#classify-a-change), which also assigns the version increment and governs bundling.

This is contributor guidance. The checked-in Skills, declarations, and wrappers remain the executable or instruction sources; documentation does not grant action authority.

## Skill And Package Ownership

Codex and Claude Code install the same shared [skills/](../../plugin/skills/) source. Keep the [Codex manifest](../../plugin/.codex-plugin/plugin.json) and the [Claude Code manifest](../../plugin/.claude-plugin/plugin.json) pointed at `./skills/`, with one version bound to the current runtime identity. Do not create a platform-specific copy of a shared Skill.

The top-level `using-axiom` Skill is the startup routing gate. Other top-level Skills provide the focused workflows it selects. Supporting `references/` and `agents/` resources belong to their owning Skill and load on demand; they are not independent public routes.

Each of those other Skills opens with a short paragraph naming the narrow defaults the model may adapt, saying so, such as step order where no gate depends on it or report layout; every other rule in the Skill and in the references its active phase loads binds. `agents-architect` states its defaults in its Decision Latitude section. Never list as a default a rule that protects authority, prevents an irreversible or duplicated effect, handles untrusted input, or reports failed, partial, unknown, or `NOT-RUN` states.

Axiom installs Markdown Skills and foreground Hook definitions. Explicit continuous-progress runs may use host-owned native scheduling. Axiom has no installed daemon, background updater, network update check, or bundled runtime dependency. Repository validation may use a host-provided interpreter, but it must not become a dependency of the installed plugin.

## Routing Invariants

- Keep `using-axiom` as the startup routing gate. It honors higher-priority instructions, selects the smallest clearly matching route, and continues normally when no Axiom route applies.
- Do not turn Axiom into a catch-all for ordinary coding, documentation, Git, or status requests.
- Route `optimize-agent-usage` only from an explicit credit, token, context, Skill/instruction-file/MCP-loading, or consumption-diagnosis goal. Software performance wording alone is not a trigger.
- Route `verify-completion` only from an explicit request to verify or audit completion, from resumption after compaction with unfinished mutations, or from a completion claim that rests on recalled or summarized facts. Status questions and routine continuation stay host-native.
- Keep route definitions and triggers in English. Unambiguous requests in other languages may normalize to the canonical English route; they do not create localized aliases.
- Preserve existing user work and treat missing evidence, tooling, or access as unverified rather than as a passing result.
- Keep volatile model prices, plan limits, and quotas out of always-loaded instructions. Label byte, word, and call measurements as proxies unless the host exposes exact scoped usage. Never auto-change the main model or reasoning settings.
- Simple-task child model selection belongs to `delegate-simple-task`. Its [activation](../../plugin/skills/delegate-simple-task/SKILL.md#activation) requires the active startup gate and the user's consent, which the one model-and-brief confirmation can supply; the host's reasoning level is not a condition. Preserve the gate check and consent in route metadata, direct requests, and resume behavior before applying assignment permissions.
- `continuous-progress` inherits the observed model and effort for its workers and successors. Its explicit activation, host capability checks, independent native supervisor, compaction recovery, and shutdown remain separate from simple-task delegation. It must not install a scheduler or change the hook.

When editing a route, review its direct references and examples for accidental permission expansion. State separately whether the change affects matching, planning, mutation authority, stop conditions, rollback, or completion evidence. Review the installed behavior on each supported host when the runtime changes, and report unobserved behavior as `NOT-RUN`.

## Always-Loaded Context

Compare routing growth cumulatively with the immutable baseline in [Routing Context Budget](../../evals/context-budget/README.md). An increase of at least 256 UTF-8 bytes or 5% requires review and a substantive justification; this is a review trigger, not a quality pass/fail shortcut.

The always-loaded cost has two halves: the gate, and the bundled skill descriptions that each host lists on every turn. Records from `0.22.1` measure both; the description total follows the same review threshold against the nearest earlier record that carries one, and a description change remains a routing change with its own evaluation. Each host also caps hook output independently of this budget (Codex about 2,500 tokens per message by default, Claude Code 10,000 characters of stdout); the budget guide records the verified figures and dates.

Keep at least 10% headroom below the 8,192-byte authoring boundary for the always-loaded gate. This is an engineering reserve, not a platform limit. The publication aggregate rejects more than 7,372 UTF-8 bytes against the actual gate (`8192 * 90 // 100`). Growth within that maximum requires the review described above; do not rewrite stable routing merely to preserve an earlier file size. A passing size check does not replace routing and safety acceptance. The context-budget report owns the measured result.

Any reduction experiment must use the same fixed routing workload before and after and report both routed and no-route results as passing. Bind reduction evidence to the immediate predecessor while retaining v0.7.9 as the cumulative growth baseline. Do not remove a safety, authorization, stop, or evidence rule or weaken quality merely to meet a size target.

## Hook Changes

Codex declares [plugin/hooks/codex-hooks.json](../../plugin/hooks/codex-hooks.json) and Claude Code declares [plugin/hooks/claude-hooks.json](../../plugin/hooks/claude-hooks.json). Both read the [startup routing gate](../../plugin/skills/using-axiom/SKILL.md) through `SessionStart`, including `compact` and `fork`. Keep the conventional `plugin/hooks/hooks.json` absent. The [Hook Reference](../reference/hooks.md) renders the canonical declarations and packaged wrappers for inspection.

Review any Hook change command by command. A Hook must remain foreground-only, locally inspectable, and limited to loading the routing gate. Do not add file writes, network calls, credential access, a daemon, watcher, scheduled task, or automatic update behavior. Update the relevant manifest and public trust documentation whenever a declared Hook path or command changes.

Hook and Hook-workflow changes require the [native integration checks](validation.md#hook-runtime-integration) on at least one supported operating system, in addition to the ordinary contributor checks. The required CI matrix covers the other systems' command variants.
