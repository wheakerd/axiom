---
name: repo-local-skills
description: Use when AGENTS Maintenance needs to create, update, split, route, or validate repository-local Codex skills under .agents/skills.
---

# Repo-Local Skills

## Purpose

Maintain repository-local Codex skills without confusing them with AGENTS routing leaves.

## Apply when

- The durable update belongs in `.agents/skills/<skill-name>/SKILL.md`.
- The user asks for a repo-local skill, project-local skill, local workflow skill, or reusable repository capability.
- Existing `.agents/skills/**` content needs review, splitting, routing, or validation.

## Do not apply when

- The content is a general AGENTS rule, workflow leaf, domain leaf, or risk overlay.
- The content belongs to a packaged plugin skill under `skills/**`.
- The requested workflow is one-off, temporary, or better kept in project documentation.

## Required actions

- Create or update repo-local skills only for repeatable user-facing workflows inside the target repository when the user explicitly asks for a repo-local skill or the repository already has that skill boundary.
- Default ordinary project workflow guidance to `.agents/workflows/**`; use `.agents/skills/**` only for intentionally surfaced project-local capabilities.
- Keep `.agents/skills/**` as protected skill metadata, not ordinary AGENTS routing leaves.
- Use lowercase hyphen-case for skill folder names and frontmatter `name`.
- Keep `SKILL.md` frontmatter to `name` and `description`.
- Put trigger conditions in `description` because the body loads only after the skill triggers.
- Keep descriptions, routes, examples, and trigger definitions in English only.
- Do not document localized aliases; allow non-English user wording only when it maps unambiguously to the canonical English trigger.
- Keep root skill bodies concise. Move long protocols, schemas, examples, or assets into on-demand references under the skill root only when needed.
- Add `agents/openai.yaml` only when UI metadata is useful for an intentionally surfaced skill.

## Placement

- Put a top-level repo-local skill at `.agents/skills/<skill-name>/SKILL.md`.
- For complex repo-local skills, use `.agents/skills/<skill-name>/skills/index.md` and `.agents/skills/<skill-name>/skills/<topic>/SKILL.md`.
- Keep child indexes as jump nodes with only purpose, enter conditions, exclusions, next hops, and stop-reading rules.

## Validation

- Validate every changed repo-local skill with the available skill validator when practical.
- Inspect route shape after adding, deleting, renaming, or materially changing repo-local skill topics.
- Report Git tracking or ignore state for `.agents/skills/**`.

## Prohibited actions

- Do not move repo-local skills into AGENTS routing branches.
- Do not recreate Axiom packaged skills, load policies, triggers, internal routes, validation protocols, or reporting formats as repo-local skills.
- Do not make a broad catch-all local skill when stable workflows can be separated.
- Do not add non-English trigger descriptions or examples.
- Do not create scaffold TODO placeholders that remain after validation.
