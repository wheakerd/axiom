# Axiom

[![Release](https://img.shields.io/github/v/release/wheakerd/axiom?sort=semver)](https://github.com/wheakerd/axiom/releases/latest)
[![Distribution and publication guards](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Think before AI thinks.

**Workflow guardrails for Codex.**

Axiom provides focused workflows for task planning and high-impact coding-agent actions.
It loads one focused, inspectable workflow when scope, authorization, evidence,
or rollback needs to be explicit, while ordinary requests continue through the
host normally.

A route never grants mutation authority. Selecting one does not by itself
permit an edit, commit, push, deployment, deletion, credential use, or external
action. Axiom is a public beta, not a sandbox or a guarantee that an agent
cannot make a mistake.

## Start Safely

| Request | Expected boundary |
| --- | --- |
| "Perform a read-only audit of this repository's `AGENTS.md` instruction system. Report findings only; do not modify files." | Select `agents-architect`, report evidence, and stop without changes |
| "Summarize the purpose of this README. Do not modify files." | Select no Axiom route and continue normally |

Install Axiom in Codex, inspect its installed Hook, and then try both requests. These
are expected contracts, not claims that your host has already reproduced them.

Codex:

```bash
codex plugin marketplace add wheakerd/axiom
codex plugin add axiom@axiom
```

Plugin Hooks execute commands in the host session. Before trusting Axiom,
compare the installed `/hooks` entry with the exact declarations and wrapper
in the [Hook reference](docs/reference/hooks.md). Stop if they differ. Continue
with [Getting Started](docs/guides/getting-started.md) for first use, or use
[Managing an Installation](docs/guides/managing-installation.md) for updates,
removal, and non-destructive troubleshooting.

## What Axiom Routes

| Outcome | Route | Core boundary |
| --- | --- | --- |
| Clarify an ambiguous request | `clarify-intent` | Offer plausible options and a custom answer before dependent actions |
| Delegate a simple task | `delegate-simple-task` | Keep the main model; use user-ordered candidates and existing authority |
| Create or revise an actionable task plan | `task-planning` | Reflect current scope; preserve valid decisions, dependencies, and acceptance criteria |
| Audit or maintain repository instructions | `agents-architect` | Inspect first; limit changes to the authorized instruction system |
| Design or audit packaged agent-plugin architecture | `agent-plugin-architect` | Require explicit package intent; keep ordinary plugin code outside |
| Reduce Codex usage overhead | `optimize-codex-usage` | Preserve required quality and safety; never invent hidden usage data |
| Review an Axiom-guided task | `review-axiom-task` | Review observable evidence independently and label unavailable facts |
| Confirm a consequential external action | `confirm-external-action` | Bind actor, target, payload, disclosure, count, and retry semantics |
| Make Git publication independently traceable | `traceable-git-submit` | Separate checkpoint, push, history, and cleanup authority |
| Plan or execute a persistent system change | `reversible-system-change` | Separate planning, rehearsal, activation, rollback, and retention |

Machine-credential lifecycle work composes `confirm-external-action` and
`reversible-system-change` when provider effects and persistent consumers are
both in scope; it does not add another public route.

Ordinary coding, documentation, explanation, status, local commits, and
conceptual requests continue through the host normally when no route clearly
matches. A no-route result is not a safety certification: host permissions and
repository instructions still apply. See [Examples](docs/examples.md) for more
routed requests and controls.

## Current Support Boundary

Axiom installs in Codex through its manifest, marketplace wrapper, and Hook.
The checked-in package, route contracts, and validation fixtures
are statically testable, but fresh-session behavior still depends on the exact
host version, operating system, policy, installation method, and installed
snapshot.

| Host | Checked-in support | Current v0.13.0 observation boundary |
| --- | --- | --- |
| Codex | Manifest, marketplace wrapper, `SessionStart` Hook, and shared Skills | Installed-host observation is `NOT-RUN` |

Claude Code installation and runtime support ended in v0.11.0.
The plugin-architecture workflow still covers other projects targeting Claude Code.

The current release-status record remains `STATIC-ONLY`; static checks do not
create host evidence. Read [Compatibility](docs/compatibility.md) for the
bounded matrix and known limitations, [Field Validation](docs/field-validation.md)
to report a result, and the [v0.13.0 notes](docs/releases/v0.13.0.md) for
version-specific detail. Historical observations remain under `evidence/` and
`evals/results/` with their original identities and terminal statuses.

### Runtime and repository identity

The installed package version, repository-policy revision, and deterministic
runtime digest are separate identities. See
[Runtime and Repository Identity](docs/runtime-identity.md) for the complete
input and version policy.

<!-- runtime-identity:current:start -->
- `pluginVersion`: `0.13.0`
- `repositoryPolicyRevision`: `33`
- `runtimeContractDigest` (schema v2): `sha256:9a1ff3534fde91c79ab7972bbf2a8efedd56d58fe914ef82532385b942b54fc8`
- Digest input manifest: [`axiom_validation/runtime-contract-inputs-v2.json`](axiom_validation/runtime-contract-inputs-v2.json)
<!-- runtime-identity:current:end -->

## Git Boundary

<!-- route-boundary:traceable-git-submit-v1:start -->
Ordinary named-remote, non-force staging, commits, and pushes stay host-native when they
include neither a tag nor a traceable trigger. A combined commit, tag, and push of an
already-prepared plugin release selects `traceable-git-submit`'s hardened phase. The
traceable triggers are an explicit `$traceable-git-submit` invocation, checkpoint,
baseline, consolidation, recovery, multi-target, force, and history replacement. Merely
mentioning `submit`, `publish`, or `push` does not select the route.
<!-- route-boundary:traceable-git-submit-v1:end -->

Route selection never authorizes Git mutation. Read the
[Trust Model](docs/trust-model.md) and [Architecture](docs/architecture.md) for
the broader authority and execution boundaries.

## Package Shape

Codex installs the checked-in `skills/` source. Supporting references
load on demand and are not separate routes.

### Shared skills

- `using-axiom`, the session-start routing gate.
- `clarify-intent`, the focused request-clarification workflow.
- `delegate-simple-task`, the model-aware simple-task delegation workflow.
- `task-planning`, the task-plan creation and revision workflow.
- `agents-architect`, the repository-instruction workflow.
- `agent-plugin-architect`, the packaged agent-plugin architecture workflow.
- `optimize-codex-usage`, the explicit Codex consumption workflow.
- `review-axiom-task`, the read-only Axiom task-review workflow.
- `confirm-external-action`, the consequential external-action workflow.
- `traceable-git-submit`, the checkpoint and Git submission workflow.
- `reversible-system-change`, the persistent-change workflow.

### Codex wrapper

- Codex uses `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`,
  and `hooks/codex-hooks.json`.

The Codex manifest points to `./skills/`. Axiom installs no daemon, network service,
watcher, background updater, or bundled runtime dependency.

## Documentation and Support

- [Documentation index](docs/README.md): guidance by audience and task.
- [Getting Started](docs/guides/getting-started.md): install, inspect, and try a routed request plus a control.
- [Managing an Installation](docs/guides/managing-installation.md): update, disable, remove, and troubleshoot.
- [Hook Reference](docs/reference/hooks.md): exact declarations, commands, wrapper, and trust checks.
- [Compatibility](docs/compatibility.md): current bounded support and evidence links.
- [Security Policy](SECURITY.md): private vulnerability reporting and public routing-report boundaries.
- [Support and bug reports](https://github.com/wheakerd/axiom/issues): public issue tracker and report templates.
- [Changelog](CHANGELOG.md): user-visible changes and required action.
- [License](LICENSE): MIT.

Contributors should read [CONTRIBUTING.md](CONTRIBUTING.md) and the public
[Documentation Policy](docs/maintainers/documentation-policy.md). Repository
validators and CI checks are contributor tooling; they are not installed
runtime dependencies or evidence that a host behavior was observed.

## License

MIT
