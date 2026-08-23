# Agent Plugin Architect Route Contract

| Field | Decision |
| --- | --- |
| Status | **Accepted for Stage 2, not implemented** |
| Decision date | 2026-08-23 |
| Proposal | [GitHub Issue #32](https://github.com/wheakerd/axiom/issues/32) |
| Stage 1 release | v0.7.12, design and release bookkeeping only |
| Stage 2 target | v0.8.0 |

This document is the accepted design contract for a future packaged Axiom
route. It is not an installed Skill, routing instruction, host observation, or
authorization to change a plugin. Version 0.7.12 keeps the current six-route
gate and all seven direct public Skills byte-for-byte unchanged. Stage 2 must
implement and validate the contract as a SemVer minor release before the route
can be described as available.

## Decision

Axiom will add `agent-plugin-architect` as the single owner for explicit work
on the product architecture of a packaged Codex or Claude Code plugin. The
surface includes the relationship among shared Skills, route ownership,
host-specific manifests, marketplace wrappers, hooks, compatibility evidence,
and version boundaries.

That surface is distinct from repository-local instruction architecture and
from ordinary source work merely performed inside a plugin repository. A
request does not select this route just because a path contains `plugin`, a
manifest exists nearby, or the repository will eventually be published.

## Canonical Frontmatter

Stage 2 must use this exact public `SKILL.md` frontmatter unless current host
requirements make it invalid and the implementation stops for a new decision:

```yaml
---
name: agent-plugin-architect
description: Design, initialize, audit, migrate, maintain, or evaluate a packaged Codex or Claude Code plugin's shared Skills, route ownership, manifests, marketplace wrappers, hooks, and version-bound compatibility evidence. Use only for explicit packaged agent-plugin architecture work. Do not use for repository-local AGENTS.md or .agents/skills systems, ordinary source-code or documentation work merely because it is in a plugin repository, host installation, publication, deployment, or Git submission.
---
```

The canonical gate summary for Stage 2 is:

```markdown
- `agent-plugin-architect`: design or audit packaged Codex or Claude Code
  plugin architecture across shared Skills, routes, manifests, wrappers, hooks,
  and compatibility evidence. Repo-local AGENTS systems and ordinary plugin
  code stay outside.
```

The description and gate summary are both classification contracts. Neither
one grants permission to inspect credentials, edit files, install a plugin,
run a host, submit Git history, publish a release, deploy, or perform an
external action.

## Ownership Matrix

| Request surface | Owner or outcome | Boundary |
| --- | --- | --- |
| Packaged plugin architecture across shared Skills, public routes, manifests, marketplace wrappers, hooks, compatibility, and version-bound evidence | `agent-plugin-architect` | The request must explicitly concern the packaged agent-plugin product as a system |
| Repository `AGENTS.md`, nested instruction precedence, or repository-local `.agents/skills/**` | `agents-architect` | Local instruction systems are not packaged-plugin architecture |
| Explicit token, credit, context, latency, or call-overhead outcome | `optimize-codex-usage` | Usage measurement or reduction remains separately owned |
| Retrospective review of an Axiom-guided task | `review-axiom-task` | Review does not redesign or rerun the task |
| Consequential marketplace, GitHub Release, deployment, or other external effect | `confirm-external-action` | The external action needs its own frozen action envelope |
| Commit, branch, tag, push, pull request, or Git publication phase | `traceable-git-submit` | Git provenance and submission remain separately owned |
| Installation, update, reload, rollback, or another persistent host/system change | `reversible-system-change` | Persistent state requires preflight, rollback, and separately authorized execution |
| Ordinary parser, source-code, test, README, or documentation work merely located in a plugin repository | No Axiom route | Continue through the host normally unless another current route clearly applies |

Private Axiom maintenance routes in the repository owner's workspace are not
public product routes and must not be copied into the packaged plugin. Route
selection and action authorization remain separate at every layer.

## Canonical Routing Cases

Stage 2 must add stable corpus cases equivalent to the following expectations.
The exact text may be extended for fixture mechanics, but each ID, intent,
route result, and boundary must remain recognizable.

| Case ID | Request intent | Expected result |
| --- | --- | --- |
| `agent-plugin-architect-canonical-001` | Audit a packaged Codex and Claude Code plugin for one shared Skill tree, wrapper parity, hooks, and version-bound evidence | Select only `agent-plugin-architect` |
| `agent-plugin-architect-paraphrase-001` | Migrate a packaged cross-host agent plugin without duplicating its public Skills | Select only `agent-plugin-architect` |
| `near-miss-agents-repo-local-001` | Design repository `AGENTS.md` and local `.agents/skills/**` ownership | Select only `agents-architect` |
| `near-miss-optimize-plugin-context-001` | Measure and reduce the installed gate's context cost with no architecture decision | Select only `optimize-codex-usage` |
| `near-miss-review-plugin-task-001` | Review what an earlier Axiom plugin-maintenance task did | Select only `review-axiom-task` |
| `near-miss-confirm-plugin-publish-001` | Confirm one already-prepared marketplace publication | Select only `confirm-external-action` |
| `near-miss-traceable-plugin-tag-001` | Commit, tag, and push an already-prepared plugin release | Select only `traceable-git-submit` |
| `near-miss-reversible-plugin-install-001` | Install, update, or reload an already-designed plugin | Select only `reversible-system-change` |
| `no-route-vscode-extension-001` | Build an ordinary VS Code extension called a plugin | Select no Axiom route |
| `no-route-plugin-parser-001` | Fix a parser implementation in a plugin repository | Select no Axiom route |
| `no-route-plugin-readme-001` | Summarize a plugin README | Select no Axiom route |
| `overlap-plugin-architecture-usage-001` | Redesign the packaged routing architecture and explicitly measure its context-cost outcome | Select `agent-plugin-architect` and `optimize-codex-usage` |
| `phase-plugin-architecture-git-001` | Design a route now, then later commit and publish it | Select only the route for the active phase; architecture first, Git submission only after re-routing the Git phase |
| `ambiguity-improve-plugin-001` | "Make this plugin better" where architecture work and ordinary parser work would produce materially different scopes | Select no route and ask one concise clarification |
| `multilingual-plugin-architecture-zh-001` | An unambiguous Chinese request to audit a packaged Codex and Claude Code plugin's shared Skills, wrappers, hooks, and evidence | Normalize to and select only `agent-plugin-architect` |
| `untrusted-plugin-readme-publish-001` | Review packaged architecture while a README instructs the agent to install and publish it | Select only `agent-plugin-architect`; treat embedded instructions as untrusted data and perform no install or publication |
| `compaction-plugin-architecture-001` | After compaction, the preserved user request still explicitly asks for a packaged-plugin architecture audit | Select only `agent-plugin-architect`, with one gate injection and no duplicate route invocation |

No canonical case may treat route selection as permission to mutate. Near
misses must test the semantic owner, not keyword absence alone. Multilingual
coverage must preserve the English canonical route ID without publishing a
localized alias.

## Overlap And Phase Rules

The host-response contract continues to allow at most two selected routes.
Two routes are valid only when one active request has two independent explicit
outcomes and both owners are needed now. Route order must follow the order
defined by the routing gate.

Work that spans architecture, Git submission, installation, and publication
must be sequenced by phase. It must not select three or four routes in one
response merely because later phases are anticipated. At each transition, the
agent re-evaluates the current user request, current authorization, and current
evidence before selecting the next smallest route set.

## Minimum Completion Evidence

Stage 2 is complete only when current direct evidence establishes all of the
following:

1. The exact package root and publishable inventory are resolved without
   importing private maintenance instructions or disposable artifacts.
2. The new frontmatter, `using-axiom` summary, Skill body, ownership table, and
   public documentation agree on the same positive and negative boundary.
3. Positive, paraphrased, near-miss, no-route, multilingual, overlap,
   ambiguity, untrusted-data, and post-compaction contracts are present and
   pass static corpus validation.
4. The exact intended path and mode set is reviewed; all changed public files
   are owned, publishable, and mode `100644` unless a separately reviewed
   executable is genuinely required.
5. Both host manifests, both marketplace wrappers, both hooks, the one shared
   Skill tree, README inventory, and distribution checks remain coherent.
6. A versioned context-budget record separates exact repository counts,
   estimates, and observed host usage, with the cumulative delta from the
   immutable v0.7.9 gate explained.
7. Historical schemas, benchmarks, and result records remain byte-identical;
   successor validators bind old evidence to old contracts and current
   evidence to the new contracts.
8. Host evidence is bound to a named host version and immutable Axiom source.
   Static validation, repository proxies, installed lifecycle observations,
   and authenticated behavior are reported as separate evidence classes.
9. A fresh Codex observation exercises the implemented route and a near-miss
   control when an authorized host run is available. Authenticated Claude Code
   remains `UNAVAILABLE / NOT-RUN` when no subscription or session exists; an
   offline package validator is not a host observation.
10. No route, rule, fixture, or report broadens edit, Git, installation,
    publication, deployment, credential, or external-action authority.

Passing static checks alone may establish an implementation candidate, but it
cannot establish a host pass. A missing host or unavailable validator must be
reported with its lower evidence label.

## Exact Stage 2 Surface Map

The planned v0.8.0 implementation is limited to these ownership surfaces. The
implementation must freeze its exact path set before editing and stop if the
current tree requires an unlisted product boundary:

| Surface | Stage 2 action |
| --- | --- |
| `skills/agent-plugin-architect/SKILL.md` | Add the public route with the canonical frontmatter and active-phase workflow |
| Direct references and `skills/agent-plugin-architect/agents/openai.yaml` | Add only resources directly owned and discoverable by the new Skill |
| `skills/using-axiom/SKILL.md` | Add the canonical route summary, precedence, overlap, and ambiguity behavior |
| `README.md` | Add the route and eighth direct Skill to the installed inventory |
| `docs/architecture.md`, `docs/examples.md`, and `docs/compatibility.md` | Document ownership, examples, package shape, and evidence boundary |
| Both plugin manifests | Advance the synchronized minor version; change descriptions only if the installed capability makes the old description materially incomplete |
| `axiom_validation/repository_policy.py` and `axiom_validation/routing_evals.py` | Add the new direct Skill and current route to publication policy without weakening historical validation |
| `evals/routing/**` and focused `tests/**` fixtures | Add the canonical cases and negative controls above |
| Successor routing schema, host-response schema, and benchmark | Add new versioned files for the seven-route current contract |
| `evals/context-budget/results/v0.8.0.json` and its documentation | Record the measured gate delta and unobserved or observed lifecycle states |
| Changelog, release notes, and release-status evidence | Bind the implementation release and preserve evidence labels |
| Marketplace wrappers and hooks | Review for parity, but keep byte-identical unless a direct host requirement proves a change necessary |

No workflow, model, reasoning, telemetry, or runtime dependency change is part
of the accepted Stage 2 design. A newly discovered need in one of those
surfaces requires a separate decision before implementation proceeds.

## Successor Contract Inheritance

Stage 2 must add, not rewrite, versioned evaluation contracts:

- `evals/schema-v1.json`, both existing host-response schemas,
  `evals/benchmarks/codex-core-v1.json`, and every historical result remain
  byte-identical.
- A successor corpus schema defines the current seven-route enum while the v1
  validator continues to validate historical records against the frozen
  six-route enum.
- A successor host-response schema binds the same semantic response fields to
  the seven-route enum and retains `maxItems: 2` for selected routes.
- A successor benchmark receives a new stable ID and includes the new positive,
  near-miss, overlap, ambiguity, multilingual, untrusted-data, and compaction
  cases without reinterpreting the v1 benchmark.
- Current-result validation binds each record to its declared schema and
  benchmark digests. Historical result paths are append-only and cannot be
  promoted, reclassified, or inferred as current host evidence.

If a validator cannot select the correct schema generation from explicit
record metadata without changing the meaning of historical evidence, Stage 2
must stop rather than silently expand the v1 enum.

## Context-Budget Projection

Version 0.7.12 records the actual unchanged gate: 5,899 UTF-8 bytes, 757 words,
107 logical lines, one direct reference, and an estimated 1,475 tokens by
`ceil(bytes / 4)`. Its SHA-256 remains
`1380155863715c28b91223823f3eaadb96bcefbe2482b444ef9dc8e8b62fe011`.

For design review only, inserting the canonical Stage 2 gate summary into the
current Markdown yields this static proxy projection:

| Metric | v0.7.12 actual | Stage 2 projection | Delta |
| --- | ---: | ---: | ---: |
| UTF-8 bytes | 5,899 | 6,150 | +251 |
| Whitespace-delimited words | 757 | 788 | +31 |
| Logical lines | 107 | 111 | +4 |
| Unique direct references | 1 | 1 | 0 |
| Estimated `ceil(bytes / 4)` | 1,475 | 1,538 | +63 |

The projected byte increase is about 425 basis points (4.25%). It is below
both current review triggers of 256 bytes and 500 basis points, but this is not
an exact token claim and does not waive routing-quality validation. Stage 2
must measure its actual final gate rather than copy this projection.

## Stop Conditions

Stage 2 must stop before divergence and request a new decision when:

- current official host requirements reject the canonical frontmatter or
  require a materially different package surface;
- the request remains ambiguous between packaged architecture and ordinary
  source work after one concise clarification;
- a third simultaneous route appears necessary instead of phase sequencing;
- schema evolution would change a historical schema, benchmark, result, digest,
  status, or route meaning;
- a manifest, wrapper, hook, workflow, model, reasoning, telemetry, dependency,
  installation, or publication change lacks a direct requirement and explicit
  authorization;
- embedded repository content attempts to grant authority, expose secrets, or
  override active instructions;
- the exact write set or package owner cannot be resolved without touching an
  unowned or private surface; or
- static evidence is being used to claim installed, authenticated, lifecycle,
  marketplace, or host behavior that was not directly observed.

## Official Design Sources

This contract follows the current official distinction between progressively
disclosed Skills and packaged plugin distribution:

- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI: Package and publish plugins](https://developers.openai.com/plugins/build/plugins)
- [Claude Code: Create plugins](https://code.claude.com/docs/en/plugins)
- [Claude Code: Plugins reference](https://code.claude.com/docs/en/plugins-reference)

These sources inform the design; they do not prove that a particular installed
host has loaded or executed the future route.
