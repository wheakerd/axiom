# Recovery Material Preparation

## Purpose And Boundary

Create missing recovery material without changing active state or needing that
same material to be restore-validated first. Load only through the parent's
preparation phase after `preflight-and-rollback.md` resolves the source and
intended recovery mechanism. Plan-only work cannot enter this phase.

Preparation may establish `present` and `readable` evidence. It never establishes
`restore-validated` or `rehearsed` evidence by itself and never authorizes
candidate preparation, promotion, active-state changes, or a restore rehearsal.

## Freeze Preparation Authority

Before preparation, bind the current authorization to:

- The exact observed source, source-read or snapshot action, recovery principal,
  capture-consistency method, and expected prior-state identity.
- An unused, non-active destination and the complete direct and indirect write
  set, including temporary output and manager-owned snapshot or backup records.
- Sensitive-content access, copying, retention, permissions, and any disclosure
  boundary. Metadata inventory alone cannot authorize reading a secret. Keep
  values out of commands, previews, logs, and verification output.
- Capacity bounds and the exact disposition of incomplete output on failure:
  safe retention or authorized removal of only newly created preparation state.

Use existing authorization when it covers this envelope; ask only for missing
necessary authority or a material ambiguity. External effects also require the
applicable `confirm-external-action` envelope. Preparation authority does not
authorize changing the source, stopping services, quiescing writes, restarting,
or overwriting any existing candidate or recovery material.

## Isolation And Failure Gate

Before the first preparation write, directly establish that:

1. The destination is unused and outside active selection, source data, and
   destructive scope. Creation fails on collision instead of replacing or
   following an existing object, link, or alias.
2. The chosen mechanism preserves source data and active state. Any generated
   manager metadata is bounded by the frozen write set and cannot select,
   promote, alter, or delete active or prior recovery state.
3. Required permissions and capacity are present; preparation cannot exhaust
   resources needed by the active system or invalidate its existing recovery.
4. Failure leaves active state and existing recovery intact. Incomplete output
   can be safely retained or disposed of within the frozen authority without
   restoring the source or relying on the not-yet-created backup.

If any condition is unproved, stop preparation. Do not use this exception to
perform a source mutation that needs the full rollback gate. Refresh source,
destination, isolation, capacity, and authority immediately before writing.

## Prepare, Verify, And Resume

Create only the bound material. Verify its identity, capture consistency,
coverage, access by the restore principal, and preservation of active state and
existing recovery. Record only the observed evidence state and non-secret
identifiers. A successful copy or snapshot command is not restore validation.

On failure or an unknown result, stop writes and inspect the exact source,
destination, and attempt state. Never overwrite partial output or blindly
repeat creation. Dispose of incomplete material only under its frozen disposal
authority after proving it is newly created preparation output, no active
consumer uses it, and its removal preserves prior state and existing recovery.
Otherwise retain it and report the unresolved state.

On resume, reconstruct the same source identity, preparation envelope, attempt
state, and isolation and disposal evidence. Missing restore validation is
expected in this phase; missing preparation evidence is not permission to
continue. Never relabel post-change source state as the original prior state.

After preparation, return to `preflight-and-rollback.md`. Require current full
coverage and target-native restore validation or an authorized isolated restore
rehearsal against this exact material before any candidate or active-state
mutation. Preparation-only authority ends with the observed material and its
evidence report; later actions use their own phase and applicable authority.
