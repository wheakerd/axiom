# Active Checkpoint Provenance

## Purpose

Prove that every commit selected for consolidation was created by the current
user-authorized traceable checkpoint workflow. A commit body containing
`Axiom-checkpoint: true` is necessary but is not provenance by itself.

## Active Record

Resolve the active record from target Git metadata. Never put it in the target
working tree or the installed plugin directory:

```bash
git -C <repo> rev-parse --path-format=absolute --git-path axiom/traceable-git-submit-active-checkpoints.json
```

The record is local workflow state. It must never be staged or committed. Use a
temporary sibling file plus an atomic rename when native file-writing tools are
available.

Its schema is:

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
  "checkpointShas": ["<checkpoint-sha>"],
  "createdAt": "<utc-iso8601>",
  "updatedAt": "<utc-iso8601>"
}
```

After consolidation succeeds locally, retain the same record and add
`oldHead`, `finalTree`, `backupRef`, and `newCommit`. This makes an interrupted
push retry auditable without recreating or re-squashing the checkpoint series.

## Begin And Record

Only after the user has explicitly authorized the current traceable checkpoint
workflow and Git preflight succeeds:

1. Resolve the record path. If no record exists, write a new record with the
   current repository identity, branch facts, upstream SHA, and an empty
   `checkpointShas` list.
2. If a record already exists, do not overwrite it. When it has no `newCommit`,
   resume only when all identity and baseline fields match and its SHA list is
   an exact ordered prefix of the current `@{u}..HEAD` list. Otherwise stop and
   report the stale record path. When it has `newCommit`, it is a
   post-consolidation recovery record: do not create or append checkpoints;
   do not apply this prefix rule or the normal consolidation gate. Route it to
   the post-consolidation recovery gate below.
3. After each checkpoint commit, verify `HEAD` equals that new SHA, verify its
   body contains `Axiom-checkpoint: true`, append only that SHA, and atomically
   update the record.
4. Report the record path, workflow id, and ordered SHA list after every update.

## Consolidation Gate

Before creating a backup ref or final commit:

1. Enumerate `git -C <repo> rev-list --reverse '@{u}'..HEAD`.
2. Read the active record and require matching `repo`, `branchRef`, `branch`,
   `upstream`, `remote`, `mergeRef`, and `baselineSha` values.
3. Require the record's `checkpointShas` to exactly equal the enumerated ordered
   commit list. Reject missing, extra, reordered, malformed, or duplicate SHAs.
4. Independently check every selected commit body for `Axiom-checkpoint: true`.

If any check fails, stop. Do not infer authorization from a marker, timestamp,
author, branch name, or cache entry. Report the unexpected SHA(s). The only way
to adopt pre-existing commits is a new explicit user confirmation naming the
exact ordered SHA list; create a new active record only after that confirmation.

## Post-Consolidation Recovery Gate

Use this gate only when the active record has `newCommit`. It replaces the
normal checkpoint-list equality gate; the old `checkpointShas` intentionally do
not equal the single consolidated commit now ahead of the remote.

1. Require the normal identity fields (`repo`, `branchRef`, `branch`,
   `upstream`, `remote`, and `mergeRef`) to match the current branch facts.
   Require `oldHead`, `finalTree`, and `newCommit` to be full commit or tree
   SHAs and `backupRef` to be a ref name. Treat a missing or malformed recovery
   field as an unsafe record and stop.
2. Require `HEAD` to equal `newCommit`; require `newCommit^` to equal the
   recorded `baselineSha`; require both `newCommit^{tree}` and
   `oldHead^{tree}` to equal `finalTree`; and require `backupRef` to resolve to
   `oldHead`. Require a clean working tree and index.
3. Fetch the resolved branch remote, then resolve its merge ref directly. Its
   SHA must equal either recorded `baselineSha` or recorded `newCommit`. Any
   other remote SHA means the remote moved independently; stop without pushing,
   rewriting, or deleting recovery state.
4. If the remote still equals `baselineSha`, require
   `git -C <repo> rev-list --reverse '@{u}'..HEAD` to contain exactly
   `newCommit`, then retry only the recorded push. Do not create another commit,
   update any local branch ref, or run checkpoint consolidation.
5. If the remote already equals `newCommit`, treat the prior push as remotely
   verified and perform only baseline-cache, backup-ref, and active-record
   cleanup. Do not push or consolidate again.

## Atomic Persistence Failure

After the branch `update-ref` succeeds, persist `oldHead`, `finalTree`,
`backupRef`, and `newCommit` through a temporary sibling file and atomic
replacement. If that write reports failure or its outcome is uncertain, do not
push or update the baseline cache. Immediately attempt this compare-and-swap
restoration:

```bash
git -C <repo> update-ref <branch-ref> <old-head> <new-commit>
```

Then verify that both `branchRef` and `backupRef` resolve to `oldHead`. Retain
the backup ref and active record whatever their on-disk write state, report the
record path and restoration result, and stop. Do not retry, push, or
re-consolidate until a new explicit recovery assessment resolves the record
state.

## Completion And Recovery

Keep the active record through local consolidation, push, and remote SHA
verification. On a failed push or interrupted session, retain it with the
backup ref and consolidated commit fields so a retry can validate and push the
existing final commit without a second consolidation. Follow the
post-consolidation recovery gate before retrying the push or cleanup.

After remote verification succeeds, update the baseline cache, delete the
backup ref with its old-value check, then delete the active record. If any of
those cleanup steps fails, retain the active record and report the recovery
state.
