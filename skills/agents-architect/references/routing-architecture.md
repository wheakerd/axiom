# Routing Architecture

## Purpose

Design the root control plane and finite on-demand routing topology.

## Apply When

- Creating or materially changing a routed AGENTS tree.
- Reducing instruction context noise.
- Splitting oversized or mixed-responsibility instruction documents.
- Defining route axes, ownership, dependencies, or cross-cutting safety and
  risk rules.

## Do Not Apply When

- Only moving one already-classified rule.
- Only authoring root, group-index, domain-entry, rule-leaf, risk-rule-leaf, or
  reference schemas without changing topology; use
  `instruction-document-contracts.md`.
- Only validating an existing structure.

## Architecture Layers

- Native auto-load layer: root `AGENTS.md` plus rare tiny nested
  `AGENTS.md` files for stable subprojects.
- On-demand layer: `.agents/` group indexes, direct domain entries, and rule
  leaves reached only through explicit `AGENTS.md` routing.
- Cross-cutting layer: safety or risk rule leaves selected only by explicit
  concern or risk signals.
- Runtime layer: `.agents/.runtime/` for temporary session capsules only.
- Protected metadata layer: the parent skill's canonical protected-metadata
  boundary. It is not an AGENTS routing branch.
- Plugin capability layer: installed Axiom skills own Axiom triggers, load
  policies, internal routes, validation protocols, and reporting formats.
  Target repository guidance must not restate that layer.

Only root or justified nested files named `AGENTS.md` belong to the native
auto-load layer Axiom writes. Every `.agents/**` document is an explicit
next-hop rule resource, never a Codex native discovery entry.

## Route Roles

- Group index: a route-only jump node for one stable axis with multiple
  reachable owners. Low-signal tasks may traverse one group index.
- Direct domain entry: a terminal, rule-bearing domain owner reached directly
  from root when one evidence-backed path, package, command, or domain signal
  is unique. It follows the rule-leaf contract and is not a domain summary.
- Rule leaf: the terminal canonical owner for one workflow, component, or
  responsibility.
- Cross-cutting safety or risk rule leaf: a terminal stricter rule set loaded
  only from an explicit safety or risk signal; it does not own domain behavior.
- Parent-owned reference: long supporting detail owned and explicitly routed
  by exactly one terminal rule owner. It is not an entry or second owner.
- Protected metadata boundary: the parent skill's canonical protected surfaces;
  none of the preceding route roles may be created inside them.

## Responsibility Axes

Derive groups from repository evidence, not symmetry:

- `session`: startup, compaction recovery, routing budget, and runtime state.
- `workflows`: implementation, Git, verification, release, dependency
  updates, and AGENTS maintenance.
- `domains`: business behavior or bounded contexts.
- `components`: framework, runtime, API, storage, integration, or shared
  library boundaries.
- `concerns` or `risks`: security, integrity, compatibility, performance,
  observability, and migration safety or risk rules.

Group indexes route within one stable axis and never store rule bodies. Direct
domain entries and rule leaves own canonical rules. Cross-cutting safety or
risk rule leaves add stricter constraints without owning domain behavior. Use
`requires` only for stable dependencies and avoid cycles.

A unique high-signal match routes directly to its owning domain entry or rule
leaf. A low-signal match may traverse one group index before reaching one
terminal owner. Never create a fixed domain branch or empty domain entry merely
to complete a template.

## Route Sinking

- Put each durable rule in the closest route where it always applies.
- Keep root `AGENTS.md` for repository-wide constraints and routing only.
- Create a group index only when one stable axis has multiple reachable owners.
- Give every direct domain entry and rule leaf concrete scope evidence: paths,
  packages, entry points, commands, source docs, owners, or risk signals.
- Split a rule leaf when it mixes independent owners, unrelated triggers,
  different validation paths, or sibling rules that normal work should not
  load.
- Put long examples, schemas, inventories, migration tables, and architecture
  facts in the owning leaf's explicitly routed parent-owned reference.
- Apply the byte boundary in `instruction-document-contracts.md`. Route-sink
  at that boundary instead of reducing precision, deleting executable detail,
  or merging independent responsibilities.

## Routing Algorithm

1. Parse task type, expected paths, domains, languages, frameworks, and risk
   signals.
2. Prefer high-signal evidence: user paths, Git diff, stack traces, entry files,
   manifests, build configuration, tests, and direct dependencies.
3. Exclude protected plugin and skill metadata unless the user explicitly
   scopes skill or plugin maintenance.
4. Route a unique signal directly to its domain entry or rule leaf; otherwise
   select at most two top-level axes for genuinely cross-axis work.
5. Within each selected axis, let a low-signal task read at most one group index
   before entering one terminal owner.
6. Load `requires` dependencies only when relevant. If any exact target is
   missing, unreachable from the current route, or ambiguous, report it. The
   safe subset is read-only assessment only: do not create, edit, move, or
   delete instruction structure and do not pass final structural acceptance.
   Writing or accepting structure requires every exact target to exist and be
   proven reachable from the current route.
7. Trigger cross-cutting safety or risk rule leaves only from explicit signals.
8. Continue with root rules when no terminal owner matches.
9. Route incrementally when scope expands.
10. Track loaded paths, load reasons, and key constraints in the active
    instruction set.

Route target repository context from project signals. Never create a target
AGENTS route whose purpose is to trigger an installed Axiom skill.

Every child index, domain entry, rule leaf, risk-rule leaf, reference, and
dependency may narrow parent scope or add stricter checks. None may broaden
authorization, erase an inherited prohibition, or turn missing evidence into
permission.

## Nested AGENTS.md

Use a nested `AGENTS.md` only when the directory is a stable subproject,
Codex commonly starts there, and local auto-loaded constraints reduce misloads
more than they duplicate root rules. Keep it tiny or route to canonical rule
owners.

## Document Contract Route

Load `instruction-document-contracts.md` when the task writes or validates
root, group-index, domain-entry, rule-leaf, risk-rule-leaf, parent-owned
reference, request-handling, command-resolution, metadata, or portable size
contracts. Topology-only work should not load it.

## Prohibited Actions

- Do not create empty branches for symmetry.
- Do not require normal tasks to scan every index.
- Do not keep multiple canonical indexes for the same rules.
- Do not create AGENTS branches inside protected plugin metadata.
- Do not put Axiom route names or packaged protocols into generated target
  guidance unless the user explicitly requests a provenance note.

## References

- `instruction-document-contracts.md`
- `validation-reporting.md`
