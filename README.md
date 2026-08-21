# Axiom

[![Release](https://img.shields.io/github/v/release/wheakerd/axiom?sort=semver)](https://github.com/wheakerd/axiom/releases/latest)
[![Distribution and publication guards](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Think before AI thinks.

**Workflow guardrails for Codex and Claude Code.**

**Axiom is a safety-first workflow router for high-impact coding-agent
actions. It makes scope, authorization, evidence, and rollback explicit while
ordinary coding requests continue normally.**

Capable coding agents can begin before the target, authority, rollback path, or
proof of success is clear. Axiom loads one focused workflow when a request
needs those boundaries. It does not grant mutation authority: selecting a
route never, by itself, permits an edit, commit, push, deployment, deletion,
credential use, or external action.

Unlike a generic prompt collection, Axiom has an inspectable session hook, a
small routing gate, shared versioned Skills, route-specific stop conditions,
and checked-in validation fixtures. It is a public beta, not a sandbox or a
guarantee that an agent cannot make a mistake.

**Scope. Authority. Evidence. Rollback.**

| Safe first request | Expected boundary |
| --- | --- |
| "Perform a read-only audit of this repository's `AGENTS.md` instruction system. Report findings only; do not modify files." | Select `agents-architect`, report evidence, and stop without changes |
| "Summarize the purpose of this README. Do not modify files." | Select no Axiom route and continue normally |

Install one host, inspect the installed hook, then test one routed request and
one no-route control. Report the observed result with the
[compatibility form](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml)
or report a false positive or false negative with the
[routing-case form](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml).

## 60-Second Start

Choose one host and install Axiom for Codex & Claude Code from the Git
marketplace.

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

Only after reviewing the hook for your host, run the two safe prompts above.
The first request is expected to select `agents-architect` and remain
read-only. The second is expected to select no Axiom route and continue through
the host normally. These are expected contracts, not claims that your host has
already reproduced them.

If either result differs, use the non-destructive checks in
[Getting Started](docs/getting-started.md) rather than deleting caches or
rewriting local state.

## When Axiom Routes

| User outcome | Route | Core boundary |
| --- | --- | --- |
| Audit or maintain repository instructions | `agents-architect` | Inspect first; changes remain limited to the authorized instruction system |
| Reduce Codex usage overhead | `optimize-codex-usage` | Preserve the required quality and safety bar; never invent hidden usage data |
| Review an Axiom-guided task | `review-axiom-task` | Keep the retrospective read-only and label unavailable history |
| Confirm a consequential external action | `confirm-external-action` | Bind actor, target, payload, disclosure, count, and retry semantics before one verified effect |
| Make Git publication traceable | `traceable-git-submit` | Keep checkpoint, consolidation, remote refresh, push, and cleanup as independent permissions |
| Plan or execute a reversible persistent change | `reversible-system-change` | Separate planning, rehearsal, promotion, rollback, and destructive retention authority |

## When Normal Execution Continues

Ordinary coding, documentation, explanation, status, local-commit, and
conceptual requests continue through the host normally when no route clearly
matches. A no-route result is not a safety certification; the host's normal
permissions and repository instructions still apply.

The startup gate is `using-axiom`. It selects the smallest matching route and
continues normally when none applies. See [Examples](docs/examples.md) for
routed requests and non-routing controls.

## Public-Beta Evidence Status

The package shape, manifests, hooks, route contracts, and validation fixtures
are checked in and statically testable. Fresh-session behavior still depends on
the named host version, operating system, policy, installation method, and
installed snapshot. A current external reproduction must therefore be reported
as such; repository presence or command success is not enough.

Follow the [field-validation protocol](docs/field-validation.md) to classify a
result as checked in, statically validated, host observed, externally
reproduced, not verified, or unavailable. Current release-specific evidence is
kept in [Compatibility](docs/compatibility.md), with the machine-readable
current boundary in [release status](evidence/release-status.json). Version
`0.7.6` is `STATIC-ONLY`: immutable v0.7.4 observations are preserved but are
not carried forward as a current-release host pass.

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

At session start and after host compaction, the platform `SessionStart` hook
reads `skills/using-axiom/SKILL.md` into the current session. That gate:

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

For Claude Code, the `compact` source follows either manual or automatic
compaction. Successful `SessionStart` stdout is added to Claude's context, so
this is Axiom's only post-compaction routing injection. Axiom declares no
`PreCompact` handler: ordinary successful stdout from that event is not
context injection. See the official
[Claude Code hooks reference](https://code.claude.com/docs/en/hooks).

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

If routing is missing after manual or automatic Claude Code compaction, confirm
that `compact` remains in the installed `SessionStart` matcher and that exactly
one matching loading event occurred. Do not add or trust a `PreCompact`
context-loading command as a workaround; its ordinary successful stdout does
not enter Claude's context.

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
- [Field Validation](docs/field-validation.md): a safe fresh-session protocol,
  evidence labels, and design-partner reporting.
- [Security Policy](SECURITY.md): private vulnerability boundaries and public
  routing/compatibility reporting paths.
- [Distribution and Launch](docs/marketing/distribution-plan.md): current
  channel requirements, prepared listing copy, and publication gates.
- [Changelog](CHANGELOG.md) and [v0.7.6 release notes](docs/releases/v0.7.6.md):
  release history and version-specific evidence.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing shared skills, platform
wrappers, hooks, or public claims. The focused distribution check is:

```bash
python3 scripts/check-distribution-drift.py
python3 scripts/check-compatibility-evidence.py --self-test
```

It compares the skill tree with both manifests, both marketplace wrappers, and
the seven-item `Shared skills` list above, then validates version-bound host
evidence and the current static-only boundary. These are contributor and CI
checks, not installed runtime dependencies.

Pull requests to `main`, including fork contributions, run these read-only
distribution and publication checks on the proposed merge tree. The workflow
grants only `contents: read`, does not reference repository secrets, and checks
out with `persist-credentials: false`; it does not require the contributor head
to be GitHub-signed or hosted in this repository. Those results validate a
proposed tree only. Release provenance is established separately for protected
`main`, immutable `v*` tags, bounded release candidates, and GitHub Releases.

## License

MIT
