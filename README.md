# Axiom

Think before AI thinks.

Axiom is a Codex-first plugin for community-native AI workflows. It helps
Codex resolve user intent before execution, then loads a focused workflow for
the work that actually needs it.

Axiom does not take over ordinary tasks. Its session-start gate selects the
smallest matching bundled skill, honors higher-priority instructions, and
continues normally when no Axiom workflow applies.

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

- Plan-only work and rehearsals remain strictly read-only.
- Execution requires one exact target, a frozen write set, and a directly
  verified, readable, executable rollback path.
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

Axiom installs four checked-in skills:

- `using-axiom`, the session-start routing gate.
- `agents-architect`, `traceable-git-submit`, and
  `reversible-system-change`, the three user workflows.

Each workflow loads its supporting Markdown references only when the active
task needs them. Axiom also installs one `SessionStart` hook that prints a
short loading message and reads the routing skill from the installed plugin.

There is no background service, automatic updater, private maintenance tool,
or bundled runtime dependency.

## Installation

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

## Updating

Axiom does not check for or install updates automatically. Refresh its
configured Git marketplace snapshot only when you choose to:

```bash
codex plugin marketplace upgrade axiom
```

In a supported workspace plugin UI, use **Refresh** instead. Start a new Codex
session after refreshing. If the hook definition changed, inspect and trust
the new definition in `/hooks` before relying on it.

## Hook Trust And Troubleshooting

The hook runs on `startup`, `resume`, `clear`, and `compact`. It reads a
checked-in Markdown skill and does not modify files or contact a network
service.

If the Axiom routing message does not appear:

1. Open `/hooks` and confirm the Axiom `SessionStart` hook is enabled and
   trusted.
2. Review any changed hook definition instead of trusting it automatically.
3. Start a new Codex session after installation or marketplace refresh.

Existing sessions may retain earlier hook and skill state.

## Contributor Review

Before publishing, confirm that:

- Public descriptions, examples, and installation commands agree with the
  bundled skills and current Codex plugin interface.
- The documented `SessionStart` hook reads only the intended routing skill.
- Use `Axiom` in prose and `axiom` for identifiers and command examples; keep
  public triggers in English.
- Published content remains runtime-relevant and reviewable.

Use available platform-native or official Codex validation during maintenance,
but do not make a particular interpreter, custom script, shell, or test runner
an installation prerequisite.

## License

MIT
