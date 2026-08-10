# Migration Policy

## Purpose

Classify existing instructions and migrate only durable agent-executable rules.

## Apply when

- Existing `AGENTS.md` files, project docs, or `.agents/` content must be
  reorganized.
- Rules may be duplicated, stale, too broad, or in the wrong location.
- Instruction documents are too large, mix independently routed responsibilities, or risk truncation.
- Git tracking and ignore strategy must be decided.

## Do not apply when

- Creating a fresh structure with no existing docs.
- Only validating an already-migrated tree.

## Classification

Apply the parent skill's protected-metadata boundary. Exclude those surfaces from
AGENTS migration tables unless the user explicitly asks for skill or plugin
maintenance; if included, route that work to the relevant skill or plugin
maintenance workflow.

Classify each candidate into exactly one category:

- Global hard constraint: root `AGENTS.md`.
- Path or business-domain rule: `.agents/domains/`, `.agents/components/`, or equivalent real boundary.
- Workflow rule: `.agents/workflows/`.
- Cross-cutting safety or risk rule leaf: an evidence-backed concern or risk
  route.
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
- Track whether each source is live source, a persistent rule, runtime state, or
  historical reference. Do not promote runtime or historical material merely
  because it is recent.
- Apply `instruction-document-contracts.md` as the canonical document and size
  contract. Route-sink every instruction document that reaches its boundary.
- Preserve precise executable rules during migration and move scoped detail to the correct canonical home.
- Sink each migrated rule to the closest owning route. Use root only for true
  global constraints, group indexes only for next-hop routing, direct domain
  entries or rule leaves for one scoped owner, cross-cutting safety or risk
  rule leaves for explicit risk signals, and owner-routed references for long
  supporting material.
- Prefer `git mv` for tracked file moves.
- Preserve full human docs in canonical locations.
- Move only agent-executable rules into `.agents/`.
- Move only project-specific rules into `.agents/`; do not migrate Axiom packaged skill load policies, trigger definitions, validation protocols, or reporting formats into the target repository.
- Keep surfaces covered by the parent skill's protected-metadata boundary out of
  AGENTS routing unless the user explicitly asks for plugin or skill
  maintenance.
- Update Markdown links, README references, AGENTS references, scripts, CI config, and documentation checks.
- Read ignored or untracked `AGENTS.md` candidates directly. Do not use a clean
  tracked diff as proof that their content is unchanged, absent, or inactive.
- Check the migration result for Axiom protocol leakage before writing: target
  guidance must not inherit Axiom triggers, generic request/language/runtime
  protocols, load policies, internal routes, validation matrices, or report
  templates.

## Nested AGENTS.md

Create or keep nested `AGENTS.md` only when:

- The directory is a stable subproject, package, or service boundary.
- Codex often starts from that directory.
- Local hard rules must auto-load.
- The nested file reduces misload more than it adds duplication.

Nested files should be tiny or route to canonical rule owners.

Before migration, classify every host-discovered instruction source by actual
current-session load state. A non-`AGENTS.md` source remains read-only even when
active and authoritative. If it shadows the intended `AGENTS.md` result,
safe-stop and report its exact path and observed precedence.

## Git strategy

- Track team-shared durable root and `.agents/**` instructions when they are meant for the repository.
- Put personal rules under `.agents/local/`.
- Prefer `.git/info/exclude` for user-local ignores.
- Put runtime and generated artifacts under `.agents/.runtime/` or `.agents/.generated/`.
- Add ignores to `.gitignore` only when all contributors should ignore them.

## Prohibited actions

- Do not use `git update-index --assume-unchanged` or `--skip-worktree` to hide durable rules.
- Do not create, edit, move, delete, migrate, or recommend a host-discovered
  instruction source whose filename is not `AGENTS.md`.
- Do not move protected plugin or skill metadata into AGENTS routing branches.
- Do not vendor Axiom packaged skill rules, triggers, internal routes,
  validation protocols, or reporting formats into target `AGENTS.md` files.

## References

- `instruction-document-contracts.md`
- `routing-architecture.md`
- `validation-reporting.md`
