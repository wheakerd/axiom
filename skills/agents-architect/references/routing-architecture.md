# Routing Architecture

## Purpose

Design the root control plane and finite on-demand routing tree.

## Apply when

- Creating or rewriting root `AGENTS.md`.
- Creating `.agents/` indexes, leaves, overlays, or maintenance docs.
- Reducing instruction context noise.
- Splitting oversized or mixed-responsibility instruction documents.
- Defining metadata, leaf schemas, or portable size models.

## Do not apply when

- Only moving a single already-classified rule.
- Only running validation on an existing structure.

## Required architecture

- Native auto-load layer: root `AGENTS.md` plus rare tiny nested `AGENTS.md` files for stable subprojects.
- On-demand routing layer: `.agents/` indexes and leaves.
- Cross-cutting overlay layer: `.agents/concerns/` or `.agents/risks/`.
- Runtime layer: `.agents/.runtime/` for temporary session capsules only.
- Protected metadata layer: `.codex-plugin/**`, `.agents/plugins/**`, `.agents/skills/**`, `skills/*/agents/**`, `<skill-root>/skills/**`, `hooks/**`, `.app.json`, `.mcp.json`, and `assets/**` for Codex plugin and skill configuration. This layer is not part of the AGENTS routing tree.
- Plugin capability layer: installed Axiom packaged skills own Axiom workflow triggers, load policies, internal routes, validation protocols, and reporting formats. Target repository AGENTS files must not restate or fork that layer.

## Responsibility Axes

Derive route groups from the repository, not symmetry. Use these axes when the evidence supports them:

- `session`: startup, compaction recovery, routing budget, and runtime state.
- `workflows`: task procedures such as implementation, Git, verification, release, dependency updates, and AGENTS maintenance.
- `domains`: business behavior ownership, product areas, or bounded contexts.
- `components`: technical framework, runtime, API, storage, integration, or shared-library boundaries.
- `concerns` or `risks`: cross-cutting overlays such as security, data integrity, compatibility, performance, observability, and migrations.

Indexes route within one axis and act as jump nodes, not rule stores. Leaves own canonical rules. Overlays add risk or concern rules without owning domain behavior. Use `requires` for stable cross-axis dependencies. Prefer deeper targeted routing over loading broad summaries so the system remains usable on smaller model contexts.

## Route Sinking

- Put each durable rule in the closest owning route where it always applies.
- Keep root `AGENTS.md` for rules that apply to every task in the repository.
- Use group indexes only when one stable route axis has multiple reachable leaves.
- Keep group indexes route-only: purpose, enter conditions, exclusion conditions, next hops, and stop-reading conditions.
- Give each domain, component, workflow, or concern leaf concrete scope evidence such as paths, packages, entry points, commands, source docs, owners, or risk signals.
- Split a leaf when it mixes independent owners, unrelated route triggers, different validation paths, or rules that make normal tasks load unrelated siblings.
- Use references or resources for long examples, schemas, inventories, and migration tables; leaves should point to them instead of carrying the full material.
- When size pressure appears, do not reduce rule precision, delete executable detail, or merge unrelated responsibilities to satisfy byte targets. Solve the pressure through route ownership, leaf splitting, or reference placement.

## Root AGENTS.md contract

Root `AGENTS.md` is a control plane. Include only:

- Short project goal.
- True global hard constraints.
- Instruction priority and conflict resolution.
- Request handling protocol.
- On-demand routing algorithm.
- Top-level route table.
- Portable loading shape and size model.
- Runtime capsule rule.
- Project-local durable-update placement rule.
- Minimum verification.

Do not include full architecture, full project tree, all leaves, all test commands, README copies, session state, domain details, Axiom skill load policies, Axiom trigger instructions, packaged `SKILL.md` content, or plugin-internal routes.

## Routing algorithm

