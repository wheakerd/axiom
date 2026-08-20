---
name: reversible-system-change
description: Plan, rehearse, or execute persistent system changes with verified rollback and postconditions. Use for an install, upgrade, deployment, migration, destructive retention action, or active-version promotion with rollback, data, service, or activation risk. Plans and non-mutating workflow rehearsals stay read-only; isolated restore rehearsals require exact rehearsal-write authority. Do not use for ordinary source/configuration edits, Git operations, status queries, or conceptual explanations.
---

# Reversible System Change

Make one authorized persistent change without losing the ability to identify,
restore, and verify the prior working state.

## Select One Phase

- Plan or non-mutating workflow rehearsal: read
  `references/preflight-and-rollback.md`. Keep the entire phase read-only; do
  not create a candidate, backup, capsule, cache, remote record, or sensitive
  content access.
- Authorized isolated restore rehearsal: read
  `references/preflight-and-rollback.md` only. Freeze an isolated non-active
  target and its complete write set, obtain exact rehearsal-write authority,
  and verify only the restore outcome. This phase may establish `rehearsed`
  evidence; it never authorizes candidate preparation, active promotion, the
  complete change, or cleanup.
- Execute a complete authorized change: read
  `references/preflight-and-rollback.md` first. Read
  `references/execution-and-verification.md` only after the exact target,
  write set, promotion authority, rollback coverage, and current restore
  validation pass.
- Conceptual explanations and pure status/version/availability queries do not
  select this skill or load either reference.

## Authority Boundary

Resolve the requested outcome, exact target, authorized actions, and expected
postcondition before mutation. Ask one concise question only when target,
environment, destructive scope, credentials, sensitive asset use, promotion,
or rollback authority would change execution.

Keep an isolated restore rehearsal, candidate preparation, active promotion,
service restart/reload, data migration, destructive retention, sensitive asset
access, rollback, and rehearsal cleanup as separate actions. Permission for one
never implies another. Freeze the exact direct and indirect write set; a newly
discovered target, dependency, service, data store, endpoint, or destructive
effect requires renewed authority.

Inventory sensitive assets by metadata only. Read or use content only after
the exact path and exact action are both frozen and authorized. Never print,
copy broadly, hash, encode, or persist secret contents merely to inventory
them.

## Rollback Gate

Before the first persistent write, require a rollback point that represents the
observed prior state, covers every non-forward-compatible effect, is currently
readable by the restore principal with all prerequisites present, and has
passed a target-native restore validation or an authorized isolated rehearsal.
Recheck that evidence immediately before mutation.

For the isolated restore rehearsal itself, first prove that its non-active
target cannot affect active state or data and that a failed rehearsal can be
abandoned or recreated within its authorized write set. If that isolation is
unproven, treat the rehearsal as complete execution and require this full gate.

Keep `identified`, `present`, `readable`, `restore-validated`, and `rehearsed`
as distinct evidence states. A backup job, artifact, script, manifest,
checksum, historical rehearsal, or user acceptance of risk is not verified
rollback. If current restore validation or complete coverage cannot run, stop
execution; a plan may report the gap.

## Change Contract

1. Observe current target and runtime state with scoped read-only probes.
2. Freeze persistent effects, destructive roots, and the postcondition layers
   that own the requested outcome.
3. Establish the rollback gate and validate an isolated candidate or dry run
   without promotion when supported.
4. Refresh drift-sensitive preconditions immediately before the authorized
   write.
5. Apply the smallest candidate mutation and promote only through separately
   authorized actions.
6. Verify every relevant materialization, selection, runtime, delivery,
   behavior, and preservation layer with fresh direct evidence.
7. On a declared failure gate, stop further writes and run only the
   pre-authorized bounded rollback; then verify the prior state at its owning
   layers.

Command success, upload acceptance, a configuration write, or process start
proves only that stage. A failed or unavailable outcome-owning observation is
unverified, not complete.

## Safety And Handoff

- Resolve destructive targets directly; never use an unresolved variable,
  broad glob, guessed parent, or symlink traversal.
- Preserve unrelated state and the only working copy. Do not reset, stash,
  clean, install adjacent tools, change global configuration, or widen remote
  permissions to make a gate pass.
- Delete candidate or rollback material only under explicit cleanup authority
  after required postconditions pass and another required recovery route
  remains.

Report the target, actions actually authorized, mutation/promotion/rollback
outcome, material failed or unavailable postconditions, final observed state,
and retained recovery material. Include detailed successful layers only when
they support a completion or recovery decision.
