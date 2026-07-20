---
name: traceable-git-submit
description: Keep Git work traceable with local checkpoint commits and publish one clean consolidated commit. Use when the user asks to enable or run a traceable Git workflow, create local checkpoint commits, cache the last remote-push baseline in .agents/.cache/traceable-git-submit-baseline.json, compare unpublished commits against upstream, squash authorized checkpoint commits, submit/publish/push through a one-final-commit workflow, or recover/audit a working tree before that workflow pushes.
---

# Traceable Git Submit

Use this skill to keep local work reviewable through checkpoint commits while
publishing a single clean commit when the user explicitly asks to submit,
publish, or push.

## Safety Rules

- Do not commit unless the user asks for a commit or authorizes the traceable
  checkpoint workflow for the current task or session.
- Do not push unless the user explicitly asks to submit, publish, or push.
- Do not use `git reset --hard`.
- Do not stage unrelated user changes.
- Do not stage or commit `.agents/.cache/traceable-git-submit-baseline.json`; it
  is local workflow state, not a project artifact.
- Do not rewrite, squash, or drop unclear, non-workflow, already-pushed, or
  user-authored commits without explicit confirmation.
- If repository instructions specify a different cache location or Git policy,
  follow the higher-priority repository instructions and report the difference.

## Baseline Cache

Use `.agents/.cache/` as the shared cache root. It is not dedicated to this
skill; future skills may store their own cache artifacts there. This skill's
artifact is `.agents/.cache/traceable-git-submit-baseline.json` under the target
repository root unless higher-priority instructions name a maintenance workspace
cache path. The cache is advisory local workflow state. The upstream
remote-tracking ref from `@{u}` remains authoritative.

Cache schema:

```json
{
  "repo": "<repository-name>",
  "branch": "<current-branch>",
  "upstream": "<remote>/<branch>",
  "lastRemotePushSha": "<upstream-sha>",
  "updatedAt": "<utc-iso8601>"
}
```

Do not require a bundled programming-language helper for cache operations.
Perform the workflow directly with Git plus the operating system's native shell
or structured file tools for the current environment. If a script is ever
needed, prefer OS-native interpreters for the target environment: POSIX shell on
macOS/Linux and PowerShell on Windows.

Use `init` semantics when a checkpoint, submit, or push workflow starts and the
cache may not exist. Use `check` semantics before squash or push. Use `update`
semantics only after a push workflow completes successfully and the new remote
HEAD has been verified.

Use these Git facts for all cache operations:

```bash
git -C <repo> branch --show-current
git -C <repo> rev-parse --abbrev-ref --symbolic-full-name '@{u}'
git -C <repo> rev-parse --verify '@{u}'
git -C <repo> rev-list --left-right --count HEAD...'@{u}'
```

On macOS/Linux, create the cache directory with `mkdir -p
<repo>/.agents/.cache` and write JSON with a shell heredoc or another available
structured JSON writer. On Windows, create the cache directory with PowerShell
`New-Item -ItemType Directory -Force` and write JSON with `ConvertTo-Json` plus
`Set-Content -Encoding utf8`. Use the equivalent native command only after
resolving `<repo>`, branch, upstream, upstream SHA, and UTC update time in the
current environment.

If `lastRemotePushSha` differs from the current `@{u}` SHA before submit or
push, stop and report that the remote baseline moved, the cache is stale, or the
branch changed. Do not squash or push until the user confirms the intended
baseline.

## Checkpoint Flow

At the start of an authorized traceable workflow:

1. Resolve the target Git root.
2. Record branch, upstream, upstream SHA, and ahead/behind state.
3. Initialize or read the baseline cache.
4. Report any existing unstaged, staged, or untracked files before changing
   state.

After each completed feature, maintenance slice, or instruction-rule update:

1. Run validation appropriate to the changed surface.
2. Inspect:

```bash
git -C <repo> status --short --branch --untracked-files=all
git -C <repo> diff --stat
git -C <repo> diff --cached --stat
```

3. Stage only intentional files.
4. Create one local checkpoint commit. Include an explicit marker so submit flow
   can identify workflow-owned commits:

```text
<type>: <concise checkpoint summary>

Axiom-checkpoint: true
Remote baseline: <upstream> @ <sha>

Scope:
<what changed and why>

Validation:
<commands run and outcomes>
```

Do not update the baseline cache after local checkpoints. The cache tracks the
last remote push point, not local progress.

## Submit Flow

When the user asks to submit, publish, or push:

1. Fetch when network access is available:

```bash
git -C <repo> fetch --prune origin
```

2. Read or initialize the cache, then compare `lastRemotePushSha` with the
   current upstream SHA from `@{u}`.
3. Stop if upstream advanced, the branch diverged, the cache mismatches
   upstream, or intentional work remains uncommitted.
4. Inspect unpublished commits:

```bash
git -C <repo> log --reverse --format='%h %s' '@{u}'..HEAD
git -C <repo> diff --stat '@{u}'..HEAD
git -C <repo> diff --name-status '@{u}'..HEAD
```

5. Confirm every unpublished commit since `@{u}` is an authorized Axiom
   checkpoint commit. The commit body should contain `Axiom-checkpoint: true`.
6. Consolidate only the authorized checkpoint series into one final local commit
   whose parent is the upstream baseline and whose tree is the final checkpoint
   state. Prefer a non-interactive flow that preserves the working tree.
7. Validate again before push.
8. Push only after validation passes and the user explicitly requested it.
9. After a successful push, verify the remote HEAD and update the cache to the
   new remote SHA.

## Reporting

Report the repository, branch, upstream, cached `lastRemotePushSha`, current
upstream SHA, ahead/behind state, changed files, validation commands, checkpoint
commit hashes, final consolidated commit hash, and pushed branch when those
actions occur. If a step stops, report the exact stop condition and leave the
working tree visible.