- Parse task type, expected paths, domains, languages, frameworks, and risk signals.
- Use high-signal sources first: user paths, Git diff, stack traces, entry files, package manifests, build config, tests, and direct dependencies.
- Exclude protected plugin and skill metadata unless the user explicitly scopes skill or plugin maintenance.
- Route target repository context from project signals. Do not encode routes whose purpose is to trigger installed Axiom skills.
- Select at most two top-level branches.
- Read at most one next-hop index per branch before entering leaves.
- Read `requires` dependencies only when relevant.
- Trigger risk overlays only from explicit risk signals.
- Continue from root rules if no leaf matches.
- Route incrementally when scope expands.
- Maintain an internal active instruction set with loaded paths, load reasons, and key constraints.

## Request handling

- Treat the newest user message as the active request.
- Resolve intent, target files, expected outcome, and risk level before acting.
- Execute clear low-risk requests without asking for confirmation.
- Ask one concise clarification question before acting on ambiguous, high-risk, destructive, credential-related, or multi-command requests.
- When the user asks for evaluation or confirmation, state the decision and evidence before changing files.
- Keep progress updates brief and action-focused during longer work.

## Command resolution

- Keep durable project-local command names, canonical command tokens, route IDs, file and folder names, and frontmatter identifiers in English.
- Axiom plugin skill triggers belong in the installed plugin, not in target AGENTS files.
- Treat the English definition as the canonical source of truth.
- Allow user requests in any language. Non-English wording may trigger a canonical command when the mapping is unambiguous.
- Normalize resolved requests to the canonical English command before reasoning, reporting, or updating durable instructions.
- Ask for clarification only when translated or paraphrased wording could map to multiple commands.
- Do not maintain localized alias tables or broad multilingual trigger catalogs. Non-English examples are allowed only when they demonstrate unambiguous normalization and do not become alternate canonical tokens.
- Keep command definitions short and specific to reduce semantic spread during trigger selection.

## Index rules

Index files may contain only purpose, enter conditions, exclusion conditions, next hops, and stop-reading conditions.

Index files must not contain coding standards, architecture summaries, copied leaf rules, or flattened descendant catalogs.

## Leaf metadata

Use compact frontmatter:

```yaml
---
id: domain.example.implementation
kind: index | leaf | overlay | maintenance
scope:
  paths:
    - "src/example/**"
  tasks:
    - feature
load_when:
  - "Modify production code under src/example"
do_not_load_when:
  - "Only editing unrelated docs"
requires:
  - concern.security
source_of_truth:
  - "docs/example-architecture.md"
last_verified: "YYYY-MM-DD"
---
```

Remove empty fields. Keep IDs globally unique. Avoid circular `requires`.

## Leaf body schema

Use:

- Purpose.
- Apply when.
- Do not apply when.
- Required actions.
- Prohibited actions.
- Validation.
- References.

Write short imperative rules. Prefer verifiable actions. Do not invent commands.

## Size Model

- Platform fact: Codex may stop adding project guidance when the configured project document byte guard is reached. Treat visible `project_doc_max_bytes` values only as truncation protection, not as Axiom's design budget.
- Axiom heuristic: keep root `AGENTS.md` under `8 KiB` by default. This is a quality target, not a Codex platform hard limit; adjust when project evidence justifies it and explain any overage.
- Do not reduce rule precision, delete executable detail, or merge unrelated responsibilities to satisfy byte targets. Move detail to the owning leaf, resource, or split responsibility.
- Keep index files as small jump nodes focused on next-hop routing.
- Keep leaves and overlays scoped to one responsibility and small enough to load with their parent indexes.
- Axiom heuristic for a normal active set: root, startup or front-door node when present, `0`-`2` branch indexes, and `1`-`3` leaves or overlays.
- Axiom heuristic for a complex active set: no more than `6` `.agents` documents. This is not a Codex platform hard limit; allow justified exceptions and explain the active document count in the report.
- For AGENTS changes, report root bytes, key index bytes, leaf bytes, and scenario active-set bytes.

## Prohibited actions

- Do not create empty branches for symmetry.
- Do not require normal tasks to scan every index.
- Do not keep multiple canonical indexes for the same rules.
- Do not design AGENTS routing branches inside protected Codex/plugin metadata directories.
- Do not write `$agents-architect`, `$using-axiom`, Axiom route names, or Axiom packaged skill protocols into generated target AGENTS content unless the user explicitly requests a provenance note.
