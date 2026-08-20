# Changelog

This file records notable changes to Axiom. Historical entries are based on
the repository's version tags and the commits they identify.

## Unreleased

## 0.7.1 - 2026-08-20

### Fixed

- Required a frozen non-executable Git process boundary before every
  `traceable-git-submit` command so target-controlled configuration, helpers,
  hooks, filters, transport commands, and ambient Git state cannot silently run.
- Distinguished read-only workflow rehearsal from an authorized isolated
  restore rehearsal, and kept that write separate from candidate preparation,
  promotion, complete execution, and cleanup.

## 0.7.0 - 2026-08-20

### Added

- Added `confirm-external-action` to bind consequential app actions to an exact
  actor, target, payload, disclosure, cost, count, and retry envelope before
  one execution and authoritative verification.

### Fixed

- Required literal argument vectors, validated refs and transports, opaque
  remote capture, and no-follow Git-metadata containment throughout
  `traceable-git-submit`.
- Made post-consolidation cleanup independently authorized and recoverable via
  a persisted `cleanupReady` state.
- Pinned every third-party GitHub Action to an immutable commit and added a
  publication guard against moving action references.

See [the v0.7.0 release notes](docs/releases/v0.7.0.md) for validation evidence
and known limits.

## 0.6.1 - 2026-08-18

### Fixed

- Limited Codex starter prompts to the three entries the host displays and
  made the AGENTS audit starter explicitly read-only.
- Anchored routing validation to the packaged front door and Skill
  descriptions, including every canonical `effective-instructions` mode.
- Repaired the agents-architect validation route to its sibling instruction
  document contract.
- Qualified host-controlled auto-update behavior and documented safe disable
  and removal workflows.

See [the v0.6.1 release notes](docs/releases/v0.6.1.md) for validation evidence
and known limits.

## 0.6.0 - 2026-08-18

### Added

- Added the explicitly user-triggered `effective-instructions:reconcile` and
  `effective-instructions:reconcile-preview` modes for comparing existing
  AGENTS guidance with current implementation.
- Added an atomized evidence ledger that separates claim kind, observed
  status, disposition, and write action before any rule is corrected, moved,
  or removed.

### Changed

- Made the live filesystem working tree the default reconciliation baseline,
  with staged divergence, unstaged, untracked, and material ignored content
  recorded separately from `HEAD`, named refs, and history.
- Required one coordinator, three independent read-only auditors, and one
  isolated non-coordinator writer after ledger freeze; incomplete role
  coverage now stops writes and is reported as `NOT-RUN`.
- Kept rollback, interrupted execution, compaction, and model or agent handoff
  as post-activation evidence rather than autonomous reconciliation triggers.
- Added focused routing and evidence scenarios for preview/apply boundaries,
  partial rollback, normative constraints, worker conflict, and active-chain
  authority.

See [the v0.6.0 release notes](docs/releases/v0.6.0.md) for validation evidence
and known limits.

## 0.5.1 - 2026-08-17

### Fixed

- Separated task-turn coverage, raw-output coverage, and unread required
  history so a compacted review cannot imply that unavailable tool output was
  recovered.
- Prevented superseded or narrowed proposals from being revived after
  compaction unless the user explicitly reauthorizes them.

### Changed

- Made current-run versus later-run activation explicit for durable
  `AGENTS.md` updates and required fresh-session loading claims to be marked
  verified, not run, or unavailable.
- Consolidated review-window and candidate-disposition ownership in the
  context-evidence reference instead of repeating it across update paths.
- Added a focused compaction regression scenario for task-context maintenance.

See [the v0.5.1 release notes](docs/releases/v0.5.1.md) for validation evidence
and known limits.

## 0.5.0 - 2026-08-15

### Added

- Added `review-axiom-task`, an explicitly triggered read-only retrospective
  for Axiom route choice, scope, authorization, actions, evidence, stops, and
  outcomes across host-visible task history.

### Changed

- Extended the shared router, public documentation, Codex interface metadata,
  and offline routing scenarios for task reviews without adding telemetry,
  persistent logs, background work, or new mutation authority.

See [the v0.5.0 release notes](docs/releases/v0.5.0.md) for validation evidence
and known limits.

## 0.4.2 - 2026-08-12

### Fixed

- Made a first `effective-instructions` or preview review cover the current
  task from its oldest available turn through the trigger instead of starting
  at the latest work phase or Skill activation point.
- Limited incremental review baselines to prior completed reviews that record
  their start, reviewed-through point, and candidate dispositions; ordinary
  AGENTS reads, narrow edits, and task completion no longer imply a baseline.
- Required task-history inspection to reach the established review-window
  boundary while keeping raw tool replay proportional to candidate decisions.
- Prevented newest-phase-only extraction from being reported as a complete task
  review and separated review coverage from the number of accepted updates.

