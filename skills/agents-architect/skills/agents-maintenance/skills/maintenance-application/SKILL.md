---
name: maintenance-application
description: Use when AGENTS Maintenance needs to apply durable update gates, choose canonical homes, reorganize existing AGENTS docs, validate route changes, and report results.
---

# Maintenance Application

## Purpose

Apply approved durable AGENTS updates to the smallest correct surface.

## Apply when

- Evidence has produced candidate durable AGENTS updates.
- Authorization is satisfied or the task is read-only preview.
- Existing AGENTS content must be patched, split, migrated, or validated.

## Do not apply when

- Candidate updates still need context extraction.
- Non-Axiom or unclear-provenance AGENTS edits are not authorized.
- The only target is a repo-local skill; use `../repo-local-skills/SKILL.md` first.

## Durable update gate

Write only candidates with:

- Persistent future reuse.
- Clear path, task, domain, risk, workflow, or skill scope.
- Concrete agent action, prohibition, routing condition, or validation step.
- Verifiable evidence from code, config, tests, commands, authoritative docs, or repeated task history.
- Target-project specificity rather than restating Axiom packaged skill protocol.
- One canonical home.
- Correct abstraction level.
- Positive context value after active-set size cost.
- No secrets, credentials, personal data, raw transcripts, or transient logs.

Reject or report temporary, speculative, duplicated, too broad, unsupported, or human-doc-only candidates.

## Canonical homes

- Root `AGENTS.md`: true global constraints, priority, routing entry points, and minimum verification.
- `.agents/**`: routed indexes, leaves, overlays, and temporary runtime capsules.
- `.agents/skills/<skill-name>/SKILL.md`: repo-local skills for repeatable repository workflows only when explicitly requested or already part of the target repository design.
- Project docs: human source-of-truth facts that are not agent-executable guidance.
- Installed Axiom plugin: Axiom workflow triggers, packaged skill rules, internal routes, validation protocols, and reporting formats.

## Existing AGENTS reorganization

- For small approved updates, patch the smallest canonical file.
- Sink each approved update to the closest owning route. Root receives only true global constraints; group indexes receive only next-hop routing; leaves receive scoped executable rules; references receive long supporting material.
- For inherited, duplicated, oversized, or mixed-responsibility systems, use `../../../migration-policy/SKILL.md`.
- Use `../../../routing-architecture/SKILL.md` when the approved outcome needs a new or materially changed routed `.agents` tree.
- Use `../../../project-initialization/SKILL.md` only as a target-shape reference after authorization when reorganizing an existing non-Axiom system. Do not treat it as fresh initialization.
- Keep no two independently editable copies of the same rule.

## Validation and report

- Run static checks for route reachability, links, duplicate rules, protected metadata boundaries, secrets, and size model.
- Run routing scenarios when AGENTS routing changed.
- Run skill validation for changed repo-local skills when applicable.
- Report authorization basis, inspected task scope, added/modified/rejected candidates, affected files, Git tracking state, byte changes, and validation results.

## Prohibited actions

- Do not update non-Axiom AGENTS systems without authorization.
- Do not rewrite protected plugin or skill metadata as ordinary AGENTS routing content.
- Do not copy Axiom packaged skill rules, trigger phrases, load policies, internal routes, validation protocols, or reporting formats into target AGENTS files.
- Do not create or update repo-local skills as local copies of Axiom packaged skills.
- Do not persist one-off task discoveries.
- Do not auto-commit, auto-push, or rewrite history.
