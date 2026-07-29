# Validation And Reporting

## Purpose

Verify the instruction architecture and report only completed facts.

## Apply when

- Completing an AGENTS creation, migration, or refactor task.
- Checking split decisions, portable size model, links, routes, or actual loading behavior.
- Preparing final output after file changes.

## Do not apply when

- The user only asks for a conceptual explanation.
- No file changes were made and no validation was requested.

## Static validation

Check:

- Link targets exist.
- Declarative metadata paths resolve from the repository root, while Markdown
  links resolve from the containing document unless an explicit base says
  otherwise.
- Document IDs are unique.
- Each direct domain entry, rule leaf, and risk-rule leaf has a reachable route
  and one canonical owner.
- Each parent-owned reference has exactly one terminal rule owner and an
  explicit owner-to-reference route.
- Durable AGENTS maintenance reports name the checked owning index, rule leaf or
  closer `AGENTS.md`, and any likely adjacent owner, including whether
  equivalent or conflicting rules were found.
- `requires` has no cycles; every exact target exists and is reachable from the
  current route. Missing or unreachable targets fail structural acceptance.
- Referenced paths exist or are explicitly future paths.
- No duplicate independently maintained rules.
- No unresolved conflicts.
- No Axiom trigger, load-policy, generic request/language/runtime protocol,
  internal route, validation matrix, or reporting-template leakage appears in
  generated target guidance.
- No secrets.
- Root and auto-load chain fit the portable size model.
- Every Axiom-created, maintained, migrated, validated, or recommended native
  auto-load entry is named `AGENTS.md`; every `.agents/**` document is reached
  only through explicit routing.
- Every AGENTS or skill instruction document satisfies the canonical byte
  boundary.
- Size pressure is resolved through route ownership, splitting, or resource placement without reducing rule precision, deleting executable detail, or merging unrelated responsibilities.
- Root rules apply repository-wide; non-global rules are sunk to the closest
  direct domain entry, rule leaf, cross-cutting safety or risk rule leaf,
  parent-owned reference, or closer nested `AGENTS.md`.
- Group indexes do not contain rule bodies.
- Group indexes route within one stable axis and do not flatten descendant rules.
- Runtime files are absent from durable routing.
- Protected plugin and skill metadata is not counted as AGENTS rule leaves or
  routes unless the task explicitly scoped skill or plugin maintenance.
- Target AGENTS content does not vendor Axiom packaged skill rules, load policies, trigger definitions, internal routes, validation protocols, or reporting formats unless the user explicitly requested a provenance note.
- Generated target AGENTS content routes project structure and associations, not installed Axiom plugin triggers.
- Every completion claim has current direct evidence at the layer it describes:
  current filesystem content for files, current parser/validator output for
  format, current route results for reachability, and current Git state for
  tracking. Historical diffs or earlier reports are supporting context only.
- Every ignored instruction candidate has a direct before/after comparison,
  tracked/ignored classification, and exact ignore-rule owner from
  `git check-ignore -v -- <path>` or an equivalent query.

Load `instruction-document-contracts.md` as the canonical size and document
contract. Validate its byte boundary, route-only group indexes, scoped rule
leaves, reference ownership, normal and complex active-set budgets, and
precision-preserving split rule.
Treat visible `project_doc_max_bytes` only as platform configuration evidence,
not as permission to fill the available context. Report root, key index, rule
leaf, and representative scenario active-set bytes.

## Scenario validation

Generate at least 16 representative scenarios from the actual repo:

- Single domain change.
- Shared infrastructure change.
- Bugfix.
- Feature.
- Performance work.
- Security work.
- Migration.
- Test-only change.
- Docs-only change.
- Command invocation through unambiguous non-English wording.
- Cross-domain change.
- Unknown-path troubleshooting.
- Simple task that should not load specialized leaves.
- Unique high-signal direct-domain routing.
- Low-signal routing through exactly one group index.
- Parent-owned reference loading without a second canonical owner.
- Current-session active guidance versus inactive or historical evidence.
- No-project-root current-directory discovery.
- Host-discovered non-`AGENTS.md` authority that requires a read-only
  shadowing safe-stop.

For each scenario record task signal, expected paths, should-load docs, should-not-load docs, actual routed docs, misloads, active doc count, active bytes, and pass/fail.

Include scenarios that prove route sinking works: a root-only task, a direct
domain task, a low-signal group task, a workflow-only task, a cross-cutting
risk task, and a task that must not load sibling leaves.

## Actual loading checks

When safe and practical:

- Verify repository-root Codex loading.
- Verify major subdirectory loading.
- If a current host loading check exposes a non-`AGENTS.md` active source,
  audit its actual precedence and shadowing read-only. Do not create such a
  source in the target repository or recommend it as an Axiom output.
- Verify visible `project_doc_max_bytes` and host discovery settings without
  treating them as Axiom authoring defaults.

If a required validator or tool is missing, provide the exact missing check and
mark it unverified or failed according to the workflow. Tool absence never
counts as a pass. If unable to run an optional check, provide exact manual
commands and mark it unverified.

## Final report order

1. Final conclusion.
2. Changed files.
3. Final instruction tree.
4. Routing summary.
   For durable AGENTS maintenance, include the owning index, rule leaf or closer
   `AGENTS.md`, adjacent owner checks, and duplicate or conflict result.
5. Migration mapping.
6. Context size model.
7. Routing test results.
8. Git strategy.
9. Validation results.
10. Remaining real risks.

## Prohibited actions

- Do not report suggestions as completed changes.
- Do not hide validation failures.
- Do not claim actual Codex loading was tested unless it was.

## References

- `instruction-document-contracts.md`
- `routing-architecture.md`
