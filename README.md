# Axiom

Think before AI thinks.

Axiom is a Codex-first plugin for community-native AI workflows. It exists to help AI understand user intent before execution, then route the work through durable, high-quality capabilities that feel native in Codex.

## Current Capabilities

- AGENTS architecture: audit, initialize, and refactor `AGENTS.md`, `AGENTS.override.md`, `.agents/` routing trees, and repo-local skills.
- Routed instruction trees: split large guidance into scoped references with explicit next-hop routing.
- Traceable Git submit: checkpoint local work and publish one clean commit when explicitly authorized.

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

### Language And Routing

Skill IDs, folder names, frontmatter `name` values, and canonical command tokens remain English. User requests can be written in any language; Axiom normalizes unambiguous requests to the matching English canonical route and asks for clarification only when a request could map to more than one workflow.

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
- `skills/` contains packaged skills bundled with the plugin. Only direct child `skills/*/SKILL.md` files are public Skill entry points; `skills/agents-architect/references/` contains internal on-demand reference material.
- `hooks/hooks.json` loads Axiom's documented routing gate at session start.
- `.agents/plugins/marketplace.json` exposes this repository as a local marketplace entry.

The plugin identifier is `axiom`. The product and README display name is `Axiom`.

## Bundled Skills

- `using-axiom`: Loads as a session-start routing gate after installation and decides whether a user request should use a more specific Axiom skill. The hook only injects this checked-in skill document; route decisions stay in the skill instructions.
- `agents-architect`: Initializes fresh repositories with scoped `AGENTS.md` plus `.agents/` routing trees, then audits, maintains, refactors, and validates existing AGENTS instruction systems and repo-local skills through an internal, on-demand skill index.
- `traceable-git-submit`: Keeps local Git work traceable with checkpoint commits, records the last remote-push baseline in target Git metadata, and publishes one clean consolidated commit when the user explicitly asks to submit, publish, or push.

## Installation

After the repository contents are committed and published, install Axiom from
its GitHub marketplace source:

```bash
codex plugin marketplace add wheakerd/axiom
codex plugin add axiom@axiom
```

In `axiom@axiom`, the first `axiom` is the plugin name and the second `axiom` is the configured marketplace name.

Start or restart Codex after installing the plugin. In the new Codex session,
open the hook review UI:

```text
/hooks
```

Review Axiom's `SessionStart` hook from `hooks/hooks.json`. It should match
these commands.

Linux and macOS:

```bash
printf '%s\n\n' 'You have Axiom. Load this startup front door before deciding whether any Axiom skill applies:'; cat "${PLUGIN_ROOT}/skills/using-axiom/SKILL.md"
```

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Write-Output 'You have Axiom. Load this startup front door before deciding whether any Axiom skill applies:'; Write-Output ''; Get-Content -Raw (Join-Path $env:PLUGIN_ROOT 'skills/using-axiom/SKILL.md')"
```

Trust the hook only after reviewing the current command. Then start a new Codex
chat or CLI session so the latest trusted hook and bundled skills are loaded.

## Updating Axiom

Axiom does not check for or install updates automatically. When you choose to
refresh Axiom from its Git marketplace source, run:

```bash
codex plugin marketplace upgrade axiom
```

This refreshes the configured Git marketplace snapshot named `axiom`. In a
supported workspace plugin UI, use **Refresh** for the marketplace plugin
instead. Start a new Codex chat or CLI session after refreshing so the latest
bundled skills and hook state can load. If Codex asks you to review a changed
hook, inspect it in `/hooks` before trusting it.

## Hook Security / Trust

Axiom bundles a `SessionStart` hook in `hooks/hooks.json`. Codex discovers that
file by default from the plugin root, so `.codex-plugin/plugin.json` does not
need a redundant `hooks` field for the current layout.

The hook runs on `startup`, `resume`, `clear`, and `compact`. It prints a short
Axiom loading message, then reads the checked-in
`skills/using-axiom/SKILL.md` file from the installed plugin root. It does not
modify files or contact a network service.

Hook trust is still a security decision. Review the exact command in `/hooks`
before trusting it. If the hook definition changes after an Axiom update, Codex
may mark the hook for review again and skip it until you review and trust the
new definition.

## Troubleshooting

If Axiom is installed but you do not see the routing load message at session
start, run `/hooks` and check that the Axiom `SessionStart` hook is enabled and
trusted.

After updating Axiom, start a new Codex chat or CLI session. Existing sessions
may keep the previous hook and skill state.

If Axiom skills are available but the `SessionStart` routing message does not
appear, focus first on the hook trust state in `/hooks`. Plugin-bundled hooks
are skipped until the current hook definition is reviewed and trusted.

## Distribution Boundary

The repository root is also the plugin root, so published contents must remain
runtime-relevant and reviewable. Plugin behavior is discovered through supported
Codex plugin entry points such as `.codex-plugin/plugin.json`, `skills/`, and
`hooks/hooks.json`.

Do not ship repository-maintenance scripts, test suites, or CI workflow files
in this plugin root. Define agent behavior in the checked-in Skills and Markdown
references instead of requiring an interpreter or runner on a user's system.
Keep maintenance-only validation, private troubleshooting, and workspace-only
overlays outside the plugin repository.

## Contributor Review

Axiom's user-facing behavior is defined by its Skills and Markdown references,
not by bundled maintenance programs. Before publishing, review that:

- `.codex-plugin/plugin.json` and marketplace metadata remain valid and describe
  the intended plugin.
- Only the direct `skills/*/SKILL.md` entries expose public capabilities.
- The documented `SessionStart` hook reads only the intended routing Skill and
  has been reviewed through `/hooks`.
- The plugin root contains no maintenance test suite, custom validator, or CI
  workflow that would introduce an interpreter or runner dependency.

Use available platform-native or official Codex validation facilities during
maintenance, but do not make a specific interpreter, shell, test runner, or
custom script a plugin installation prerequisite.

## License

MIT
