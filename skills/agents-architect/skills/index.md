# AGENTS Architect Internal Skill Index

## Purpose

Select the smallest AGENTS Architect internal skill needed for the current repository instruction task.

## Enter when

- `../SKILL.md` has triggered.
- A low-cost metadata inventory has been collected, or the environment could not support one and assumptions are recorded.
- The task needs detailed AGENTS architecture guidance.

## Do not enter when

- The user only asked a simple factual question about `AGENTS.md`.
- The task is already fully answerable from `SKILL.md`.

## Next hops

### Audit

- `inventory-audit/SKILL.md`: collect facts, honor Codex behavior boundaries, and audit progressively.

### Initialization

- `project-initialization/SKILL.md`: initialize root `AGENTS.md` and a `.agents/` routing tree for a repository with no existing AGENTS definition.

### Design

- `routing-architecture/SKILL.md`: design root control plane, `.agents` tree, routing graph, metadata, leaf schema, splitting, and portable size model.

### Migration

- `migration-policy/SKILL.md`: classify existing content, apply admission gates, move or preserve docs, and choose Git handling.

### Maintenance

- `agents-maintenance/SKILL.md`: inspect current task context or a user-specified task ID for durable AGENTS updates, then maintain existing AGENTS docs, `.agents` routing docs, or repo-local skills after the required authorization gate.

### Runtime

- `runtime-and-updates/SKILL.md`: create session capsules and handle durable AGENTS instruction updates during an active AGENTS Architect workflow.

### Verification

- `validation-reporting/SKILL.md`: run static checks, routing scenarios, loading checks, split/size checks, and final reporting.

## Stop reading

Load only the matching internal skill. Load a second internal skill only for cross-phase work. Do not scan every internal skill as a default step.
