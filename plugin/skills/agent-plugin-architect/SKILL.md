---
name: agent-plugin-architect
description: Design, audit, or migrate a packaged Codex or Claude Code plugin's architecture across shared Skills, routes, manifests, hooks, and compatibility evidence. Use only for explicit packaged agent-plugin architecture work. Do not use for evaluating or reviewing an individual Skill or Skill proposal, repository-local AGENTS.md, .agents/skills, or .claude/skills systems, host installation, publication, deployment, or Git submission.
---

# Agent Plugin Architect

Design or audit the smallest coherent packaged-plugin control plane for Codex and Claude Code. Keep each host's experience native, and keep one shared Skill tree when both hosts can discover it without weakening either host.

## Invariants

These invariants bind in every phase, including the references that phase loads. Everything else in this skill is a default you may adapt, saying so when you depart.

1. **Architecture only.** Confirm that the selected request explicitly concerns packaged agent-plugin architecture. Repo-local `AGENTS.md`, `.agents/skills`, or `.claude/skills` work belongs to `agents-architect`, and ordinary plugin code or documentation has no Axiom route solely because it lives in a plugin repository.
2. **No silent workflow choice.** When mutually exclusive workflows differ materially in route ownership, write surfaces, persistent metadata or authority, ask one clear question and keep the workflow unselected until the user chooses, or settle it under the startup gate's delegated-choice rule.
3. **An audit stays read-only.** A release-readiness audit classifies impact, identity, evidence, and the one next decision, then stops before every mutation phase.
4. **Effects keep their owners.** Git submission, installation, publication, deployment, and consequential external effects remain separate active phases that select their owning route instead of inheriting authority from this skill.
5. **Host evidence is observed or `NOT-RUN`.** File presence and static parity are not host execution evidence; report every host or lifecycle check that is `NOT-RUN` or `UNAVAILABLE`.

## Route The Work

1. Restate each option's original end goal and explain permission limits separately. Preparation, review, planning or preflight may support a chosen goal but cannot replace it without the user's choice. Outside a delegated choice, read-only authority, lower risk, lighter work or current feasibility never justify defaulting to one option. Explicit installation stays with its owner; explain unavailable authority without substituting an architecture audit. After selection, do not reconfirm unchanged conditions; ask only for necessary missing input or a material conflict.
2. Inventory the package before editing. Read `references/package-inventory.md`.
3. For a read-only audit of one packaged release candidate, read `references/release-readiness.md`.
4. Define route ownership and trigger boundaries with `references/route-and-trigger-contracts.md`.
5. For shared Skill structure and direct discovery, read `references/packaged-skill-architecture.md`.
6. For startup hooks, untrusted content, credentials, or runtime effects, read `references/hooks-and-trust-boundaries.md`.
7. For manifests, wrappers, and Codex/Claude Code parity, read `references/cross-host-packaging.md`.
8. For routing cases, context cost, or host observations, read `references/evaluation-and-evidence.md`.
9. Before completion, read `references/validation-reporting.md`.

Load only references needed for the active phase. A request may compose this route with at most one other Axiom route when both contracts are independently necessary. An explicit usage-cost goal may add `optimize-agent-usage`; retrospective review may add `review-axiom-task`. Git submission, installation, publication, deployment, and consequential external effects remain separate active phases, as invariant 4 states.

## Deliverable

Return the package inventory, route and trust decisions, changed surfaces, validation evidence, compatibility class, and every host or lifecycle check that is `NOT-RUN` or `UNAVAILABLE`.
