# Post-Consolidation Recovery And Cleanup

## Purpose

Resume exactly one consolidated commit, verify every frozen push target and the
authoritative refreshed upstream, then clean recovery state in a safe order.

## Apply When

Use only when the active provenance record contains `newCommit`, including the
normal submit flow after branch consolidation. Never create another final
commit, append a checkpoint, or consolidate again on this route.

## Recovery Gate

1. Require `repo`, `branchRef`, `branch`, `upstream`, `remote`, and `mergeRef`
   to match current facts. Require full-SHA `oldHead`, `finalTree`, and
   `newCommit`, a valid `backupRef`, and exact equality between current and
   recorded ordered push-target fingerprint sets.
2. Require `HEAD == newCommit`, `newCommit^ == baselineSha`, and both
   `newCommit^{tree}` and `oldHead^{tree}` to equal `finalTree`.
3. Resolve `backupRef`. If present, require `backupRef == oldHead`. Treat a
   missing ref only as observed state until the cleanup-proof gate permits it.
4. Fetch the resolved branch remote, then resolve authoritative `@{u}`. Query
   every frozen push target's `mergeRef` directly. Each target must equal
   either `baselineSha` or `newCommit`; any other or unreadable result stops.
5. If every target and refreshed `@{u}` equal `baselineSha`, require the backup
   ref, a clean index and worktree for submitted content, and exactly
   `newCommit` in `@{u}..HEAD`. Retry only the recorded push, after the immediate
   all-target baseline gate in `repository-and-remote-targets.md` passes.
6. If every target equals `newCommit`, require refreshed `@{u} == newCommit`
   before baseline-cache update, cleanup proof, or backup deletion. If `@{u}`
   differs or cannot be resolved after fetch, retain all recovery state and
   stop even when push targets agree.
7. If targets disagree between `baselineSha` and `newCommit`, or `@{u}` and
   targets disagree, report partial remote state and stop. Do not push again,
   restore the local branch, update cache, or begin cleanup automatically.

Never expose raw endpoints. Render every displayed filesystem path with
JSON-string, Git C-style, or equivalent reversible escaping.

## Cleanup Proof And Order

Only after every target and refreshed `@{u}` directly equal `newCommit`:

1. Update and verify baseline-cache identity and
   `lastRemotePushSha == newCommit`.
2. Atomically persist:

   ```json
   {
     "cleanup": {
       "remoteVerifiedSha": "<newCommit>",
       "upstreamVerifiedSha": "<newCommit>",
       "baselineUpdated": true,
       "backupRefDeleted": false
     }
   }
   ```

3. Delete an existing backup ref with its old-value check:

   ```bash
   git -C <repo> update-ref -d <backup-ref> <old-head>
   ```

4. Atomically set `backupRefDeleted: true`.
5. Delete the active record.

A missing backup ref is acceptable only when the record already contains the
cleanup proof, including `upstreamVerifiedSha`, and current target, upstream,
and cache state all equal `newCommit`. Otherwise stop as unsafe. If any cleanup
step fails, retain the active record; re-enter at the first incomplete step
only after re-verifying actual target, upstream, cache, and backup-ref state.

## References

- `repository-and-remote-targets.md`
- `baseline-and-preflight.md`
- `checkpoint-provenance.md`
- `consolidation-and-push.md`
