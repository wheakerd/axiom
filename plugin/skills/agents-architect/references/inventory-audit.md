# Inventory And Audit

## Purpose

Establish repository facts and narrow the reading scope before designing instructions.

## Apply when

- Starting an AGENTS architecture task.
- Existing `AGENTS.md` files or `.agents/` content may already exist.
- Repository documentation must be audited before migration.

## Do not apply when

- The user provides a complete synthetic tree and asks only for review.
- The task is a narrow edit to an already-selected leaf.

## Required actions

- Confirm the current directory and whether the target has no Git repository,
  one unambiguous Git root, an unborn branch, or nested roots/worktrees.
  Inspect the host version, discovery settings, or a size limit such as Codex
  `project_doc_max_bytes` only when the task makes a version-sensitive loading
  or size claim.
- When more than one plausible Git root could own the requested files, stop and
  ask for the exact target instead of selecting a parent or nested root.
- When edits or Git evidence are in scope, record the branch/ref state and
  classify tracked, modified, staged, untracked, and ignored candidates
  separately. Do not describe an unborn branch as a normal branch with an
  empty history.
- Use the active host's current official documentation only when platform discovery
  behavior affects the outcome; otherwise avoid a network lookup. Record
  version-sensitive uncertainty instead of filling gaps with Axiom policy.
- Record unverified assumptions instead of treating them as facts.
- Start with metadata and references only.
- Collect locations of `AGENTS.md`, host-configured or host-discovered
  non-`AGENTS.md` instruction candidates, `.agents/`, and candidate project
  docs.
- Record candidate path, size, line count, and relevant Git state. Add
  modification time only when freshness affects the decision.
- Record leftover `.agents/.runtime/` or `.agents/.generated/` directories as
  migration candidates for the Git-metadata state directory in
  `memory-and-state.md`.
- Classify evidence as one of four kinds: live source, persistent rule, runtime
  state, or historical reference. Use current files/config as live source;
  active instruction sources or canonical docs as persistent rules; current
  Git/tool state
  as runtime state; and diffs, history, transcripts, or prior reports as
  historical references. Historical reference alone does not prove current
  behavior or completion.
- Classify an instruction source as current-session active only when the visible
  instruction context, a current session record, or a direct host loading check
  proves it. Filesystem presence alone proves only a discovery candidate; it
  does not prove that the current session loaded that content.
- Apply the parent skill's protected-metadata boundary when classifying the
  inventory. Record those surfaces as protected plugin or skill metadata,
  not routed rule leaves, unless the user explicitly scopes skill or plugin
  maintenance.
- Read document bodies in small batches only after metadata narrows scope.
- For large docs, inspect headings, tables of contents, summaries, or targeted sections first.
- For each scoped ignored instruction candidate, run
  `git check-ignore -v -- <exact-path>` or an equivalent exact owner query;
  separately resolve whether it is tracked. Report ignored/tracked state and
  the owning ignore source, line, and pattern.
- Read each scoped candidate directly before work and, if it could have
  changed, again afterward. A clean status or tracked diff cannot prove that an
  ignored or untracked instruction is absent, unchanged, or inactive.

## Host discovery boundaries

Hosts discover and load instruction sources differently. Determine the active host's behavior from its current documentation and observable state before making a loading claim. The dated host facts in `../../using-axiom/references/codex-host.md` and `../../using-axiom/references/claude-code-host.md` summarize how Codex and Claude Code build their instruction chains; they do not replace that check. Each directory contributes at most one host-recognized instruction source, a recognized non-`AGENTS.md` source may replace the same-directory `AGENTS.md` rather than add to it, and a visible host size limit is a truncation guard, not an authoring budget.

## Prohibited actions

- Do not recursively read all Markdown at the start.
- Do not read full logs or large source files for instruction design unless a targeted rule depends on them.
- Do not migrate, rewrite, or validate protected plugin or skill metadata as AGENTS routing content.
- Do not import unrelated historical notes into the durable instruction system.
- Do not create a runtime capsule during a strictly read-only task.

## Validation

Run a metadata inventory when possible using read-only commands that fit the user's operating system and available tools.

Confirm generated inventory output with an available parser only when you explicitly write structured output to disk.
