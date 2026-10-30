# Consolidation

Replace an explicitly authorized checkpoint series with one final commit that carries the same tree, keep a backup ref until the result is verified, and push only under separate authority. Load this file only for explicit consolidation; an ordinary submit, publish, or push never loads it.

Consolidation, remote refresh, and network push are independent authorities. Network-push authority never authorizes a refresh, and refresh authority never authorizes a push.

## Preconditions

Run the preflight in `baseline-and-preflight.md`, read the cache and the active record, and require: a record without `newCommit` whose `checkpointShas` equals the exact ordered output of `git -C <repo> rev-list --reverse '@{u}'..HEAD`; every commit outside `adoptedShas` to carry the `Axiom-checkpoint: true` trailer, read with `git -C <repo> cat-file -p <sha>`; `git -C <repo> merge-base --is-ancestor <upstream-sha> HEAD` to succeed with the branch ahead and not behind; no merge commits in that range; no operation in progress; and no staged, unstaged, or untracked changes belonging to the submitted work. An out-of-record commit, unknown commit, merge, missing marker, or stale record stops; only stored exact full-SHA adoption authorizes an adopted commit. A record that already has `newCommit` enters recovery in `remote-targets.md` and is never consolidated again.

## Exact Remote Refresh

Only with explicit refresh authority, fetch the upstream's merge ref without touching any other ref and update the tracking ref by compare-and-swap:

```bash
git -C <repo> fetch --no-tags --no-recurse-submodules --refmap= <upstream-remote> <merge-ref>
git -C <repo> ls-remote <upstream-remote> <merge-ref>
git -C <repo> update-ref --no-deref <upstream-tracking-ref> <source-oid> <old-tracking-oid>
```

`--refmap=` keeps the fetch from updating configured refs. Require the single `ls-remote` result and `FETCH_HEAD` to name the same commit before the update, and stop when `upstreamRemote` is `.`. Afterwards recompute `@{u}`, the ahead/behind counts, the cache comparison, and the record checks. Generic prune needs separate exact authority.

## Backup And Final Commit

Record `branchRef`, `oldHead`, `upstreamSha`, `finalTree` (the tree of `oldHead`), the ordered SHA list, and a unique backup ref name `refs/axiom/backups/traceable-git-submit/<unique-id>` built from a UTC timestamp and a short `oldHead` prefix. Create the backup before any branch change with a create-only transaction; the null old value makes it fail when the ref already exists, in which case choose a fresh id. Never fall back to an unconditional `update-ref`.

```bash
git -C <repo> update-ref --no-deref <backup-ref> <old-head> <null-oid>
git -C <repo> rev-parse --verify <backup-ref>
```

Construct the final commit from `oldHead`'s tree with `upstreamSha` as its only parent, passing the message on standard input:

```bash
git -C <repo> commit-tree <final-tree> -p <upstream-sha>
```

```text
<type>: <concise final summary>

Remote baseline: <upstream> @ <sha>

Scope:
<consolidated outcome>

Checkpoints:
<ordered checkpoint SHA and subject list>

Validation:
<commands run and outcomes>
```

Carry `Axiom-checkpoint: true` into the final commit only when the user asks. Verify `newCommit^ == upstreamSha`, `newCommit^{tree} == finalTree`, `git diff --quiet <old-head>^{tree} <new-commit>^{tree}`, the message, and that `branchRef` still equals `oldHead`; stop and keep the backup on any failure.

## Install And Persist

```bash
git -C <repo> update-ref --no-deref <branch-ref> <new-commit> <old-head>
```

After the compare-and-swap, require `HEAD == newCommit`, `HEAD^ == upstreamSha`, the exact tree, no new index or worktree changes, and `backupRef == oldHead`. If verification fails before any push, restore the branch with compare-and-swap and report the result:

```bash
git -C <repo> update-ref --no-deref <branch-ref> <old-head> <new-commit>
```

Then persist `oldHead`, `finalTree`, `backupRef`, and `newCommit` in the record. If that write fails or is uncertain, restore the branch the same way, verify that the branch and the backup both resolve to `oldHead`, keep the backup and the record, and stop; do not push, update the cache, or consolidate again.

Without push authority, stop here: retain the backup and the record with `pushRemote` unset, and do not inventory targets or update the cache.

## Push

With push authority, resolve and freeze the push identity and targets as `remote-targets.md` describes, bind `pushRemote` in the record once, and recheck every target's merge ref against `baselineSha` immediately before the first push; any mismatch means zero pushes. Push one frozen target at a time in the authorized order with one exact ref update and repository hooks running:

```bash
git -C <repo> push --no-follow-tags <push-remote> <branch-ref>:<merge-ref>
```

Add `--no-verify` only when the user explicitly authorized bypassing this repository's pre-push hook for this push; general push authority never includes it. Stop issuing pushes at the first failure, then query every authorized target and record which hold `newCommit` and which still hold `baselineSha`. Completion requires every target to equal `newCommit`; a push exit status alone is insufficient. Only refresh authority may then advance `@{u}`; without it, keep the cache unchanged and report the refresh as pending. Cleanup of the backup and the record follows `remote-targets.md` under its own authority. Never retry a push automatically, restore the branch after a partial push, or delete the backup or the record while any target or the refreshed upstream disagrees.
