# Checkpoint Consolidation And Push

## Purpose

Consolidate the exact authorized checkpoint series into one final commit,
update the current branch with compare-and-swap semantics, push only when
authorized, and hand verified cleanup to the provenance state machine.

## Submit Flow

When the user explicitly asks to submit, publish, or push:

1. Run Git preflight. Defer a baseline-cache mismatch decision until the active
   record selects the normal or post-consolidation path.
2. Read or initialize the baseline cache and read the active provenance record.
3. Select exactly one path:
   - Without `newCommit`, require the recorded ordered SHA list to equal every
     unpublished commit before consolidation.
   - With `newCommit`, use only the recovery gate in
     `checkpoint-provenance.md`.
4. Fetch the resolved branch remote when network access is available:

```bash
git -C <repo> fetch --prune <remote>
```

Resolve `<remote>` from `branch.<branch>.remote`. Stop if it is `.` for a
network push.

5. Refresh `@{u}`, ahead/behind state, cache comparisons, and provenance after
   fetch.
6. For a normal record, run the consolidation algorithm below.
7. For a post-consolidation record, retry only the recorded push or verified
   cleanup. Never consolidate again.
8. Validate again before push or cleanup.

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
git -C <repo> push <push-target> <branch-ref>:<merge-ref>
```

Stop issuing later pushes on the first failure, then query the merge ref at
every authorized target to record any partial state:

```bash
git -C <repo> ls-remote <push-target> <merge-ref>
```

Require exactly one matching ref result and `newCommit` from every target.
Then follow `post-consolidation-recovery.md`: fetch the branch remote, require
authoritative refreshed `@{u} == newCommit`, update and verify the cache,
persist cleanup proof, and only then delete recovery state in order.

If push or remote verification fails, do not update the baseline, delete the
backup, or delete the active record. Leave the consolidated commit and recovery
state in place. Report each target by ordinal and fingerprint with its observed
and expected SHA; never print raw endpoints. When targets disagree, report a
partial remote state and stop without retrying or restoring the local branch.
