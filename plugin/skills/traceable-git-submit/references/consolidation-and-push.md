# Checkpoint Consolidation And Push

## Purpose

Consolidate an explicitly authorized checkpoint series into one final commit,
optionally push under separate authorization, and hand verified cleanup to the
provenance state machine.

## Authorization And Phase Selection

Load only for explicit consolidation or recovery of a record with `newCommit`.
An ordinary submit, publish, or push never loads it.

Treat consolidation, remote refresh, and network push as independent
authorization axes:

Apply `safe-git-values-and-metadata.md` to every Git invocation. Command blocks
show argument order; derived values remain separate literal arguments.

1. Run Git preflight. Defer a baseline-cache mismatch decision until the active
   record selects the normal or post-consolidation path.
2. Read or initialize the baseline cache and read the active provenance record.
3. Select exactly one path:
   - Without `newCommit`, require explicit consolidation authority and require
     the recorded ordered SHA list to equal every unpublished commit.
   - With `newCommit`, use only the recovery gate in
     `checkpoint-provenance.md`.
4. Run the exact refresh protocol below only with explicit remote-refresh
   authority. Network-push authority never authorizes it. Use
   `upstreamRemote` from `branch.<branch>.remote`; stop the refresh if it is
   `.`. Never substitute effective `pushRemote` for fetch identity.

5. After authorized fetch, refresh `@{u}`, divergence, cache, and provenance.
   Without it, use and report the unrefreshed tracking ref.
6. For a normal record, run the consolidation algorithm below.
7. For a post-consolidation record, retry only recorded push or verified
   cleanup; never consolidate again.
8. Without push authority, stop after the consolidated commit and recoverable
   post-consolidation state are persisted. Retain the backup and active record;
   retain `pushTargetState.state == unbound`; do not inventory endpoints,
   update the remote-push baseline cache, or run remote-dependent cleanup.
9. With push authority, validate again before push or cleanup.

## Exact Remote Refresh

Freeze and validate `objectFormat`, `upstreamRemote`, its raw fetch target and
fingerprint, source `mergeRef`, destination `upstreamTrackingRef`, current
`oldTrackingOid`, and directly queried `sourceOid`. Keep the target secret. The
source-only refspec is exactly validated `mergeRef`: no wildcard, leading `+`,
or destination. Require one direct source-ref result.

Fetch objects without updating any ref or consuming configured fetch refspecs:

```bash
git -C <repo> -c fetch.all=false -c fetch.prune=false -c fetch.pruneTags=false -c fetch.recurseSubmodules=false -c fetch.writeCommitGraph=false -c maintenance.auto=false fetch --no-all --no-tags --no-prune --no-prune-tags --no-recurse-submodules --no-write-fetch-head --no-auto-maintenance --no-write-commit-graph --refmap= <fetch-target> <source-ref>
```

Require support for every closure flag. Re-query `sourceRef`, require the same
`sourceOid` and commit type, then recheck format, target identity, refs, and old
destination before updating only the authorized tracking ref:

```bash
git -C <repo> update-ref --no-deref <upstream-tracking-ref> <source-oid> <old-tracking-oid>
```

The old value is compare-and-swap. Drift or failure stops. After success,
require destination `sourceOid`, then recompute `@{u}`, divergence, cache, and
provenance. Generic prune needs separate exact authority.

## Preconditions

Before creating a commit or updating a ref, require:

- A normal branch with full `branchRef`, resolvable `@{u}`, and verified
  `upstreamSha`.
- `git -C <repo> merge-base --is-ancestor <upstream-sha> HEAD` succeeds.
- Ahead is greater than zero and behind is zero.
- `git -C <repo> rev-list --merges '@{u}'..HEAD` is empty.
- Every unpublished commit exactly matches active provenance. Each commit
  outside exact user-authorized `adoptedShas` passes the safe exact marker gate
  in `safe-git-values-and-metadata.md`.
- No merge, rebase, cherry-pick, or revert is in progress.
- No staged, unstaged, or untracked intentional changes belonging to the work
  being submitted remain.

Inspect:

```bash
git -C <repo> status --porcelain=v1 -z --untracked-files=all
git -C <repo> diff --numstat -z
git -C <repo> diff --cached --numstat -z
git -C <repo> merge-base --is-ancestor <upstream-sha> HEAD
git -C <repo> rev-list --merges '@{u}'..HEAD
git -C <repo> rev-list --reverse '@{u}'..HEAD
git -C <repo> diff --numstat -z '@{u}'..HEAD
git -C <repo> diff --name-status -z '@{u}'..HEAD
```

Capture NUL-delimited path output internally and render paths only with
reversible escaping. Capture each selected commit object invisibly and apply
the hostile metadata boundary in `safe-git-values-and-metadata.md` before any
subject is displayed or copied. Do not run visible subject-formatted `git log`.

An out-of-record checkpoint, unknown commit, merge, missing marker, stale
record, or mixed commit stops. Only stored exact full-SHA adoption authorizes
an adopted commit.

## Construct The Final Commit

Follow `commit-construction.md` exactly to record state, create and verify the
backup, construct the final commit, compare-and-swap the branch, and persist
the post-consolidation record. Do not push unless all of those checks pass.

## Push And Remote Verification

Push only when explicitly authorized. First apply the one-time binding gate in
`post-consolidation-recovery.md`; use the bound target set from
`repository-and-remote-targets.md`, not a fetch URL or assumed target.
Immediately before the first push, apply that reference's drift gate: every
effective push-identity field and target must still equal the bound state, and
each `mergeRef` must equal `baselineSha`. Any failure means zero pushes.

Multiple targets remain non-atomic despite this gate. Proceed only after the
user authorized that risk. Invoke one push per authorized target in frozen
order so each outcome is attributable:

```bash
git -C <repo> -c push.followTags=false -c push.recurseSubmodules=no -c push.gpgSign=false -c push.pushOption= -c push.negotiate=false -c push.autoSetupRemote=false push --no-verify --no-follow-tags --recurse-submodules=no --no-signed --no-push-option --no-set-upstream --no-prune --no-force --no-force-with-lease --no-force-if-includes <push-target> <branch-ref>:<merge-ref>
```

This is one raw frozen target and one exact ref update. `--no-verify` is
mandatory unless the user separately authorized the exact frozen pre-push hook
identity and action under `safe-git-values-and-metadata.md`; no generic push
authority permits that hook.

Stop issuing later pushes on the first failure, then query the merge ref at
every authorized target to record any partial state:

```bash
git -C <repo> ls-remote <push-target> <merge-ref>
```

Require one matching ref and `newCommit` from every target, then follow
`post-consolidation-recovery.md`. Only current refresh authority may advance
authoritative `@{u}`. Without it, do not update cache or persist `cleanupReady`;
retain state and report pending refresh. Delete no backup or active record
without the separately authorized exact cleanup envelope.

If push or remote verification fails, do not update the baseline, delete the
backup, or delete the active record. Leave the consolidated commit and recovery
state in place. Report each target by ordinal and fingerprint with its observed
and expected SHA; never print raw endpoints. When targets disagree, report a
partial remote state and stop without retrying or restoring the local branch.
