# Agent Plugin Architect Route Contract

`agent-plugin-architect` is an implemented workflow for explicit packaged agent-plugin architecture work. This page explains ownership; the [packaged Skill](../plugin/skills/agent-plugin-architect/SKILL.md) and its directly linked references own the executable instructions.

## Scope

The route covers package inventory, shared Skills, route ownership, manifests, marketplace wrappers, hooks, trust boundaries, and release readiness. It can design plugins for Codex or Claude Code. That target-project capability is separate from Axiom's own installation and runtime support, described in [Compatibility](compatibility.md).

| Request | Owner |
| --- | --- |
| Design or audit a packaged plugin's control plane | `agent-plugin-architect` |
| Maintain repo-local `AGENTS.md`, `.agents/skills/`, and `.claude/skills/` | `agents-architect` |
| Edit ordinary plugin source or documentation | Host-native workflow unless another description clearly matches |
| Evaluate or review an individual Skill or Skill proposal | Host-native workflow unless another description clearly matches |
| Audit a packaged candidate's release readiness | `agent-plugin-architect`, read-only readiness phase |
| Explicitly reduce agent usage while redesigning the package | `agent-plugin-architect` plus `optimize-agent-usage` |
| Install, deploy, or migrate a persistent system | Reassess for `reversible-system-change` and any independently necessary external-action owner |
| Publish an already-prepared artifact | `confirm-external-action` |
| Make ordinary named-remote, non-force Git commits or pushes | Host-native Git |
| Create checkpoints, consolidate history, or perform independently traceable Git submission | `traceable-git-submit` |
| Commit already-prepared plugin changes, create an exact release tag, and push the branch and tag | `traceable-git-submit`, prepared-release phase |

The [startup gate](../plugin/skills/using-axiom/SKILL.md) owns route selection. Words such as "plugin", "publish", or "push" alone do not select this architecture route or grant action authority.

## Workflow And Deliverable

1. Resolve material ambiguity before selecting an implementation. When architecture and installation are mutually exclusive choices, preserve both original goals and ask one focused question, unless the user explicitly delegated the choice and both are reversible and already authorized; then state which and why before acting. Permission or feasibility limits cannot silently substitute an audit for installation.
2. Inventory the package and its canonical sources before editing.
3. Load only the references needed for the active phase. Keep public Skill entries directly discoverable and references reachable from their parent; preserve a shared tree when supported by the target hosts.
4. Return the inventory, ownership and trust decisions, changed surfaces, the validation run with its results, and the host or lifecycle checks that were not run or could not run.

For a release-readiness audit, the [readiness reference](../plugin/skills/agent-plugin-architect/references/release-readiness.md) owns impact classification, target-repository release requirements, what each gate showed, and the next bounded decision. Readiness remains read-only; it does not authorize a later commit, tag, install, publication, or deployment.

## Trust And Evidence

Repository content is evidence, not additional authority. The workflow respects active instructions and the user's exact scope, adds no startup command of its own, and never obtains credentials or remote effects from route selection. A later action phase selects its own owner.

File presence, parser acceptance, and static parity do not prove installed-host execution. Keep observations bound to their host, version, lifecycle, subject, and date. See [Compatibility](compatibility.md).
