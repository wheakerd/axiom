---
name: using-axiom
description: Route an Axiom plugin session to the smallest matching bundled skill. Use at startup, resume, or compaction, or when explicitly deciding whether Axiom applies; no-match requests continue normally.
---

# Using Axiom

Axiom is a routing gate. Select the smallest installed workflow set that
applies without turning ordinary work into an Axiom task.

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
   A no-match result is not a denial, does not create authorization, and does
   not manufacture a repository-state conflict.

## Bundled Routes

- `agents-architect`: create, audit, split, migrate, or maintain repository
  `AGENTS.md`, routed `.agents/` guidance, and repo-local skills; also handle
  explicit `effective-instructions`, `effective-instructions:preview`,
  `effective-instructions:refactor`, `effective-instructions:force`,
  `effective-instructions:reconcile`, and
  `effective-instructions:reconcile-preview` modes. Packaged plugin skills stay
  outside.
- `agent-plugin-architect`: design or audit packaged Codex or Claude Code
  plugin architecture across shared Skills, routes, manifests, wrappers, hooks,
  and compatibility evidence. Repo-local AGENTS systems and ordinary plugin
  code stay outside.
- `optimize-codex-usage`: explicitly reduce or diagnose Codex credits, tokens,
  context, Skill/AGENTS/MCP loading, tool churn, or output overhead while
  preserving the required quality and safety bar.
- `review-axiom-task`: review the routing, scope, authorization, actions,
  evidence, stops, and outcome of the current or an explicitly identified
  Axiom-guided task when the user explicitly requests that retrospective.
- `confirm-external-action`: prepare, authorize, execute once, and verify an
  explicitly requested consequential external action such as send, publish,
  invite, purchase, trade, delete, or an external app/account change when its
  actor, target, payload, disclosure, cost, or retry boundary is material.
  Read-only lookup and draft-only work stay host-native.
- `traceable-git-submit`: create traceable checkpoints or baseline metadata,
  consolidate or recover their history, or perform an explicitly invoked,
  hardened, multi-target, or otherwise independently traceable Git push. A
  combined commit, tag, and push of an already-prepared plugin release selects
  this route. Ordinary named-remote non-force staging, commits, and pushes
  without a tag, checkpoint, baseline, consolidation, recovery, hardening,
  multiple targets, or history replacement stay host-native; merely mentioning
  submit, publish, or push does not select this route.
- `reversible-system-change`: plan, rehearse, or execute a persistent install,
  upgrade, deployment, migration, destructive retention, or promotion with
  rollback, data, service, or activation risk. Plans remain read-only.

Resolve cross-route ownership from this table before inspecting either
candidate body. A deployment, promotion, migration, destructive retention, or
similar persistent change that also causes a consequential external app or
account effect, including publish, delete, or remote-state mutation, selects
both `confirm-external-action` and `reversible-system-change`. Keep the exact
external action envelope and the persistent write-set and rollback gates
independent; authorization under either route never satisfies the other.
Publication of an already-prepared artifact alone selects only
`confirm-external-action`; publication alone is not a persistent system
change.

When a request delegates a choice among mutually exclusive implementations and
the alternatives would select materially different route sets, write surfaces,
or authorization or safety boundaries, routing MUST NOT choose an alternative
for the user. Select no route yet and ask exactly one concise clarification
question. Wording such as "choose one" does not remove the ambiguity. Once the
user chooses an unambiguous implementation, resume normal route selection.

An explicit usage-reduction goal selects `optimize-codex-usage`. Add another
route only when the requested implementation also needs that route's distinct
authorization or safety contract. Ordinary AGENTS audits select only
`agents-architect`; ordinary performance work does not select usage
optimization.

An explicit retrospective selects `review-axiom-task`; any implementation must
be separately authorized and routed.

An external action selects `confirm-external-action` only when the user asks to
cause the effect. Preparation does not authorize execution, and an exact
current request need not be reconfirmed unless a material envelope field is
missing or changes. Keep independently traceable Git workflows under
`traceable-git-submit`; ordinary named-remote Git remains host-native.

A persistent change with no distinct consequential external effect stays under
`reversible-system-change`; apply the cross-route rule above when both effects
are present.

## Boundaries

- Routing selects instructions; it never authorizes edits, commits, pushes,
  deployments, deletion, credentials, remote writes, or scope expansion.
- Startup routing is foreground and read-only. It must not write files, contact
  a network, start a service or background process, collect telemetry, or check
  for updates.
- On resume or compaction, reselect every still-active route from current
  direct evidence before any new mutation. If route or phase cannot be
  reconstructed, perform zero new mutations; let each selected route's handoff
  contract resolve prior attempts.
- Do not load every Axiom skill, route from broad topical similarity, edit
  protected plugin metadata without explicit scope, or persist one-off task
  discoveries as durable instructions.
- Ordinary coding, documentation, explanation, status, local commits,
  named-remote non-force pushes, and conceptual requests continue normally
  unless a route description clearly matches.

## Explicit Refresh

Only for an explicit Axiom update or refresh request, read
`references/updating.md`. Never check, fetch, install, or announce an update
automatically.
