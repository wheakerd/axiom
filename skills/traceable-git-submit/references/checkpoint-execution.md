# Checkpoint Execution

## Purpose

Freeze an authorized write set, create one isolated checkpoint commit, and
recover safely when the commit exists but provenance persistence failed.

## Existing Unpublished Commits

Before creating a new active record, enumerate the exact ordered full-SHA list:

```bash
git -C <repo> rev-list --reverse '@{u}'..HEAD
```

If the list is non-empty, stop before writing the record or creating a
checkpoint. Continue only when the user explicitly adopts that exact ordered
full-SHA list for the current workflow.

For adoption:

- Repeat the list after any fetch and require an exact match.
- Name every SHA; a range, count, branch, or "all local commits" is not exact.
- Reject merges, already-pushed commits, malformed SHAs, or commits outside
  `@{u}..HEAD`.
- Record the ordered list in both `checkpointShas` and `adoptedShas` before new
  checkpoint work.
- The record proves adoption. `Axiom-checkpoint: true` is required only for
  workflow-created commits outside `adoptedShas`.

Without exact adoption, leave existing commits and the working tree unchanged.

## Freeze The Authorized Write Set

Before staging:

1. Complete the applicable read-only repository, identity, baseline,
   operation-state, and unpublished-commit/adoption gates.
2. Prove the staged-change set is empty. Any path, even an overlapping one,
   stops before `pendingCheckpoint`.
3. Run validation appropriate to the work slice when it can remain read-only.
4. Resolve every intended path relative to the exact target Git root.
5. Resolve and freeze the exact authorized currently changed path set in a
   NUL-safe representation.
6. Record staged, unstaged, untracked, and rename/copy state separately.

Use NUL-delimited Git output such as `git status --porcelain=v1 -z` and
`git diff [--cached] --name-only -z`. Compare raw bytes with native arrays or
NUL-safe sorting, never newlines, word splitting, or whitespace loops.

Digest the sorted raw NUL-delimited set cryptographically. Only after all gates
pass, atomically record parent SHA, algorithm, digest, and count in
`pendingCheckpoint`. Do not persist sensitive path names. A write failure means
zero staging and a stop.

Render every reported path with JSON-string, Git C-style, or equivalent
reversible escaping. Never display raw control characters or newlines. Do not
unstage, overwrite, or commit a pre-existing index.

## Stage And Prove Isolation

After `pendingCheckpoint` is verified, stage only the frozen paths with a
path-safe mechanism. Do not use `git add .`, broad directory globs, or
newline-expanded path lists.

Collect the complete staged set again with NUL-delimited output and require
exact equality with the frozen set:

- Any extra, missing, spelling, rename-pair, or byte mismatch stops.
- An empty staged diff stops unless the user explicitly requested an empty
  checkpoint and repository policy permits it.

Review the full staged diff, including binary/rename summaries, and require only
the validated slice. Do not alter unrelated state to satisfy comparison.

Then resolve the exact staged tree with `git write-tree`; atomically record and
reread `stagedTreeSha` before commit. Any staging, comparison, tree, or record
failure prohibits commit.

## Create And Record The Checkpoint

Create one commit with the required structure:

```text
<type>: <concise checkpoint summary>

Axiom-checkpoint: true
Remote baseline: <upstream> @ <sha>

Scope:
<what changed and why>

Validation:
<commands run and outcomes>
```

After commit creation:

1. Require `HEAD` to equal the new full SHA.
2. Require its parent to equal the previous `HEAD`.
3. Require its body to contain `Axiom-checkpoint: true`.
4. Require its tree to equal recorded `stagedTreeSha`.
5. Require its changed path set to equal the frozen authorized set using
   NUL-safe comparison.
6. Atomically append only that SHA and remove `pendingCheckpoint` in the same
   record replacement.

Do not update the remote baseline cache after a local checkpoint.

## Failure Points And Bounded Abort

- Pending write failure: no staging is allowed; stop.
- Staging or staged-set failure: stop with pending state visible. Do not
  auto-unstage or clear evidence.
- Staged-tree record failure: do not commit. Retain the index and pending state.
- Commit failure: retain pending and the index. Retry only when identity,
  `HEAD == parentSha`, the full staged path set, and the current
  `git write-tree` result exactly matches `stagedTreeSha`.
- Append failure: use only the recovery gate below.

A no-commit pending record may be cleared only when identity/baseline match,
there is no `newCommit`, `HEAD == parentSha`, `checkpointShas` exactly equals
`@{u}..HEAD`, and the staged-change set is empty. Atomically remove only
`pendingCheckpoint`, reread, report, and leave worktree changes untouched. Any
staging, commit, or uncertainty retains it for user direction.

## Provenance Append Failure Recovery

If the checkpoint commit succeeds but the atomic append fails or is uncertain,
stop immediately. Do not create another checkpoint, consolidate, push, replace
the record, or infer that the append succeeded.

On an explicitly resumed recovery, append the unrecorded `HEAD` only when all
of these are directly verified:

- The record identity and baseline still match current facts.
- The record has no `newCommit`.
- Its `pendingCheckpoint` matches the current parent, the previously frozen
  write-set digest, digest algorithm, path count, and full `stagedTreeSha`.
- Its `checkpointShas` exactly equals an ordered prefix of `@{u}..HEAD`.
- Exactly one commit follows that prefix.
- That commit is current `HEAD`, its parent is the last recorded SHA or
  `baselineSha`, and its body contains `Axiom-checkpoint: true`.
- Its commit tree exactly equals recorded `stagedTreeSha`.
- Its changed path set produces the exact recorded NUL-safe write-set digest
  and path count.
- The working tree/index state has not introduced ambiguity.

Atomically append that one exact SHA and remove `pendingCheckpoint`, reread the
record, and require the stored list to equal the full `@{u}..HEAD` list. Any
larger gap, missing write-set evidence, identity change, or content mismatch
requires manual user direction; never adopt it automatically.

When the one-commit shape is clear but workflow identity or content binding is
missing or uncertain, do not auto-append. Ask the user to explicitly adopt the
current exact full SHA. Only after the standard adoption exclusions pass may
an atomic update append that SHA to `checkpointShas` and `adoptedShas`, remove
`pendingCheckpoint`, and record the independent adoption path. A marker,
subject, author, time, or apparent path match never replaces that confirmation.
