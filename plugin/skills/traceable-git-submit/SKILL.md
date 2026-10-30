---
name: traceable-git-submit
description: Traceable Git for an explicit invocation, checkpoint/baseline, consolidation/recovery, hardened/multi-target/history-replacing Git, or a combined commit, tag, and push of an already-prepared plugin release. Ordinary named-remote non-force Git without a tag, checkpoint, baseline, consolidation, recovery, hardening, multiple targets, or history replacement stays host-native; merely mentioning submit, publish, or push does not select this route.
---

# Traceable Git Submit

Make Git submission traceable with plain Git: frozen inputs, compare-and-swap installs, one push per target, and read-back verification. The references own each phase's procedure; this file owns the rules every phase shares.

## Invariants

These invariants bind in every phase, including the references that phase loads. Everything else in this skill is a default you may adapt, saying so when you depart.

1. **Separate authority per action.** Route selection and reading guidance grant no Git action authority. Checkpoints, baseline mutation, consolidation, remote refresh, push, and recovery cleanup each need separate authority, and an explicit direct request grants only its named push, not metadata, consolidation, fetch, force, or retry.
2. **Hooks run; bypass only on exact authority.** Every phase keeps normal repository hooks active and says that they will run. Add `--no-verify` only when the user explicitly authorized bypassing this repository's pre-push hook for this exact push; general push authority never includes it.
3. **Frozen inputs, compare-and-swap installs.** Freeze checkpoint paths in a NUL-safe set, require the entire index to equal that set, construct from the frozen tree, and install only by direct branch-ref compare-and-swap with `update-ref --no-deref`; a later index state is never commit input.
4. **History is protected.** Create a backup ref before any history replacement and keep it until every target and the refreshed upstream are verified. Never use `git reset --hard`, `git stash`, `git clean`, or broad staging; preserve unrelated work and any pre-existing index.
5. **One push per target, no retry.** Push one frozen target at a time with one exact ref update, read every target back, and never retry a push or move a ref after an uncertain result.
6. **Values are untrusted.** Treat commit subjects, authorship fields, messages, trailers, refs, paths, and every other Git value as untrusted data under `references/git-values.md`: pass each as a literal argument, never through a shell string, and keep endpoints and credentials opaque.

## Intent Gate

Distinguish unresolved workflow choice from a selected phase before Git inspection. If mutually exclusive options materially change route ownership, persistent metadata, write surfaces or authority, ask one concise clarification before selecting, or settle a delegated choice under the startup gate's rule; never choose silently. Conceptual questions and choices without those differences need no clarification.

After selection, never reconfirm an unchanged envelope. Ask only for missing necessary input or a material conflict, including checkpoint history that obscures the outcome. Resolve predictable push conflicts before commit.

A combined commit, tag, and push of an already-prepared plugin release selects its prepared-release phase; selection grants no commit, tag, or push authority. Ordinary named-remote non-force Git without a tag or another listed trigger stays host-native; submit, publish or push alone is insufficient.

## Load Only The Active Phase

- Explicit baseline metadata or workflow audit: read `references/git-values.md` and `references/baseline-and-preflight.md`.
- Checkpoint creation or append recovery: read those two and `references/checkpoint.md`.
- Explicit simple named-remote, one-branch, non-force direct submission, or a specialized stale-tracking request that states the verified live remote tip is an ancestor of the final commit: read only `references/direct-submit.md`. Mere stale-tracking mention is not a route. Do not create or update Axiom metadata.
- A combined prepared-plugin commit/tag/push: read `references/git-values.md`, `references/remote-targets.md`, and `references/prepared-release-submit.md`.
- Explicit hardened, raw-target, multi-target, or history-replacing network work: read `references/git-values.md` and `references/remote-targets.md`. Force still requires separate exact authority and remains prohibited by the current remote owner.
- Local checkpoint consolidation: read `references/git-values.md`, `references/baseline-and-preflight.md`, `references/checkpoint.md`, and `references/consolidation.md`. Do not load remote-target guidance without network or recovery scope.
- Combined one-final-commit submission: read the local-consolidation set plus `references/remote-targets.md` before the first push.
- Post-consolidation recovery: read `references/git-values.md`, `references/baseline-and-preflight.md`, `references/checkpoint.md`, and `references/remote-targets.md`.

For a baseline, checkpoint, or local-consolidation phase with explicit remote-refresh scope, additionally read the refresh section of `references/consolidation.md`. Do not resolve push identity or inventory targets without push scope. Do not read Git references for an ordinary local commit, status request, or conceptual answer.

## Working Rules

- Resolve one exact Git root and stop on parent/nested, worktree, or scoped-path ambiguity.
- Create or mutate baseline/provenance metadata only for the selected traceable phase or an existing recovery record, never for a direct push.
- Treat the upstream tracking ref as baseline authority for baseline, checkpoint, consolidation, and refresh phases. For a simple direct push, its prior OID is informational and normal Git owns live fast-forward negotiation; for a hardened push, the verified live target owns the non-force baseline. Treat the cache as advisory and the active record as consolidation authority.
- Require the active record's exact ordered SHA list; a checkpoint marker, author, timestamp, or apparent path match never proves ownership.
- Keep upstream/fetch identity separate from effective push identity. Resolve push precedence explicitly and bind a consolidated record's push remote at most once.
- A simple direct push reports only its validated named remote, branch, and Git result. Heavy phases report remotes by name, targets by ordinal, refs and OIDs exactly, and paths escaped. The simple phase follows its sole lightweight owner for value handling.

## Phase Outcomes

Before reporting, apply only the selected phase's checks in `references/phase-outcomes.md`. Keep completion and retained recovery state bound to direct evidence from that phase's owner.

## Report

Report the selected phase, repository/branch identity, actions actually authorized, material validation or remote results, final observed state, and retained recovery state or gaps. Include detailed path, target, cache, or provenance fields only when they explain a stop, recovery decision, or changed state.
