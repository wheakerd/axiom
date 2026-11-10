# Plans, Task Records, And Deferred Decisions

## Purpose

Keep a task's agreement, its progress, and what it postponed where the next session finds them, so compaction, a resume, or a new session continues from the record instead of from recollection. `memory-and-state.md` owns where each file lives; this reference owns what goes in it and when it is written, read, and removed.

## Apply When

- A task that changes files may outlive the current session or context: it has several steps, runs long, or is being resumed.
- The context is at risk: a long operation is about to start, or the host signals compaction.
- A session starts, resumes, or continues after compaction with a task in progress.
- The user postpones a decision, or a task ends with a known gap outside its scope.

## Do Not Apply When

- The request is a question, a read-only inspection, or a one-step edit; such a task gets no plan and no task record.
- The repository has no project memory, or it is not accepted in this clone; `completion-maintenance.md` says what to do in each case.

## Plan

A plan is the agreement about the work, tracked in Git so the team shares it.

- Hold the goal, the user's decisions with their dates, the steps, and the acceptance criteria. Keep requirements in the user's words, without anything the content exclusions in `memory-and-state.md` forbid.
- The latest explicit decision governs. Keep a superseded decision visible beside the one that replaced it until the task ends, so a later session does not revive it.
- Update the plan when the user changes scope, not at every step; progress belongs in the task record.
- A plan that another workflow already keeps, such as a host's plan file or an issue, is pointed at, not copied.

## Task Record

A task record is where the work stands, local to the clone. Keep it in two parts:

- **Inline**, what the next session must have in front of it: the acceptance criteria as they now stand, the exact repositories and commits the task depends on, what is done, what is open, the next step and who must grant it, and temporary notes that matter only to this task.
- **Spilled**, everything else: command output, diffs, and reports stay in their own files or remote objects, and the record names each by a path, number, or identifier that lets a reader verify it. A pointer never carries a summary that stands in for what it names.

Write it at each completed step and before a long operation starts, never only at the end, so a compaction never holds the only copy. Aim for under 2 KiB and keep it under 4 KiB. Exclude long logs, large code, and guesses, in addition to the content exclusions that `memory-and-state.md` sets for every class.

## Restore

After compaction, a resume, or a new session that continues the task:

1. Read root, the registry, the task's plan, and the task record before any mutation. A compaction summary is a claim, not the record, and where the record and the plan disagree, the plan's latest dated decision governs.
2. Treat the record's statements as claims about the past: re-observe the repositories, commits, and files it names before acting on them, and correct the record where the present differs.
3. Continue from the recorded next step. When no record exists for work that was in progress, reconstruct from current direct evidence, say that the record was missing, and perform no mutation that depends on a recalled decision.

## Deferred Decisions

One entry per postponed item: the date, the decision or issue, its owner, the trigger that reopens it, and its state, written as categories and pointers under the same content exclusions.

- Record an entry when the user says "not now", when a task ends with a known gap, or when the work found a problem outside the task's write scope.
- A deferred entry postpones work; it forbids nothing. Raise it in one line when its reopen trigger matches the current request, and let the user decide.
- Resolve an entry by recording what resolved it and when. Remove a resolved entry at a later completion maintenance only once a commit that records its resolution is in the repository's history; until then keep it, marked resolved.

## Completion

When the task ends, `completion-maintenance.md` runs these steps:

- Move what remains open from the task record into deferred decisions, then delete the task record.
- Delete the plan once its outcome is in the repository's history, unless the user wants it kept.
- Leave nothing that describes finished work as if it were pending.

## Prohibited Actions

- Do not create a plan or a task record for a read-only or one-step task.
- Do not treat a task record, a plan, or a deferred entry as a rule.
- Do not keep a finished task's record, or carry its temporary notes into another task.
- Do not write any of these outside the homes that `memory-and-state.md` resolves.
