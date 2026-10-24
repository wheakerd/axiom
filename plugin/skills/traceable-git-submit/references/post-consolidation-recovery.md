# Post-Consolidation Recovery And Cleanup

## Purpose

Bind a consolidated workflow to one push identity at most once, resume its
exact commit, verify every target and refreshed upstream, and make cleanup
independently authorizable.

## Apply When

Use only when the active provenance record contains `newCommit`, including the
combined consolidation-and-push flow. Never create another final commit,
append a checkpoint, or consolidate again on this route.

## One-Time Push Target Binding

Local-only consolidation persists the initial
`pushTargetState.state == unbound` from `checkpoint-provenance.md`. It must not
inventory endpoints, invent an empty target list, or derive push identity from
upstream.

Only after `newCommit` and `backupRef` are verified, and only under current
explicit push authority, apply `repository-and-remote-targets.md` to resolve,
confirm, inventory, and authorize current push identity. An unbound record may
then transition once to:

```json
{
  "pushTargetState": {
    "state": "bound",
    "pushRemote": "<effective-configured-remote>",
    "resolutionSource": "<explicit|branch-push-remote|remote-push-default|upstream-remote>",
    "mergeRef": "refs/heads/<branch>",
    "fingerprintAlgorithm": "<stable-cryptographic-algorithm>",
    "orderedFingerprints": ["<fingerprint>"],
    "boundAt": "<utc-iso8601>"
  }
}
```

Never store raw endpoints. Immediately before binding, re-resolve and
re-enumerate and require exact equality with the authorized frozen values.
Apply metadata containment, acquire an exclusive verified sibling lock, reread
the exact unbound record, atomically replace it with the bound form, reread,
and release the lock. If serialization or exact reread is unproved, leave it
unbound and stop. Never overwrite or rebind a bound record.

Combined submission first persists recoverable `newCommit` unbound, then binds
before any push. A later explicit push binds at that time. On unbound resume,
make no prior-target assumption. On bound resume, re-resolve and require exact
repository, workflow, final commit, `pushRemote`, `mergeRef`, algorithm, and
ordered fingerprints. An explicit mention of the same remote confirms rather
than changes the binding. Zero targets, unresolved multi-target authorization,
or pre-bind drift leaves the record unbound. Post-bind drift retains the record
and backup; no target fallback, subset, superset, reorder, or rebinding is safe.

A missing state, loose legacy fingerprints, or mismatch cannot auto-migrate or
enter remote verification. Only a bound record can reach `cleanupReady`.

## Recovery Gate

1. Require `repo`, `branchRef`, `branch`, `upstream`, `upstreamRemote`, and
   `mergeRef` to match current facts. Require valid full-SHA `oldHead`,
   `finalTree`, and `newCommit`, with commit/tree types as applicable. Validate
   `backupRef` as the exact full `refs/axiom/backups/` ref name through
   `safe-git-values-and-metadata.md`, not as an OID. Bind an unbound record
   through the gate above before remote work; require equality for a bound one.
2. Require `HEAD == newCommit`, `newCommit^ == baselineSha`, and
   `newCommit^{tree} == oldHead^{tree} == finalTree`.
3. If `backupRef` exists, require a non-symbolic ref whose resolved commit OID
   equals `oldHead`. A missing ref is only observed state until the cleanup
   intent and proof below permit reconciliation.
4. Query each bound target's `mergeRef`; require exactly `baselineSha` or
   `newCommit`. Refresh only through `consolidation-and-push.md` under explicit
   refresh authority. Push/recovery authority never implies fetch; without it,
   mark `@{u}` unrefreshed and prohibit upstream-dependent transitions.
5. If all targets equal `baselineSha`, require the backup, clean submitted
   content, and exactly `newCommit` over that baseline. Retry only the recorded
   push under current authority after the all-target baseline gate. If refresh
   ran, also require refreshed `@{u} == baselineSha`.
6. If all targets equal `newCommit`, require authorized refresh and
   `@{u} == newCommit` before baseline update, cleanup proof, or deletion.
   Otherwise retain recovery state despite direct target success.
7. On target disagreement or refreshed-upstream mismatch, report partial state
   and stop. Do not push again, restore the branch, update cache, or clean up.

Keep endpoints opaque and render filesystem paths reversibly.

## Cleanup Readiness And Independent Authority

Only after every bound target and refreshed `@{u}` equal `newCommit`:

1. Update and verify baseline identity and
   `lastRemotePushSha == newCommit`.
2. Atomically persist readiness without deletion:

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

3. Without separate authority for both deletions bound to exact repository,
   workflow, refs, OIDs, effective push identity, and ordered fingerprints,
   retain backup and record, report `cleanupReady`, and ask one concise
   question. Prior push, consolidation, recovery, or generic cleanup is
   insufficient.
4. Under exact authority, recheck identity, bound targets, upstream, cache,
   containment, and backup immediately before deletion. Drift stops cleanup.
5. Before deletion, atomically persist and reread `cleanupReady.backupDeletion`
   with state `pending`, the exact `backupRef`, and expected OID `oldHead`.
   Bind it to the unchanged record identity, final commit, push target set,
   and current exact cleanup authority. Use the verified sibling lock and
   no-follow atomic replacement contract for this and later record updates.
   If intent persistence is uncertain, do not delete the ref.
6. Delete an existing backup with old-value compare-and-swap:

   ```bash
   git -C <repo> update-ref --no-deref -d <backup-ref> <old-head>
   ```

7. Verify that the exact ref is absent. Atomically set
   `cleanupReady.backupRefDeleted: true` and `backupDeletion.state: complete`,
   reread through the no-follow boundary, and verify every bound field.
8. Delete the active record through the same containment boundary.

A pending deletion resumes only after identity, intent, current authority,
containment, every target, upstream, and baseline proofs still pass. If the ref
still equals `oldHead`, resume its compare-and-swap deletion; if absent, record
the observed desired state through step 7 without issuing another deletion or
claiming who removed it. A changed or symbolic ref stops. Absence without a
matching persisted intent or an already-true deletion flag never proves
authorized cleanup. An already-complete flag requires absence and current
proofs before record deletion. On failure retain the record and resume at the
first incomplete step; never recreate the backup or invent intent afterward.

## References

- `repository-and-remote-targets.md`
- `baseline-and-preflight.md`
- `checkpoint-provenance.md`
- `consolidation-and-push.md`
