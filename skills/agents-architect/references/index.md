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

- `project-initialization.md`: initialize root `AGENTS.md` and a `.agents/`
  routing tree when no existing `AGENTS.md` system or active shadowing source
  controls the target scope.

### Design

- `routing-architecture.md`: design route topology, responsibility axes,
  ownership, dependencies, cross-cutting safety or risk rules, and route
  sinking.
- `instruction-document-contracts.md`: author or validate root, group index,
  domain entry, rule leaf, risk-rule leaf, parent-owned reference, metadata,
  language, and portable size contracts.

### Migration

- `migration-policy.md`: classify existing content, apply admission gates, move or preserve docs, and choose Git handling.

### Maintenance

- `maintenance/index.md`: inspect current task context or a user-specified task
  ID for durable updates, then maintain existing `AGENTS.md`, `.agents` routing
  docs, or repo-local skills after the required authorization gate.

### Runtime

- `runtime-and-updates.md`: create session capsules and handle durable AGENTS instruction updates during an active AGENTS Architect workflow.

### Verification

- `validation-reporting.md`: run static checks, routing scenarios, loading checks, split/size checks, and final reporting.

### Selection precedence

- Existing oversized or mixed-responsibility instruction content routes first
  to `migration-policy.md`, with `instruction-document-contracts.md` as its
  required document and size contract. Load `routing-architecture.md` as well
  only when canonical ownership or topology must change.
- A pure schema, metadata, reference-ownership, or size audit routes directly
  to `instruction-document-contracts.md`.
- A topology-only design routes to `routing-architecture.md`; do not load
  migration merely because a size boundary exists.

## Stop reading

Follow one bounded route chain from the parent. A grouped route may load this
index, one child index, and either one terminal owner or the finite phase chain
declared by that child index: zero to two prerequisites and exactly one terminal
owner. A selected owner may then load only the shared contract or validation
reference it explicitly requires. Do not scan undeclared siblings or adjacent
references.
