# Inventory And Audit

## Purpose

Establish repository facts and narrow the reading scope before designing instructions.

## Apply when

- Starting an AGENTS architecture task.
- Existing AGENTS files or `.agents/` content may already exist.
- Repository documentation must be audited before migration.

## Do not apply when

- The user provides a complete synthetic tree and asks only for review.
- The task is a narrow edit to an already-selected leaf.

## Required actions

- Confirm Git root, current working directory, Git status, Codex version, and visible `project_doc_max_bytes`.
- Use official OpenAI/Codex docs for version-sensitive behavior when available.
- Record unverified assumptions instead of treating them as facts.
- Start with metadata and references only.
- Collect locations of `AGENTS.md`, `AGENTS.override.md`, fallback instruction files, `.agents/`, and candidate project docs.
- Record candidate doc path, size, line count, Git tracking state, status, and modification time.
- Record `.codex-plugin/**`, `.agents/plugins/**`, `.agents/skills/**`, `skills/*/agents/**`, `<skill-root>/skills/**`, `hooks/**`, `.app.json`, `.mcp.json`, and `assets/**` as protected Codex plugin or skill metadata, not AGENTS routing leaves, unless the user explicitly scopes skill or plugin maintenance.
- Read document bodies in small batches only after metadata narrows scope.
- For large docs, inspect headings, tables of contents, summaries, or targeted sections first.

## Codex behavior boundaries

- Codex builds the instruction chain at run or TUI session start.
- Project instruction discovery walks from project root to current working directory.
- Each directory contributes at most one matching instruction file.
- Same-directory priority is `AGENTS.override.md`, then `AGENTS.md`, then configured fallback names.
- `AGENTS.override.md` replaces same-level `AGENTS.md`; it is not additive.
- Ordinary Markdown files under `.agents/` are not recursively auto-loaded.
- Do not assume generic include syntax or recursive imports.
- User instructions outrank persistent repository instructions.
- More specific path or domain rules outrank broader rules.

## Prohibited actions

- Do not recursively read all Markdown at the start.
- Do not read full logs or large source files for instruction design unless a targeted rule depends on them.
- Do not migrate, rewrite, or validate protected plugin or skill metadata as AGENTS routing content.
- Do not import unrelated historical notes into the durable instruction system.

## Validation

Run a metadata inventory when possible using read-only commands that fit the user's operating system and available tools.

Confirm generated inventory output with an available parser only when you explicitly write structured output to disk.
