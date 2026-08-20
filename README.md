# Axiom

[![Release](https://img.shields.io/github/v/release/wheakerd/axiom?sort=semver)](https://github.com/wheakerd/axiom/releases/latest)
[![Distribution and publication guards](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Think before AI thinks.

Axiom is a safety-first, request-routed workflow plugin for Codex and Claude
Code. It is for developers and maintainers who want repository instructions,
Codex usage optimization, read-only Axiom task reviews, consequential external
actions, Git publication, and persistent system changes to begin with explicit
scope, authority, and evidence without turning every coding request into a
special workflow.

Capable agents can start executing before the target, permission, rollback, or
proof of success is clear. Axiom places a small routing gate into the foreground
session context and loads one focused workflow only when the request matches.
Codex and Claude Code use the same checked-in skills through separate platform
wrappers and hooks.

Route selection is not action authorization. Loading an Axiom workflow never,
by itself, permits an edit, commit, push, deployment, deletion, credential use,
or other mutation.

| Ask | Observable routing decision |
| --- | --- |
| "Perform a read-only audit of this repository's `AGENTS.md` instruction system. Report findings only; do not modify files." | Select `agents-architect`, inventory the instruction system, and report findings without changes |
| "Run `effective-instructions:reconcile-preview` against this repository's current implementation." | Select `agents-architect`, compare existing AGENTS claims with the live working tree through the strict read-only reconciliation protocol, and report without changes |
| "Explain the routing, authorization, actions, and evidence for this Axiom-guided task." | Select `review-axiom-task`, review only the available task evidence, and label missing history without rerunning the task |
| "Send this approved message to this exact recipient once, then verify delivery state." | Select `confirm-external-action`, bind the actor, target, payload, disclosure, count, and retry boundary before one verified external effect |
| "Summarize the purpose of this README. Do not modify files." | Select no Axiom workflow and continue normally without changing files |

## 60-Second Start

Choose one host and install from the Git marketplace.

Codex:

```bash
codex plugin marketplace add wheakerd/axiom
codex plugin add axiom@axiom
```

Start a new Codex chat or CLI session. In that fresh session, open `/hooks` and
compare the installed handler with the
[exact checked-in commands](#inspect-the-hooks).

Claude Code:

```text
/plugin marketplace add wheakerd/axiom
/plugin install axiom@axiom
/reload-plugins
```

After `/reload-plugins`, open `/hooks` and compare the installed handlers with
the [exact checked-in commands](#inspect-the-hooks).

Only after reviewing the hook for your host, run the `AGENTS.md` audit and
control request above. Expect `agents-architect` to inventory and report only
for the read-only audit; the README summary request should continue normally
without changing files. The task-review request is an optional follow-up after
a routed task and must not rerun it.

If either result differs, use the non-destructive checks in
[Getting Started](docs/getting-started.md) rather than deleting caches or
rewriting local state.

## Workflows At A Glance

| Route | Select it for | Core boundary |
| --- | --- | --- |
| `agents-architect` | Initializing, auditing, splitting, migrating, or maintaining an `AGENTS.md` system, or explicitly reconciling existing guidance with current implementation | Inspect first; reconciliation is user-triggered, evidence-led, and limited to the authorized instruction system |
| `optimize-codex-usage` | Explicitly reducing or diagnosing Codex credits, tokens, context, Skill/AGENTS/MCP loading, tool churn, or reporting overhead | Preserve the required quality, safety, authorization, rollback, and evidence bar; label proxies and never invent hidden usage data |
| `review-axiom-task` | Explicitly reviewing the routing, scope, authorization, actions, evidence, stops, and outcome of an Axiom-guided task | Keep the review read-only; separate Axiom guidance from host-agent actions; label evidence as observed, reconstructed, or unavailable |
| `confirm-external-action` | Explicitly sending, publishing, inviting, purchasing, trading, deleting, or changing external app/account state | Bind actor, target, payload, disclosure, cost, count, and retry semantics; execute once and verify through the external system of record |
| `traceable-git-submit` | Explicit checkpoint commits, baseline metadata, consolidation, recovery, or Git submit/publish/push | Keep checkpoint/provenance, consolidation, remote refresh, push, and cleanup independent; a direct push preserves history and creates no Axiom metadata |
| `reversible-system-change` | Planning, rehearsing, or executing a persistent install, upgrade, deployment, migration, retention action, or promotion with rollback or data risk | Plan-only work stays read-only; mutation requires an exact target, explicit authority, and current rollback evidence |

The startup gate is `using-axiom`. It selects the smallest matching route and
continues normally when none applies. See [Examples](docs/examples.md) for
routed requests and non-routing controls.

## Deliberate Non-Goals

Axiom is not a general-purpose memory system, persistent context database,
autonomous multi-agent framework, background policy daemon, or workflow for
every coding task. It does not prevent every model error, replace host or
repository permissions, or turn command success into proof of an outcome.

It also does not start a service, watcher, polling job, or updater. The host
controls marketplace refresh and plugin installation; Claude Code can perform
those actions in the background when marketplace auto-update is enabled.

An Axiom task review is a bounded retrospective over evidence the host exposes.
It is not telemetry, an instrumented execution trace, a source of hidden model
reasoning, or a promise that compacted or unavailable history can be recovered.

## How Routing Works

At session start or the configured compaction events, the platform hook reads
`skills/using-axiom/SKILL.md` into the current session. That gate:

1. Honors higher-priority system, developer, user, and repository instructions.
2. Matches an explicit Axiom request or a request that clearly fits a bundled
   route.
3. Selects the smallest matching skill set.
4. Loads only the references needed for the active phase.
5. Continues through the host's normal workflow when no route clearly applies.

The gate decides which instructions are relevant; it does not grant permission
to act. For example, selecting `review-axiom-task` permits only a retrospective
of the scoped task evidence; it does not rerun that task. Selecting
`reversible-system-change` for a migration plan keeps the work read-only. An
explicit consequential app action selects `confirm-external-action`; a preview
does not authorize execution, and an uncertain result is not retried blindly.
An explicit Git submit, publish, or push selects `traceable-git-submit`, while
checkpoint creation, metadata, consolidation, remote refresh, push, and cleanup
remain separate actions. A direct push preserves history and creates no Axiom
metadata. Read the
[Architecture](docs/architecture.md) and [Trust Model](docs/trust-model.md) for
the full boundary.

## What Gets Installed

Both platforms install the same checked-in `skills/` source. No `SKILL.md`
content is copied or forked for a host.

### Shared skills

- `using-axiom`, the session-start routing gate.
- `agents-architect`, the repository-instruction workflow.
- `optimize-codex-usage`, the explicit Codex consumption workflow.
- `review-axiom-task`, the read-only Axiom task-review workflow.
- `confirm-external-action`, the consequential external-action workflow.
- `traceable-git-submit`, the checkpoint and Git submission workflow.
- `reversible-system-change`, the persistent-change workflow.

Each task workflow loads its supporting Markdown references on demand.

### Platform wrappers

- Codex uses `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`,
  and `hooks/codex-hooks.json`.
- Claude Code uses `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, and `hooks/claude-hooks.json`.

Both manifests point to `./skills/`. The platform-specific hooks read the same
`skills/using-axiom/SKILL.md` gate from the installed plugin root. There is no
bundled runtime dependency or private maintenance tool in the release package.

## Inspect The Hooks

Plugin hooks execute commands in the host session, so inspect the installed
definition in `/hooks` before trusting it. Axiom's checked-in commands perform
foreground output and one local file read. If the installed definition differs,
stop trusting that hook until the installed package and this repository have
been reconciled.

### Codex `SessionStart`

The matcher is `startup|resume|clear|compact`. On Linux and macOS, the exact
checked-in command is:

```bash
printf '%s\n\n' 'You have Axiom. Load this startup front door before deciding whether any Axiom skill applies:'; cat "${PLUGIN_ROOT}/skills/using-axiom/SKILL.md"
```

On Windows, the exact checked-in command is:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Write-Output 'You have Axiom. Load this startup front door before deciding whether any Axiom skill applies:'; Write-Output ''; Get-Content -Raw (Join-Path $env:PLUGIN_ROOT 'skills/using-axiom/SKILL.md')"
```

### Claude Code `SessionStart`

The matcher is `startup|resume|clear|compact`. The exact checked-in command is:

```bash
echo 'You have Axiom. Load this startup front door before deciding whether any Axiom skill applies:'; cat "${CLAUDE_PLUGIN_ROOT}/skills/using-axiom/SKILL.md"
```

### Claude Code `PreCompact`

The matcher is `manual|auto`. The exact checked-in command is:

```bash
echo 'You have Axiom. Preserve this routing front door while compacting:'; cat "${CLAUDE_PLUGIN_ROOT}/skills/using-axiom/SKILL.md"
```

These commands contain only `printf` or `echo` plus `cat`, or PowerShell output
plus `Get-Content`. They contain no file-writing, background-launch, or network
command. The hook reads the routing gate; the gate makes the route decision.

## Updating

Axiom itself does not check for, download, or install updates. The host owns
that lifecycle. To request a manual update, use the relevant host workflow.

Codex:

```bash
codex plugin marketplace upgrade axiom
```

Claude Code:

```text
/plugin marketplace update axiom
/plugin update axiom@axiom
/reload-plugins
```

In a supported Codex workspace plugin UI, use **Refresh**. Start a new Codex
session after refreshing, or reload Claude Code plugins. Review any changed hook
again before trusting it.

Claude Code can also refresh a marketplace and update its installed plugins on
disk in the background after startup. Auto-update is disabled by default for
third-party and local development marketplaces, but a user or administrator
can enable it. The running session keeps the version loaded at launch; use
`/reload-plugins` after an update notification or wait for the next launch.
Therefore, the absence of a manual refresh does not prove that the installed
files are unchanged. See Claude Code's
[auto-update documentation](https://code.claude.com/docs/en/discover-plugins#configure-auto-updates)
and review any changed Axiom hook before trusting the new snapshot.

## Disabling Or Removing

To remove the exact Codex installation from the `axiom` marketplace:

```bash
codex plugin remove axiom@axiom
```

In Claude Code, disable Axiom while keeping it installed, or uninstall it:

```text
/plugin disable axiom@axiom
/plugin uninstall axiom@axiom
```

After a Codex removal, start a new session. After a Claude Code change, run
`/reload-plugins` or start a new session. Confirm that Axiom is no longer
enabled in the host's plugin list and that its hook is absent from `/hooks`
before treating it as inactive. Do not edit installed files or delete host
caches as a substitute for the host-managed disable or removal workflow.

## Troubleshooting

If the loading message or expected route is missing, first confirm in `/hooks`
that the plugin hook is installed, enabled, trusted, and identical to the
checked-in definition. Then start a fresh Codex session or run
`/reload-plugins` in Claude Code. Existing sessions may retain earlier hook and
skill state.

Do not delete host data, clear caches, edit the installed plugin, or change
global configuration merely to make routing appear. Follow the bounded
[troubleshooting sequence](docs/getting-started.md#non-destructive-troubleshooting)
and report an unavailable validator as unavailable, not passed.

## Documentation

- [Getting Started](docs/getting-started.md): installation, hook review, first
  route, control request, and non-destructive troubleshooting.
- [Examples](docs/examples.md): requests, expected routes, safety boundaries,
  and actions each route does not authorize.
- [Architecture](docs/architecture.md): wrappers, hooks, routing, on-demand
  references, and normal continuation.
- [Trust Model](docs/trust-model.md): authority, credentials, mutation,
  evidence, and update boundaries.
- [Compatibility](docs/compatibility.md): checked-in support and validation
  evidence levels.
- [Changelog](CHANGELOG.md) and [v0.7.0 release notes](docs/releases/v0.7.0.md):
  release history and version-specific evidence.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing shared skills, platform
wrappers, hooks, or public claims. The focused distribution check is:

```bash
python3 scripts/check-distribution-drift.py
```

It compares the skill tree with both manifests, both marketplace wrappers, and
the seven-item `Shared skills` list above. It is a contributor and CI check, not
an installed runtime dependency.

## License

MIT
