# Axiom

Think before AI thinks.

Axiom is a Codex-first plugin for community-native AI workflows. It exists to help AI understand user intent before execution, then route the work through durable, high-quality capabilities that feel native in Codex.

## Brand Foundations

### Mission

Bridge the gap between user intent and AI execution.

### Vision

Make community innovations feel native.

### Philosophy

If it doesn't feel native, it isn't finished.

### Brand Story

Axiom is built on the belief that understanding should always come before execution. It represents the principles that guide AI toward the right action before work begins.

### Positioning

Axiom is not named after a platform, a tool category, or an implementation boundary. Codex is the first-class target, but the brand is independent of any single AI surface.

### Voice

- Clear over clever.
- Native over novel.
- Durable over flashy.
- Practical over abstract.

## Principles

### Understand First

Before execution, clarify the user's real goal, constraints, context, and success criteria.

### Codex First

Codex CLI and Codex Desktop are the primary targets. Axiom should fit their interaction model, trust boundaries, and workflow surfaces before optimizing for portability elsewhere.

### Community Native

Community-built capabilities should feel like they naturally belong in the host product. The user should not need to care whether a capability came from the core product or from Axiom.

### Real Workflows

Capabilities should come from repeated real-world friction, not speculative feature lists.

### Skills Are Implementation Units

Skill files and topic trees are implementation units. Packaged skill IDs can be public handles, but user-facing language should lead with outcomes such as progress, review, Git, Docker, context, workspace, or documentation workflows.

### Native Is The Quality Bar

If it doesn't feel native, it isn't finished.

## Capability Model

```text
User request
    |
    v
Axiom
    |
    +-- Detect
    +-- Clarify
    +-- Route
    +-- Plan
    +-- Execute
```

Axiom should sit before execution, not after it.

## Naming Rules

- Use `Axiom` for the product and brand.
- Use `axiom` for plugin identifiers, CLI-like examples, marketplace entries, and package namespaces.
- Keep `AI` uppercase in the tagline.
- Do not title-case the tagline.

## Project Shape

Axiom is initialized as a single-plugin repository:

- `.codex-plugin/plugin.json` is the required Codex plugin manifest.
- `skills/` contains packaged skills bundled with the plugin.
- `hooks/hooks.json` loads Axiom's documented routing gate at session start.
- `.agents/plugins/marketplace.json` exposes this repository as a local marketplace entry.

The plugin identifier is `axiom`. The product and README display name is `Axiom`.

## Bundled Skills

- `using-axiom`: Loads as a session-start routing gate after installation and decides whether a user request should use a more specific Axiom skill. The hook only injects this checked-in skill document; route decisions stay in the skill instructions.
- `agents-architect`: Initializes fresh repositories with scoped `AGENTS.md` plus `.agents/` routing trees, then audits, maintains, refactors, and validates existing AGENTS instruction systems and repo-local skills through an internal, on-demand skill index.
- `traceable-git-submit`: Keeps local Git work traceable with checkpoint commits, records the last remote-push baseline in `.agents/.cache/traceable-git-submit-baseline.json`, and publishes one clean consolidated commit when the user explicitly asks to submit, publish, or push.

## Installation

After the repository contents are committed and published, install Axiom from its GitHub marketplace source:

```bash
codex plugin marketplace add wheakerd/axiom
codex plugin add axiom@axiom
```

In `axiom@axiom`, the first `axiom` is the plugin name and the second `axiom` is the configured marketplace name.

Start a new Codex chat or CLI session after installing or updating the plugin so the latest bundled skills are loaded.

## Distribution Boundary

The repository root is also the plugin root. Files in the plugin root may be present in installed plugin caches, but plugin behavior is discovered through supported Codex plugin entry points such as `.codex-plugin/plugin.json`, `skills/`, and `hooks/hooks.json`.

Keep repository project introduction, plugin structure, distribution notes, and contributor-facing validation guidance in this README. Keep local maintenance policy, private troubleshooting, and workspace-only validation overlays outside the plugin repository.

## Contributor Validation

Choose commands that fit the current operating system and available runtime. Do not hard-code one Python launcher as the only valid command.

Common checks from the repository root:

```bash
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
python3 "$CODEX_HOME/skills/.system/plugin-creator/scripts/validate_plugin.py" .
python3 "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" skills/agents-architect
python3 "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" skills/traceable-git-submit
python3 "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" skills/using-axiom
for f in .codex-plugin/plugin.json .agents/plugins/marketplace.json hooks/hooks.json; do
  python3 -m json.tool "$f" >/dev/null
done
```

Use equivalent commands when a different interpreter, shell, or JSON parser is the native fit for the environment.

## License

MIT
