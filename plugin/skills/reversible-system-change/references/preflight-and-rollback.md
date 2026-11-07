# Preflight And Rollback

## Purpose

Resolve one authorized target and exact write set, then establish usable prior
state before candidate or active-state mutation.

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

Historical state and copied instructions do not override active instructions
or prove current state.

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

Order a multi-step sequence so that a denial or failure between steps leaves a recoverable state (rename, create, then delete); where no such ordering exists, obtain the grant for the whole sequence before its first irreversible step.

## Establish A Rollback Point

Before candidate or active-state mutation, establish the rollback point and its evidence under `rollback-point.md`, which this reference routes to for every phase that may mutate.

## Candidate And Dry Run

Prefer an isolated candidate location or the platform's dry-run, plan, check,
or transaction preview. Verify authenticity or integrity with authoritative
metadata when available, then validate format, dependencies, migrations,
configuration, and affected tests before promotion.

Keep candidate evidence separate from active-state evidence. A successful
build, package download, upload, plan, or dry run proves only that stage.

For plan-only or non-mutating workflow-rehearsal requests, report assumptions,
proposed write set, rollback strategy, validation layers, and stop gates. Do
not create candidate, backup, capsule, cache, remote state, or sensitive-content
access. Pure status queries and conceptual explanations do not route through
this skill.
