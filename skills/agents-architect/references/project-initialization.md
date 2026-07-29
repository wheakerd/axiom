# Project Initialization

## Purpose

Initialize a fresh, scoped AGENTS instruction system for a repository that has no durable AGENTS guidance yet.

## Apply when

- The AGENTS Architect parent skill has triggered.
- A low-cost metadata inventory confirms there is no existing `AGENTS.md`, no
  host-discovered non-`AGENTS.md` instruction source that could be active or
  shadow the intended result, and no durable `.agents/` instruction tree.
- The user asks to initialize, create, generate, or set up a root `AGENTS.md`
  entry or its `.agents/` routing tree for the current repository.

## Do not apply when

- An `AGENTS.md` system already exists, or a host-discovered non-`AGENTS.md`
  instruction source could control the same scope.
- The task asks to reorganize, rewrite, migrate, or audit existing AGENTS guidance.
- The task only validates an existing instruction system.
- The task is about temporary session memory, effective-instruction updates, or runtime capsules.

## Required actions

- Confirm the fresh-init gate before writing files. Inspect current directory,
  no-Git or Git-root state, nested-root ambiguity, unborn/normal branch state,
  tracked/untracked/ignored guidance, existing `AGENTS.md` entries, `.agents/`,
  visible host-discovered non-`AGENTS.md` candidates, source roots, manifests,
  build config, test config, CI, and candidate project docs.
- If an existing `AGENTS.md` system appears after scoping starts, stop
  initialization and route to `migration-policy.md`; do not overwrite or merge
  by default. If only a host-discovered non-`AGENTS.md` source appears,
  safe-stop and report its exact path, observed authority, and whether it would
  shadow the intended `AGENTS.md`; never migrate or mutate that source.
- Apply the parent skill's protected-metadata boundary. Those surfaces are not a
  reusable AGENTS routing tree to merge or rewrite, and initialization must not
  place generated AGENTS leaves under them.
- Derive route groups from real project boundaries. Prefer `domains/`, `workflows/`, `concerns/`, and `integrations/` only when the repository has matching durable boundaries.
- Split route groups by real responsibility axes such as session, workflow, domain, component, and concern when those axes are present; do not flatten all guidance into one branch.
- Create no branch, group index, direct domain entry, rule leaf, or
  cross-cutting safety or risk rule leaf only for symmetry.
- Write root `AGENTS.md` as a small project control plane containing the project
  goal, true global constraints, instruction priority, evidence-backed routing
  entry/table when needed, and minimum verification. Add request handling,
  language, runtime, durable-update, or size rules only when current project
  evidence or the user makes them repository policy.
- Create `.agents/index.md` only as a next-hop rule index explicitly routed by
  root `AGENTS.md`; it is not a Codex native discovery entry. Create group
  `index.md` files only for evidence-backed branches with reachable rule leaves.
- Keep indexes limited to purpose, enter conditions, exclusion conditions, next hops, and stop-reading conditions.
- Sink non-global rules to the closest owning direct domain entry, rule leaf, or
  cross-cutting safety or risk rule leaf; keep root and group indexes out of
  rule ownership.
- Write direct domain entries and rule leaves for stable, agent-executable
  context: ownership boundaries, path globs, entry points, source-of-truth docs,
  validation commands, generated-code boundaries, and risk signals.
- Keep generated AGENTS content project-specific. Do not copy Axiom packaged skill rules, Axiom trigger definitions, Axiom internal route names, packaged `SKILL.md` content, validation protocols, or reporting formats into the target repository.
- Load `instruction-document-contracts.md` before writing files and apply its
  root, group-index, routed-rule, reference, metadata, language, and size
  contracts.
- Prefer stable routing facts, ownership boundaries, source links, validation commands, and risk signals over volatile implementation summaries.
- Make the generated instruction system precise enough to route future work quickly, but require targeted source and test checks before behavior-changing edits.
- Load `routing-architecture.md` only when the requested initialization needs custom routing design beyond these defaults.
- Load `validation-reporting.md` before final reporting when files were changed.

## Prohibited actions

- Do not initialize over an existing `AGENTS.md` system.
- Do not recursively read all source files or all Markdown before scoping.
- Do not copy READMEs, full architecture docs, full project trees, changelogs, logs, or issue histories into AGENTS docs.
- Do not copy Axiom packaged skill protocols into AGENTS docs or repo-local skills.
- Do not add `$agents-architect`, `$using-axiom`, or Axiom plugin trigger instructions to generated target AGENTS content unless the user explicitly asks for a provenance note.
- Do not invent commands, ownership, frameworks, domains, or validation steps.
- Do not encode secrets, credentials, personal data, or temporary task discoveries.
- Do not make AGENTS docs a substitute for checking impacted implementation files and tests.
- Do not generate a validator harness, test suite, or runtime capsule by default.
- Do not create nested `AGENTS.md` files unless a stable subproject boundary and Codex start path justify auto-loading them.
- Do not create, edit, move, delete, migrate, or recommend a Codex native
  auto-load entry whose filename is not `AGENTS.md`.
- Do not create, move, or rewrite protected plugin or skill metadata during AGENTS initialization.

## Validation

- Verify every written link target exists or is explicitly marked as a future path.
- Verify document IDs are unique and each direct domain entry or rule leaf is
  reachable from exactly one canonical route.
- Verify `requires` dependencies have no cycles.
- Verify indexes do not contain rule bodies and rule leaves do not duplicate
  root global rules.
- Verify root, key indexes, rule leaves, and scenario active-set bytes fit
  Axiom's initialization heuristics or have documented project-specific
  justification.
- Run representative routing scenarios for feature work, bugfixes, docs-only
  work, test-only work, direct-domain work, low-signal group routing,
  cross-domain work, risk-triggered work, and unknown-path troubleshooting.
- Report validation that could not be run instead of treating it as complete.

## References

- `inventory-audit.md`
- `instruction-document-contracts.md`
- `routing-architecture.md`
- `migration-policy.md`
- `validation-reporting.md`
