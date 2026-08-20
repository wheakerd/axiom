# Checkpoint Consolidation And Push

## Purpose

Consolidate an explicitly authorized checkpoint series into one final commit,
optionally push under separate authorization, and hand verified cleanup to the
provenance state machine.

## Authorization And Phase Selection

Load this reference only after the user explicitly authorizes checkpoint
consolidation or when an active record with `newCommit` requires recovery. An
ordinary submit, publish, or push request never loads this reference.

Treat consolidation, remote refresh, and network push as independent
authorization axes:

Apply `safe-git-values-and-metadata.md` to every Git invocation in this
reference. All command blocks show argument order only; derived values must be
validated and passed as separate literal arguments.

1. Run Git preflight. Defer a baseline-cache mismatch decision until the active
   record selects the normal or post-consolidation path.
2. Read or initialize the baseline cache and read the active provenance record.
3. Select exactly one path:
   - Without `newCommit`, require explicit consolidation authority and require
     the recorded ordered SHA list to equal every unpublished commit.
   - With `newCommit`, use only the recovery gate in
     `checkpoint-provenance.md`.
4. Run the exact refresh protocol below only with explicit remote-refresh
   authority. Network-push authority never authorizes it. Resolve `remote` from
   `branch.<branch>.remote`; stop if it is `.` for network work.

5. After an authorized fetch, refresh `@{u}`, ahead/behind state, cache
   comparisons, and provenance. Without fetch, use the current remote-tracking
   ref and report that remote state was not refreshed.
6. For a normal record, run the consolidation algorithm below.
7. For a post-consolidation record, retry only the recorded push or verified
   cleanup. Never consolidate again.
8. Without push authority, stop after the consolidated commit and recoverable
   post-consolidation state are persisted. Retain the backup and active record;
   do not update the remote-push baseline cache or run remote-dependent cleanup.
9. With push authority, validate again before push or cleanup.

## Exact Remote Refresh

Freeze and validate `objectFormat`, `remote`, its resolved raw fetch target and
fingerprint, source `mergeRef`, full destination `upstreamTrackingRef`, its
current `oldTrackingOid`, and the source's directly queried `sourceOid`. Keep
the raw target inside the secrecy boundary. The source-only refspec is exactly
the validated `mergeRef`: no wildcard, leading `+`, or destination. Require a
direct query of that target to return the source ref once.

Fetch objects without updating any ref or consuming configured fetch refspecs:

```bash
git -C <repo> -c fetch.all=false -c fetch.prune=false -c fetch.pruneTags=false -c fetch.recurseSubmodules=false -c fetch.writeCommitGraph=false -c maintenance.auto=false fetch --no-all --no-tags --no-prune --no-prune-tags --no-recurse-submodules --no-write-fetch-head --no-auto-maintenance --no-write-commit-graph --refmap= <fetch-target> <source-ref>
```

The installed Git must support every shown closure flag. Re-query `sourceRef`
at the frozen target after fetch and require the same `sourceOid`; require that
OID now resolves as a commit. Recheck object format, remote/fetch-target
identity, source/destination refs, and the frozen old destination, then update
only the authorized tracking ref:

```bash
git -C <repo> update-ref --no-deref <upstream-tracking-ref> <source-oid> <old-tracking-oid>
```

The old value makes this compare-and-swap. On drift or failure, stop without a
tracking-ref update. After success, require the destination to equal
`sourceOid`, then recompute `@{u}`, ahead/behind, cache comparison, and
provenance. Generic prune is outside this protocol and needs separate exact
authority.

## Preconditions

Before creating a commit or updating a ref, require:

- A normal branch with full `branchRef`, resolvable `@{u}`, and verified
  `upstreamSha`.
- `git -C <repo> merge-base --is-ancestor <upstream-sha> HEAD` succeeds.
- Ahead is greater than zero and behind is zero.
- `git -C <repo> rev-list --merges '@{u}'..HEAD` is empty.
- Every unpublished commit exactly matches active provenance. Every commit not
  listed in exact user-authorized `adoptedShas` contains
  `Axiom-checkpoint: true`.
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
git -C <repo> log --reverse --format='%h %s' '@{u}'..HEAD
git -C <repo> diff --numstat -z '@{u}'..HEAD
git -C <repo> diff --name-status -z '@{u}'..HEAD
```

Capture NUL-delimited path output internally and render paths only with
reversible escaping.

Any old checkpoint outside the record, unknown-provenance commit, merge,
missing required marker, stale record, or mixed commit stops the flow. An
adopted commit is authorized only by the exact ordered full-SHA adoption stored
in the record.

## Construct The Final Commit

Follow `commit-construction.md` exactly to record state, create and verify the
backup, construct the final commit, compare-and-swap the branch, and persist
the post-consolidation record. Do not push unless all of those checks pass.

## Push And Remote Verification

Push only when explicitly authorized. Use the frozen push-target set from
`repository-and-remote-targets.md`, not a fetch URL or a single assumed target.
Immediately before the first push, apply that reference's drift gate: every
target must still be in the frozen ordered fingerprint set and its `mergeRef`
must equal `baselineSha`. Any failure means zero pushes.

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

Require exactly one matching ref result and `newCommit` from every target.
Then follow `post-consolidation-recovery.md`. Only when current explicit
remote-refresh authority covers a post-push refresh may the exact protocol
above advance authoritative `@{u}`. Without it, target verification may prove
the push result, but do not update the cache or persist `cleanupReady`; retain
recovery state and report that refresh remains pending. Do not delete the backup ref or active record unless
the user separately authorized the exact
cleanup envelope bound to this repository, workflow, refs, OIDs, and deletion
operations.

If push or remote verification fails, do not update the baseline, delete the
backup, or delete the active record. Leave the consolidated commit and recovery
state in place. Report each target by ordinal and fingerprint with its observed
and expected SHA; never print raw endpoints. When targets disagree, report a
partial remote state and stop without retrying or restoring the local branch.
