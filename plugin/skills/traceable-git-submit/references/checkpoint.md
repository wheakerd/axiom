# Checkpoints And Provenance

Create isolated checkpoint commits from a frozen write set and keep an active record that proves which commits belong to the current user-authorized workflow. `Axiom-checkpoint: true` marks workflow-created checkpoints; it is never provenance by itself. A commit in `adoptedShas` relies on the user's exact full-SHA authorization and the record.

## Active Record

Resolve the record with `git -C <repo> rev-parse --path-format=absolute --git-path axiom/traceable-git-submit-active-checkpoints.json` and apply `git-values.md` to every read, write, and deletion. Keep it out of the worktree, the index, and commits.

```json
{
  "repo": "<repository-name>",
  "branchRef": "refs/heads/<branch>",
  "branch": "<branch>",
  "upstream": "<remote>/<branch>",
  "upstreamRemote": "<branch-upstream-remote>",
  "mergeRef": "refs/heads/<branch>",
  "baselineSha": "<upstream-sha>",
  "workflowId": "<utc-timestamp>-<head-prefix>",
  "checkpointShas": [],
  "adoptedShas": [],
  "pushRemote": null,
  "createdAt": "<utc-iso8601>",
  "updatedAt": "<utc-iso8601>"
}
```

`adoptedShas` is an ordered subset of `checkpointShas`; every entry needs recorded exact full-SHA user authorization. A `pendingCheckpoint` object holds recovery evidence while one checkpoint is in flight: `parentSha`, the sorted NUL-delimited write set's digest and path count, `stagedTreeSha` once staged, and `candidateCommitSha` plus the message digest once the candidate exists. After consolidation the record gains `oldHead`, `finalTree`, `backupRef`, and `newCommit`, and `pushRemote` is set at most once by the push phase in `remote-targets.md`.

## Begin And Resume

1. Enumerate `git -C <repo> rev-list --reverse '@{u}'..HEAD`. With no record, create one with empty arrays only when that list is empty. When it is non-empty, stop unless the user adopts that exact ordered full-SHA list; a range, count, branch name, or "all local commits" is insufficient, and merges, pushed commits, and commits outside `@{u}..HEAD` are never adopted. Seed both arrays with the adopted list.
2. Never overwrite an existing record. Resume a record without `newCommit` only when its identity and baseline fields match current facts and `checkpointShas` is an ordered prefix of the current `@{u}..HEAD` list; otherwise stop and report a stale record.
3. A record with `newCommit` is post-consolidation state: do not append checkpoints or consolidate again; recover it through `remote-targets.md`.
4. Report the record path, workflow id, and ordered SHA list after every update.

## Freeze The Write Set

Complete the repository, identity, baseline, operation-state, and adoption gates and run applicable read-only validation first. Require an empty index; any staged path stops before `pendingCheckpoint`. Resolve every intended path under the exact Git root, freeze the authorized set as NUL-delimited bytes, and record its digest, algorithm, and count in `pendingCheckpoint` before staging. Record staged, unstaged, untracked, and rename state separately; a write failure means zero staging.

## Stage And Prove

Stage only the frozen paths with `git add --pathspec-from-file=<file> --pathspec-file-nul` or an equivalent literal path list; never `git add .` or a glob. Read the staged set back with `git diff --cached --name-status -z` and require exact equality with the frozen set; any extra, missing, or renamed path stops. An empty staged diff stops unless the user asked for an empty checkpoint. Review the staged diff; never alter unrelated state to make it match. Record `git write-tree` as `stagedTreeSha`.

## Construct And Install

Build the message from validated lines in this shape, pass it on standard input, and construct the candidate from the recorded tree, never from the current index and never with ordinary `git commit`:

```text
<type>: <concise checkpoint summary>

Axiom-checkpoint: true
Remote baseline: <upstream> @ <sha>

Scope:
<what changed and why>

Validation:
<commands run and outcomes>
```

```bash
git -C <repo> commit-tree <staged-tree-sha> -p <parent-sha>
```

Before any ref mutation, verify with `git cat-file -p` and `git diff-tree` that the candidate has exactly one parent `parentSha`, tree `stagedTreeSha`, the frozen message, and the frozen changed path set; record `candidateCommitSha`. Recheck that `HEAD` is the symbolic ref `branchRef` resolving to `parentSha`, then install with compare-and-swap:

```bash
git -C <repo> update-ref --no-deref <branch-ref> <candidate-commit-sha> <parent-sha>
```

A failed compare-and-swap is branch drift: keep every record and never retry or fall back to `git commit`. After success, require `HEAD` and `branchRef` to resolve to the candidate and repeat the parent, tree, message, and path proofs. Capture the index and status before and after the transaction; concurrent index state is reported, not normalized, and cannot change the commit. Append the SHA to `checkpointShas` and remove `pendingCheckpoint` in one record replacement. Do not update the baseline cache after a local checkpoint.

## Failure And Recovery

- A pending-record, staging, staged-set, or tree-record failure stops with the index and pending state as found; never auto-unstage or clear evidence.
- A candidate construction, proof, or record failure performs no ref mutation.
- A no-commit pending record may be removed only when identity and baseline match, there is no `newCommit`, `HEAD == parentSha`, `checkpointShas` equals `@{u}..HEAD`, and the index is empty.
- If the commit succeeded but the record append failed or is uncertain, stop; never create another checkpoint, consolidate, or push. On an explicitly resumed recovery, append the unrecorded `HEAD` only when the record has no `newCommit`, `pendingCheckpoint` matches the current parent, write-set digest, path count, and `stagedTreeSha`, `checkpointShas` is an ordered prefix of `@{u}..HEAD` followed by exactly that one commit, and the commit's parent, tree, message digest, marker, and changed paths all match. Any larger gap or uncertain binding needs the user to adopt the exact full SHA; a marker, subject, author, time, or apparent path match never replaces that confirmation.
