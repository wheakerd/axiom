# Runtime And Effective Updates

## Purpose

Handle durable instruction updates, whether the user triggers one or a completed task does, and say where task state is kept.

## Apply when

- An AGENTS Architect workflow is already active for a target repository's AGENTS instruction architecture.
- A durable update trigger follows ordinary work in the current task, even when
  AGENTS Architect was not active for the earlier work.
- A task that changed files completes in a clone with accepted project memory; `completion-maintenance.md` owns that step.
- A task risks context compaction; `task-records.md` owns the record.
- During that active task, the user says exactly `effective-instructions`.
- During that active task, the user says exactly `effective-instructions:preview`.
- During that active task, the user says exactly `effective-instructions:refactor`.
- During that active task, the user says exactly `effective-instructions:force <instruction>`.
- In any task or fresh session, the user says exactly
  `effective-instructions:reconcile`.
- In any task or fresh session, the user says exactly
  `effective-instructions:reconcile-preview`.
- During that active task, the user makes a non-English request that unambiguously maps to one canonical effective-instructions mode.
- In any task or fresh session, the user explicitly makes an unambiguous
  non-English request to reconcile existing AGENTS guidance with current
  implementation.

## Do not apply when

- No mode was explicitly requested, and the task was read-only or ended with nothing to record. An explicitly requested mode still runs after a read-only investigation.
- Reconciliation was not explicitly requested. Implementation drift or an
  execution or context discontinuity is only possible evidence after
  activation, never an activation signal.
- A discovery is useful only for the current task.
- The user wording could map to multiple effective-instructions modes.
- The task is Axiom repository maintenance; follow the active repository's higher-priority maintenance instructions instead of this target-repository workflow unless the user explicitly invokes the agents-architect skill for a target AGENTS architecture task.
- The task would update protected plugin or skill metadata as AGENTS routing content.

## Task records

A task that changes files and may outlive its session keeps a plan and a task record; a read-only or one-step task keeps neither. `memory-and-state.md` owns where they live and `task-records.md` owns their contents, when they are written, how a later session restores from them, and their removal at completion. A session opens a task record only for the task it continues.

## Effective instruction modes

Treat English trigger definitions as the canonical source of truth. User requests may be written in any language. Normalize unambiguous non-English user wording to the matching English trigger before acting. After normalization, refer to the selected mode by its canonical English token. Ask a concise clarification question only when wording could map to multiple modes. Do not maintain localized alias tables or alternate canonical tokens.

Scope these modes to the active target repository's AGENTS instruction system. Do not update protected plugin or skill metadata unless the user explicitly asks for skill or plugin maintenance.

Do not use these modes to persist Axiom packaged skill rules, Axiom trigger definitions, load policies, internal routes, validation protocols, or reporting formats into a target repository.

For `effective-instructions` and `effective-instructions:preview`, load
`maintenance/context-evidence.md` and follow its review-window, decision-
disposition, coverage, and retrieval-friction rules before extracting
candidates. Keep their full definitions in that reference rather than
redefining them here.

`effective-instructions`:

- Extract durable candidates from the established review window.
- Apply the admission gate.
- Update the smallest canonical leaf.
- Update indexes only when routing changes.
- Update root only for true global hard constraints.
- Remove stale duplicates.
- Validate and report changes.

`effective-instructions:preview`:

- Propose updates only.
- Do not edit files.
- Include retrieval-friction candidates and explain which source reads remain
  necessary.
- Explain rejected temporary candidates.

`effective-instructions:refactor`:

- Re-audit relevant branches.
- Move, split, or merge only when routing improves.
- Do not refactor unrelated branches.

`effective-instructions:force <instruction>`:

- Treat supplied content as high-priority.
- Still check scope, conflicts, safety, and canonical placement.
- If temporary, put it in a runtime note, not durable rules.

`effective-instructions:reconcile` and
`effective-instructions:reconcile-preview`:

- Load `maintenance/implementation-reconciliation.md` as the sole detailed
  contract for these modes.
- Permit a fresh-session start; no earlier task context or review-window
  baseline is required unless the user includes it in scope.
- Do not infer either mode from repository or execution evidence.

## Activation semantics

Editing an `AGENTS.md` file does not retroactively change the instruction chain
already loaded for the current run. Treat the edit as durable input for later
in-scope runs. Report fresh host loading as verified only when it was directly
checked in a new run or session; otherwise say it was not checked or could
not be checked.
A task record carries current-task state; a durable AGENTS update does not replace that role.

## Report required

For every triggered update, report:

- Selected canonical effective-instructions mode.
- Added rules.
- Modified rules.
- Removed or merged rules.
- Affected routes.
- Byte changes.
- Git tracking or ignore state.
- Plans, task records, and deferred entries created, updated, or removed, with their paths.
- Validation results.
- Current-run versus later-run activation status, including whether fresh host
  loading was verified, not checked, or could not be checked.

For `effective-instructions` and `effective-instructions:preview`, also report which candidates were confirmed, superseded, left unresolved, or rejected, with reasons, what you decided about each retrieval-friction signal, and the source checks that remain. Report the review-window start, the reviewed-through point, the baseline reason, how far back you read, which raw outputs you did not open, and any required history that stayed unread. For either
reconciliation mode, use the baseline, ledger, collaboration, and stop fields
defined by `maintenance/implementation-reconciliation.md` instead.

## Prohibited actions

- Do not persist secrets.
- Do not write a single-task preference as a durable rule or a working agreement; it stays in the task record until the user repeats or states it.
- Do not keep conflicting durable versions.
- Do not use file counts, tool counts, duration, or context compaction alone as
  evidence that AGENTS guidance is incomplete.
