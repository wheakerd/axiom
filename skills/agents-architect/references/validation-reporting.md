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
- protected plugin metadata, Axiom routing protocols, secrets, runtime state,
  and one-off task detail did not leak into target guidance;
- completion claims use current evidence from the layer they describe; and
- an ignored or untracked instruction file has a direct before/after content
  comparison, tracked/ignored classification, and exact ignore-rule owner.

Use the existing project parser or validator when one owns the changed format.
A missing tool or observation is unavailable or unverified, never passed.

## Conditional Checks

Add only checks triggered by the changed surface:

- Route or ownership changes: validate reachability, unique IDs, acyclic
  `requires`, terminal ownership, sibling rejection, and route-only indexes.
- Root, nested entry, or discovery changes: verify the applicable instruction
  chain and current host behavior when safely available.
- Metadata or document-role changes: read
  `../instruction-document-contracts.md` and validate its schema.
- Size or split changes: measure root, key indexes, selected owners, and
  representative active chains; do not use `project_doc_max_bytes` as an
  authoring target.
- Migration: validate the source-to-owner mapping and that no independently
  editable duplicate remains.
- Repo-local Skill changes: validate frontmatter, direct routes, resources,
  and the AGENTS owner that selects the Skill.

Do not repeat a conclusive check unless its target changed or the check failed.
Batch independent read-only checks when their results do not affect the next
decision. Potentially writing host validators must run against a disposable
copy.

## Routing Scenarios

Use the smallest set that covers every changed branch plus its important
rejection boundary:

- A narrow leaf or wording change normally needs two to four scenarios.
- A route-table or owner change needs each changed route, one no-match, one
  sibling rejection, and one cross-route or ambiguous case.
- A broad initialization or migration needs at least eight representative
  scenarios spanning direct, grouped, workflow, risk, docs/test-only,
  non-English, unknown-path, and no-match behavior.

For each scenario record the signal, expected and actual route, loaded files,
unexpected files, active bytes, authorization boundary, and result. Add
current-session versus inactive evidence and host-discovered shadowing cases
only when those behaviors are in scope.

When task-context maintenance, update-trigger, or compaction handling changes,
include one regression scenario with an early proposal that a later user
message narrows or reverses, followed by compaction before the durable update.
Verify that the canonical mode is reported, only the controlling decision is
admitted, superseded and unrelated one-off candidates are rejected, turn and
raw-output coverage are reported separately, and the current-run versus
later-run activation boundary is explicit. Use a Markdown scenario or a
disposable host prompt; do not add a custom harness merely for this case.

Static construction or `codex debug prompt-input` can prove file discovery or
prompt assembly but not semantic model selection. Label actual host routing as
not run or unavailable unless directly observed in a fresh session.

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
Codex loading without direct evidence.

## References

- `instruction-document-contracts.md`
- `routing-architecture.md`
