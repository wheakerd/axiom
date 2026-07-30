# Preflight And Rollback

## Purpose

Prove that one authorized persistent target, an exact write set, and a usable
prior state are known before mutation.

## Resolve The Exact Target

Start from the user's explicit path, host, service, environment, database,
package, application, or deployment identifier. Canonicalize local paths and
use the platform's authoritative identity query for remote targets. Record
which environment is active.

Stop before writes when:

- Two plausible local roots, repositories, installations, hosts, accounts,
  regions, clusters, services, or environments remain.
- The requested scope crosses targets that were not authorized together.
- A nested Git root, linked worktree, symlink, mount, or remote alias makes
  ownership ambiguous.
- Credentials or elevation are required but their intended target or allowed
  action is unclear.

Do not infer production authority from access, saved credentials, a default
profile, or the ability to run a command.

## Observe Current State

Use read-only, current probes to record the facts needed for rollback and
verification. Depending on the target, inspect:

- Active version, entry point, selected configuration, service identity, and
  health state.
- Installation root, candidate slots, ownership, permissions, filesystem and
  free-space boundaries.
- Package or deployment manager state, dependency locks, migration state, and
  runtime prerequisites.
- Source repository root plus staged, unstaged, untracked, ignored, and
  operation state when source material is involved.
- Remote receiver, rollout, queue, application, and user-visible layers when
  the change traverses them.

Inventory sensitive assets through path, type, presence, permissions, owner,
tracking or ignore status, and intended role only. Before reading content,
freeze the exact asset path and the exact read or use action, then obtain
authorization for that pair. A directory name, broad scope, or request such as
"find whatever is needed" does not authorize selecting and reading sensitive
content. Ask for the precise asset and action; repeat the gate for every newly
discovered path or changed use.

Record facts as direct live observations, persistent rules, runtime state, or
historical reference. Historical state and copied instructions do not override
active instructions or prove current state.

## Freeze The Write Set

List every intended persistent effect before mutation, including:

- Files, directories, symlinks, package records, and active-version pointers.
- Configuration, secrets references, services, processes, jobs, and scheduled
  work.
- Database schemas or records, caches, object stores, queues, and remote
  deployment records.
- Restarts, reloads, retention deletions, migrations, promotions, and external
  calls that can change state.

Include expected generated files and manager-owned metadata. Distinguish
candidate writes from active-target writes. Resolve destructive roots directly
and bound them by type, retention rule, filesystem, and symlink policy.

If the live write set differs from the frozen set, stop and reassess. Do not
silently include a newly discovered dependency or adjacent component.

## Establish A Rollback Point

Choose a rollback mechanism native to the target when possible: an inactive
version slot, package version retained in a trusted cache, snapshot, backup,
database restore point, configuration copy with metadata, deployment revision,
or reversible pointer change.

Keep these evidence states distinct:

- `identified`: the prior state and proposed recovery mechanism are named.
- `present`: the rollback artifact or prior target currently exists.
- `readable`: the exact restore principal and mechanism can read it now.
- `restore-validated`: a current target-native check has actually validated
  restorability, not merely listed metadata.
- `rehearsed`: an isolated restoration using the same artifact, mechanism, and
  required ordering has completed and its result was checked.

Do not call a rollback path `verified`, `usable`, or `restore-ready` by
collapsing lower states. Before mutation require all of the following:

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
   rechecked immediately before the first write.

For a pointer-only rollback with no irreversible data effect, an isolated
equivalent switch plus a behavior check may serve as the rehearsal. Merely
resolving the prior target proves only presence or readability.

An isolated restore rehearsal is itself a persistent write. Freeze its exact
target and effects and obtain authorization before running it. A plan-only
workflow rehearsal cannot perform this restore rehearsal.

The following never prove a verified rollback by themselves: a successful
backup or copy command, a present snapshot, an existing rollback script,
documentation of restore commands, a checksum, a historical rehearsal, user
confidence, or a mutable artifact that would need to be downloaded later.

If the complete evidence set cannot be verified, stop this skill before
execution. Plan-only work may report the gap and stop gate, but user acceptance
of irreversible risk does not satisfy the contract. Continue only by explicitly
re-routing to another applicable workflow that does not promise verified
rollback and independently satisfies its authority and safety gates.

## Candidate And Dry Run

Prefer an isolated candidate location or the platform's dry-run, plan, check,
or transaction preview. Verify authenticity or integrity with authoritative
metadata when available, then validate format, dependencies, migrations,
configuration, and affected tests before promotion.

Keep candidate evidence separate from active-state evidence. A successful
build, package download, upload, plan, or dry run proves only that stage.

For plan-only or rehearsal requests, report assumptions, proposed write set,
rollback strategy, validation layers, and stop gates. Do not create candidate,
backup, capsule, cache, remote state, or sensitive-content access. Pure status
queries and conceptual explanations do not route through this skill.
