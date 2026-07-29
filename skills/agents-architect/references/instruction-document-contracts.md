# Instruction Document Contracts

## Purpose

Define canonical content, ownership, metadata, and size rules for root
`AGENTS.md` and its routed documents.

## Apply When

- Writing or refactoring root `AGENTS.md`.
- Writing a group index, domain entry, rule leaf, risk-rule leaf, parent-owned
  reference, or nested `AGENTS.md`.
- Defining request handling, command resolution, metadata, or size budgets.
- Validating whether route sinking is complete.

## Do Not Apply When

- Only choosing route topology or ownership; use `routing-architecture.md`.
- Only collecting repository metadata.

## Root AGENTS Contract

Root `AGENTS.md` is the project control plane and the only native auto-load
entry filename Axiom writes. A justified nested native entry must also be named
`AGENTS.md`. Include only evidence-backed repository rules such as:

- Short project goal.
- True repository-wide constraints.
- Instruction priority and conflict resolution.
- On-demand routing entry and project route table when routed guidance exists.
- Minimum verification.

Do not include full architecture, complete project trees, leaf catalogs, all
test commands, README copies, session state, domain details, Axiom skill load
policies, Axiom triggers, packaged skill bodies, plugin-internal routes, or
generic Axiom request/language/runtime/size protocols.

## Evidence-Driven Optional Rules

Add request handling, canonical command/language rules, runtime capsules,
durable-update modes, or repository-local size budgets only when the user or
current project evidence establishes them as repository policy. Axiom may apply
its own authoring and active-set limits while producing files without copying
those limits into the target repository.

## Optional Request Handling Contract

When the target repository has an explicit request-handling policy, preserve
that policy at the smallest scope where it applies. Do not seed a repository
with Axiom's own interaction protocol merely because AGENTS Architect is active.

## Optional Command Resolution Contract

- Keep durable command names, canonical tokens, route IDs, paths, and
  frontmatter identifiers in English.
- Treat the English definition as canonical.
- Normalize non-English wording only when it maps unambiguously to one
  canonical command.
- Ask for clarification when translated or paraphrased wording maps to multiple
  commands.
- Do not maintain localized alias tables or multilingual trigger catalogs.
- Keep Axiom plugin triggers in the installed plugin, not target `AGENTS.md`.
- Emit these rules only when the target repository actually defines durable
  commands or identifiers that need them.

## Group Index Contract

A group index may contain only:

- Purpose.
- Enter conditions.
- Exclusion conditions.
- Next hops.
- Stop-reading conditions.

A group index contains no coding standards, architecture summaries, copied rule
bodies, validation matrices, or descendant catalogs. Create one only for an
evidence-backed stable axis with multiple reachable owners.

## Routed Rule Metadata

Use compact frontmatter and remove empty fields:

```yaml
---
id: domain.example.implementation
kind: group-index | domain-entry | rule-leaf | risk-rule-leaf | maintenance
scope:
  paths:
    - "src/example/**"
  tasks:
    - feature
load_when:
  - "Modify production code under src/example"
do_not_load_when:
  - "Only editing unrelated docs"
requires:
  - concern.security
source_of_truth:
  - "docs/example-architecture.md"
---
```

Keep IDs globally unique and keep `requires` acyclic. Omit fields that do not
improve routing.

`last_verified` is optional. Add it only as the receipt of a completed semantic
audit that names what was checked. A date, modification time, or copied value
does not prove that instructions remain correct.

## Rule Body Contract

Use only the sections needed by the responsibility:

- Purpose.
- Apply when.
- Do not apply when.
- Required actions.
- Prohibited actions.
- Validation.
- References.

Write short imperative rules with concrete scope and verifiable actions. Link
to authoritative project docs rather than copying them. Do not invent commands,
owners, paths, frameworks, or validation steps.

A direct domain entry is a terminal rule leaf reached directly by one unique,
evidence-backed domain signal. A risk-rule leaf contains only cross-cutting
safety or risk constraints and loads only from an explicit matching signal.

## Parent-Owned Reference Contract

- Exactly one domain entry, rule leaf, or risk-rule leaf owns each reference
  and explicitly routes to it.
- Use a reference for long protocols, examples, schemas, inventories, or
  architecture facts sunk from that owner.
- Keep the rule and load condition in the owning leaf. A reference is not a
  native entry, public capability, independent route, shared rule store, or
  second canonical owner.
- Validate the owner-to-reference edge and reject orphaned, multiply owned, or
  independently editable duplicate content.

## Size And Active-Set Contract

- Platform fact: a visible `project_doc_max_bytes` value is truncation
  protection or configuration evidence, not Axiom's authoring budget.
- Axiom authoring rule: keep root `AGENTS.md` below 8192 bytes.
- Keep every other AGENTS or skill instruction document below 8192 bytes. If a
  document reaches or exceeds that boundary, split by canonical owner or move
  scoped examples, schemas, and protocols to a directly routed reference.
- Never reduce rule precision, delete executable detail, or merge independent
  owners merely to satisfy the byte boundary.
- Keep indexes small route-only jump nodes.
- Keep domain entries, rule leaves, and risk-rule leaves scoped to one
  responsibility and small enough to load with their parent indexes.
- Normal active set: root, an optional startup/front-door node, zero to two
  branch indexes, and one to three rule leaves.
- Complex active set: at most six `.agents` documents unless repository
  evidence requires and the final report explains an exception.
- For AGENTS changes, report root, key index, rule-leaf, and representative
  scenario active-set byte totals.

These are Axiom authoring rules, not claims about a universal Codex hard limit.

## Validation Contract

- Verify every link target or mark it explicitly as future work.
- Resolve declarative metadata paths from the target repository root. Resolve
  Markdown links from the directory containing the Markdown file, unless the
  document explicitly declares another base.
- Verify unique IDs, canonical ownership, route reachability, and acyclic
  `requires`. Every exact `requires` target must exist and be reachable from
  the current route before structural writes or final acceptance. A missing or
  unreachable target permits read-only assessment only.
- Verify root rules are global and indexes are route-only.
- Verify no independently maintained duplicate or unresolved conflict remains.
- Check generated target guidance for leaked Axiom triggers, load policies,
  internal route names, generic runtime/request protocols, validation matrices,
  and reporting formats.
- Verify representative scenarios load intended rule owners without siblings.
- Verify no instruction document reaches 8192 bytes.
- Report actual loading only when it was directly tested.

## Prohibited Actions

- Do not use an instruction byte guard as permission to fill the available
  context.
- Do not create a native auto-load entry whose filename is not `AGENTS.md`.
- Do not create nested `AGENTS.md` files without a stable subproject boundary.
- Do not encode secrets, credentials, personal data, raw transcripts, or
  temporary task state in durable instructions.
- Do not vendor Axiom packaged protocols into target repositories.
- Do not generate a custom validator harness by default. Reuse existing project
  checks or report missing validation capability.

## References

- `routing-architecture.md`
- `project-initialization.md`
- `migration-policy.md`
- `validation-reporting.md`
