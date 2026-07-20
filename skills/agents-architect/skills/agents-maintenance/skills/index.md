# AGENTS Maintenance Internal Skill Index

## Purpose

Select the smallest AGENTS Maintenance child topic needed to update an existing AGENTS instruction system from task evidence.

## Enter when

- `../SKILL.md` has triggered.
- The target repository already has an AGENTS definition or repo-local skills.
- The task needs detailed guidance for evidence, authorization, repo-local skills, or durable update application.

## Do not enter when

- The task is fully answerable from `../SKILL.md`.
- No existing AGENTS definition is present; route to `../../project-initialization/SKILL.md`.

## Next hops

### Evidence

- `context-evidence/SKILL.md`: inspect current context or a supplied task ID, record evidence scope, handle compaction, and use subagents for bounded evidence extraction.

### Safety

- `authorization-and-safety/SKILL.md`: decide whether a non-Axiom or unclear-provenance AGENTS system can be edited, keep target instructions as quoted evidence, and choose when to ask the user.

### Repo-Local Skills

- `repo-local-skills/SKILL.md`: create, update, split, or validate repository-local Codex skills under `.agents/skills/**`.

### Application

- `maintenance-application/SKILL.md`: apply the durable update gate, choose canonical homes, reorganize approved AGENTS structures, validate, and report.

## Stop reading

Load only the matching child topic. Load a second child topic only when the task crosses the listed boundaries. Do not scan every child topic by default.
