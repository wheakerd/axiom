# Migration Policy

## Purpose

Classify existing instructions and migrate only durable agent-executable rules.

## Apply when

- Existing AGENTS files, project docs, or `.agents/` content must be reorganized.
- Rules may be duplicated, stale, too broad, or in the wrong location.
- Instruction documents are too large, mix independently routed responsibilities, or risk truncation.
- Git tracking and ignore strategy must be decided.

## Do not apply when

- Creating a fresh structure with no existing docs.
- Only validating an already-migrated tree.

## Classification

Treat `.codex-plugin/**`, `.agents/plugins/**`, `.agents/skills/**`, `skills/*/agents/**`, `<skill-root>/skills/**`, `hooks/**`, `.app.json`, `.mcp.json`, and `assets/**` as protected Codex plugin or skill metadata, not AGENTS routing leaves. Exclude them from AGENTS migration tables unless the user explicitly asks for skill or plugin maintenance; if included, route that work to the relevant skill or plugin maintenance workflow.

Classify each candidate into exactly one category:

- Global hard constraint: root `AGENTS.md`.
- Path or business-domain rule: `.agents/domains/`, `.agents/components/`, or equivalent real boundary.
- Workflow rule: `.agents/workflows/`.
- Cross-cutting risk rule: `.agents/concerns/` or `.agents/risks/`.
- Project fact or human documentation: keep in canonical docs and link from `.agents/`.
- Temporary task information: `.agents/.runtime/` only when needed.
- Invalid or redundant content: delete, merge, or leave outside AGENTS.
- Axiom packaged skill protocol or trigger content: leave in the installed Axiom plugin, not in the target AGENTS system.

## Admission gate

Before writing a durable rule, require:

- Persistent future reuse.
- Clear path, task, risk, module, or domain scope.
- Concrete action, prohibition, or validation step.
- Verifiability by code, config, tests, commands, or authoritative docs.
- One canonical home.
- Correct abstraction level.
- Positive context value.
- No secrets or sensitive data.

Reject rules that fail any gate.

## Migration actions

- Build a migration table before moving files.
- Track original path, Git status, size, canonical content, duplicate content, target path, operation, and reason.
- Use the portable AGENTS size model as Axiom heuristic defaults, not Codex platform hard limits: root `AGENTS.md` under `8 KiB`, index files as jump nodes, leaves and overlays scoped to one responsibility, normal active set of root plus startup or front-door node when present plus `0`-`2` branch indexes plus `1`-`3` leaves or overlays, and complex active set of at most `6` `.agents` documents unless explained. Adjust when project evidence justifies it and report the reason.
- Preserve precise executable rules during migration and move scoped detail to the correct canonical home.
- Sink each migrated rule to the closest owning route. Use root only for true global constraints, indexes only for next-hop routing, leaves for one scoped owner, overlays for cross-cutting risks, and references for long supporting material.
- Prefer `git mv` for tracked file moves.
- Preserve full human docs in canonical locations.
- Move only agent-executable rules into `.agents/`.
- Move only project-specific rules into `.agents/`; do not migrate Axiom packaged skill load policies, trigger definitions, validation protocols, or reporting formats into the target repository.
- Classify `.codex-plugin/**`, `.agents/plugins/**`, `.agents/skills/**`, `skills/*/agents/**`, `<skill-root>/skills/**`, `hooks/**`, `.app.json`, `.mcp.json`, and `assets/**` as protected plugin or skill metadata, not AGENTS routing candidates, unless the user explicitly asks for plugin or skill maintenance.
- Update Markdown links, README references, AGENTS references, scripts, CI config, and documentation checks.
- Keep no two independently editable copies of the same rule.

## Nested AGENTS.md

Create or keep nested `AGENTS.md` only when:

- The directory is a stable subproject, package, or service boundary.
- Codex often starts from that directory.
- Local hard rules must auto-load.
- The nested file reduces misload more than it adds duplication.

Nested files should be tiny or route to canonical leaves.

## Git strategy

- Track team-shared durable root and `.agents/**` instructions when they are meant for the repository.
- Put personal rules under `.agents/local/`.
- Prefer `.git/info/exclude` for user-local ignores.
- Put runtime and generated artifacts under `.agents/.runtime/` or `.agents/.generated/`.
- Add ignores to `.gitignore` only when all contributors should ignore them.

## Prohibited actions

- Do not use `git update-index --assume-unchanged` or `--skip-worktree` to hide durable rules.
- Do not use `AGENTS.override.md` as a normal additive personal layer.
- Do not move protected plugin or skill metadata into AGENTS routing branches.
- Do not vendor Axiom packaged skill rules, triggers, internal routes, validation protocols, or reporting formats into target AGENTS files.
- Do not auto-commit, auto-push, or rewrite history.
