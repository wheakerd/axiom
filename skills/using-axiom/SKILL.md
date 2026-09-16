---
name: using-axiom
description: Route startup, resume, compaction, and new requests to the smallest matching Axiom skill. Resolve material ambiguity before action routing; assess supported simple-task delegation using user-ordered models. No-match requests continue normally.
---

# Using Axiom

Axiom routes only the smallest installed workflow set that matches.

## Route Once

1. Honor all higher-priority instructions.
2. Route only an explicit Axiom invocation or a clear bundled-description match.
3. Load the smallest matching skill set and active-phase references. Do not
   inspect candidate bodies before selection.
4. Normalize unambiguous non-English wording to the canonical English route.
   Clarify only material unresolved intent; tentative wording alone is not a trigger.
5. On no match, continue through the host normally without mentioning Axiom.
   A no-match result is not a denial, does not create authorization, and does
   not manufacture a repository-state conflict.

## Bundled Routes

- `clarify-intent`: resolve ambiguity between plausible meanings with a
  focused question, useful options, and a custom answer; do not reopen settled
  choices or ask about routine details.
- `delegate-simple-task`: assess a clear simple task for an available subagent
  using user-ordered candidates. Keep the main model; announce exact child model
  and task. Verified Full Access permits assignment within authority; otherwise
  use existing assignment confirmation or ask. Host restrictions still apply.
- `task-planning`: create or revise current task or implementation plans,
  including scope removal or replacement. Scheduling, status, corrections, and
  execution stay outside. Preserve specialized planning ownership and authority.
- `agents-architect`: audit or maintain repository `AGENTS.md`, `.agents/` guidance,
  and repo-local skills; also handle
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
  context, Skill/AGENTS/MCP loading, tool or output overhead without lowering
  required quality or safety.
- `review-axiom-task`: review an identified Axiom task's observable routing,
  authorization, actions, evidence, stops, and outcome, including a disputed
  decision. Prior refusal does not govern the review or a narrower request.
- `confirm-external-action`: prepare, authorize, execute once, and verify a
  requested consequential external action when actor, target, payload,
  disclosure, cost, or retry boundaries matter. Lookup and drafts stay host-native.
- `traceable-git-submit`: create traceable checkpoints or baseline metadata,
  consolidate or recover their history, or perform an explicitly invoked,
  hardened, multi-target, or otherwise independently traceable Git push. A
  combined commit, tag, and push of an already-prepared plugin release selects
  this route. Ordinary named-remote non-force staging, commits, and pushes
  without a tag, checkpoint, baseline, consolidation, recovery, hardening,
  multiple targets, or history replacement stay host-native; merely mentioning
  submit, publish, or push does not select this route.
- `reversible-system-change`: plan, rehearse, or execute persistent installs,
  upgrades, deployments, migrations, destructive retention, or promotions with
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
`references/credential-lifecycle.md`. Inventory, planning, consumer activation
and cleanup select `reversible-system-change`; provider creation, revocation
and disclosure select `confirm-external-action`; end-to-end work selects both.
Human login, conceptual help, and secret reveal stay no-route. Each owner keeps
its authority, write-set, rollback and verification gates.

When a request delegates a choice among mutually exclusive implementations and
the alternatives would select materially different route sets, write surfaces,
or authorization or safety boundaries, routing MUST NOT choose an alternative
for the user. Select only `clarify-intent` and ask exactly one concise
clarification question before selecting an action route. Wording such as
"choose one" does not remove the ambiguity. Once the
user chooses an unambiguous implementation, resume normal route selection.

Assess ambiguity before useful, host-supported delegation. Only this gate may
select `clarify-intent` during that assessment; `delegate-simple-task` must not
invoke it. Full Access never resolves intent or expands authority.

An explicit usage-reduction goal selects `optimize-codex-usage`; ordinary
performance work does not. Ordinary AGENTS audits select only `agents-architect`.

Exact existing authorization needs no repeated confirmation unless its scope
changes. Prior refusal or assistant prose creates no policy.
Ordinary named-remote Git remains host-native.

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

## Explicit Refresh

Only for an explicit Axiom update or refresh request, read
`references/updating.md`. Never check, fetch, install, or announce an update
automatically.
