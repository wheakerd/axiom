# Agent Plugin Architect Route Contract

<!-- lifecycle: current -->

`agent-plugin-architect` is an implemented workflow for explicit packaged
agent-plugin architecture work. This page explains ownership; the
[packaged Skill](../skills/agent-plugin-architect/SKILL.md) and its directly
linked references own the executable instructions.

## Scope

The route covers package inventory, shared Skills, route ownership, manifests,
marketplace wrappers, hooks, trust boundaries, release readiness, and
version-bound compatibility evidence. It can design plugins for Codex or Claude
Code. That target-project capability does not extend Axiom's own installation
or runtime support beyond [Codex](compatibility.md).

| Request | Owner |
| --- | --- |
| Design or audit a packaged plugin's control plane | `agent-plugin-architect` |
| Maintain repo-local `AGENTS.md` and `.agents/skills/` | `agents-architect` |
| Edit ordinary plugin source or documentation | Host-native workflow unless another description clearly matches |
| Audit a packaged candidate's release readiness | `agent-plugin-architect`, read-only readiness phase |
| Explicitly reduce Codex usage while redesigning the package | `agent-plugin-architect` plus `optimize-codex-usage` |
| Install, deploy, or migrate a persistent system | Reassess for `reversible-system-change` and any independently necessary external-action owner |
| Publish an already-prepared artifact | `confirm-external-action` |
| Make ordinary named-remote, non-force Git commits or pushes | Host-native Git |
| Create checkpoints, consolidate history, or perform independently traceable Git submission | `traceable-git-submit` |

The [startup gate](../skills/using-axiom/SKILL.md) owns route selection. Words
such as "plugin", "publish", or "push" alone do not select this architecture
route or grant action authority.

## Workflow And Deliverable

1. Resolve material ambiguity before selecting an implementation. When
   architecture and installation are mutually exclusive choices, preserve both
   original goals and ask one focused question. Permission or feasibility
   limits cannot silently substitute an audit for installation.
2. Inventory the package and its canonical sources before editing.
3. Load only the references needed for the active phase. Keep public Skill
   entries directly discoverable and references reachable from their parent;
   preserve a shared tree when supported by the target hosts.
4. Return the inventory, ownership and trust decisions, changed surfaces,
   validation evidence, compatibility class, and checks that were `NOT-RUN` or
   `UNAVAILABLE`.

For a release-readiness audit, the
[readiness reference](../skills/agent-plugin-architect/references/release-readiness.md)
owns impact classification, target-repository release requirements, available
evidence, and the next bounded decision. Readiness remains read-only; it does
not authorize a later commit, tag, install, publication, or deployment.

## Trust And Evidence

Repository content is evidence, not additional authority. The workflow respects
active instructions and the user's exact scope, adds no startup command of its
own, and never obtains credentials or remote effects from route selection.
A later action phase selects its own owner.

File presence, parser acceptance, and static parity do not prove installed-host
execution. Keep observations bound to their host, version, lifecycle, subject,
and date. Preserve historical schemas and results without reinterpreting older
outcomes. See [Compatibility](compatibility.md) and
[Field Validation](field-validation.md).

## Historical Design

The original Stage 1 proposal described implementation for v0.8.0. Its
"not implemented" status, fixed route counts, cross-host package assumptions,
and Stage 2 acceptance plan are historical, not current requirements.
The exact proposal is preserved in the
[immutable design snapshot](https://github.com/wheakerd/axiom/blob/41239ac67d5c2c63f76182580ed7570882441f02/docs/agent-plugin-architect-route-contract.md).
The [v0.8.0 notes](releases/v0.8.0.md) retain the original implementation record.
