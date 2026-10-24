# Repo-Local Skills

## Purpose

Maintain repository-local skills for the hosts a target repository uses
without confusing them with routed rule documents.

## Apply when

- The durable update belongs in a repository-local skill: Codex reads
  `.agents/skills/<skill-name>/SKILL.md` and Claude Code reads
  `.claude/skills/<skill-name>/SKILL.md`.
- The user asks for a repo-local skill, project-local skill, local workflow skill, or reusable repository capability.
- Existing `.agents/skills/**` or `.claude/skills/**` content needs review, splitting, routing, or validation.

## Do not apply when

- The content is a general AGENTS rule, workflow leaf, direct domain entry, or
  cross-cutting safety or risk rule leaf.
- The content belongs to a packaged plugin skill under `skills/**`.
- The requested workflow is one-off, temporary, or better kept in project documentation.

## Host Discovery

- Codex discovers repository skills under `.agents/skills/`, including nested
  topic entries. Claude Code discovers them under `.claude/skills/` and never
  reads `.agents/` on its own.
- Select each skill directory from the hosts the target repository actually
  uses, as shown by its existing skill directories, instruction files, or the
  user's statement. Ask when that evidence is missing or conflicting.
- A `.claude/skills/` entry is a skill, not an instruction source. Do not
  create or edit `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/`,
  `.claude/settings*.json`, other `.claude/` content, or `.codex/`
  configuration.

## Required actions

- Create or update repo-local skills only for repeatable user-facing workflows inside the target repository when the user explicitly asks for a repo-local skill or the repository already has that skill boundary.
- Default ordinary project workflow guidance to `.agents/workflows/**`; use a repository skill directory only for intentionally surfaced project-local capabilities.
- Keep `.agents/skills/**` and `.claude/skills/**` as protected skill metadata,
  not ordinary routed rule leaves.
- Use lowercase hyphen-case for skill folder names and frontmatter `name`.
- Keep `SKILL.md` frontmatter to `name` and `description`.
- Put trigger conditions in `description` because the body loads only after the skill triggers.
- Keep skill folder names, frontmatter `name`, and canonical trigger definitions in English.
- User requests may be written in any language. Normalize unambiguous non-English wording to the matching English canonical trigger, and ask for clarification only when wording could map to multiple triggers.
- Do not maintain localized alias tables or broad multilingual trigger catalogs.
- Keep root skill bodies concise. Move long protocols, schemas, examples, or assets into on-demand references under the skill root only when needed.
- Add `agents/openai.yaml` to a Codex skill only when UI metadata is useful for
  an intentionally surfaced skill; Claude Code does not read it.

## Placement

- Codex: put a top-level skill at `.agents/skills/<skill-name>/SKILL.md`.
- Claude Code: put a top-level skill at `.claude/skills/<skill-name>/SKILL.md`.
- For a repository that uses both hosts, `.agents/` is the shared home: keep
  the one skill body in `.agents/skills/<skill-name>/`, beside the AGENTS
  documents. Give Claude Code an entry at `.claude/skills/<skill-name>`:
  - a relative symlink to `../../.agents/skills/<skill-name>` when every
    platform that checks out the repository supports Git symlinks; Claude
    Code reads `SKILL.md` from a symlinked skill folder's target;
  - otherwise a pointer `SKILL.md` with the same `name` and `description`
    whose body tells Claude Code to read and follow
    `.agents/skills/<skill-name>/SKILL.md`.
- When a skill body already lives in `.claude/skills/<skill-name>/`, ask the
  user before moving it into `.agents/skills/`. Never maintain two divergent
  skill bodies.
- For complex skills, use `<skill-root>/skills/index.md` and
  `<skill-root>/skills/<topic>/SKILL.md` under the skill body.
- Keep child indexes as jump nodes with only purpose, enter conditions, exclusions, next hops, and stop-reading rules.

## Validation

- Validate every changed repo-local skill with the available skill validator when practical.
- When both host entries exist, confirm that the Claude Code entry is a
  symlink resolving to the `.agents/skills/` body, or a pointer whose `name`
  and `description` match that body and whose text points to it.
- Inspect route shape after adding, deleting, renaming, or materially changing repo-local skill topics.
- Report Git tracking or ignore state for each changed skill directory.

## Prohibited actions

- Do not move repo-local skills into AGENTS routing branches.
- Do not recreate Axiom packaged skills, load policies, triggers, internal routes, validation protocols, or reporting formats as repo-local skills.
- Do not make a broad catch-all local skill when stable workflows can be separated.
- Do not add non-English canonical trigger tokens or localized alias tables.
- Do not create scaffold TODO placeholders that remain after validation.
