# Completion Maintenance

## Purpose

Keep project memory current when a task ends: record what the task settled, remove what it finished or made obsolete, and offer the user the durable rules and working agreements the task revealed. This runs without being asked, inside the write boundary below.

## Apply When

- A task that changed files in the repository completes, the clone's project memory is accepted as the Acceptance section of `memory-and-state.md` defines, and the task leaves something to record, propose, or remove. A completed task that leaves nothing selects no route and produces no notice.
- The user asks to update project memory after a task.

## Do Not Apply When

- The task was read-only, or it changed nothing in the repository.
- Project memory exists but is not accepted in this clone, as in a freshly cloned or third-party tree. A route or files that merely exist authorize nothing: ask once before the first write, as the Acceptance section of `memory-and-state.md` describes.
- The repository has no project memory. Write nothing. When the task produced something worth keeping, a durable candidate or a postponed decision, say in one line that the repository has no project memory and that it can be set up; initialization needs the user's request.
- A `CLAUDE.md` shadows `AGENTS.md` in Claude Code; the parent skill's stop applies.

## Write Boundary

- Writes touch only `AGENTS.md` and routed `.agents/**` files. This skill never edits, moves, or deletes code, tests, documentation, configuration, or Git metadata as maintenance; a legacy capsule in Git metadata is read and reported, not removed.
- Automatic classes are written directly and reported: deferred decisions, plans, and task records.
- A durable rule or a working agreement is proposed and written only after the user confirms it. Removing or changing an existing durable rule is the same kind of change and needs the same confirmation.
- A permission-bypass mode changes none of this; it grants execution, not a decision about what the project remembers.

## Steps

1. **Settle the automatic classes.** Follow the Completion section of `task-records.md`: carry open items into deferred decisions, delete the finished task record, and delete the finished plan. Resolve the deferred entries this task settled and remove entries resolved and reported earlier.
2. **Find what the task made obsolete.** Inside AGENTS-related files, look for a rule the result contradicts, a route to a path the task removed, a registry line without a target, and a dated note the task outdated. Each is a durable change: propose it. Outside those files, obsolete code, tests, documents, and evidence are the task's own work: remove them only inside the write scope the user already gave the task, report the rest, and record what stays as a deferred decision.
3. **Collect candidates.** From the task just completed, list what may be a durable rule or a working agreement, and apply the admission gate in `maintenance/maintenance-application.md`, including its user signals. Read `maintenance/context-evidence.md` first when the history is long or compacted, or when the user asks for a full review.
4. **Propose.** Present each candidate in one line: the rule or agreement, its class and home, the evidence, and what it replaces. Each can be confirmed or declined on its own. Write the confirmed ones through the maintenance owner; do not propose a declined candidate again without new evidence.
5. **Report.** State what was written automatically with its paths, what awaits confirmation, and what obsolete material lies outside the boundary.

## Proportion

- A task with nothing to record does not select this step: no notice, no statement that nothing changed, and no question about updating memory.
- One postponed decision or one closed plan needs one line, not a section.
- Never invent a candidate to have something to propose. A preference inferred from one occurrence stays in the task record until the user repeats or states it.

## Prohibited Actions

- Do not write a durable rule or a working agreement without the user's confirmation.
- Do not delete or rewrite anything outside `AGENTS.md` and routed `.agents/**` as maintenance.
- Do not initialize project memory in a repository that has none.
- Do not store project knowledge in a host's private memory.
- Do not copy Axiom's own protocol, triggers, or report formats into the target repository's memory.
