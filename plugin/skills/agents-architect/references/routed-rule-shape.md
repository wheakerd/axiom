# Routed Rule Shape

## Purpose

Define the frontmatter and body shape of a routed rule document. `instruction-document-contracts.md` owns document roles, ownership, and size; these are the same kind of default, kept when a repository has no established shape of its own.

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

Keep IDs globally unique and keep `requires` acyclic. Omit fields that do not improve routing.

`last_verified` is optional. Add it only as the receipt of a completed semantic audit that names what was checked. A date, modification time, or copied value does not prove that instructions remain correct.

## Rule Body Contract

Use only the sections needed by the responsibility:

- Purpose.
- Apply when.
- Do not apply when.
- Required actions.
- Prohibited actions.
- Validation.
- References.

Write short imperative rules with concrete scope and verifiable actions. Link to authoritative project docs rather than copying them. Do not invent commands, owners, paths, frameworks, or validation steps.

A direct domain entry is a terminal rule leaf reached directly by one unique, evidence-backed domain signal. A risk-rule leaf contains only cross-cutting safety or risk constraints and loads only from an explicit matching signal.

## References

- `instruction-document-contracts.md`
- `routing-architecture.md`
