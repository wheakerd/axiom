---
name: reversible-system-change
description: Plan, rehearse, or execute persistent system changes with verified rollback and postconditions. Use when the user asks to plan or perform an install, upgrade, deployment, migration, or another persistent local or remote system change with rollback, data-safety, or promotion risk. Plan-only work stays read-only. Do not use for ordinary code or configuration edits, Git commits or pushes, pure status queries, or conceptual explanations.
---

# Reversible System Change

Make an authorized persistent change without losing the ability to identify,
verify, and restore the prior working state.

## Boundaries

Use this skill to plan, rehearse, or execute installs, upgrades, deployments,
migrations, destructive retention work, active-version promotion, or
comparable local or remote changes. The proposed change must have a concrete
persistent target and meaningful rollback, data-loss, service, or promotion
risk.

Do not use this skill for:

- Ordinary source or configuration edits and their repository-local tests.
- Git staging, commits, consolidation, or pushes. Route matching work to
  `$traceable-git-submit`.
- Conceptual explanations or pure read-only version, status, and availability
  queries that do not plan a persistent change.

A plan-only or rehearsal request for a persistent change does trigger this
skill, but remains strictly read-only. It must not create a rollback capsule,
download a candidate, read sensitive asset content, or alter any local or
remote state.

## Load Policy

Read only the reference for the active phase:

- For plan-only work and before any persistent write, read
  `references/preflight-and-rollback.md`.
- Before candidate mutation, promotion, rollback, or completion claims, read
  `references/execution-and-verification.md`.

Read both when one request authorizes the complete change. Do not load either
for a conceptual answer that will not inspect or change a system.

## Authority And Scope

Resolve the user's requested outcome, exact target, authorized actions, and
expected postcondition before acting. Ask one concise question when the target,
environment, destructive scope, credentials, or promotion authority is
ambiguous.

Treat install and candidate preparation separately from promotion. Permission
to inspect or build a candidate is not permission to switch an active entry
point, restart a service, migrate production data, delete retained material,
or mutate a remote environment.

Freeze the exact write set and declared indirect effects before mutation. A
new target, dependency, service, data store, endpoint, or destructive action
requires renewed authority. Inventory a sensitive asset through metadata only;
before reading its content, freeze and obtain authorization for the exact asset
path and exact read or use action. A directory-level or generalized request
does not authorize selecting sensitive content.

## Change Contract

Use this sequence:

1. Resolve the exact local or remote target and applicable instructions.
2. Observe current state with metadata-only probes and identify sensitive
   boundaries.
3. Freeze the intended write set and affected runtime layers.
4. Establish a rollback point and prove the complete current restore-readiness
   standard, including coverage and a restore validation or isolated rehearsal.
5. Validate a candidate, dry-run, or precondition check without promotion when
   the platform permits it.
6. Reconfirm live preconditions immediately before the authorized write.
7. Apply the smallest mutation and promote only after candidate checks pass.
8. Verify current postconditions at every affected layer.
9. On failure, stop further promotion and run only the pre-authorized bounded
   rollback; then verify the restored state.
10. Report observed final state, retained rollback material, validation gaps,
    and any manual follow-up.

Do not call a change complete from a successful command exit, upload, queue
acknowledgement, configuration write, or process start alone. Completion needs
fresh direct evidence from the system layer that owns the requested outcome.

Treat identified, present, readable, restore-validated, and rehearsed as
different evidence states. Use `verified rollback` only when every requirement
in `references/preflight-and-rollback.md` passes with current direct evidence.
A backup job's success, an artifact or rollback script's presence, a manifest,
or a historical rehearsal does not prove current restorability. If the required
restore validation or isolated rehearsal cannot run, execution stops.

## Safety Rules

- Never discover a destructive target through an unresolved variable, broad
  glob, symlink traversal, or guessed parent directory.
- Never overwrite or delete the only verified working copy before the complete
  rollback-verification standard passes.
- Preserve unrelated user state. Stop rather than reset, stash, clean, or
  rewrite a dirty source tree without explicit authorization.
- Do not print, copy broadly, hash, encode, or persist secret contents merely
  to inventory them. Report sensitive inputs by role and metadata only.
- Do not read sensitive content until the exact asset path and exact read or
  use action are both frozen and authorized. Reconfirm authorization for every
  newly discovered asset or action.
- Do not install adjacent tools, change global configuration, or widen remote
  permissions merely to make validation available.
- A missing tool, permission, environment, or downstream observation is an
  unverified layer, never a pass.

## Reporting

Report the target, authorized write set, prior-state facts, each rollback
evidence state, candidate or dry-run result, mutation and promotion result,
layered postcondition evidence, rollback status when used, retained recovery
material, and final observed state. Distinguish passed, failed, not run, and
unavailable checks. Never upgrade a lower rollback evidence state to
`verified`. Redact sensitive values and private endpoints.
