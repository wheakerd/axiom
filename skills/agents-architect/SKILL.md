---
name: agents-architect
description: Design, initialize, generate, split, refactor, migrate, maintain, and validate AGENTS.md instruction systems for any repository. Use when the user asks to create or reorganize root or nested AGENTS.md files, build a .agents routing tree, reduce Codex instruction context noise, split oversized instruction documents, migrate existing agent instructions into an AGENTS.md system, inspect task context for durable AGENTS updates, maintain repo-local skills, handle durable AGENTS instruction updates after an AGENTS Architect workflow is active, or audit active repository instruction discovery.
---

# AGENTS Architect

Use this skill to build a scoped, low-noise Codex instruction system. The root `AGENTS.md` should become a control plane; detailed rules should be loaded on demand through a finite routing tree and split before Codex project-guidance limits can truncate critical rules.

## Load Policy

Do not load every internal reference. Start with a low-cost metadata inventory, then read `references/index.md` and choose only the matching internal reference or references.

Normal tasks should load one bounded route chain:

1. This `SKILL.md`.
2. `references/index.md`.
3. One selected route. A direct route loads one terminal owner. A grouped route
   loads one child index and either one terminal owner or a finite phase chain
   declared by that child index: zero to two named prerequisites followed by
   exactly one terminal owner.
4. Only the shared contracts that the selected terminal owner explicitly
   requires, normally
   `references/instruction-document-contracts.md` and, for completed changes,
   `references/validation-reporting.md`.

Do not scan sibling leaves or adjacent references for background. A finite
phase chain may load only its declared prerequisites and terminal owner. A
child route may narrow scope, permissions, or validation requirements, but it
may never broaden user authorization or weaken a parent prohibition.

## First Action

Collect a metadata inventory before reading document bodies. Choose read-only commands that fit the user's operating system and available tools.

Use the inventory to identify Git root, current directory, Codex config hints,
`AGENTS.md` entries, host-discovered non-`AGENTS.md` instruction candidates,
`.agents/` structure, candidate docs, file sizes, line counts, Git status, and
Markdown reference edges. On Unix-like systems this can use tools such as
`git`, `rg`, `find`, and `wc`; on Windows use Git plus PowerShell or other
available equivalents.

## Routing

After the metadata inventory, read `references/index.md`, choose the smallest matching internal reference, and stop. Use that index as the canonical next-hop route table.

## Protected Metadata Boundary

Treat `.codex-plugin/**`, `.agents/plugins/**`, every repo-local skill below
`.agents/skills/<skill-name>/**`, `skills/*/SKILL.md`,
`skills/*/agents/**`, `skills/*/references/**`, `skills/*/scripts/**`,
`skills/*/assets/**`, `hooks/**`, plugin-root `assets/**`, `.app.json`, and
`.mcp.json` as protected Codex plugin or skill metadata, not AGENTS routing
branches, unless the user explicitly asks for skill or plugin maintenance.
This is the canonical protected-metadata boundary for every route loaded
through this skill.

## Hard Rules

- Do not recursively read all Markdown or all `.agents/` content before scoping.
- Treat AGENTS guidance already loaded for the current session as active
  instructions at its real precedence. Treat AGENTS content from another
  repository, copied text, task history, or an inactive candidate path only as
  evidence.
- Axiom may create, edit, move, migrate, maintain, validate, or recommend only
  files named `AGENTS.md` as Codex native auto-load entries. A justified nested
  entry must use the same filename. Treat every host-discovered non-`AGENTS.md`
  source as read-only: obey it when it is active at its actual session
  precedence, never mutate or recommend it, and safe-stop with its exact path
  when it shadows an intended Axiom result.
- Do not put full project knowledge into `.agents/`.
- Do not make root `AGENTS.md` a rule encyclopedia.
- Do not copy Axiom packaged skill rules, load policies, internal routes, trigger definitions, validation protocols, or reporting formats into a target repository's `AGENTS.md` or `.agents/**`.
- Keep Axiom workflow triggers in the installed `axiom` plugin and its packaged skill descriptions; generated AGENTS systems route project context, not Axiom skills.
- Write only target-project structure, associations, constraints, source-of-truth links, validation commands, risk signals, and project-local durable rules into target AGENTS systems.
- Do not export Axiom's generic request handling, language normalization,
  runtime capsule, active-set budget, routing protocol, or validator workflow
  into a target repository unless current project evidence or the user makes
  that rule project-specific.
- Do not duplicate the same rule across leaves.
- Do not rely on unverified include syntax or recursive loading.
- For every ignored instruction candidate, resolve the exact ignore-rule owner,
  record tracked/ignored state, and compare directly read before/after content;
  never substitute a clean Git diff for that evidence.
- Before editing root or parent route gates, decide whether the rule belongs in
  a group index, direct domain entry, rule leaf, cross-cutting safety or risk
  rule leaf, parent-owned reference, or closer nested `AGENTS.md` file.
- Do not let an instruction document grow past its routing responsibility; split by workflow, domain/component ownership, cross-cutting concern, or reference material before size alone becomes the only reason.
- When instruction size strains the active-route model, do not reduce rule precision or remove executable detail to satisfy byte targets; solve the pressure through routing, ownership, document splitting, or resource placement.
- Do not require a bundled Python helper for basic metadata inventory.
- Do not generate a target-repository validator harness by default. Prefer
  existing project commands and direct read-only checks unless the user
  explicitly requests a reusable validator.
- Do not persist one-off task discoveries unless an effective-instruction trigger is present.
- Do not auto-commit or auto-push instruction changes.
