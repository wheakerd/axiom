---
name: agent-plugin-architect
description: Design, initialize, audit, migrate, maintain, or evaluate a packaged Codex or Claude Code plugin's shared Skills, route ownership, manifests, marketplace wrappers, hooks, and version-bound compatibility evidence. Use only for explicit packaged agent-plugin architecture work. Do not use for repository-local AGENTS.md or .agents/skills systems, ordinary source-code or documentation work merely because it is in a plugin repository, host installation, publication, deployment, or Git submission.
---

# Agent Plugin Architect

Design or audit the smallest coherent packaged-plugin control plane for Codex
and Claude Code. Treat Codex as the first-class target and preserve a single
shared Skill tree when both hosts can discover it without weakening Codex.

## Route The Work

1. Confirm that the request explicitly concerns packaged agent-plugin
   architecture. Repo-local `AGENTS.md` or `.agents/skills` work belongs to
   `agents-architect`; ordinary plugin code or documentation has no Axiom
   route solely because it lives in a plugin repository.
2. Inventory the package before editing. Read
   `references/package-inventory.md`.
3. For a read-only audit of one packaged release candidate, read
   `references/release-readiness.md`. It classifies impact, version and runtime
   identity, local and remote evidence, and the one next decision, then stops
   before every mutation phase.
4. Define route ownership and trigger boundaries with
   `references/route-and-trigger-contracts.md`.
5. For shared Skill structure and direct discovery, read
   `references/packaged-skill-architecture.md`.
6. For startup hooks, untrusted content, credentials, or runtime effects, read
   `references/hooks-and-trust-boundaries.md`.
7. For manifests, wrappers, and Codex/Claude Code parity, read
   `references/cross-host-packaging.md`.
8. For routing cases, context cost, or host observations, read
   `references/evaluation-and-evidence.md`.
9. Before completion, read `references/validation-reporting.md`.

Load only references needed for the active phase. A request may compose this
route with at most one other Axiom route when both contracts are independently
necessary. An explicit usage-cost goal may add `optimize-codex-usage`;
retrospective review may add `review-axiom-task`. Git submission, installation,
publication, deployment, and consequential external effects remain separate
active phases and select their owning route instead of inheriting authority
from this Skill.

## Deliverable

Return the package inventory, route and trust decisions, changed surfaces,
validation evidence, compatibility class, and every host or lifecycle check
that is `NOT-RUN` or `UNAVAILABLE`. File presence and static parity are not
host execution evidence.
