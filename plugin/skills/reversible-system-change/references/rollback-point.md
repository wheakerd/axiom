# Rollback Point

## Purpose

Own the rollback-point evidence contract that `preflight-and-rollback.md` routes to before candidate or active-state mutation: the native mechanism, the five evidence states, the nine requirements, the isolated restore rehearsal, and what never proves a verified rollback.

## Establish A Rollback Point

Choose a rollback mechanism native to the target when possible: an inactive
version slot, package version retained in a trusted cache, snapshot, backup,
database restore point, configuration copy with metadata, deployment revision,
or reversible pointer change.

If the material must first be created, use the parent's recovery-material
preparation phase and its directly routed reference. Its isolation gate permits
only bounded preparation; all requirements below still govern candidate and
active-state mutation.

Keep these evidence states distinct:

- `identified`: the prior state and proposed recovery mechanism are named.
- `present`: the rollback artifact or prior target currently exists.
- `readable`: the exact restore principal and mechanism can read it now.
- `restore-validated`: a current target-native check has actually validated
  restorability, not merely listed metadata.
- `rehearsed`: an isolated restoration using the same artifact, mechanism, and
  required ordering has completed and its result was checked.

Do not call a rollback path `verified`, `usable`, or `restore-ready` by
collapsing lower states. Before candidate or active-state mutation require:

1. The rollback point represents the directly observed pre-change state.
2. Its identifier and location are unambiguous and excluded from destructive
   scope.
3. The exact restore principal and current restore mechanism can read it now,
   not merely see that an artifact or record exists.
4. The restore tool, credentials, permissions, required files, metadata,
   dependencies, capacity, and operation ordering are currently available.
5. Recovery covers every non-forward-compatible effect in the frozen write
   set. If restoration could discard newer data, define and authorize its
   preservation or reconciliation; otherwise stop.
6. A current platform-native validation that actually checks restorability or
   an isolated restore rehearsal has succeeded against the same rollback point
   and mechanism. A listing, manifest, checksum, or snapshot status that checks
   only existence or integrity does not satisfy this requirement.
7. The restore action and affected write set are bounded and authorized as the
   failure path.
8. A post-restore check can prove the active state, runtime, data, and behavior
   returned to the observed prior state at every affected layer.
9. The rollback point and all evidence have a recorded current identity and are
   rechecked immediately before candidate or active-state mutation.

For a pointer-only rollback with no irreversible data effect, an isolated
equivalent switch plus a behavior check may serve as the rehearsal. Merely
resolving the prior target proves only presence or readability.

An isolated restore rehearsal is itself a persistent write, bounded by the parent's isolated-restore-rehearsal phase. Before running it, prove that its non-active target cannot affect active state or data and that a failed rehearsal can be abandoned or recreated within its authorized write set; otherwise require the complete execution gate. A plan-only or non-mutating workflow rehearsal cannot perform it. Freeze an isolated non-active target and its complete write set, obtain exact rehearsal-write authority, and verify only the restore outcome. The rehearsal may establish `rehearsed` evidence; it never authorizes candidate preparation, active promotion, the complete change, or cleanup.

The following never prove a verified rollback by themselves: a successful
backup or copy command, a present snapshot, an existing rollback script,
documentation of restore commands, a checksum, a historical rehearsal, user
confidence, or a mutable artifact that would need to be downloaded later.

If the complete evidence set cannot be verified, stop before candidate or active-state mutation and name the missing evidence and the specific effects that would stay unrecoverable. Plan-only work may report the gap, but user acceptance of irreversible risk does not satisfy the contract.

Only an informed waiver lifts this rollback requirement, and only for its exact target and scope; `informed-waiver.md` owns its conditions and limits.

