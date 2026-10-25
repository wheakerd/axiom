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

Hosts discover and load instruction sources differently. Determine the active
host's behavior from its current documentation and observable state before
making a loading claim. The models below summarize Codex and Claude Code; they
do not replace that check.

### Codex

- Codex builds the instruction chain once per run or TUI session. A new run or
  session rebuilds it; later filesystem or configuration changes do not prove
  that the current chain changed.
- The chain may include host-recognized global instruction sources before
  repository guidance.
- Project discovery walks from project root to current working directory. When
  no project root is found, Codex checks only the current directory.
- Each directory contributes at most one non-empty host-recognized instruction
  source. Codex skips empty sources.
- Codex applies its host-defined same-directory selection order before adding
  that directory. A recognized non-`AGENTS.md` source may replace the
  same-directory `AGENTS.md`; it is not additive.
- Project sources are concatenated from root toward the current directory, so
  closer discovered guidance loads later than broader guidance.
- Codex stops adding project guidance when the combined chain reaches the
  visible `project_doc_max_bytes` limit. That limit is a platform truncation
  guard, not Axiom's authoring budget.
- Ordinary Markdown files under `.agents/` are not recursively auto-loaded.
- Do not assume generic include syntax or recursive imports.
- User instructions outrank persistent repository instructions.

### Claude Code

- Claude Code loads instruction files at session start: a managed policy file,
  the user's `~/.claude/CLAUDE.md`, and every `CLAUDE.md` and `CLAUDE.local.md`
  in the working directory and the directories above it. A project may keep
  its file at `.claude/CLAUDE.md`.
- Discovered files are concatenated rather than replaced. Directory content is
  ordered from the filesystem root down to the working directory, so closer
  guidance loads later.
- Subdirectory instruction files load on demand, when Claude works with a file
  in that subdirectory. Their presence alone does not prove that they loaded.
- By default, from v2.1.277, Claude Code reads `AGENTS.md` and
  `.claude/AGENTS.md` only when no `CLAUDE.md`, `.claude/CLAUDE.md`, or
  `CLAUDE.local.md` exists in the working directory or above it. Its
  **Project instructions** setting can load both, only `CLAUDE.md`, or only
  managed instructions. It never reads `AGENTS.override.md`,
  `AGENTS.local.md`, or files under `.agents/`.
- `@path` imports expand up to four hops and resolve from the importing file.
  Imports from outside the working directory need approval.
- `.claude/rules/` files without `paths` frontmatter load at session start;
  path-scoped rules load when Claude works with matching files.
- `claudeMdExcludes` can skip discovered files. Directories added with
  `--add-dir` contribute instruction files only when the host is configured to
  load them.
- After compaction, Claude Code rereads the project-root `CLAUDE.md`; nested
  files and path-scoped rules load again on demand.
- `/context` lists the instruction files the session loaded under
  **Memory files**; use it as the direct loading check. `/memory` also lists
  `CLAUDE.md` locations that do not exist yet.

## Prohibited actions

- Do not recursively read all Markdown at the start.
- Do not read full logs or large source files for instruction design unless a targeted rule depends on them.
- Do not migrate, rewrite, or validate protected plugin or skill metadata as AGENTS routing content.
- Do not import unrelated historical notes into the durable instruction system.
- Do not create a runtime capsule during a strictly read-only task.

## Validation

Run a metadata inventory when possible using read-only commands that fit the user's operating system and available tools.

Confirm generated inventory output with an available parser only when you explicitly write structured output to disk.
