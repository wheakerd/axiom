# Axiom

Think before AI thinks.

Axiom is a Codex-first plugin with parallel Claude Code support for
community-native AI workflows. It helps the active agent resolve user intent
before execution, then loads a focused workflow for the work that actually
needs it.

Axiom does not take over ordinary tasks. Its startup routing gate selects the
smallest matching bundled skill, honors higher-priority instructions, and
continues normally when no Axiom workflow applies.

## Axiom In Practice

Suppose you ask:

```text
Upgrade the staging service to v2.4.1, but do not proceed unless we can restore
the version running now.
```

Axiom routes that request to `reversible-system-change`. The agent first
identifies the exact staging target and intended writes, then distinguishes a
backup that merely exists from a rollback path whose current restore mechanism
has actually been validated or rehearsed. Candidate preparation does not grant
permission to promote it. After an authorized change, the agent checks the
selected version, runtime, and behavior before claiming completion. If recovery
cannot be proven, it stops and reports the missing evidence.

An ordinary request such as `Fix this README typo` does not match an Axiom
workflow and continues normally.

## Workflows

### AGENTS Architecture

Use `agents-architect` to initialize, audit, split, migrate, maintain, or
validate repository instruction systems:

- Turn root `AGENTS.md` into a small control plane and route scoped guidance on
  demand.
- Organize `.agents/` group indexes, domain entries, rule files, cross-cutting
  safety or risk rules, references, and repo-local skills without recursively
  loading everything.
- Separate active instructions and current repository facts from copied,
  historical, or external evidence.
- Handle no-Git repositories, unborn branches, nested roots, linked worktrees,
  ignored instruction files, route dependencies, and oversized documents
  explicitly.
- Keep generated guidance project-specific instead of copying Axiom's own
  triggers, routing protocol, or validation format into the target repository.

### Traceable Git Submit

Use `traceable-git-submit` when local work needs authorized checkpoint commits
or a one-final-commit publish flow:

- Create isolated local checkpoints only after the user authorizes commits.
- Freeze the exact path set, prove staged-tree identity, and store baseline and
  provenance state in Git metadata rather than the worktree.
- Consolidate only the exact authorized unpublished commit series into one
  final commit while preserving the final tree.
- Push only after an explicit submit, publish, or push request.
- Verify every configured push target, require explicit acceptance of
  non-atomic multi-target risk, and retain recovery state until the refreshed
  upstream and every target prove the final commit.

A checkpoint marker is not authority by itself, and a successful Git command
is not treated as proof that every remote reached the requested state.

### Reversible System Change

Use `reversible-system-change` to plan, rehearse, or execute an install,
upgrade, deployment, migration, destructive retention action, or active-version
promotion with meaningful rollback or data-safety risk:

- Plan-only and workflow-rehearsal requests remain strictly read-only.
- Execution requires one exact target, a frozen write set, and a current
  restore-validated or isolated-rehearsed rollback path that covers it.
- Candidate preparation and active promotion are separate permissions.
- Sensitive content requires authorization for the exact asset path and exact
  read or use action; broad directory access is not enough.
- Completion requires fresh evidence from every affected materialization,
  selection, runtime, delivery, behavior, and preservation layer that owns the
  requested outcome.

If usable recovery cannot be verified, this workflow stops. Accepting
irreversible risk does not satisfy its contract.

## Routing And Safety

`using-axiom` is the checked-in session-start routing gate. It:

1. Honors user, system, developer, and repository instructions first.
2. Matches a request against the most specific bundled skill description.
3. Loads only the selected route and the references needed for its active
   phase.
4. Accepts unambiguous requests in any language while keeping canonical route
   definitions in English.
5. Continues without invoking Axiom when no workflow clearly applies.

Across all workflows:

- A narrower route may add checks but cannot broaden authorization.
- Existing user work is preserved; unrelated state is not reset, hidden,
  staged, or rewritten to make a check pass.
- Access, saved credentials, default profiles, or the ability to run a command
  do not establish authority for a target or action.
- Completion claims require current direct evidence from the owning system
  layer. Missing tools, permissions, or observations are unverified, not a
  pass.
- Axiom does not commit, push, promote, delete, or mutate a remote environment
  merely because the corresponding skill was loaded.

## What Gets Installed

Both platforms install the same checked-in skill source. No `SKILL.md` content
is copied or forked for a platform.

### Shared skills

- `using-axiom`, the session-start routing gate.
- `agents-architect`, the repository-instruction workflow.
- `traceable-git-submit`, the checkpoint and publish workflow.
- `reversible-system-change`, the persistent-change workflow.

Each workflow loads its supporting Markdown references only when the active
task needs them.

### Distribution wrappers

- Codex uses `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`,
  and `hooks/codex-hooks.json`.
