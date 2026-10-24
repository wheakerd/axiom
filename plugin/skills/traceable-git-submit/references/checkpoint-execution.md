# Checkpoint Execution

## Purpose

Freeze one authorized write set, create its isolated checkpoint, and recover
when commit creation outlives provenance persistence.

## Existing Unpublished Commits

Before a new active record, enumerate the ordered full-SHA list:

```bash
git -C <repo> rev-list --reverse '@{u}'..HEAD
```

If non-empty, stop before record or checkpoint creation unless the user adopts
that exact ordered full-SHA list for this workflow.

For adoption:

- Repeat the list after any fetch; require every named full SHA and exact order.
  A range, count, branch, or "all local commits" is insufficient.
- Reject merges, pushed commits, malformed SHAs, and commits outside
  `@{u}..HEAD`; seed both `checkpointShas` and `adoptedShas` before new work.
- The record proves adoption. Only workflow-created commits outside
  `adoptedShas` require `Axiom-checkpoint: true`.

Without exact adoption, leave existing commits and the working tree unchanged.

## Freeze The Authorized Write Set

Before staging:

1. Complete repository, identity, baseline, operation-state, and adoption
   gates; run applicable read-only validation.
2. Require an empty staged set. Any path stops before `pendingCheckpoint`.
3. Resolve every intended path under the exact Git root; freeze the authorized
   changed set in a NUL-safe representation.
4. Record staged, unstaged, untracked, and rename/copy state separately.

Use NUL-delimited Git output. Compare raw bytes with native arrays or NUL-safe
sorting, never newlines, word splitting, or whitespace loops.

Digest the sorted raw NUL-delimited set cryptographically. Only after all gates
pass, atomically record parent SHA, algorithm, digest, and count in
`pendingCheckpoint`. Do not persist sensitive path names. A write failure means
zero staging and a stop.

Render paths with reversible JSON or Git C-style escaping. Never display raw
controls or newlines, or alter a pre-existing index.

## Stage And Prove Isolation

After `pendingCheckpoint` is verified, stage only the frozen paths with a
path-safe mechanism. Do not use `git add .`, broad directory globs, or
newline-expanded path lists.

Collect the complete staged set again with NUL-delimited output and require
exact equality with the frozen set:

- Any extra, missing, spelling, rename-pair, or byte mismatch stops.
- An empty staged diff stops unless the user explicitly requested an empty
  checkpoint and repository policy permits it.

Review the full staged diff and binary/rename summaries; require only the
validated slice and never alter unrelated state to make it match.

Resolve the staged tree with `git write-tree`; atomically record and reread
`stagedTreeSha`. Any staging, comparison, tree, or record failure prohibits
candidate construction.

## Construct, Verify, And Install The Checkpoint

Build one exact message from independently validated lines under
`safe-git-values-and-metadata.md`'s hostile metadata boundary. Hash the final
message bytes and keep the bytes
inside a non-visible capture or permission-restricted native temporary file.
The required structure is:

```text
<type>: <concise checkpoint summary>

Axiom-checkpoint: true
Remote baseline: <upstream> @ <sha>

Scope:
<what changed and why>

Validation:
<commands run and outcomes>
```

Recheck `HEAD` as a symbolic ref exactly equal to recorded `branchRef`. Require
`branchRef` itself to be a validated direct, non-symbolic ref and to resolve to
`parentSha`. Construct the candidate from the recorded tree, never from the
current index and never with ordinary `git commit`:

```bash
git -C <repo> commit-tree <staged-tree-sha> -p <parent-sha>
```

Pass the exact message through standard input or the protected file. Before
any ref mutation, require the resulting full OID to be a commit with exactly
one parent equal to `parentSha`, tree equal to `stagedTreeSha`, exact message
bytes and digest equal to the frozen message, and NUL-safe changed path set
equal to the frozen authorized set. Atomically add `candidateCommitSha`,
`messageDigest`, and `messageDigestAlgorithm` to `pendingCheckpoint`, reread
them, and repeat the branch direct-ref/old-OID checks.

Capture the current index tree and NUL-safe status immediately before the ref
transaction; this is concurrent-state evidence, not commit input. Install only
the verified candidate with compare-and-swap:

```bash
git -C <repo> update-ref --no-deref <branch-ref> <candidate-commit-sha> <parent-sha>
```

After success, require symbolic `HEAD` still names `branchRef`, both resolve to
the candidate, and repeat parent, tree, message, and path proofs. Capture the
index tree and status again. Never normalize the index: if either differs from
`stagedTreeSha`, or the captures differ from each other, preserve that
concurrent state and report it as staged relative to the new `HEAD`. It cannot
change the already constructed commit.

Atomically append only `candidateCommitSha` and remove `pendingCheckpoint` in
the same record replacement. Do not update the remote baseline cache after a
local checkpoint.

## Failure Points And Bounded Abort

- Pending write failure: no staging is allowed; stop.
- Staging or staged-set failure: stop with pending state visible. Do not
  auto-unstage or clear evidence.
- Staged-tree record failure: do not construct a candidate. Retain the index
  and pending state.
- Candidate construction, proof, or candidate-record failure: perform no ref
  mutation. Retain pending state and the index exactly as found.
- Branch compare-and-swap failure: treat it as branch drift, retain all
  evidence, and do not retry or fall back to `git commit`.
- Append failure: use only the recovery gate below.

A no-commit pending record may be cleared only when identity/baseline match,
there is no `newCommit`, `HEAD == parentSha`, `checkpointShas` equals
`@{u}..HEAD`, and the staged set is empty. Atomically remove only
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
- That commit is current `HEAD` and recorded `candidateCommitSha`; its parent
  is the last recorded SHA or `baselineSha`.
- Its exact message digest matches the pending record and it passes the safe
  exact marker gate in `safe-git-values-and-metadata.md`.
- Its commit tree exactly equals recorded `stagedTreeSha`.
- Its changed path set produces the exact recorded NUL-safe write-set digest
  and path count.
- Current index/worktree state is captured without modification; any
  concurrent state is reported and cannot alter the candidate proof.

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
