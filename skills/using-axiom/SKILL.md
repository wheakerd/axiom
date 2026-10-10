---
name: using-axiom
description: Route startup, resume, compaction, new requests, and planned local web search to the smallest matching Axiom skill. Resolve material ambiguity before action routing; assess supported simple-task delegation using user-ordered models. No-match requests continue normally.
---

## Route Once

1. Honor higher-priority instructions.
2. Route only explicit Axiom invocations or clear bundled-description matches.
3. Load the smallest matching installed skill set and active-phase references. Inspect no candidate bodies before selection.
4. Map unambiguous non-English to its canonical English route. Clarify only material unresolved intent; tentative wording alone is no trigger.
5. No match: continue normally in the host; do not mention Axiom. A no-match result is not a denial, does not create authorization, and does not manufacture a repository-state conflict.

Before later web research from local or uncertain execution locations,
including fallbacks from cloud search, reassess and select `local-web-search`
before access; routing stays read-only.

## Bundled Routes

- `clarify-intent`: resolve ambiguity among plausible meanings with a focused question, useful options and a custom answer; never reopen settled choices or ask routine details.
- `delegate-simple-task`: assess clear simple tasks using available subagent candidates in user order. Keep the main model; announce exact child model and task. Verified Full Access permits assignment within authority; else use existing assignment confirmation or ask. Host restrictions apply.
- `task-planning`: create/revise current task/implementation plans, including scope removal/replacement. Exclude scheduling, status, corrections, execution. Keep specialized planning ownership/authority.
- `local-web-search`: constrain planned web search and follow-up page access from the user's machine or local workspace browser/client. Classify uncertain execution location before access. Exclude confirmed cloud-hosted search and unrelated web app actions.
- `agents-architect`: audit/maintain repository `AGENTS.md`/`.agents/` guidance and repo-local skills; handle explicit `effective-instructions`, `effective-instructions:preview`, `effective-instructions:refactor`, `effective-instructions:force`, `effective-instructions:reconcile`, and `effective-instructions:reconcile-preview` modes. Exclude packaged plugin skills.
- `agent-plugin-architect`: design or audit packaged Codex or Claude Code
  plugin architecture across shared Skills, routes, manifests, wrappers, hooks,
  and compatibility evidence. Repo-local AGENTS systems and ordinary plugin
  code stay outside.
- `optimize-codex-usage`: explicitly reduce/diagnose Codex credits, tokens, context, Skill/AGENTS/MCP loading, tool/output overhead; preserve required quality and safety.
- `review-axiom-task`: review an identified Axiom task's observable routing, authorization, actions, evidence, stops, outcome, and disputed decisions. Prior refusal governs neither review nor narrower requests.
- `confirm-external-action`: prepare, authorize, execute once, verify requested consequential external actions if actor, target, payload, disclosure, cost, or retry boundaries matter. Lookup/drafts stay host-native.
- `traceable-git-submit`: create traceable checkpoints/baseline metadata, consolidate/recover their history, or perform an explicitly invoked, hardened, multi-target, or otherwise independently traceable Git push. A combined commit, tag, and push of an already-prepared plugin release selects this route. Ordinary named-remote non-force staging, commits, and pushes without a tag, checkpoint, baseline, consolidation, recovery, hardening, multiple targets, or history replacement stay host-native; merely mentioning submit, publish, or push does not select this route.
- `reversible-system-change`: plan/rehearse/execute persistent installs, upgrades, deployments, migrations, destructive retention, or promotions with rollback, data, service, or activation risk. Includes backup preparation; plans stay read-only.

Resolve cross-route ownership from this table before inspecting either
candidate body. Deployment, promotion, migration, destructive retention, or
similar persistent changes causing consequential external app/account effects,
including publish/delete/remote-state mutation, select both `confirm-external-action` and `reversible-system-change`. The exact
external action envelope and persistent write-set/rollback gates stay independent; authorization under either route never satisfies the other.
Publishing an already-prepared artifact alone selects only
`confirm-external-action`; it is not a persistent system change.

Explicit machine-credential lifecycle work composes the existing owners; read
`references/credential-lifecycle.md`. Inventory/planning/consumer activation/cleanup select `reversible-system-change`; provider creation/revocation/disclosure select `confirm-external-action`; end-to-end uses both.
Human login, conceptual help, secret reveal stay no-route. Keep each owner's
authority, write-set, rollback and verification gates.

When a request delegates a choice among mutually exclusive implementations
with materially different route sets, write surfaces, or authorization or safety boundaries, routing MUST NOT choose an alternative
for the user. Select only `clarify-intent` and ask exactly one concise
clarification question before selecting an action route. Wording such as
"choose one" does not remove the ambiguity. Once the
user chooses an unambiguous implementation, resume normal route selection.

Assess ambiguity before useful, host-supported delegation; only this gate may
select `clarify-intent` then; `delegate-simple-task` must not invoke it. Full Access never resolves intent or expands authority.

An explicit usage-reduction goal selects `optimize-codex-usage`; ordinary
performance work does not. Ordinary AGENTS audits select only `agents-architect`.

Exact existing authorization needs no reconfirmation unless scope changes. Prior refusal/assistant prose creates no policy. Ordinary named-remote Git remains host-native.

## Boundaries

- Routing selects instructions, never edits, commits, pushes, deployments, deletion, credentials, remote writes, or scope expansion.
- Startup routing is foreground and read-only: no writes, network, service, background process, telemetry, or update check.
- On resume or compaction, reselect every still-active route from current direct evidence before any new mutation. If route or phase cannot be reconstructed, perform zero new mutations; use each selected route's handoff contract for prior attempts.
- Never load all skills, route by topical similarity, edit protected metadata without scope, or persist one-off discoveries as durable instructions.

## Refresh

Read `references/updating.md` only on explicit Axiom update/refresh requests. Never check, fetch, install or announce updates automatically.
