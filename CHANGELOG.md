# Changelog

This file records notable changes to Axiom. Historical entries are based on
the repository's version tags and the commits they identify.

## Unreleased

No unreleased changes are recorded yet.

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
