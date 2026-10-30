# Baseline Cache And Git Preflight

Resolve the Git facts a traceable phase needs, keep the advisory remote-push baseline, and stop unsafe state before any mutation. Ordinary Git stays host-native. Return to `../SKILL.md` for phase selection; an explicitly selected simple direct push reads only `direct-submit.md` and creates no Axiom metadata. Reading Git facts never authorizes cache mutation; use the cache only for the exact selected traceable phase.

Remote refresh and network push are separate authorities: push authority never grants a refresh or any fetch. Without refresh authority, use the current tracking ref and report that it was not refreshed.

## Baseline Cache

Resolve the cache path with `git -C <repo> rev-parse --path-format=absolute --git-path axiom/traceable-git-submit-baseline.json` and apply `git-values.md` to every read and write. The cache is advisory; the upstream tracking ref `@{u}` stays authoritative.

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

Initialize it only when an authorized checkpoint, baseline, or consolidation workflow starts, check it before consolidation or a recovery push, and update it only after every authorized remote ref equals the final commit.

A legacy file at `.agents/.cache/traceable-git-submit-baseline.json` in the worktree is migrated only when its `repo`, `branch`, `upstream`, and `lastRemotePushSha` equal the current facts; add `upstreamRemote` and `mergeRef` from preflight, leave the legacy file untouched, and report any mismatch or invalid JSON without copying it. Never stage, commit, delete, or rewrite that file automatically.

## Required Git Facts

```bash
git -C <repo> rev-parse --show-object-format
git -C <repo> symbolic-ref --quiet HEAD
git -C <repo> rev-parse --verify HEAD
git -C <repo> rev-parse --abbrev-ref --symbolic-full-name '@{u}'
git -C <repo> rev-parse --symbolic-full-name '@{u}'
git -C <repo> rev-parse --verify '@{u}'
git -C <repo> config --get "branch.<branch>.remote"
git -C <repo> config --get "branch.<branch>.merge"
git -C <repo> rev-list --left-right --count HEAD...'@{u}'
```

Retain the object format, the branch's full ref and short name, the upstream display name and full tracking ref, `upstreamRemote`, the merge ref, the upstream OID, the `HEAD` OID, and the ahead/behind counts. Take `upstreamRemote` from `branch.<branch>.remote`, never by splitting upstream text; it owns fetch identity only and never implies the push destination. An `upstreamRemote` of `.` is a valid local upstream that cannot perform a network refresh.

## Operation State

`git rev-parse --git-path` prints a path whether or not it exists. Resolve `MERGE_HEAD`, `CHERRY_PICK_HEAD`, `REVERT_HEAD`, `REBASE_HEAD`, `rebase-merge`, and `rebase-apply` and test each for existence; any present entry means an operation is in progress.

## Stop Before Mutation

For a normal checkpoint or consolidation, require the cached `branch`, `upstream`, `upstreamRemote`, `mergeRef`, and `lastRemotePushSha` to equal the current facts; report a branch change, stale cache, changed upstream configuration, or moved baseline instead of repairing it. A post-consolidation record defers this comparison to the recovery gate in `remote-targets.md`, because push targets may already hold `newCommit` while the cache still names the old baseline.

Stop before a checkpoint, baseline mutation, consolidation, workflow push, or recovery when `HEAD` is detached or the branch is unborn; the branch lacks an upstream, upstream remote, or merge ref, or a push lacks a resolved push remote; a network refresh is requested while `upstreamRemote` is `.`; an operation is in progress; the branch has diverged from its upstream rather than only being ahead; the cache does not match; or a consolidation or push still has staged, unstaged, or untracked changes that belong to the work being submitted. During checkpoint work, report every changed path before staging and stage only intentional paths.
