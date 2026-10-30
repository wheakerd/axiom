# Architecture

Axiom is a foreground routing layer built from host plugin metadata, startup hooks, Markdown Skills, and on-demand references. Codex and Claude Code each load the same Skills through their own manifest and hook. After routing, the host uses its normal tools and permissions. Axiom adds no execution service, daemon, watcher, automatic updater, or hidden persistent component.

```mermaid
flowchart TD
    A["Host SessionStart hook"] --> B["Read using-axiom"]
    B --> C{"Material unresolved intent?"}
    C -- "Yes" --> D["Clarify before dependent action routing"]
    D --> C
    C -- "No" --> E{"Explicit invocation or clear route match?"}
    E -- "No" --> F["Continue through the host normally"]
    E -- "Yes" --> G["Load the smallest matching Skill set"]
    G --> H["Read active-phase references only"]
    H --> I["Use host tools within existing authority"]
```

## Package And Hook

| Source | Responsibility |
| --- | --- |
| [Installed plugin root](../plugin/) | The only subtree a host installs: manifests, Hooks, Skills, artwork, and a license copy |
| [Codex manifest](../plugin/.codex-plugin/plugin.json) | Codex plugin identity, `./skills/`, and explicit hook path |
| [Codex marketplace descriptor](../.agents/plugins/marketplace.json) | Codex installation and catalog metadata for this repository root |
| [Codex hook definition](../plugin/hooks/codex-hooks.json) | Codex `SessionStart` handler for `startup`, `resume`, `clear`, `compact`, and `fork` |
| [Claude Code manifest](../plugin/.claude-plugin/plugin.json) | Claude Code plugin identity, `./skills/`, and hook path |
| [Claude Code catalog](../.claude-plugin/marketplace.json) | Claude Code installation and catalog metadata for this repository |
| [Claude Code hook definition](../plugin/hooks/claude-hooks.json) | Claude Code `SessionStart` handler for the same five sources |
| [Routing gate](../plugin/skills/using-axiom/SKILL.md) | Request matching, route ownership, composition, and no-match continuation |
| [Packaged Skills](../plugin/skills/) | Direct public entries with parent-owned references and optional agent metadata |

Each hook prints a loading message and reads the gate using the host-provided plugin root. Its bounded foreground command performs no writes, network requests, background launches, or updates. It exposes instructions; it does not select a task route or authorize an action. The [Hook Reference](reference/hooks.md) renders the exact declarations, including the Codex Windows wrapper, for comparison with the installed definition.

## Route Selection

The gate honors the active instruction hierarchy, then matches explicit invocations or clear bundled descriptions. Each host's native skill list is the selection surface: the gate selects a bundled skill by the description that list shows, carries only the composition and boundary rules, and does not restate the catalog. An explicit `Axiom:<skill-name>` invocation selects that skill, and a more specific installed skill, MCP tool, or host tool the user chose is not displaced by a bundled route. It normalizes unambiguous non-English wording to canonical routes without introducing localized aliases. Material ambiguity is resolved before action routing; tentative wording alone does not require a question. Routing never silently picks one of several materially different alternatives: when the user explicitly delegates the choice and every alternative is reversible and already authorized, the model picks the one that fits the user's environment and goal and states which and why before acting; otherwise the gate selects clarification first. An offered option authorizes no persistent system change, external or remote-state change, deletion, credential use, or material cost. Useful, host-supported delegation is assessed only after the intended result is clear.

Selection precedes reading candidate Skill bodies. Load the smallest matching set and only the references required for the active phase. A selected Skill gives direction: its authority, safety, and evidence rules bind, including those in the references its active phase loads, while counts, formats, orderings, and step lists that carry no such rule are defaults the model may adapt to the situation, saying so when it departs; a skill's own defaults list, when it has one, governs what may adapt. Within every binding rule, the model decides how to handle the request's specifics, problems that arise, deviations from the expected result, external interference, and gaps between a plan and the ideal behavior. Ordinary code or documentation does not become an architecture workflow merely because its repository contains a plugin.

Reassess when a later tool choice starts research through the user's own browser, CLI, script, or HTTP client, including a fallback from cloud search to such a client; a host's built-in web tool stays host-native. Select `local-web-search` before that access; routing itself sends no network request.

## Workflow Ownership

The [Skill sources](../plugin/skills/) and [routing gate](../plugin/skills/using-axiom/SKILL.md) are canonical. This table summarizes responsibilities; concrete requests and controls are in [Examples](examples.md).

