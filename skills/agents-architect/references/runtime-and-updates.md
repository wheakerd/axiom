# Runtime And Effective Updates

## Purpose

Handle long-task state and user-triggered durable instruction updates.

## Apply when

- An AGENTS Architect workflow is already active for a target repository's AGENTS instruction architecture.
- A durable update trigger follows ordinary work in the current task, even when
  AGENTS Architect was not active for the earlier work.
- The active AGENTS task risks context compaction.
- During that active task, the user says exactly `effective-instructions`.
- During that active task, the user says exactly `effective-instructions:preview`.
- During that active task, the user says exactly `effective-instructions:refactor`.
- During that active task, the user says exactly `effective-instructions:force <instruction>`.
- During that active task, the user makes a non-English request that unambiguously maps to one canonical effective-instructions mode.

## Do not apply when

- No trigger phrase is present and the task is short.
- A discovery is useful only for the current task.
- The user wording could map to multiple effective-instructions modes.
- The task is Axiom repository maintenance; follow the active repository's higher-priority maintenance instructions instead of this target-repository workflow unless the user explicitly invokes `$agents-architect` for a target AGENTS architecture task.
- The task would update protected plugin or skill metadata as AGENTS routing content.

## Runtime capsules

Use `.agents/.runtime/session-<unique-id>.md` only for a mutating, long-running
AGENTS task that risks losing critical state. Do not create a capsule during a
strictly read-only task.

Target under 2 KiB; hard target 4 KiB.

Include only:

- Current user goal.
- Confirmed scope.
- Active instruction files.
- Critical constraints.
- Modified files.
- Completed validation.
- Failed validation and brief reason.
- Open decisions.
- Next action.

Do not include full chats, long logs, large code, whole document summaries, unverified guesses, secrets, or sensitive data.

Delete or mark obsolete when complete. Future sessions must not auto-load old capsules.

## Effective instruction modes

Treat English trigger definitions as the canonical source of truth. User requests may be written in any language. Normalize unambiguous non-English user wording to the matching English trigger before acting. After normalization, refer to the selected mode by its canonical English token. Ask a concise clarification question only when wording could map to multiple modes. Do not maintain localized alias tables or alternate canonical tokens.

Scope these modes to the active target repository's AGENTS instruction system. Do not update protected Codex plugin or skill metadata unless the user explicitly asks for skill or plugin maintenance.

Do not use these modes to persist Axiom packaged skill rules, Axiom trigger definitions, load policies, internal routes, validation protocols, or reporting formats into a target repository.

For `effective-instructions` and `effective-instructions:preview`, review what
the current task had to read in each phase for retrieval-friction signals. Load
`maintenance/context-evidence.md` and establish the review window before
extracting candidates. The first whole-task review begins at the task's oldest
available turn; only a prior completed review with an explicit start,
reviewed-through point, and candidate dispositions creates an incremental
baseline. An earlier AGENTS read, narrow edit, ordinary task completion, or
Skill activation is not such a baseline. Classify each signal as
`instruction-gap`, `routing-gap`, `validation-gap`,
`expected-live-verification`, or `one-off-code-defect`.

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

## Report required

For every triggered update, report:

- Added rules.
- Modified rules.
- Removed or merged rules.
- Rejected candidates and reasons.
- Retrieval-friction dispositions and source checks that remain necessary.
- Review-window start, reviewed-through point, baseline reason, and any unread
  required history.
- Affected routes.
- Byte changes.
- Git tracking or ignore state.
- Validation results.

## Prohibited actions

- Do not persist secrets.
- Do not persist single-task preferences by default.
- Do not keep conflicting durable versions.
- Do not use file counts, tool counts, duration, or context compaction alone as
  evidence that AGENTS guidance is incomplete.
