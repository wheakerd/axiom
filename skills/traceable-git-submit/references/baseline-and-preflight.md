# Baseline Cache And Git Preflight

## Purpose

Resolve authoritative Git facts for an explicitly selected traceable phase,
maintain the advisory remote-push baseline only when authorized, and stop
unsafe workflow changes before they occur.

## Apply when

- Inspecting an explicitly requested traceable checkpoint, baseline,
  consolidation, one-final-commit submission, or recovery flow.
- Initializing, checking, migrating, or updating the baseline cache.
- Refreshing upstream facts before one-final consolidation or recovery push.

## Authorization Separation

Ordinary local staging and commits do not apply this reference. A direct
history-preserving submit, publish, or push uses
`repository-and-remote-targets.md` instead and must not create, migrate, or
update Axiom metadata. Reading Git facts never authorizes cache mutation. Use
cache init, check, migration, or update semantics only for the exact selected
traceable phase.

Do not fetch solely for local consolidation. Remote refresh and network push
each require independent explicit authority; push authority never grants a
refresh or any fetch. Without refresh authority, use the current tracking ref
and report that it was not refreshed.

## Baseline Cache

Resolve the cache path from the target repository's Git metadata:

```bash
git -C <repo> rev-parse --path-format=absolute --git-path axiom/traceable-git-submit-baseline.json
```

Use that resolved path as the only current cache location. It must live under
Git metadata, remain absent from `git status`, avoid dependence on the target
repository's `.gitignore`, and work when `.git` is a file in a linked worktree.
Do not hand-build `.git/axiom/...` or use `PLUGIN_ROOT` as target state.

The cache is advisory. The upstream remote-tracking ref from `@{u}` remains
authoritative.

Cache schema:

```json
{
  "repo": "<repository-name>",
  "branch": "<current-branch>",
  "upstream": "<remote>/<branch>",
  "upstreamRemote": "<branch-upstream-remote>",
  "mergeRef": "<branch-merge-ref>",
  "lastRemotePushSha": "<upstream-sha>",
  "updatedAt": "<utc-iso8601>"
}
```

Use `init` semantics only when an authorized checkpoint, baseline, or
consolidation workflow starts and the cache may not exist. Use `check`
semantics before consolidation or one-final recovery push. Use `update`
semantics only after every authorized remote ref equals the final commit.

### Legacy migration

The legacy path is
`.agents/.cache/traceable-git-submit-baseline.json` in the target worktree.

- If the Git metadata cache exists, use it and leave any legacy file untouched.
- If only the legacy file exists, parse it and require its `repo`, `branch`,
  `upstream`, and `lastRemotePushSha` to match the current repository name,
  branch, upstream, and `@{u}` SHA.
- Migrate only an exact match, adding `upstreamRemote` and `mergeRef` from
  preflight.
- Ignore and report invalid JSON or any mismatch. Do not copy that state.
- Never stage, commit, delete, or rewrite the legacy file automatically.

Use Git plus native structured-data and file APIs available in the current
environment. Do not require a bundled programming-language helper. Apply
`safe-git-values-and-metadata.md` before any cache read, directory creation,
write, replacement, or deletion. Its canonical containment, no-follow,
exclusive temporary-file, parent revalidation, and fail-closed rules replace
ordinary pathname creation such as `mkdir -p` or `New-Item -Force`.

## Required Git Facts

Resolve these facts before cache or workflow decisions:

