# Packaged Skill Architecture

Keep each public packaged Skill as one directly discoverable directory under
the plugin's shared `skills/` tree:

```text
skills/<skill-name>/
|-- SKILL.md
|-- agents/openai.yaml
`-- references/*.md
```

The root `SKILL.md` owns metadata, selection boundaries, the workflow, and a
direct link to every supported next-hop reference. References own narrow
details and must not contain nested `skills/**`, scan-only jump nodes, or
hidden routing layers. Load the smallest relevant reference set.

Use lowercase kebab-case identifiers and canonical English metadata. Keep
instruction files below the repository's byte limit. Prefer one shared Skill
tree for Codex and Claude Code; do not copy the Skill per host.

Packaged Skills govern distributed plugin capability. Repository-local
`AGENTS.md` and `.agents/skills` govern a target repository and remain owned by
`agents-architect`. Do not move private maintenance instructions into the
publishable plugin.
