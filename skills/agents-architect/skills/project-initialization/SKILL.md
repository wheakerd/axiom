---
name: project-initialization
description: Use when AGENTS Architect needs to initialize a root AGENTS.md and .agents routing tree for a repository with no existing AGENTS.md, AGENTS.override.md, fallback instruction file, or durable .agents instruction system.
---

# Project Initialization

## Purpose

Initialize a fresh, scoped AGENTS instruction system for a repository that has no durable AGENTS guidance yet.

## Apply when

- `../../SKILL.md` has triggered.
- A low-cost metadata inventory confirms there is no existing `AGENTS.md`, `AGENTS.override.md`, configured fallback instruction file, or durable `.agents/` instruction tree.
- The user asks to initialize, create, generate, or set up AGENTS guidance, a root instruction entry, or a `.agents/` routing tree for the current repository.

## Do not apply when

- Any AGENTS definition already exists.
- The task asks to reorganize, rewrite, migrate, or audit existing AGENTS guidance.
- The task only validates an existing instruction system.
- The task is about temporary session memory, effective-instruction updates, or runtime capsules.

## Required actions

- Confirm the fresh-init gate before writing files. Inspect Git root, current directory, Git status, existing AGENTS files, `.agents/`, configured fallback names when visible, source roots, manifests, build config, test config, CI, and candidate project docs.
- If an existing AGENTS definition appears after scoping starts, stop initialization and route to `../migration-policy/SKILL.md`; do not overwrite or merge by default.
- Treat `.codex-plugin/**`, `.agents/plugins/**`, `.agents/skills/**`, `skills/*/agents/**`, `<skill-root>/skills/**`, `hooks/**`, `.app.json`, `.mcp.json`, and `assets/**` as protected Codex plugin or skill metadata. Their presence is not a reusable AGENTS routing tree to merge or rewrite, and initialization must not place generated AGENTS leaves under them.
- Derive route groups from real project boundaries. Prefer `domains/`, `workflows/`, `concerns/`, and `integrations/` only when the repository has matching durable boundaries.
- Split route groups by real responsibility axes such as session, workflow, domain, component, and concern when those axes are present; do not flatten all guidance into one branch.
- Create no branch, index, leaf, or overlay only for symmetry.
- Write root `AGENTS.md` as a small project control plane: project goal, true global constraints, instruction priority, request handling protocol, routing algorithm, top-level route table, portable loading shape, runtime capsule rule, project-local durable-update placement rule, and minimum verification.
- Create `.agents/index.md` as the on-demand entry index. Create branch `index.md` files only for branches that have reachable leaves.
- Keep indexes limited to purpose, enter conditions, exclusion conditions, next hops, and stop-reading conditions.
- Sink non-global rules to the closest owning leaf or overlay; keep root and group indexes out of leaf-rule ownership.
- Write leaves for stable, agent-executable context: ownership boundaries, path globs, entry points, source-of-truth docs, validation commands, generated-code boundaries, and risk signals.
- Keep generated AGENTS content project-specific. Do not copy Axiom packaged skill rules, Axiom trigger definitions, Axiom internal route names, packaged `SKILL.md` content, validation protocols, or reporting formats into the target repository.
- Use compact leaf frontmatter with only needed fields: `id`, `kind`, `scope`, `load_when`, `do_not_load_when`, `requires`, `source_of_truth`, and `last_verified`.
- Use leaf body sections only when useful: Purpose, Apply when, Do not apply when, Required actions, Prohibited actions, Validation, and References.
- Prefer stable routing facts, ownership boundaries, source links, validation commands, and risk signals over volatile implementation summaries.
- Make the generated instruction system precise enough to route future work quickly, but require targeted source and test checks before behavior-changing edits.
- Do not use `project_doc_max_bytes` as a design budget. Treat it only as a truncation guard or visible configuration fact.
- Keep root `AGENTS.md` under `8 KiB`.
- Preserve precise executable rules when size pressure appears by routing detail to the owning leaf, resource, or split responsibility.
- Keep index files as small jump nodes focused on next-hop routing.
- Keep leaves and overlays scoped to one responsibility and small enough to load with their parent indexes.
- Target a normal active set of root, startup or front-door node when present, `0`-`2` branch indexes, and `1`-`3` leaves or overlays.
- Target a complex active set of no more than `6` `.agents` documents unless the final report explains the overage.
- Load `../routing-architecture/SKILL.md` only when the requested initialization needs custom routing design beyond these defaults.
- Load `../validation-reporting/SKILL.md` before final reporting when files were changed.

## Prohibited actions

- Do not initialize over an existing AGENTS definition.
- Do not recursively read all source files or all Markdown before scoping.
- Do not copy READMEs, full architecture docs, full project trees, changelogs, logs, or issue histories into AGENTS docs.
- Do not copy Axiom packaged skill protocols into AGENTS docs or repo-local skills.
- Do not add `$agents-architect`, `$using-axiom`, or Axiom plugin trigger instructions to generated target AGENTS content unless the user explicitly asks for a provenance note.
- Do not invent commands, ownership, frameworks, domains, or validation steps.
- Do not encode secrets, credentials, personal data, or temporary task discoveries.
- Do not make AGENTS docs a substitute for checking impacted implementation files and tests.
- Do not create nested `AGENTS.md` files unless a stable subproject boundary and Codex start path justify auto-loading them.
- Do not create, move, or rewrite protected plugin or skill metadata during AGENTS initialization.

## Validation

- Verify every written link target exists or is explicitly marked as a future path.
- Verify document IDs are unique and each leaf is reachable from exactly one canonical index path.
- Verify `requires` dependencies have no cycles.
- Verify indexes do not contain leaf rules and leaves do not duplicate root global rules.
- Verify root, key indexes, leaves, and scenario active-set bytes fit the initialization limits.
- Run representative routing scenarios for feature work, bugfixes, docs-only work, test-only work, cross-domain work, risk-triggered work, and unknown-path troubleshooting.
- Report validation that could not be run instead of treating it as complete.

## References

- `../inventory-audit/SKILL.md`
- `../routing-architecture/SKILL.md`
- `../migration-policy/SKILL.md`
- `../validation-reporting/SKILL.md`
