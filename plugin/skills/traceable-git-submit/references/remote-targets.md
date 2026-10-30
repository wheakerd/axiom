# Repository, Remote Targets, And Recovery

Resolve one exact Git root, freeze the push identity and every target it reaches, verify remote state after a push, and make cleanup separately authorizable. Simple named-remote submission belongs to `direct-submit.md`, not here.

## Exact Repository Root

Resolve the user's explicit path or scoped files before the session directory with `git -C <candidate> rev-parse --show-toplevel` and `git -C <candidate> rev-parse --path-format=absolute --git-common-dir`. Stop if a path lies outside the root, paths span repositories or worktrees, a parent or nested repository is ambiguous, or an explicit path conflicts with the session directory. A linked worktree is valid when Git resolves both identities.

## Push Identity

`upstreamRemote` comes only from `branch.<branch>.remote` and owns `@{u}` and refresh. Resolve the effective `pushRemote` independently, in this order: a configured remote explicitly named in the current request; `branch.<branch>.pushRemote` when present; `remote.pushDefault` when present; current `upstreamRemote`. Only an absent key falls through; an empty, malformed, option-shaped, `.`, or non-enumerated value stops. A raw URL is not a configured remote name. Freeze `pushRemote`, its resolution source, `mergeRef`, the branch, and the upstream identity, and re-resolve them before inventory and again before the push; a change is drift. Refresh still uses `upstreamRemote`. When a fallback selects `pushRemote != upstreamRemote` and the user did not name it, confirm that destination before any push.

## Targets

List the targets with `git -C <repo> remote get-url --push --all <push-remote>`, keep the output out of reports and records, and classify each URL under `git-values.md`. Zero targets stops with zero pushes. One target may proceed under an explicit submit, publish, or push request. Several targets need the user's authorization of that exact ordered set and the acknowledgement that Git updates them one after another, so a failure can leave them disagreeing. Any change of count, order, or identity invalidates that authorization.

For a hardened push of existing commits, freeze `finalSha` as current `HEAD` and bind a `liveBaselineSha` per target from `git -C <repo> ls-remote <push-url> <merge-ref>`: one result, a locally present commit, and `git merge-base --is-ancestor <target-baseline-sha> <final-sha>` succeeding. Different targets may have different ancestor baselines; never borrow one target's proof for another. A stale local tracking ref is informational and never a baseline. Never stage, stash, clean, commit, or require a clean worktree merely to push existing commits, and never force-push on this route. A consolidated submission uses its recorded `baselineSha` for every target instead.

## Push And Read-Back

Immediately before the first push, re-resolve the identity, re-list the targets, require the branch ref to equal `finalSha` (or the recorded `newCommit`), check that no operation is in progress, and query every target's merge ref. Any missing, changed, non-commit, or non-ancestor result means zero pushes. Then push once per frozen target in order with one exact ref update and repository hooks running:

```bash
git -C <repo> push --no-follow-tags <push-remote> <branch-ref>:<merge-ref>
```

Add `--no-verify` only when the user explicitly authorized bypassing this repository's pre-push hook for this push. Stop issuing pushes at the first failure. Read every target back with `ls-remote`; completion requires each merge ref to equal `finalSha` or `newCommit`, and a push exit status, fetch, or tracking-ref update is insufficient. On disagreement, retain the backup and the record, leave the cache unchanged, and report the partial state; never retry automatically. Push authority never grants fetch: report `@{u}` as unrefreshed unless a separately authorized refresh ran.

## Recovery Of A Consolidated Record

Use only for a record that contains `newCommit`; never consolidate again or append a checkpoint.

1. Require `repo`, `branchRef`, `branch`, `upstream`, `upstreamRemote`, and `mergeRef` to match current facts; `oldHead`, `finalTree`, and `newCommit` to be full OIDs of the right type; and `backupRef` to be a full `refs/axiom/backups/` name validated as a ref, not as an OID. Bind `pushRemote` now under current push authority when it is unset, and require it to match when it is set.
2. Require `HEAD == newCommit`, `newCommit^ == baselineSha`, and `newCommit^{tree} == oldHead^{tree} == finalTree`. If `backupRef` exists, it must be a non-symbolic ref resolving to `oldHead`.
3. Query each target's merge ref; accept only `baselineSha` or `newCommit`. If every target still holds `baselineSha`, retry only the recorded push under current authority. If every target holds `newCommit`, require an authorized refresh showing `@{u} == newCommit` before the cache update and cleanup. On disagreement, report the partial state and stop: no push, no branch restore, no cache update, no cleanup.

## Cleanup

Only after every target and the refreshed `@{u}` equal `newCommit`: update the cache so that `lastRemotePushSha == newCommit`, then record `cleanupReady: true` in the active record. Deleting the backup ref and the record needs separate exact authority naming this repository, ref, and OID; a prior push, consolidation, or recovery request is not that authority, so retain both and ask once. Under that authority, recheck the identity, targets, upstream, and backup, then delete with compare-and-swap and verify absence:

```bash
git -C <repo> update-ref --no-deref -d <backup-ref> <old-head>
git -C <repo> rev-parse --verify <backup-ref>
```

A changed or symbolic ref stops. An already absent ref is observed state, not proof that cleanup ran. Remove the record last; on any failure keep it and resume at the first incomplete step. Report targets by remote name and ordinal with expected and observed OIDs, never by URL.
