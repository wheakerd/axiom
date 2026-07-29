# AGENTS Maintenance Reference Index

## Purpose

Route maintenance of existing AGENTS instruction systems from task evidence without letting that evidence become ambient authority.

AGENTS maintenance has stable subresponsibilities: evidence inspection, authorization safety, repo-local skills, and update application. Load only the matching child reference.

## Enter when

- The AGENTS Architect parent skill has selected maintenance from `../index.md`.
- A repository already has `AGENTS.md`, `.agents/` routing docs, or
  `.agents/skills/**`.
- The user asks whether current task context implies durable AGENTS updates.
- The user supplies a Codex task, thread, chat, session, or conversation ID as evidence for AGENTS maintenance.
- The work may update repo-local skills under `.agents/skills/<skill-name>/`.
- The task needs detailed guidance for evidence, authorization, repo-local skills, or durable update application.

## Do not enter when

- No `AGENTS.md` or durable `.agents/` system exists; use
  `../project-initialization.md`. If only a host-discovered non-`AGENTS.md`
  instruction source exists, inventory it and safe-stop instead of treating it
  as an Axiom maintenance target.
- The user wants only a one-off answer, task summary, or temporary note.
- The task is plugin or packaged skill maintenance for the current plugin repository.
- The task is fully answerable from the parent AGENTS Maintenance route selection.

## Next hops

Before selecting phases, identify the target repository, existing `AGENTS.md`
and `.agents/` surfaces, current-session active host-discovered sources, task-ID
scope, likely provenance, intended update surface, and existing authorization.

### Evidence

- `context-evidence.md`: inspect current context or a supplied task ID, record evidence scope, handle compaction, and use subagents for bounded evidence extraction.

### Safety

- `authorization-and-safety.md`: decide whether a non-Axiom or
  unclear-provenance `AGENTS.md` system can be edited, preserve active loaded
  guidance at its actual authority, isolate inactive evidence, and choose when
  to ask the user.

### Repo-Local Skills

- `repo-local-skills.md`: create, update, split, or validate repository-local Codex skills under `.agents/skills/**`.

### Application

- `maintenance-application.md`: apply the durable update gate, choose canonical homes, reorganize approved AGENTS structures, validate, and report.

### Finite phase chain

A maintenance route loads zero to two named prerequisites, then exactly one
terminal owner:

1. Load `context-evidence.md` when a task ID, compacted history, or unresolved
   task evidence must be inspected.
2. Load `authorization-and-safety.md` when provenance or edit authority is
   unclear, or when a host-discovered source may shadow the requested result.
3. Select exactly one terminal owner: `maintenance-application.md` for an
   `AGENTS.md` or routed-rule outcome, including a read-only preview; or
   `repo-local-skills.md` for a repo-local skill outcome.

Skip unneeded prerequisites. Do not load both terminal owners, reorder phases,
or scan undeclared siblings. A prerequisite may narrow the terminal action but
cannot authorize it.

## Stop reading

Follow only the declared finite phase chain and stop after its terminal owner.
Do not load a child for background or continue into the other terminal owner.
