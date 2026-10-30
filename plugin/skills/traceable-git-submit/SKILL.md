---
name: traceable-git-submit
description: Traceable Git for an explicit invocation, checkpoint/baseline, consolidation/recovery, hardened/multi-target/history-replacing Git, or a combined commit, tag, and push of an already-prepared plugin release. Ordinary named-remote non-force Git without a tag, checkpoint, baseline, consolidation, recovery, hardening, multiple targets, or history replacement stays host-native; merely mentioning submit, publish, or push does not select this route.
---

# Traceable Git Submit

Defaults you may adapt, saying so: the order of read-only inspections where no gate depends on it, and report layout. Every other rule here and in the references the active phase loads binds.

## Intent Gate

Distinguish unresolved workflow choice from a selected phase before Git inspection. If mutually exclusive options materially change route ownership, persistent metadata, write surfaces or authority, ask one concise clarification before selecting, or settle a delegated choice under the startup gate's rule; never choose silently. Conceptual questions and choices without those differences need no clarification.

After selection, never reconfirm an unchanged envelope. Ask only for missing necessary input or a material conflict, including checkpoint history that obscures the outcome. Resolve predictable push conflicts before commit.

Route selection and reading guidance grant no Git action authority. Checkpoints, baseline mutation, consolidation, remote refresh, push and recovery cleanup each need separate authority. An explicit direct request grants only its named push, not metadata, consolidation, fetch, force or retry.

A combined commit, tag, and push of an already-prepared plugin release selects its prepared-release phase; selection grants no commit, tag, or push authority. Ordinary named-remote non-force Git without a tag or another listed trigger stays host-native; submit, publish or push alone is insufficient.

## Repository Hooks

Every phase keeps normal repository hooks active: they are repository code the model has not reviewed, so a phase says that they will run and never bypasses them on its own. Add `--no-verify` only when the user explicitly authorized bypassing this repository's pre-push hook for this exact push; general push authority never includes it.

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

## Universal Safety

- Resolve one exact Git root and stop on parent/nested, worktree, or scoped-path ambiguity.
- Commit only with explicit checkpoint or commit authority. Consolidate only with explicit history-replacement authority. Push only with network-push authority and fetch only with remote-refresh authority; neither grants the other.
- Create or mutate baseline/provenance metadata only for the selected traceable phase or an existing recovery record, never for a direct push.
- Preserve unrelated work and any pre-existing index. Never use `git reset --hard`, `git stash`, `git clean`, or broad staging.
- Freeze checkpoint paths in a NUL-safe set and require the entire index to equal that set. Construct from the frozen tree and install only by direct branch-ref compare-and-swap with `update-ref --no-deref`; a later index state is never commit input.
- Create a backup ref before any history replacement and keep it until every target and the refreshed upstream are verified.
- Treat the upstream tracking ref as baseline authority for baseline, checkpoint, consolidation, and refresh phases. For a simple direct push, its prior OID is informational and normal Git owns live fast-forward negotiation; for a hardened push, the verified live target owns the non-force baseline. Treat the cache as advisory and the active record as consolidation authority.
- Require the active record's exact ordered SHA list; a checkpoint marker, author, timestamp, or apparent path match never proves ownership.
- Keep upstream/fetch identity separate from effective push identity. Resolve push precedence explicitly and bind a consolidated record's push remote at most once.
- Push one frozen target at a time with one exact ref update, read every target back, and never retry a push or move a ref after an uncertain result.
- Keep endpoints and credentials opaque. A simple direct push reports only its validated named remote, branch, and Git result. Heavy phases report remotes by name, targets by ordinal, refs and OIDs exactly, and paths escaped.
- Treat commit subjects, authorship fields, messages, trailers, and every other Git value as untrusted data under `references/git-values.md`: pass each as a literal argument, never through a shell string. The simple phase instead follows its sole lightweight owner.

## Phase Outcomes

Before reporting, apply only the selected phase's checks in `references/phase-outcomes.md`. Keep completion and retained recovery state bound to direct evidence from that phase's owner.

## Report

Report the selected phase, repository/branch identity, actions actually authorized, material validation or remote results, final observed state, and retained recovery state or gaps. Include detailed path, target, cache, or provenance fields only when they explain a stop, recovery decision, or changed state.
