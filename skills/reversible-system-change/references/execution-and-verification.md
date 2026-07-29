# Execution And Verification

## Purpose

Apply only the authorized mutation, promote deliberately, verify its real
postconditions, and restore the prior state when a pre-authorized failure gate
is reached.

## Final Gate

Immediately before the first persistent write, refresh the facts that could
invalidate the plan:

- Target identity and active environment.
- Current active version, entry point, configuration, and service state.
- Frozen write set and destructive root boundaries.
- Free space, locks, in-progress operations, dependency and migration state.
- Rollback-point presence, readability, ownership, and restore prerequisites.
- Candidate identity, integrity, validation result, and promotion authority.

Stop on drift. Do not repair an unrelated dirty state or widen scope merely to
make the gate pass.

## Apply And Promote

Apply the smallest authorized candidate mutation first. Preserve the active
version and rollback material until completion evidence is established.

When promotion is distinct from preparation:

1. Validate the candidate in its inactive location.
2. Recheck the current active pointer or revision with compare-and-swap
   semantics when the platform supports it.
3. Switch only the authorized entry point, configuration, revision, or traffic
   target.
4. Perform only declared reloads, restarts, migrations, or rollout actions.
5. Stop further promotion immediately when any required gate fails.

Do not treat build success as installation, installation as selection,
selection as process readiness, remote acceptance as application, or queue
acceptance as rollout completion.

For destructive retention work, enumerate the bounded candidates immediately
before deletion, verify their type, age, root, filesystem, and symlink policy,
then delete only that exact set. Re-inventory survivors afterward.

## Layered Postconditions

Verify with fresh direct evidence at each affected layer. Select only relevant
layers, but do not skip a layer that owns part of the requested outcome:

1. Materialization: expected files, package records, database state, or remote
   objects exist with the intended identity.
2. Selection: active pointer, configuration, deployment revision, or routing
   state resolves to the candidate.
3. Runtime: service or process loaded that selection and reached required
   readiness.
4. Delivery: remote receiver, orchestrator, queue consumer, or rollout layer
   applied the change rather than merely accepting it.
5. Behavior: an affected command, health check, query, or user-visible path
   demonstrates the requested result.
6. Preservation: unrelated state and the verified rollback point remain intact
   until cleanup is safe.

Use current authoritative queries after the change. Cached output, a prior dry
run, expected configuration text, or one successful lower layer cannot prove a
higher layer. A command's zero exit status proves only that command's reported
operation.

If a tool, permission, network path, environment, or downstream layer is
unavailable, record that layer as unverified. Never translate inability to run
a check into a pass.

## Failure And Rollback

Define the failure gates before mutation. On a required validation failure:

1. Stop new writes, promotion, cleanup, and destructive follow-on work.
2. Preserve failure evidence without exposing secrets.
3. If rollback was included in the authorized change plan, restore only the
   frozen write set from the verified rollback point in the required order.
4. Re-resolve the active entry point, configuration, data state, runtime, and
   behavior; require direct evidence that the prior state is active again.
5. Retain rollback and candidate material when restoration is incomplete or
   evidence is uncertain.

If rollback itself would exceed the authorized scope, risk newer user data, or
target a different live state than preflight observed, stop and request
direction. Never hide a failed change through an unverified reinstall,
destructive reset, broad cleanup, or deletion of recovery material.

## Cleanup

Delete temporary candidate or rollback material only when the user authorized
cleanup, all required postconditions pass, retention policy permits deletion,
and another verified recovery route remains when policy requires one. Resolve
each cleanup target directly and report whether retained material is still
needed for recovery.

## Completion Report

Report:

- Exact target and authorized effects.
- Directly observed prior state and verified rollback point.
- Candidate, dry-run, mutation, and promotion outcomes.
- Each relevant postcondition layer as passed, failed, not run, or unavailable.
- Rollback trigger, action, and restored-state evidence when used.
- Final observed state, retained recovery material, and validation gaps.

Do not expose secret values or private endpoints. Do not claim the requested
system change completed when any outcome-owning layer remains failed or
unverified.
