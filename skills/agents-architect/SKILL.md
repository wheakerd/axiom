---
name: agents-architect
description: Design, initialize, generate, split, refactor, maintain, and validate AGENTS.md instruction systems for any repository. Use when the user asks to initialize or create AGENTS files, reorganize AGENTS files, build a .agents routing tree, reduce Codex instruction context noise, split oversized instruction documents, migrate existing agent instructions, inspect task context for durable AGENTS updates, maintain repo-local skills, handle durable AGENTS instruction updates after an AGENTS Architect workflow is active, or audit AGENTS.md / AGENTS.override.md / repository agent guidance.
---

# AGENTS Architect

Use this skill to build a scoped, low-noise Codex instruction system. The root `AGENTS.md` should become a control plane; detailed rules should be loaded on demand through a finite routing tree and split before Codex project-guidance limits can truncate critical rules.

## Load Policy

Do not load every internal reference. Start with a low-cost metadata inventory, then read `references/index.md` and choose only the matching internal reference or references.

Normal tasks should load:

1. This `SKILL.md`.
2. `references/index.md`.
3. One internal reference.

Load two internal references only when the task spans both initialization and custom routing design, both initialization and validation, both design and validation, or both migration and effective-instruction updates.

## First Action

Collect a metadata inventory before reading document bodies. Choose read-only commands that fit the user's operating system and available tools.

Use the inventory to identify Git root, current directory, Codex config hints, AGENTS files, `.agents/` structure, candidate docs, file sizes, line counts, Git status, and Markdown reference edges. On Unix-like systems this can use tools such as `git`, `rg`, `find`, and `wc`; on Windows use Git plus PowerShell or other available equivalents.

## Routing

After the metadata inventory, read `references/index.md`, choose the smallest matching internal reference, and stop. Use that index as the canonical next-hop route table.

## Hard Rules

- Do not recursively read all Markdown or all `.agents/` content before scoping.
- Do not put full project knowledge into `.agents/`.
- Do not make root `AGENTS.md` a rule encyclopedia.
- Do not copy Axiom packaged skill rules, load policies, internal routes, trigger definitions, validation protocols, or reporting formats into a target repository's `AGENTS.md` or `.agents/**`.
- Keep Axiom workflow triggers in the installed `axiom` plugin and its packaged skill descriptions; generated AGENTS systems route project context, not Axiom skills.
- Write only target-project structure, associations, constraints, source-of-truth links, validation commands, risk signals, and project-local durable rules into target AGENTS systems.
- Do not duplicate the same rule across leaves.
- Do not rely on unverified include syntax or recursive loading.
- Before editing root or parent route gates, decide whether the rule belongs in a group index, leaf, overlay, reference, or closer nested instruction file.
- Do not let an instruction document grow past its routing responsibility; split by workflow, domain/component ownership, cross-cutting concern, or reference material before size alone becomes the only reason.
- When instruction size strains the active-route model, do not reduce rule precision or remove executable detail to satisfy byte targets; solve the pressure through routing, ownership, document splitting, or resource placement.
- Do not require a bundled Python helper for basic metadata inventory.
- Treat `.codex-plugin/**`, `.agents/plugins/**`, `.agents/skills/**`, `skills/*/agents/**`, `skills/*/references/**`, `hooks/**`, `.app.json`, `.mcp.json`, and `assets/**` as protected Codex plugin or skill metadata, not AGENTS routing branches, unless the user explicitly asks for skill or plugin maintenance.
- Do not persist one-off task discoveries unless an effective-instruction trigger is present.
- Do not auto-commit or auto-push instruction changes.
