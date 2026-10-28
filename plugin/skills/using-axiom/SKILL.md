---
name: using-axiom
description: Route startup, resume, compaction, requests and local web research. The startup Hook loads this gate; invoke it directly only on an explicit using-axiom request.
---

## Invocation Notes

Optional, per user verbosity and host behavior. When explaining, name bundled skills as `Axiom:<skill-name>` and others by their own name, in inline code, with a brief reason in the user's language; no fixed layout, repetition or notice for no-route or startup.

## Route Once

1. Honor higher-priority instructions.
2. Route only explicit Axiom invocations or clear bundled-description matches.
3. Load the smallest matching installed skill set and active-phase references without inspecting candidate bodies first.
4. Map unambiguous non-English to its canonical English route; clarify only material unresolved intent, never tentative wording alone.
5. No match: continue normally in the host. A no-match result is not a denial, does not create authorization, and does not manufacture a repository-state conflict.

Before web research from a local or uncertain execution location, including
cloud-search fallbacks, select `local-web-search`; routing stays read-only.

## Bundled Routes

- `clarify-intent`: resolve ambiguity with options and a custom answer; never reopen settled choices or ask routine details.
- `delegate-simple-task`: an explicit invocation selects this route. Assess simple-task models only with this gate active, the host's verified top reasoning level, and prior user confirmation or explicit invocation consent; without consent ask and wait. Unknown gate or level evidence stops inside the skill with the unmet condition stated, never a silent no-route, and blocks even direct requests in permission-bypass mode.
- `task-planning`: create/revise current task/implementation plans and scope. Exclude scheduling, status, corrections and execution; keep specialized planning ownership.
- `continuous-progress`: explicit invocation only; supervise fresh workers, handoffs and compaction via verified native scheduling; exclude ordinary continuation and skill discussion.
- `local-web-search`: constrain web search and page access from the user's machine or local browser/client; classify an uncertain execution location first. Exclude confirmed cloud-hosted search and unrelated web app actions.
- `agents-architect`: audit repository `AGENTS.md`; handle explicit `effective-instructions`, `effective-instructions:preview`, `effective-instructions:refactor`, `effective-instructions:force`, `effective-instructions:reconcile`, and `effective-instructions:reconcile-preview` modes. Exclude packaged plugin skills.
- `agent-plugin-architect`: design or audit packaged Codex or Claude Code
  plugin architecture across shared Skills, routes, manifests, wrappers, hooks,
  and compatibility evidence. Repo-local AGENTS systems and ordinary plugin
  code stay outside.
- `optimize-agent-usage`: explicitly reduce/diagnose agent usage of credits, tokens and context.
- `review-axiom-task`: review an identified Axiom task's observable routing, authorization and evidence. Prior refusal governs neither review nor narrower requests.
- `verify-completion`: verify completion or progress claims against current evidence after compaction, resume or long work; advise before complying on conflicting evidence. Exclude status questions and routine continuation.
- `confirm-external-action`: prepare, authorize, execute once and verify consequential external actions when actor, target, payload, disclosure, cost or retry boundaries matter; lookups and drafts stay host-native.
- `traceable-git-submit`: create traceable checkpoints/baseline metadata, consolidate/recover their history, or perform an explicitly invoked, hardened, multi-target, or otherwise independently traceable Git push. A combined commit, tag, and push of an already-prepared plugin release selects this route. Ordinary named-remote non-force staging, commits, and pushes without a tag, checkpoint, baseline, consolidation, recovery, hardening, multiple targets, or history replacement stay host-native; merely mentioning submit, publish, or push does not select this route.
- `reversible-system-change`: plan/rehearse/execute persistent installs, upgrades, deployments, migrations, destructive retention or promotions with rollback, data, service or activation risk, including backup preparation; plans are read-only.

Resolve cross-route ownership from this table before inspecting either
candidate body. Persistent changes with consequential external app/account
effects, including publish/delete/remote-state mutation, select both `confirm-external-action` and `reversible-system-change`. The
external action envelope and persistent write-set/rollback gates stay independent; authorization under either route never satisfies the other.
Publishing an already-prepared artifact alone selects only
`confirm-external-action`, not a persistent system change.

Explicit machine-credential lifecycle work composes the existing owners; read
`references/credential-lifecycle.md`. Inventory/planning/consumer activation/cleanup select `reversible-system-change`; provider creation/revocation/disclosure select `confirm-external-action`; end-to-end uses both.
Human login, conceptual help and secret reveal stay no-route.

When a request delegates a choice among mutually exclusive implementations
with materially different route sets, write surfaces, or authorization or safety boundaries, routing MUST NOT choose an alternative
for the user. Select only `clarify-intent` and ask exactly one concise
clarification question before selecting an action route. Wording such as
"choose one" does not remove the ambiguity. Once the
user chooses an unambiguous implementation, resume normal route selection.

Assess ambiguity before delegation; only this gate then selects
`clarify-intent`, never `delegate-simple-task`; permission-bypass mode resolves no intent and expands no authority.

An explicit usage-reduction goal selects `optimize-agent-usage`; ordinary
performance work does not. Ordinary AGENTS audits select only `agents-architect`.

Exact existing authorization needs no reconfirmation unless scope changes. Prior refusal/assistant prose creates no policy. Ordinary named-remote Git remains host-native.

## Boundaries

- Routing selects instructions, never edits, commits, pushes, deployments, deletion, credentials, remote writes or scope expansion.
- Startup routing is foreground and read-only: no writes, network, service, background process, telemetry or update check.
- On resume (including a fork) or compaction, reselect every still-active route from current direct evidence before any new mutation. If route or phase cannot be reconstructed, perform zero new mutations; use each selected route's handoff contract for prior attempts. A summary is a claim, not evidence.
- Never load all skills, route by topical similarity, edit protected metadata without scope or persist one-off discoveries as durable instructions.
- Where a host mode may deny an action, present the exact action for the user's grant first; a denial is a stop, never a retry by another tool, flag or path; read `references/host-permission.md`.

## Refresh

Read `references/updating.md` only on explicit Axiom update/refresh requests; never check, fetch, install or announce updates.