```bash
git -C <repo> rev-parse --path-format=absolute --git-path axiom/traceable-git-submit-baseline.json
git -C <repo> rev-parse --show-object-format
git -C <repo> symbolic-ref --quiet HEAD
git -C <repo> branch --show-current
git -C <repo> rev-parse --abbrev-ref --symbolic-full-name '@{u}'
git -C <repo> rev-parse --symbolic-full-name '@{u}'
git -C <repo> config --get "branch.<branch>.remote"
git -C <repo> config --get "branch.<branch>.merge"
git -C <repo> rev-parse --verify HEAD
git -C <repo> rev-parse --verify '@{u}'
git -C <repo> rev-list --left-right --count HEAD...'@{u}'
git -C <repo> rev-parse --path-format=absolute --git-path MERGE_HEAD
git -C <repo> rev-parse --path-format=absolute --git-path CHERRY_PICK_HEAD
git -C <repo> rev-parse --path-format=absolute --git-path REVERT_HEAD
git -C <repo> rev-parse --path-format=absolute --git-path REBASE_HEAD
git -C <repo> rev-parse --path-format=absolute --git-path rebase-merge
git -C <repo> rev-parse --path-format=absolute --git-path rebase-apply
```

Retain frozen object format, branch full ref and short name, upstream display
name and full tracking ref, `upstreamRemote`, merge ref, upstream OID, `HEAD`
OID, and ahead/behind state. Resolve `upstreamRemote` from
`branch.<branch>.remote`, never by splitting upstream text. It owns upstream
and fetch identity only; never infer the effective push destination from it.
Apply the object-format recheck rules in
`safe-git-values-and-metadata.md`; report only fields needed for a mutation,
stop, or recovery state and reversibly escape filesystem paths.

When `upstreamRemote` is not `.`, perform the equivalent of
`git -C <repo> config --get "remote.<upstream-remote>.url" >/dev/null 2>&1`
only through the literal-argument boundary and use only its exit status to
confirm that the key exists. Never expose or retain the value or unsanitized
error output. An `upstreamRemote` of `.` is a valid local upstream but cannot
perform the network refresh protocol. It does not prohibit a separately
resolved network `pushRemote`; that push still cannot satisfy refreshed-
upstream cleanup until authoritative `@{u}` reaches the verified final SHA.

## Operation-State Check

`git rev-parse --git-path` only prints a path. Test each resolved path for
existence before changing state.

```bash
for git_state in MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD REBASE_HEAD rebase-merge rebase-apply; do
  git_state_path="$(git -C <repo> rev-parse --path-format=absolute --git-path "$git_state")"
  if [ -e "$git_state_path" ]; then
    printf 'Git operation in progress: %s\n' "$git_state" >&2
    exit 1
  fi
done
```

PowerShell equivalent:

```powershell
$gitStates = @('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'REBASE_HEAD', 'rebase-merge', 'rebase-apply')
foreach ($gitState in $gitStates) {
  $gitStatePath = git -C <repo> rev-parse --path-format=absolute --git-path $gitState
  if (Test-Path -LiteralPath $gitStatePath) {
    throw "Git operation in progress: $gitState"
  }
}
```

## Consistency Gates

For a normal checkpoint or consolidation path, require cached `branch`,
`upstream`, `upstreamRemote`, `mergeRef`, and `lastRemotePushSha` to equal the
current branch, upstream, upstream remote, merge ref, and `@{u}` SHA. Stop and
report a branch change, stale cache, upstream configuration change, or moved
baseline. A Git-metadata cache with legacy `remote` and no `upstreamRemote` may
be atomically migrated only when that value exactly equals current
`upstreamRemote`; do not derive or persist push identity during this migration.

For a post-consolidation record, defer this baseline decision to the recovery
gate. Push targets may already equal `newCommit` while the cache still records
the old upstream baseline.

Stop before checkpoint, baseline mutation, consolidation, workflow push, or
recovery when:

- `HEAD` is detached or the branch is unborn.
- The branch lacks an upstream, upstream remote, or merge ref; or a workflow
  push or recovery flow lacks a resolved effective push remote or push target.
- A network refresh is requested while `upstreamRemote` is `.`.
- Merge, rebase, cherry-pick, or revert state exists.
- Ahead/behind shows divergence rather than only local ahead commits.
- Normal-path cache identity or baseline facts do not match.
- Consolidation or workflow push still has staged, unstaged, or untracked intentional changes
  belonging to the work being submitted.

During checkpoint work, report all changed paths before staging and stage only
intentional paths.
