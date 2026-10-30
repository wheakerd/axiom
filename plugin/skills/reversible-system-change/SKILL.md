---
name: reversible-system-change
description: Plan, rehearse, or execute a persistent system change with verified rollback and postconditions for an install, upgrade, deployment, migration, destructive retention action, version promotion, or credential lifecycle step with rollback, data, service, or activation risk. Plans and rehearsals stay read-only; recovery preparation needs bounded write authority. Not for ordinary edits, Git, or status queries.
---

# Reversible System Change

Make one authorized persistent change without losing the ability to identify, restore, and verify the prior state.

## Invariants

These invariants bind in every phase, including the references that phase loads. Everything else in this skill is a default you may adapt, saying so when you depart.

1. **Separate authority per action.** Recovery-material preparation, isolated restore rehearsal, candidate preparation, active promotion, service restart or reload, data migration, destructive retention, sensitive asset access, rollback, and cleanup are separate actions. Permission for one never implies another, and a newly discovered target, dependency, service, data store, endpoint, or destructive effect requires renewed authority.
2. **Verified rollback before mutation.** Before candidate or active-state mutation, require a rollback point that represents the observed prior state and covers every non-forward-compatible effect. It must be readable by the restore principal with its prerequisites present and must have passed a target-native restore validation or an authorized isolated rehearsal, rechecked immediately before mutation.
3. **Evidence states stay distinct.** `identified`, `present`, `readable`, `restore-validated`, and `rehearsed` are distinct states. A backup job, artifact, script, manifest, checksum, historical rehearsal, or user acceptance of risk is not verified rollback, and authority alone cannot waive the rollback gate.
4. **Only an informed waiver lifts rollback.** An informed waiver under `references/informed-waiver.md` lifts this rollback requirement only for the effects named to the user; every other effect and rule still binds.
5. **Preserve what exists.** Resolve destructive targets directly, never through an unresolved variable, broad glob, guessed parent, or symlink traversal. Preserve unrelated state and the only working copy; never reset, stash, clean, install tools, change global configuration, or widen remote permissions to make a gate pass.
6. **Fail closed on resume.** After resume or compaction, mutate nothing until current direct evidence reconstructs the phase, the authority, the write set, prior attempts, and the recovery evidence; never adopt post-change state as the prior rollback baseline.

## Select One Phase

- Explicit machine-credential lifecycle: read `../using-axiom/references/credential-lifecycle.md` first. A metadata-only inventory stops there. For persistent activation, rollout, retirement, or cleanup, continue into the applicable phase below; provider-side creation, revocation, or secret disclosure also loads `confirm-external-action` under an independent envelope.
- Plan or non-mutating workflow rehearsal: read `references/preflight-and-rollback.md`. Keep the phase read-only: no candidate, backup, capsule, cache, remote record, or sensitive content access.
- Prepare missing recovery material: read `references/preflight-and-rollback.md` and `references/recovery-material-preparation.md`. This bounded authorized phase may create an isolated backup before restore validation, but cannot prepare a candidate, overwrite prior material, or alter active state.
- Authorized isolated restore rehearsal: read `references/preflight-and-rollback.md` only. Freeze an isolated non-active target and its complete write set, obtain exact rehearsal-write authority, and verify only the restore outcome. This phase may establish `rehearsed` evidence; it never authorizes candidate preparation, active promotion, the complete change, or cleanup.
- Execute a complete authorized change: read `references/preflight-and-rollback.md` first. If recovery material must be created, enter its preparation phase within the current authority. Read `references/execution-and-verification.md` only after the exact target, write set, promotion authority, rollback coverage, and current restore validation pass, or after an informed waiver replaces the last two.
- Conceptual explanations and pure status, version, or availability queries select nothing here.

## Authority Boundary

Resolve the requested outcome, exact target, authorized actions, and expected postcondition before mutation. Ask one question only when target, environment, destructive scope, credentials, sensitive asset use, promotion, or rollback authority would change execution; settle a delegated target or environment choice under the startup gate's rule.

Inventory sensitive assets by metadata only. Read or use content only after the exact path and exact action are frozen and authorized. Never print, copy broadly, hash, encode, or persist secret contents merely to inventory them.

## Rollback Gate

Recheck the rollback evidence immediately before mutation. If current restore validation or complete coverage cannot run, stop execution; a plan may report the gap.

## Change Contract

1. Observe current target and runtime state with scoped read-only probes.
2. Freeze persistent effects, destructive roots, and the postcondition layers that own the requested outcome.
3. Prepare missing recovery material through its bounded phase, establish the full rollback gate, then validate a candidate or dry run without promotion.
4. Refresh drift-sensitive preconditions immediately before the authorized write.
5. Apply the smallest candidate mutation and promote only through separately authorized actions.
6. Verify every relevant materialization, selection, runtime, delivery, behavior, and preservation layer with fresh direct evidence.
7. On a declared failure gate, stop further writes and run only the pre-authorized bounded rollback; then verify the prior state at its owning layers.

Command success, upload acceptance, a configuration write, or a process start proves only that stage; a failed or unavailable outcome-owning observation is unverified, not complete.

## Resume And Compaction Handoff

After resume or compaction, reobserve the target and drift-sensitive state. Then fail closed unless host-native task context and current direct evidence from the owning system reconstruct the active phase, the exact current user authority, the frozen action envelope and complete write set, prior mutations and attempt identifiers, and the idempotency status. The same evidence must show phase-appropriate recovery evidence. Preparation resumes through its isolation and disposal gate; candidate or active-state mutation still requires current full rollback validation. If any required field is missing, stale, or inconsistent, perform zero new mutations. Never adopt post-change state as the prior rollback baseline. An unknown external outcome enters Verify only and must not be resent. Reestablish changed or missing evidence and obtain renewed authority; authority alone cannot waive the rollback gate, and only an informed waiver that current host-native context still shows lifts its rollback requirement. Do not add a daemon, cache, telemetry, or persistent handoff tool to reconstruct the handoff.

## Safety And Handoff

- A host-mode denial is a stop, never a retry by another tool, flag or path; present the exact action for the user's grant first. Read `../using-axiom/references/host-permission.md`.
- Dispose of failed preparation output only through its frozen disposal gate. Delete other candidate or rollback material only under explicit cleanup authority after required postconditions pass and another required recovery route remains.

Report the target, the actions actually authorized, the mutation, promotion, and rollback outcome, material failed or unavailable postconditions, the final observed state, and retained recovery material; detail successful layers only when they support a completion or recovery decision.
