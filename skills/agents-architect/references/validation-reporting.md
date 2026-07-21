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
- Document IDs are unique.
- Each leaf has at least one reachable route.
- Each leaf has one canonical owner.
- `requires` has no cycles.
- Referenced paths exist or are explicitly future paths.
- No duplicate independently maintained rules.
- No unresolved conflicts.
- No secrets.
- Root and auto-load chain fit the portable size model.
- Size pressure is resolved through route ownership, splitting, or resource placement without reducing rule precision, deleting executable detail, or merging unrelated responsibilities.
- Root rules apply repository-wide; non-global rules are sunk to the closest owning leaf, overlay, reference, or closer nested instruction file.
- Indexes do not contain leaf bodies.
- Group indexes route within one stable axis and do not flatten descendant rules.
- Runtime files are absent from durable routing.
- Protected plugin and skill metadata is not counted as AGENTS leaves or routes unless the task explicitly scoped skill or plugin maintenance.
- Target AGENTS content does not vendor Axiom packaged skill rules, load policies, trigger definitions, internal routes, validation protocols, or reporting formats unless the user explicitly requested a provenance note.
- Generated target AGENTS content routes project structure and associations, not installed Axiom plugin triggers.

Size-model validation follows the portable AGENTS size model. Separate Codex platform facts from Axiom defaults:

- Platform fact: visible `project_doc_max_bytes` is a truncation guard or configuration fact, not Axiom's design budget.
- Axiom heuristic: keep root `AGENTS.md` under `8 KiB` by default. This is not a Codex platform hard limit; allow project-evidence-based exceptions and explain them.
- Do not reduce rule precision, delete executable detail, or merge unrelated responsibilities to satisfy byte targets. Move detail to the owning leaf, resource, or split responsibility.
- Keep index files as small jump nodes focused on next-hop routing.
- Keep leaves and overlays scoped to one responsibility and small enough to load with their parent indexes.
- Axiom heuristic for a normal active set: root, startup or front-door node when present, `0`-`2` branch indexes, and `1`-`3` leaves or overlays.
- Axiom heuristic for a complex active set: no more than `6` `.agents` documents. This is not a Codex platform hard limit; allow justified overages and explain them in the final report.
- For AGENTS changes, report root bytes, key index bytes, leaf bytes, and scenario active-set bytes.

## Scenario validation

Generate 8-12 representative scenarios from the actual repo:

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

For each scenario record task signal, expected paths, should-load docs, should-not-load docs, actual routed docs, misloads, active doc count, active bytes, and pass/fail.

Include scenarios that prove route sinking works: a root-only task, a single-domain task, a workflow-only task, a cross-cutting risk task, and a task that must not load sibling leaves.

## Actual loading checks

When safe and practical:

- Verify repository-root Codex loading.
- Verify major subdirectory loading.
- Verify `AGENTS.override.md` replacement behavior only in a safe fixture.
- Verify `project_doc_max_bytes` and fallback settings if visible.

If unable to run, provide exact manual commands and mark the check unverified.

## Final report order

1. Final conclusion.
2. Changed files.
3. Final instruction tree.
4. Routing summary.
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