- Claude Code uses `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, and `hooks/claude-hooks.json`.

Both plugin manifests point at the same `./skills/` directory. Their hooks read
the same `skills/using-axiom/SKILL.md` routing gate from the installed plugin.

There is no background service, automatic updater, private maintenance tool,
or bundled runtime dependency.

## Installation

### Codex

Add the Git marketplace, then install Axiom from its configured snapshot:

```bash
codex plugin marketplace add wheakerd/axiom
codex plugin add axiom@axiom
```

In `axiom@axiom`, the first `axiom` is the plugin name and the second is the
configured marketplace name.

Start a new Codex chat or CLI session after installation. Open the hook review
UI:

```text
/hooks
```

Review Axiom's `SessionStart` command before trusting it. The hook should only
print the Axiom loading message and read
`skills/using-axiom/SKILL.md` from `PLUGIN_ROOT`.

The checked-in hook definition should match these commands exactly.

Linux and macOS:

```bash
printf '%s\n\n' 'You have Axiom. Load this startup front door before deciding whether any Axiom skill applies:'; cat "${PLUGIN_ROOT}/skills/using-axiom/SKILL.md"
```

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Write-Output 'You have Axiom. Load this startup front door before deciding whether any Axiom skill applies:'; Write-Output ''; Get-Content -Raw (Join-Path $env:PLUGIN_ROOT 'skills/using-axiom/SKILL.md')"
```

If `/hooks` shows any other command, do not trust it until the installed hook
and this documented definition have been reconciled.

### Claude Code

Add the Git marketplace and install Axiom from inside Claude Code:

```text
/plugin marketplace add wheakerd/axiom
/plugin install axiom@axiom
/reload-plugins
```

Open `/hooks` and review the plugin hooks before trusting them. The checked-in
Claude Code handlers use `${CLAUDE_PLUGIN_ROOT}` and run these commands:

`SessionStart` on `startup`, `resume`, `clear`, and `compact`:

```bash
echo 'You have Axiom. Load this startup front door before deciding whether any Axiom skill applies:'; cat "${CLAUDE_PLUGIN_ROOT}/skills/using-axiom/SKILL.md"
```

`PreCompact` on `manual` and `auto`:

```bash
echo 'You have Axiom. Preserve this routing front door while compacting:'; cat "${CLAUDE_PLUGIN_ROOT}/skills/using-axiom/SKILL.md"
```

Claude Code exposes `PreCompact` separately from the post-compaction
`SessionStart` source. Axiom runs the routing read before manual or automatic
compaction. Current Claude Code only adds `SessionStart` stdout, not successful
`PreCompact` stdout, to agent context, so the `SessionStart: compact` handler
performs the supported post-compaction reinjection as well. If `/hooks` shows
another command, do not trust it until the installed definition and this
documentation agree.

## Updating

Axiom does not check for or install updates automatically. Refresh the relevant
Git marketplace snapshot only when you choose to.

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

In a supported Codex workspace plugin UI, use **Refresh** instead. Start a new
Codex session after refreshing, or run `/reload-plugins` in Claude Code. If the
hook definition changed, inspect and trust the new definition in `/hooks`
before relying on it.

## Hook Trust And Troubleshooting

The Codex hook runs on `startup`, `resume`, `clear`, and `compact`. Claude Code
runs the corresponding `SessionStart` sources plus `PreCompact` on `manual` and
`auto`. Every handler reads a checked-in Markdown skill and does not modify
files or contact a network service.

That claim is inspectable in the exact commands above: they contain only
foreground output and a local file read, with no redirection, file-writing,
background-launch, or network command.

If the Axiom routing message does not appear:

1. Open `/hooks` and confirm the Axiom hooks are enabled and trusted.
2. Review any changed hook definition instead of trusting it automatically.
3. Start a new Codex session or run `/reload-plugins` in Claude Code after
   installation or marketplace refresh.

Existing sessions may retain earlier hook and skill state.

## Contributor Review

The `distribution-drift` CI job runs
`python3 scripts/check-distribution-drift.py`. It fails with a unified diff if
the skill directories on disk disagree with either platform manifest, either
marketplace wrapper, or the shared skill list above. The script is a CI and
contributor check; it is not an installed runtime dependency.

Before publishing, confirm that:

- The direct public skill entries are exactly `using-axiom`,
  `agents-architect`, `traceable-git-submit`, and
  `reversible-system-change`.
- Public descriptions, examples, and installation commands agree with the
  bundled skills and current Codex and Claude Code plugin interfaces.
- The parsed platform hook commands match the documented command blocks and
  read only the intended routing skill.
- `using-axiom` still prohibits background services, scheduled refresh work,
  network update checks, and automatic update downloads or installation.
- Use `Axiom` in prose and `axiom` for identifiers and command examples; keep
  public triggers in English.
- Published content remains runtime-relevant and reviewable.

Use available platform-native or official Codex validation during maintenance,
but do not make a particular interpreter, custom script, shell, or test runner
an installation prerequisite.

## License

MIT