See [the v0.4.2 release notes](docs/releases/v0.4.2.md) for validation evidence
and known limits.

## 0.4.1 - 2026-08-12

### Changed

- Extended AGENTS Architect task evidence to treat repeated source reads,
  history recovery, user corrections, and missing-route scans as signals for
  an instruction-maintenance review rather than automatic proof of a gap.
- Added explicit `instruction-gap`, `routing-gap`, `validation-gap`,
  `expected-live-verification`, and `one-off-code-defect` dispositions so
  durable guidance remains scoped and implementation defects stay in source
  or regression tests under separate authorization.
- Applied the retrieval-friction review to both `effective-instructions` and
  `effective-instructions:preview`, including required reporting of source
  checks that remain necessary.

See [the v0.4.1 release notes](docs/releases/v0.4.1.md) for validation evidence
and known limits.

## 0.4.0 - 2026-08-10

### Added

- Added `optimize-codex-usage`, an explicitly triggered workflow for reducing
  or diagnosing Codex credit, token, context, Skill/AGENTS/MCP-loading, tool,
  validation, and reporting overhead without weakening quality or safety.

### Changed

- Reduced the always-loaded `using-axiom` gate and moved explicit marketplace
  refresh detail to an on-demand reference.
- Replaced AGENTS Architect's forwarding indexes with direct one-hop reference
  routes and made inventory, scenarios, validation, and reporting proportional
  to the changed surface.
- Split direct history-preserving Git submission from checkpoint metadata and
  consolidation so publish/push requests load only their active phase.
- Shortened the reversible-change parent while retaining rollback,
  authorization, sensitive-data, and layered completion gates before mutation.
- Updated shared documentation, UI metadata, both platform wrappers, and
  publication validation for the five-skill source without changing the
  hook behavior.

See [the v0.4.0 release notes](docs/releases/v0.4.0.md) for validation evidence
and known limits.

## 0.3.1 - 2026-07-31

### Added

- Expanded public onboarding, architecture, examples, trust, compatibility,
  and release documentation.
- Added contributor guidance plus focused bug, feature, and pull-request
  intake templates.
- Added an offline publication validator for durable documentation, repository
  metadata, hook declarations, and packaged-skill shape.

### Changed

- Reorganized the public project introduction around installation, first-use
  verification, observable routing, and explicit non-goals.
- Extended the read-only repository guard workflow to run both distribution
  drift and publication checks without persisting checkout credentials.
- Synchronized the Codex and Claude Code manifests at version `0.3.1`.

See [the v0.3.1 release notes](docs/releases/v0.3.1.md) for validation evidence
and known limits.

## 0.3.0 - 2026-07-29

### Added

- Added the Claude Code plugin manifest, marketplace wrapper, and isolated
  `SessionStart` and `PreCompact` hooks.
- Added a standard-library distribution drift guard and a read-only GitHub
  Actions job that compares the checked-in skill tree with both platform
  wrappers and the README shared-skill list.

### Changed

- Kept Codex and Claude Code on one shared `skills/` source while separating
  their manifests, marketplaces, and hook definitions.
- Moved the Codex hook definition to `hooks/codex-hooks.json` and declared the
  Claude Code hook separately at `hooks/claude-hooks.json`.
- Synchronized both plugin manifests at version `0.3.0`.

See [the v0.3.0 release notes](docs/releases/v0.3.0.md) for evidence and known
limits.

## 0.2.1 - 2026-07-29

### Fixed

- Hardened `reversible-system-change` so rollback claims require current
  restore evidence, complete coverage, and freshness.
- Made the Codex session-start hook independently reviewable and codified
  foreground-only, explicitly requested updates.

### Changed

- Preserved the exact four-skill release shape and added a concrete routed
  workflow example to the README.

## 0.2.0 - 2026-07-29

### Added

- Added `reversible-system-change` with rollback and layered postcondition
  requirements.

### Changed

- Strengthened `agents-architect` with explicit instruction ownership,
  `AGENTS.md` write boundaries, and current Codex discovery semantics.
- Split `traceable-git-submit` into phase-specific references covering
  provenance, multi-target verification, consolidation, and recovery.
- Aligned routing, plugin metadata, and documentation with the four direct
  public skills.

## 0.1.1 - 2026-07-20

### Changed

- Reorganized `agents-architect` internals into on-demand references.
- Added checkpoint-provenance safeguards to `traceable-git-submit`.
- Documented host-controlled marketplace refreshes and explicit update
  behavior.

## 0.1.0 - 2026-07-20

### Added

- Created the initial Codex plugin distribution with its manifest, local
  marketplace entry, session-start routing hook, and public README.
- Added the initial `using-axiom`, `agents-architect`, and
  `traceable-git-submit` packaged skills.
