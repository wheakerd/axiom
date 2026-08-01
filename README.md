# Axiom

Think before AI thinks.

Axiom is a safety-first, request-routed workflow plugin for Codex and Claude
Code. It is for developers and maintainers who want repository instructions,
Git publication, and persistent system changes to begin with explicit scope,
authority, and evidence without turning every coding request into a special
workflow.

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

Only after reviewing the hook for your host, run the routed request and control
request above. Expect `agents-architect` to inventory and report only for the
read-only `AGENTS.md` audit; the README summary request should continue normally
without changing files.

If either result differs, use the non-destructive checks in
[Getting Started](docs/getting-started.md) rather than deleting caches or
rewriting local state.

## Workflows At A Glance

| Route | Select it for | Core boundary |
| --- | --- | --- |
| `agents-architect` | Initializing, auditing, splitting, migrating, or maintaining an `AGENTS.md` system, its `.agents/` routes, or repo-local skills | Inspect first; change only the authorized instruction system and keep protected plugin metadata out of scope |
| `traceable-git-submit` | Authorized checkpoint commits, baseline/provenance tracking, consolidation, or a one-final-commit submit or push flow | Freeze the exact Git root, path set, commit series, and push targets; a checkpoint request does not authorize a push |
| `reversible-system-change` | Planning, rehearsing, or executing a persistent install, upgrade, deployment, migration, retention action, or promotion with rollback or data risk | Plan-only work stays read-only; mutation requires an exact target, explicit authority, and current rollback evidence |

The startup gate is `using-axiom`. It selects the smallest matching route and
continues normally when none applies. See [Examples](docs/examples.md) for
routed requests and non-routing controls.

## Deliberate Non-Goals

Axiom is not a general-purpose memory system, persistent context database,
autonomous multi-agent framework, background policy daemon, or workflow for
every coding task. It does not prevent every model error, replace host or
repository permissions, or turn command success into proof of an outcome.

It also does not start a service, watcher, polling job, or automatic update
channel. Updates happen only through an explicit host marketplace action.

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
to act. For example, selecting `reversible-system-change` for a migration plan
keeps the work read-only, and selecting `traceable-git-submit` does not create
authority to commit or push unless the user's request supplies it. Read the
[Architecture](docs/architecture.md) and [Trust Model](docs/trust-model.md) for
the full boundary.

## What Gets Installed

Both platforms install the same checked-in `skills/` source. No `SKILL.md`
content is copied or forked for a host.

### Shared skills

- `using-axiom`, the session-start routing gate.
- `agents-architect`, the repository-instruction workflow.
- `traceable-git-submit`, the checkpoint and publication workflow.
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

Axiom does not check for or install updates automatically. Refresh the relevant
marketplace only when you choose to.

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
- [Changelog](CHANGELOG.md) and [v0.3.1 release notes](docs/releases/v0.3.1.md):
  release history and version-specific evidence.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing shared skills, platform
wrappers, hooks, or public claims. The focused distribution check is:

```bash
python3 scripts/check-distribution-drift.py
```

It compares the skill tree with both manifests, both marketplace wrappers, and
the four-item `Shared skills` list above. It is a contributor and CI check, not
an installed runtime dependency.

## License

MIT
