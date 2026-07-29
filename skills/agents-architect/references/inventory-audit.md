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

- Confirm current working directory, Codex version, and visible
  `project_doc_max_bytes`. Determine whether the target has no Git repository,
  one unambiguous Git root, an unborn branch, or nested Git roots/worktrees.
- When more than one plausible Git root could own the requested files, stop and
  ask for the exact target instead of selecting a parent or nested root.
- When Git exists, record branch/ref state and classify tracked, modified,
  staged, untracked, and ignored candidates separately. Do not describe an
  unborn branch as a normal branch with an empty history.
- Use the official Codex manual as the current source for platform discovery
  behavior, and record version-sensitive uncertainty instead of filling gaps
  with Axiom policy.
- Record unverified assumptions instead of treating them as facts.
- Start with metadata and references only.
- Collect locations of `AGENTS.md`, host-configured or host-discovered
  non-`AGENTS.md` instruction candidates, `.agents/`, and candidate project
  docs.
- Record candidate doc path, size, line count, Git tracking state, status, and modification time.
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
  inventory. Record those surfaces as protected Codex plugin or skill metadata,
  not routed rule leaves, unless the user explicitly scopes skill or plugin
  maintenance.
- Read document bodies in small batches only after metadata narrows scope.
- For large docs, inspect headings, tables of contents, summaries, or targeted sections first.
- For each ignored instruction candidate, run
  `git check-ignore -v -- <exact-path>` or an equivalent exact owner query;
  separately resolve whether it is tracked. Report ignored/tracked state and
  the owning ignore source, line, and pattern.
- Read every such candidate directly before work and again afterward, then
  compare the actual content. A clean status or tracked diff cannot prove that
  an ignored or untracked instruction is absent, unchanged, or inactive.

## Codex behavior boundaries

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

## Prohibited actions

- Do not recursively read all Markdown at the start.
- Do not read full logs or large source files for instruction design unless a targeted rule depends on them.
- Do not migrate, rewrite, or validate protected plugin or skill metadata as AGENTS routing content.
- Do not import unrelated historical notes into the durable instruction system.
- Do not create a runtime capsule during a strictly read-only task.

## Validation

Run a metadata inventory when possible using read-only commands that fit the user's operating system and available tools.

Confirm generated inventory output with an available parser only when you explicitly write structured output to disk.
