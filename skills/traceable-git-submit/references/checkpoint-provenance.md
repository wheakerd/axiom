# Active Checkpoint Provenance

## Purpose

Prove that every commit selected for consolidation belongs to the current
user-authorized traceable workflow, and keep interrupted consolidation, push,
and cleanup states recoverable.

`Axiom-checkpoint: true` is necessary only for workflow-created checkpoints and
is never provenance by itself. A commit in `adoptedShas` instead relies on the
user's exact full-SHA authorization and the active record.

## Active Record

Resolve the active record from target Git metadata:

```bash
git -C <repo> rev-parse --path-format=absolute --git-path axiom/traceable-git-submit-active-checkpoints.json
```

Keep the record out of the worktree, plugin directory, index, and commits.
Update it through a temporary sibling and atomic replacement when supported.

Initial schema:

```json
{
  "repo": "<repository-name>",
  "branchRef": "refs/heads/<branch>",
  "branch": "<branch>",
  "upstream": "<remote>/<branch>",
  "remote": "<branch-remote>",
  "mergeRef": "refs/heads/<branch>",
  "baselineSha": "<upstream-sha>",
  "workflowId": "<utc-timestamp>-<head-prefix>",
  "checkpointShas": [],
  "adoptedShas": [],
  "createdAt": "<utc-iso8601>",
  "updatedAt": "<utc-iso8601>"
}
```

`adoptedShas` may be omitted when empty. Every entry must have recorded exact
full-SHA user authorization, occur once in `checkpointShas`, and preserve the
same relative order. Existing commits adopted before record creation form the
same prefix in both arrays. A later uncertain recovery commit may enter both
arrays only through the explicit gate in `checkpoint-execution.md`.

Before each workflow-created checkpoint, atomically add:

```json
{
  "pendingCheckpoint": {
    "parentSha": "<current-full-head-sha>",
    "writeSetDigest": "<digest-of-sorted-raw-nul-delimited-path-set>",
    "digestAlgorithm": "<algorithm>",
    "pathCount": 0,
    "stagedTreeSha": "<added-after-staging>"
  }
}
```

Use the actual `pathCount`; omit `stagedTreeSha` until staging is complete,
then add the exact `git write-tree` result before commit. This is recovery
evidence, not authority to widen scope. Remove it atomically when appending the
verified checkpoint SHA.

After consolidation, add `oldHead`, `finalTree`, `backupRef`, `newCommit`, and
authorized push-target fingerprints. Cleanup state is owned by
`post-consolidation-recovery.md`.

## Begin And Record

Only after the user authorizes the checkpoint workflow and applicable read-only
preflight succeeds:

1. If no record exists, first enumerate `@{u}..HEAD`. Write a normal new record
   with empty `checkpointShas` and `adoptedShas` only when that list is empty.
   When it is non-empty, stop unless the user explicitly adopts the exact
   ordered full-SHA list under `checkpoint-execution.md`; then seed both arrays
   with that list.
2. Do not overwrite an existing record. Without `newCommit`, resume only when
   all identity and baseline fields match and `checkpointShas` is an exact
   ordered prefix of the current `@{u}..HEAD` list.
3. A record with `newCommit` is post-consolidation recovery state. Do not create
   or append checkpoints and do not apply the normal consolidation gate.
4. Before writing each `pendingCheckpoint`, require the complete staged-change
   set to be empty and all gates in `checkpoint-execution.md` to pass. Resolve
   an existing pending object only through its recovery or bounded abort gate.
5. After each workflow-created checkpoint commit, require `HEAD` to equal the
   new SHA, require its body to contain `Axiom-checkpoint: true`, then atomically
   append only that SHA and remove `pendingCheckpoint` in the same replacement.
6. Report the record path, workflow id, and ordered SHA list after every update.

Stop and report a stale record instead of replacing it.

## Consolidation Gate

Before creating a backup ref or final commit:

1. Enumerate `git -C <repo> rev-list --reverse '@{u}'..HEAD`.
2. Require matching `repo`, `branchRef`, `branch`, `upstream`, `remote`,
   `mergeRef`, and `baselineSha` fields.
3. Require `checkpointShas` to exactly equal the enumerated ordered list.
   Reject missing, extra, reordered, malformed, or duplicate SHAs.
4. Require `adoptedShas`, when present, to be an ordered, duplicate-free subset
   of `checkpointShas`; require recorded exact full-SHA authorization for every
   entry. Initial existing-commit adoption must be the matching prefix.
5. Independently require every selected commit not present in `adoptedShas` to
   contain `Axiom-checkpoint: true`.

Stop on any mismatch. Do not infer authorization from a marker, timestamp,
author, branch name, or cache entry. Adoption requires a new explicit
confirmation naming the exact ordered full-SHA list before record creation. It
never authorizes a merge, already-pushed commit, or SHA outside refreshed
`@{u}..HEAD`.

## Atomic Persistence Failure

After the branch `update-ref` succeeds, persist `oldHead`, `finalTree`,
`backupRef`, and `newCommit` atomically. If that write fails or is uncertain,
do not push or update the baseline cache. Immediately attempt:

```bash
git -C <repo> update-ref <branch-ref> <old-head> <new-commit>
git -C <repo> rev-parse --verify <branch-ref>
git -C <repo> rev-parse --verify <backup-ref>
```

Require both refs to resolve to `oldHead`. Retain the backup and active record,
report their paths and the restoration result, and stop. Do not retry, push, or
re-consolidate until a new explicit recovery assessment resolves the state.

Resume any active record with `newCommit` only through
`post-consolidation-recovery.md`.

## References

- `checkpoint-execution.md`
- `post-consolidation-recovery.md`
