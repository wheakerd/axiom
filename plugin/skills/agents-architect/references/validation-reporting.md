# Validation And Reporting

## Purpose

Validate only the AGENTS surfaces and claims changed or explicitly requested,
then report current evidence without repeating routine detail.

## Apply When

- Completing AGENTS creation, migration, routing, or maintenance changes.
- Auditing route reachability, ownership, size, links, or actual loading.

Do not load this reference for a conceptual answer or an unchanged surface
whose validation was not requested.

## Core Checks

For every changed instruction file, verify:

- the file and repository owner are exact and unrelated work is preserved;
- links and declared paths resolve from their documented bases;
- the file is below the Axiom instruction-byte boundary;
- its rule scope has one reachable canonical owner with no conflicting copy;
- newly authored prose follows the parent skill's Document Language contract:
  inspect every changed file, identify any explicit user document-language
  request and its scope, and reject a mismatch without translating preserved
  source literals or unrelated content;
- protected plugin metadata, Axiom routing protocols, secrets, runtime state,
  and one-off task detail did not leak into target guidance;
- completion claims use current evidence from the layer they describe; and
- an ignored or untracked instruction file has a direct before/after content
  comparison, tracked/ignored classification, and exact ignore-rule owner.

Use the existing project parser or validator when one owns the changed format.
A missing tool or observation is unavailable or unverified, never passed.

## Conditional Checks

Add only checks triggered by the changed surface:

- Route or ownership changes: validate reachability, unique IDs, acyclic `requires`, terminal ownership, sibling rejection, and route-only indexes.
- Root, nested entry, or discovery changes: verify the applicable instruction chain and current host behavior when safely available.
- Metadata or document-role changes: read [instruction document contracts](instruction-document-contracts.md) and validate the schema in [routed rule shape](routed-rule-shape.md).
- Size or split changes: measure root, key indexes, selected owners, and representative active chains; do not use a host size limit such as Codex `project_doc_max_bytes` as an authoring target.
- Project-memory changes: validate that each class has one home, that the registry lists every home that exists, that `.agents/local/` is ignored and untracked, and that no automatic class holds a rule.
- Migration: validate the source-to-owner mapping and that no independently editable duplicate remains.
- Repo-local Skill changes: validate discovery metadata, frontmatter, direct routes, and resources. Check the AGENTS selector only for a declared AGENTS-to-Skill route; standalone Skills need none. Discovery proves neither explicit-route reachability nor body loading.
- Implementation reconciliation: validate explicit activation, recorded working-tree or ref baseline, per-rule evidence status and disposition, active-chain authority, collaboration separation, preview/apply authorization, and the selected maintenance or migration terminal owner.

Do not repeat a conclusive check unless its target changed or the check failed.
Batch independent read-only checks when their results do not affect the next
decision. Potentially writing host validators must run against a disposable
copy.

## Routing Scenarios

For every completed change, read `routing-scenarios.md` and cover the change with its smallest scenario set: a narrow leaf or wording change, a route-table or owner change, and a broad initialization or migration each have a default there. It also owns the scenario record and the regression cases for task-context, update-trigger, compaction, implementation-reconciliation, and document-language changes.

## Actual Loading

Run host-native root or subdirectory loading checks only when the task changes
or claims native discovery. Record the host/version and exact scope. Do not
create a shadowing non-`AGENTS.md` source merely to test precedence, install a
missing validator, or treat an optional unavailable check as failure.

## Final Report

Lead with the outcome. Include changed files and owners, material routing or
authorization changes, before/after context when relevant, validation results,
and remaining real gaps. Include a full tree, migration map, scenario table,
Git strategy, or manual commands only when that artifact changed a decision or
is needed for recovery.

Do not report suggestions as completed changes, hide failures, or claim actual
host loading without direct evidence.

## References

- `instruction-document-contracts.md`
- `routed-rule-shape.md`
- `routing-architecture.md`
- `routing-scenarios.md`
