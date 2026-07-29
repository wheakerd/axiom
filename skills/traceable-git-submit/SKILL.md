---
name: traceable-git-submit
description: Keep Git work traceable with local checkpoint commits and publish one clean consolidated commit. Use when the user asks to enable or run a traceable Git workflow, create local checkpoint commits, cache the last remote-push baseline in Git metadata, compare unpublished commits against upstream, consolidate authorized checkpoint commits, submit/publish/push through a one-final-commit workflow, or recover/audit a working tree before that workflow pushes.
---

# Traceable Git Submit

Keep local work reviewable through authorized checkpoint commits while
publishing a single clean commit only when the user explicitly asks to submit,
publish, or push.

## Load Policy

Load only the references required for the active phase, and read them before
changing Git state:

- Checkpoint work: read `references/repository-and-remote-targets.md`,
  `references/baseline-and-preflight.md`,
  `references/checkpoint-execution.md`, and
  `references/checkpoint-provenance.md`.
- Normal submit, publish, or push: read
  `references/repository-and-remote-targets.md`,
  `references/baseline-and-preflight.md`,
  `references/checkpoint-provenance.md`,
  `references/commit-construction.md`, and
  `references/consolidation-and-push.md`. Before push or cleanup, also read
  `references/post-consolidation-recovery.md`.
- Post-consolidation recovery: read
  `references/repository-and-remote-targets.md`,
  `references/baseline-and-preflight.md`,
  `references/checkpoint-provenance.md`, and
  `references/post-consolidation-recovery.md` first. Load
  `references/consolidation-and-push.md` only for an authorized push retry.

Do not load them for a conceptual answer that will not inspect a repository.

## Safety Rules

- Do not commit unless the user asks for a commit or authorizes the traceable
  checkpoint workflow for the current task or session.
- Do not push unless the user explicitly asks to submit, publish, or push.
- Do not use `git reset --hard`.
- Do not stage unrelated user changes.
- Freeze authorized paths before staging; use NUL-safe set comparison and
  require the entire index to be exactly that set. Stop on any pre-existing,
  extra, or missing staged path without altering unrelated index state.
- Keep baseline and provenance in Git-resolved metadata paths, never the index,
  commits, worktree, or installed plugin directory.
- Do not treat `Axiom-checkpoint: true` as sufficient proof that a commit
  belongs to the current authorized workflow. Require the active provenance
  record and its exact ordered SHA list. The marker is required only for
  workflow-created checkpoints; an exact user-authorized `adoptedShas` entry is
  an independent allowed provenance path.
- Do not rewrite, squash, drop, or adopt unclear, non-workflow, pushed, or
  user-authored commits without exact confirmation.
- If repository instructions define a different Git policy, follow the
  higher-priority instructions and report the difference.

## Workflow Contract

- Treat `@{u}` as the authoritative remote-tracking baseline.
- Resolve branch, upstream, remote, merge ref, operation paths, cache, and
  provenance from Git; do not infer or hand-build them.
- The baseline cache is advisory; active provenance is consolidation authority.
- Stop on detached HEAD, an unborn branch, a missing upstream or remote,
  divergence, an in-progress Git operation, a stale identity or baseline, or
  unpublished commits not covered by the authorized provenance record.
- Resolve one exact Git root; stop on cross-root paths or parent/nested ambiguity.
- For submit, push, or post-consolidation recovery only, inspect every push
  target configured for the resolved remote. More than one requires explicit
  authorization of the complete fingerprint set and its non-atomic risk. This
  gate does not apply to checkpoint-only work, including local upstream `.`.
- Use only `commit-tree` plus compare-and-swap `update-ref` for consolidation.
  Preserve the exact final tree and keep a verified backup ref until remote
  verification and cleanup-state persistence make its deletion safe.
- Never re-consolidate a record that already contains `newCommit`.

## Checkpoint Route

For an authorized checkpoint workflow:

1. Read the checkpoint references selected above.
2. Resolve the exact repository and run applicable read-only Git preflight.
3. Before creating a new active record, enumerate existing unpublished commits
   and stop unless the user explicitly adopts the exact ordered full-SHA list.
   An existing record follows its own exact identity and list validation; do
   not re-adopt its recorded commits.
4. Only then initialize or validate baseline cache and active provenance.
5. Freeze and report the authorized write set plus current staged, unstaged,
   and untracked paths.
6. Validate, stage only intentional paths, and prove exact index equality.
7. Create and verify one checkpoint commit, then atomically append that exact
   SHA. If the append fails, use only the bounded recovery gate in
   `references/checkpoint-execution.md`.

Do not update the baseline cache after local checkpoints. It records the last
verified remote push, not local progress.

## Submit Route

When the user explicitly asks to submit, publish, or push:

1. Read all references selected for the matching normal or recovery path.
2. Run preflight, fetch the branch remote when available, and refresh facts.
3. Resolve and freeze the complete push-target fingerprint set. Stop on
   multiple targets until the user explicitly authorizes that exact set and
   acknowledges that sequential targets cannot be updated atomically.
4. Select exactly one path from the active provenance record:
   - Without `newCommit`: require its ordered SHA list to exactly equal every
     unpublished commit, then use the normal consolidation path.
   - With `newCommit`: use only the post-consolidation recovery gate. Do not
     create checkpoints, create another final commit, or consolidate again.
5. Validate again before the authorized push or verified cleanup.
6. Immediately before the first push, require every frozen target's current
   `mergeRef` to equal `baselineSha`; any drift means zero pushes. After push,
   require direct SHA verification for every authorized target.
7. Follow `references/post-consolidation-recovery.md`; never delete the backup
   before recoverable cleanup state is persisted.

## Reporting

Report observed repository/branch/upstream identity, baseline and HEAD state,
provenance/checkpoint identity, authorized write and target sets, validation,
consolidation, push, verification, cleanup, and stop state when present. Show
endpoints only as ordinal/fingerprint plus ref/SHA; never expose URLs,
credentials, usernames, or private endpoints. Leave recovery state visible on
a stop. Render every path with JSON-string, Git C-style, or equivalent
reversible escaping; never emit raw control characters or newlines.
