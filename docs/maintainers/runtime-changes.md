# Runtime Changes

Use this guide when changing installed Skills, route matching, always-loaded
context, package declarations, or Hooks. Start with the contributor workflow in
[CONTRIBUTING.md](../../CONTRIBUTING.md) and classify the exact final diff under
[Runtime and Repository Identity](../runtime-identity.md#classify-a-change).

This is contributor guidance. The checked-in Skills, declarations, and wrappers
remain the executable or instruction sources; documentation does not grant
action authority.

## Skill And Package Ownership

Codex installs the shared [skills/](../../skills/) source. Keep the
[Codex manifest](../../.codex-plugin/plugin.json) pointed at `./skills/` and
bind its version to the current runtime identity. Do not create a
platform-specific copy of a shared Skill.

The top-level `using-axiom` Skill is the startup routing gate. Other top-level
Skills provide the focused workflows it selects. Supporting `references/` and
`agents/` resources belong to their owning Skill and load on demand; they are
not independent public routes.

Axiom installs Markdown Skills and foreground Hook definitions. It has no
installed daemon, background updater, network update check, or bundled runtime
dependency. Repository validation may use a host-provided interpreter, but it
must not become a dependency of the installed plugin.

## Routing Invariants

- Keep `using-axiom` as the startup routing gate. It honors higher-priority
  instructions, selects the smallest clearly matching route, and continues
  normally when no Axiom route applies.
- Do not turn Axiom into a catch-all for ordinary coding, documentation, Git,
  or status requests.
- Route `optimize-codex-usage` only from an explicit Codex credit, token,
  context, Skill/AGENTS/MCP-loading, or consumption-diagnosis goal. Software
  performance wording alone is not a trigger.
- Keep route definitions and triggers in English. Unambiguous requests in
  other languages may normalize to the canonical English route; they do not
  create localized aliases.
- Preserve existing user work and treat missing evidence, tooling, or access
  as unverified rather than as a passing result.
- Keep volatile model prices, plan limits, and quotas out of always-loaded
  instructions. Label byte, word, and call measurements as proxies unless the
  host exposes exact scoped usage. Never auto-change the main model or
  reasoning settings.
- Child model selection belongs to `delegate-simple-task`: use the user's
  ordered candidates and current host support, disclose the exact model and
  task, and retain the Full Access and assignment-authority boundaries.

When editing a route, review its direct references and examples for accidental
permission expansion. State separately whether the change affects matching,
planning, mutation authority, stop conditions, rollback, or completion
evidence. Review the installed behavior in Codex when the runtime changes, and
report unobserved behavior as `NOT-RUN`.

## Always-Loaded Context

Compare routing growth cumulatively with the immutable baseline in
[Routing Context Budget](../../evals/context-budget/README.md). An increase of
at least 256 UTF-8 bytes or 5% requires review and a substantive justification;
this is a review trigger, not a quality pass/fail shortcut.

Keep the always-loaded gate at least 15% below the 8,192-byte instruction
boundary after equivalent routing and safety acceptance, with roughly 6-6.5
KiB preferred when precision permits. Treat 8,192 bytes as a rejection guard,
not an authoring target. These targets do not establish that the current gate
meets them; the context-budget report owns the measured result.
The publication aggregate enforces the 15% minimum against the actual gate
bytes, allowing at most 6,963 bytes. A passing size check does not replace
equivalent routing and safety acceptance.

Any reduction experiment must use the same fixed routing workload before and
after and report both routed and no-route results as passing. Bind reduction
evidence to the immediate predecessor while retaining v0.7.9 as the cumulative
growth baseline. Do not remove a safety, authorization, stop, or evidence rule
or weaken quality merely to meet a size target.

## Hook Changes

Codex declares [hooks/codex-hooks.json](../../hooks/codex-hooks.json) and reads
the [startup routing gate](../../skills/using-axiom/SKILL.md) through
`SessionStart`, including `compact`.
Keep the conventional `hooks/hooks.json` absent. The [Hook Reference](../reference/hooks.md)
renders the canonical declarations and packaged wrappers for inspection.

Review any Hook change command by command. A Hook must remain foreground-only,
locally inspectable, and limited to loading the routing gate. Do not add file
writes, network calls, credential access, a daemon, watcher, scheduled task, or
automatic update behavior. Update the relevant manifest and public trust
documentation whenever a declared Hook path or command changes.

Hook and Hook-workflow changes require the
[native integration checks](validation.md#hook-runtime-integration) on every
available target host, in addition to the ordinary contributor checks. A pass
on one operating system does not establish behavior on another.
