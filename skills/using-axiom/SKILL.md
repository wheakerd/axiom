---
name: using-axiom
description: Route an Axiom plugin session to the smallest matching bundled skill. Use at startup, resume, or compaction, or when explicitly deciding whether Axiom applies; no-match requests continue normally.
---

# Using Axiom

Axiom is a routing gate. Decide whether one installed workflow applies without
turning ordinary work into an Axiom task.

## Route Once

1. Honor higher-priority system, developer, user, and repository instructions.
2. Select a route only when Axiom is explicitly invoked or the request clearly
   matches a bundled skill description.
3. Load only the smallest necessary skill set, then only its active-phase
   references. Do not inspect candidate skill bodies before selection.
4. Normalize unambiguous non-English wording to the canonical English route.
   Ask one concise question only when the route or permitted action would
   materially differ.
5. On no match, continue through the host normally without mentioning Axiom.

## Bundled Routes

- `agents-architect`: create, audit, split, migrate, or maintain a target
  repository's `AGENTS.md` system, routed `.agents/` guidance, or supporting
  repo-local skills. Packaged plugin skills are outside this route.
- `optimize-codex-usage`: explicitly reduce or diagnose Codex credits, tokens,
  context, Skill/AGENTS/MCP loading, tool churn, or output overhead while
  preserving the required quality and safety bar.
- `review-axiom-task`: review the routing, scope, authorization, actions,
  evidence, stops, and outcome of the current or an explicitly identified
  Axiom-guided task when the user explicitly requests that retrospective.
- `traceable-git-submit`: create traceable checkpoints or baseline metadata,
  consolidate or recover their history, or perform an explicit Git
  submit/publish/push. Ordinary local staging and commits stay host-native.
- `reversible-system-change`: plan, rehearse, or execute a persistent install,
  upgrade, deployment, migration, destructive retention, or promotion with
  rollback, data, service, or activation risk. Plans remain read-only.

An explicit usage-reduction goal selects `optimize-codex-usage`. Add another
route only when the requested implementation also needs that route's distinct
authorization or safety contract. Ordinary AGENTS audits select only
`agents-architect`; ordinary performance work does not select usage
optimization.

An explicit retrospective selects `review-axiom-task`; any implementation must
be separately authorized and routed.

## Boundaries

- Routing selects instructions; it never authorizes edits, commits, pushes,
  deployments, deletion, credentials, remote writes, or scope expansion.
- Startup routing is foreground and read-only. It must not write files, contact
  a network, start a service or background process, collect telemetry, or check
  for updates.
- Do not load every Axiom skill, route from broad topical similarity, edit
  protected plugin metadata without explicit scope, or persist one-off task
  discoveries as durable instructions.
- Ordinary coding, documentation, explanation, status, local-commit, and
  conceptual requests continue normally unless a route description clearly
  matches.

## Explicit Refresh

Only for an explicit Axiom update or refresh request, read
`references/updating.md`. Never check, fetch, install, or announce an update
automatically.
