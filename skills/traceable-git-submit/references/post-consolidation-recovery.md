# Post-Consolidation Recovery And Cleanup

## Purpose

Resume exactly one consolidated commit, verify every frozen push target and the
authoritative refreshed upstream, then make cleanup independently authorizable
and recoverable.

## Apply When

Use only when the active provenance record contains `newCommit`, including the
combined consolidation-and-push flow after branch consolidation. Never create
another final commit, append a checkpoint, or consolidate again on this route.

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

## Cleanup Readiness And Independent Authority

Only after every target and refreshed `@{u}` directly equal `newCommit`:

1. Update and verify baseline-cache identity and
   `lastRemotePushSha == newCommit`.
2. Atomically persist readiness without deleting anything:

   ```json
   {
     "cleanupReady": {
       "remoteVerifiedSha": "<newCommit>",
       "upstreamVerifiedSha": "<newCommit>",
       "baselineUpdated": true,
       "backupRefDeleted": false
     }
   }
   ```

3. If the current user request does not separately authorize both deletion
   operations for this exact repository, `workflowId`, `backupRef`, `oldHead`,
   `newCommit`, and ordered target fingerprint set, retain the backup and active
   record, report `cleanupReady`, and ask one concise cleanup question. A prior
   push, consolidation, recovery, or generic cleanup request is insufficient.
4. Under exact cleanup authority, re-run every recovery identity, target,
   upstream, cache, metadata-containment, and backup-ref check immediately
   before deletion. Any changed fact invalidates authority and stops cleanup.
5. Delete an existing backup ref with its old-value compare-and-swap check:

   ```bash
   git -C <repo> update-ref -d <backup-ref> <old-head>
   ```

6. Atomically set `cleanupReady.backupRefDeleted: true`, reread it through the
   no-follow boundary, and verify every bound field again.
7. Delete the active record through the same no-follow containment boundary.

A missing backup ref is acceptable only when `cleanupReady.backupRefDeleted` is
already true, the exact cleanup authority covers active-record deletion, and
current target, upstream, cache, identity, and metadata containment still pass.
Otherwise stop as unsafe. If any cleanup step fails, retain the active record;
re-enter at the first incomplete step only after fresh verification and fresh
or still-valid exact cleanup authority.

## References

- `repository-and-remote-targets.md`
- `baseline-and-preflight.md`
- `checkpoint-provenance.md`
- `consolidation-and-push.md`
