# AGENTS Architect Internal Reference Index

## Purpose

Select the smallest AGENTS Architect internal reference needed for the current repository instruction task.

## Enter when

- The AGENTS Architect parent skill has triggered.
- A low-cost metadata inventory has been collected, or the environment could not support one and assumptions are recorded.
- The task needs detailed AGENTS architecture guidance.

## Do not enter when

- The user only asked a simple factual question about `AGENTS.md`.
- The task is already fully answerable from the parent skill.

## Next hops

### Audit

- `inventory-audit.md`: collect facts, honor Codex behavior boundaries, and audit progressively.

### Initialization

- `project-initialization.md`: initialize root `AGENTS.md` and a `.agents/` routing tree for a repository with no existing AGENTS definition.

### Design

- `routing-architecture.md`: design root control plane, `.agents` tree, routing graph, metadata, leaf schema, splitting, and portable size model.

### Migration

- `migration-policy.md`: classify existing content, apply admission gates, move or preserve docs, and choose Git handling.

### Maintenance

- `maintenance/index.md`: inspect current task context or a user-specified task ID for durable AGENTS updates, then maintain existing AGENTS docs, `.agents` routing docs, or repo-local skills after the required authorization gate.

### Runtime

- `runtime-and-updates.md`: create session capsules and handle durable AGENTS instruction updates during an active AGENTS Architect workflow.

### Verification

- `validation-reporting.md`: run static checks, routing scenarios, loading checks, split/size checks, and final reporting.

## Stop reading

Load only the matching internal reference. Load a second internal reference only for cross-phase work. Do not scan every internal reference as a default step.
