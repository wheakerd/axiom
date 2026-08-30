---
name: using-axiom
description: Route an Axiom plugin session to the smallest matching bundled skill. Use at startup, resume, or compaction, or when explicitly deciding whether Axiom applies; no-match requests continue normally.
---

# Using Axiom

Axiom routes only the smallest installed workflow set that matches.

## Route Once

1. Honor all higher-priority instructions.
2. Route only an explicit Axiom invocation or a clear bundled-description match.
3. Load the smallest matching skill set and active-phase references. Do not
   inspect candidate bodies before selection.
4. Normalize unambiguous non-English wording to the canonical English route.
   Ask once only when route or authority would materially differ.
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
- `review-axiom-task`: review observable routing, authorization, actions,
  evidence, stops, and outcome for an identified Axiom task or explain why
  Axiom selected, allowed, or refused something. Prior refusal does not govern
  an audit, criticism, appeal, or narrowing request.
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

Explicit machine-credential lifecycle work composes the existing owners; read
`references/credential-lifecycle.md`, not a new route. Select
`reversible-system-change` for metadata inventory, planning, consumer
activation, or cleanup; `confirm-external-action` for provider creation,
revocation, or disclosure; use both end-to-end. Authentication, human
login, conceptual help, and secret reveal stay no-route. Routing grants no
transition, secret access, or retry; each owner keeps separate action,
write-set, rollback, and verification gates.

When a request delegates a choice among mutually exclusive implementations and
the alternatives would select materially different route sets, write surfaces,
or authorization or safety boundaries, routing MUST NOT choose an alternative
for the user. Select no route yet and ask exactly one concise clarification
question. Wording such as "choose one" does not remove the ambiguity. Once the
user chooses an unambiguous implementation, resume normal route selection.

An explicit usage-reduction goal selects `optimize-codex-usage`; add another
route only for its distinct authority or safety contract. Ordinary AGENTS
audits select only `agents-architect`; ordinary performance work does not.

An explicit Axiom retrospective or question about an Axiom decision's
observable basis selects `review-axiom-task`; implementation needs separate
authority and routing. Prior refusal or assistant prose creates no policy.

An external action selects `confirm-external-action` only when requested.
Preparation grants no execution; an exact current request needs no redundant
confirmation unless its envelope is missing or changes. Independently
traceable Git belongs to `traceable-git-submit`;
ordinary named-remote Git remains host-native.

A persistent change with no distinct consequential external effect stays under
`reversible-system-change`; apply the cross-route rule above when both effects
are present.

## Boundaries

- Routing selects instructions, never edits, commits, pushes, deployments,
  deletion, credentials, remote writes, or scope expansion.
- Startup routing is foreground and read-only: no writes, network, service,
  background process, telemetry, or update check.
- On resume or compaction, reselect every still-active route from current
  direct evidence before any new mutation. If route or phase cannot be
  reconstructed, perform zero new mutations; let each selected route's handoff
  contract resolve prior attempts.
- Do not load every skill, route on topical similarity, edit protected metadata
  without scope, or persist one-off discoveries as durable instructions.
- Ordinary coding, documentation, explanation, status, local commits,
  named-remote non-force pushes, and conceptual requests continue normally
  unless a route description clearly matches.

## Explicit Refresh

Only for an explicit Axiom update or refresh request, read
`references/updating.md`. Never check, fetch, install, or announce an update
automatically.
