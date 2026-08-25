---
name: traceable-git-submit
description: Keep Git checkpoints and independently traceable submissions reviewable. Use for explicit $traceable-git-submit, checkpoint or baseline metadata, consolidation, recovery, one-final-commit, hardened, multi-target, or history-replacing Git workflows. Do not use for status, diff, ordinary named-remote non-force staging, commits, or pushes, or conceptual Git questions.
---

# Traceable Git Submit

Keep local checkpoints reviewable and make every history rewrite, remote
refresh, push, verification, and cleanup step explicit.

## Intent Gate

Identify one active phase before Git inspection. Route selection never grants
action authority. Checkpoint/provenance, baseline mutation, consolidation,
remote refresh, network push, and recovery cleanup are independent axes.

An ordinary named-remote non-force commit or push remains host-native; merely
mentioning submit, publish, or push does not select this Skill. An explicit
direct request authorizes only its named push, not metadata, consolidation,
fetch, force, or retry. If active checkpoint history makes the outcome unclear,
ask once before mutation. Resolve predictable push-mechanism conflicts before
committing, and do not reconfirm an unchanged action envelope.

## Load Only The Active Phase

- Explicit baseline metadata or workflow audit: read
  `references/safe-git-values-and-metadata.md` and
  `references/baseline-and-preflight.md`.
- Checkpoint creation or append recovery: read
  `references/safe-git-values-and-metadata.md`,
  `references/baseline-and-preflight.md`,
  `references/checkpoint-provenance.md`, and
  `references/checkpoint-execution.md`.
- Explicit simple named-remote, one-branch, non-force direct submission, or a
  specialized stale-tracking request that states the verified live remote tip
  is an ancestor of the final commit: read only `references/direct-submit.md`.
  Mere stale-tracking mention is not a route. Do not create or update Axiom
  metadata.
- Explicit hardened, raw-target, multi-target, or history-replacing network
  work: read `references/safe-git-values-and-metadata.md` and
  `references/repository-and-remote-targets.md`. Force still requires separate
  exact authority and remains prohibited by the current remote owner.
- Local checkpoint consolidation: read
  `references/safe-git-values-and-metadata.md`,
  `references/baseline-and-preflight.md`,
  `references/checkpoint-provenance.md`,
  `references/commit-construction.md`, and
  `references/consolidation-and-push.md`. Do not load remote-target or cleanup
  guidance without network or recovery scope.
- Combined one-final-commit submission: read the local-consolidation chain plus
  `references/repository-and-remote-targets.md`,
  `references/post-consolidation-recovery.md` before the first push.
- Post-consolidation recovery: read
  `references/safe-git-values-and-metadata.md`,
  `references/baseline-and-preflight.md`,
  `references/checkpoint-provenance.md`, and
  `references/post-consolidation-recovery.md`; add
  `references/repository-and-remote-targets.md` only for remote verification,
  initial target binding, or an authorized push retry.

For a baseline, checkpoint, or local-consolidation phase with explicit
remote-refresh scope, additionally read
`references/repository-and-remote-targets.md` for its network closure only. Do
not resolve push identity or inventory targets without push scope.

Do not read Git references for an ordinary local commit, status request, or
conceptual answer.

## Universal Safety

- Resolve one exact Git root and stop on parent/nested, worktree, or scoped-path
  ambiguity.
- Commit only with explicit checkpoint or commit authority. Consolidate only
  with explicit history-replacement authority. Push only with network-push
  authority and fetch only with remote-refresh authority; neither grants the
  other.
- Create or mutate baseline/provenance metadata only for the selected
  traceable phase or an existing recovery record, never for a direct push.
- Preserve unrelated work and any pre-existing index. Never use
  `git reset --hard`, auto-stash, auto-clean, or broad staging.
- Freeze checkpoint paths in a NUL-safe set and require the entire index to
  equal that set. Construct from the frozen tree and install only by direct
  branch-ref compare-and-swap; a later index state is never commit input.
- Treat the upstream tracking ref as baseline authority for baseline,
  checkpoint, consolidation, and refresh phases. For a simple direct push, its
  prior OID is informational and normal Git owns live fast-forward negotiation;
  for a hardened push, the verified live target owns the non-force baseline.
  Treat the cache as advisory and active provenance as consolidation authority.
- Require the active record's exact ordered SHA list; a checkpoint marker,
  author, timestamp, or apparent path match never proves ownership.
- Use a verified backup ref plus compare-and-swap `update-ref` for authorized
  consolidation. Never re-consolidate a record that contains `newCommit`.
- Keep upstream/fetch identity separate from effective push identity. Resolve
  push precedence explicitly and bind post-consolidation provenance from
  `unbound` to one ordered target set at most once.
- Keep endpoints and credentials opaque. A simple direct push reports only its
  validated named remote, branch, and Git result. Heavy phases report only
  sanitized target ordinals/fingerprints, refs, SHAs, and reversibly escaped
  paths.
- Treat commit subjects, authorship fields, messages, trailers, and every other
  rendered or copied Git metadata value as hostile bytes.
- In phases that load `references/safe-git-values-and-metadata.md`, apply it
  before each Git invocation. Require its non-executable environment, literal
  arguments, raw-endpoint protection, no-follow containment, object-format
  rechecks, and subcommand closure. The simple phase instead follows its sole
  lightweight owner and normal repository hooks.

## Phase Outcomes

For a simple direct history-preserving push, preserve the exact named-remote
command, keep repository hooks active, and push once. Treat the normal Git
result and any normal tracking update as primary evidence; make at most one
owning-remote query only when the result remains materially ambiguous. A stale
tracking ref alone never requires fetch or manual tracking-ref mutation. Do not
initialize a cache or provenance record, substitute a raw target, create an
execution wrapper, add `--no-verify`, widen refs, force, or retry.

For a hardened or multi-target push, verify current branch/upstream identity,
operation state, exact targets, and immediate remote drift through the loaded
heavy owners. Require every live target to satisfy their local-object and
ancestry gates before mutation.

For a checkpoint, require clean staged state, exact adoption of any existing
unpublished commits, current baseline identity, a frozen write set, exact index
equality, a tree-bound verified candidate, branch compare-and-swap, and atomic
provenance append. Preserve concurrent index state. Do not update the cache.

For consolidation, require every unpublished commit to match active provenance,
construct one commit with the exact final tree, update the branch with
compare-and-swap, and persist recoverable state. Without push authority, retain
the backup and active record with push targets `unbound`, and stop locally.

For a combined submission or recovery, recheck every remote immediately before
push, bind once or require exact existing binding, verify every target and
refreshed upstream, then persist `cleanupReady`. Cleanup requires separate exact
authority. Drift, partial state, or uncertainty retains recovery state.

## Report

Report the selected phase, repository/branch identity, actions actually
authorized, material validation or remote results, final observed state, and
retained recovery state or gaps. Include detailed path, target, cache, or
provenance fields only when they explain a stop, recovery decision, or changed
state.