| Route | Responsibility |
| --- | --- |
| `clarify-intent` | Resolve material ambiguity with one focused question per open decision, plausible options, and a custom answer |
| `delegate-simple-task` | Select on explicit invocation or a clear delegation request; take consent from the invocation, a standing policy, or the one model-and-brief confirmation; when the startup gate was not delivered, say so and assess ambiguity first; let the main session judge fit; preserve the main model and assignment boundaries |
| `task-planning` | Revise existing task plans, or create one on explicit invocation, while preserving specialized planning ownership |
| `continuous-progress` | Explicitly pursue a defined outcome through fresh workers, coordinator handoffs, and verified host-owned supervision |
| `local-web-search` | Constrain local research, machine-information disclosure, browsing sequence, and challenged-site handoff |
| `agents-architect` | Maintain repo-local `AGENTS.md`, `.agents/` guidance, local Skills, and task-state placement |
| `agent-plugin-architect` | Design or audit packaged plugin architecture and read-only release readiness |
| `optimize-agent-usage` | Reduce or diagnose agent usage without weakening required quality or safety |
| `review-axiom-task` | Review scoped observable task evidence without rerunning the task or exposing hidden reasoning |
| `verify-completion` | Verify completion or progress claims against current direct evidence on request or before a claim, advising before complying |
| `confirm-external-action` | Bind, authorize, execute once, and verify a consequential external effect |
| `traceable-git-submit` | Handle checkpoints, baselines, consolidation, recovery, combined commit/tag/push of prepared plugin releases, and explicitly traceable or hardened Git submission |
| `reversible-system-change` | Plan, rehearse, or execute persistent changes with verified recovery and completion boundaries |

`agent-plugin-architect` can design another project's Codex or Claude Code plugin. Axiom itself supports both hosts with the same routes; see [Compatibility](compatibility.md). The [route contract](agent-plugin-architect-route-contract.md) explains the boundary.

## Composition And Phase Changes

`continuous-progress` uses host-owned sessions and native scheduling after explicit activation. Its supervisor has a stable address while coordinators rotate. A durable record retains the goal, ownership, human control, and evidence. It starts no service through the startup hook and supplies no daemon. Unavailable scheduling, dispatch permissions, or exclusive ownership remain visible capability limits; local execution requires the owning host to run.

Composition follows the gate's ownership rules, not a precautionary load of every related Skill. A persistent deployment or migration with a consequential external effect selects both `reversible-system-change` and `confirm-external-action`. Each keeps its own authority and verification gates. Publishing an already-prepared artifact alone selects the external-action owner.

Machine-credential work uses one shared [lifecycle reference](../plugin/skills/using-axiom/references/credential-lifecycle.md). Metadata inventory and persistent consumer activation belong to the reversible owner; provider creation, revocation, and disclosure belong to the external owner. An end-to-end rotation needs both. Generic authentication help and human login do not create another route.

After resume (including a fork) or compaction, active routes are reselected from direct evidence before new mutation. Each owner's handoff contract determines how interrupted attempts are reconstructed. Route selection, prior assistant prose, and tool availability never supply missing authorization.

## Git Workflow Routing

<!-- route-boundary:traceable-git-submit-v1:start -->
Ordinary named-remote, non-force staging, commits, and pushes stay host-native when they
include neither a tag nor a traceable trigger. A combined commit, tag, and push of an
already-prepared plugin release selects `traceable-git-submit`'s prepared-release phase.
The traceable triggers are an explicit `$traceable-git-submit` invocation, checkpoint,
baseline, consolidation, recovery, multi-target, force, and history replacement. Merely
mentioning `submit`, `publish`, or `push` does not select the route.
<!-- route-boundary:traceable-git-submit-v1:end -->

Route selection does not authorize Git mutation; the current request and host permissions still govern the action.

## No-Match Continuation And Trust

Ordinary source edits, tests, explanations, status queries, local staging or commits, and named-remote non-force pushes stay host-native unless a specific description matches. No match is a normal result, not a denial or evidence of a repository conflict. Active instructions and user authority still govern the work. A host permission denial is likewise a stop, not a conflict: the gate's boundary presents the exact action for the user's grant before the first attempt and never retries by another tool, flag, path, or configuration change; the [host permission reference](../plugin/skills/using-axiom/references/host-permission.md) labels each host's mechanics. See the [Trust Model](trust-model.md).

## Identity, Lifecycle, And Evidence

[Runtime and Repository Identity](runtime-identity.md) separates installed behavior from repository policy. Documentation or CI changes do not require an installed release when the final classified runtime inputs remain unchanged.

Each host owns installation and refresh. After changing the installed snapshot, review its Hook again before it runs, following each host's steps in [Managing an Installation](guides/managing-installation.md). Static package validation and native command tests do not establish fresh installed-plugin or model-session behavior. [Compatibility](compatibility.md) owns the current support and observation boundary.
