---
name: using-axiom
description: Route startup, resume, compaction, requests and local web research. The startup Hook loads this gate; invoke it directly only on an explicit using-axiom request.
---

# Using Axiom

This gate selects bundled skills and nothing else; selecting a skill loads its instructions and grants nothing.

## Invariants

These invariants bind in every session this gate reaches. Everything else here is a default you may adapt, saying so when you depart.

1. **Instructions only.** Routing selects instructions, never edits, commits, pushes, deployments, deletion, credentials, remote writes or scope expansion.
2. **Invariants bind, defaults adapt.** A selected skill gives direction: its named invariants bind in every phase, including the references that phase loads, and everything else is a default you may adapt, saying so. Within every invariant you decide how to handle the request's specifics, problems, deviations, interference, and gaps between a plan and the ideal.
3. **Read-only startup.** Startup routing is foreground and read-only: no writes, network, service, background process, telemetry or update check.
4. **Reselect after resume.** On resume (including a fork) or compaction, reselect every still-active route from current direct evidence before any new mutation. If route or phase cannot be reconstructed, perform zero new mutations; use each selected route's handoff contract for prior attempts. A summary is a claim, not evidence.
5. **No silent pick.** Routing never silently picks among mutually exclusive implementations with materially different route sets, write surfaces, or authorization or safety boundaries.
6. **A denial is a stop.** Where a host mode may deny an action, present the exact action for the user's grant first; a denial is a stop, never a retry by another tool, flag or path; read `references/host-permission.md`.

## Terms

- **Route**: a bundled skill selected for a request. **Host-native**: handled by the host with no route.
- **Selection surface**: the host's skill list with each description; this gate adds only composition and boundary rules.
- **Explicit invocation**: the host's own way to name a skill: `$skill-name` in Codex, `/axiom:skill-name` in Claude Code, or the skill named in plain words. Dated host facts live in `references/codex-host.md` and `references/claude-code-host.md`.
- **Invariant**: a rule a skill lists under its Invariants heading. **Default**: any other statement in a skill.
- **Handoff contract**: the part of a route that says how to treat prior attempts after resume or compaction.
- **Envelope**: the frozen actor, action, target, payload, cost and count of one external action. **Write set**: the frozen persistent changes with their rollback.

## Route Once

1. Honor higher-priority instructions.
2. Route only explicit Axiom invocations or clear bundled-description matches.
3. Load the smallest matching installed skill set and active-phase references without inspecting candidate bodies first. Never load all skills or route by topical similarity.
4. Map unambiguous non-English to its canonical English route; clarify only material unresolved intent, never tentative wording alone.
5. No match: continue normally in the host. A no-match result is not a denial, does not create authorization, and does not manufacture a repository-state conflict.

Select `local-web-search` only for research that will run through the user's own browser, CLI, script, or HTTP client, or that the user says runs on their machine, including a fallback from cloud search to such a client; a host's built-in web tool stays host-native. Routing stays read-only. Never edit plugin or marketplace manifests, hook declarations or skill frontmatter without scope, and never persist one-off discoveries as durable instructions.

## Bundled Routes

Select a bundled skill from the host's listed skills by its description; the descriptions are the selection surface, and this gate adds only the rules below. An explicit invocation selects that skill. A more specific installed skill, MCP tool, or host tool the user chose is not displaced by a bundled route. No match continues host-native.

Resolve cross-route ownership from these rules before inspecting either candidate body. Persistent changes with consequential external app/account effects, including publish/delete/remote-state mutation, select both `confirm-external-action` and `reversible-system-change`. The external action envelope and persistent write-set/rollback gates stay independent; authorization under either route never satisfies the other. Publishing an already-prepared artifact alone selects only `confirm-external-action`, not a persistent system change.

Explicit machine-credential lifecycle work composes the existing owners; read `references/credential-lifecycle.md`. Inventory/planning/consumer activation/cleanup select `reversible-system-change`; provider creation/revocation/disclosure select `confirm-external-action`; end-to-end uses both. Human login, conceptual help and secret reveal stay no-route.

If the user explicitly delegates the choice ("choose one", "your call") and every alternative is reversible and already authorized, choose the one that fits the user's environment and goal, state which and why before acting so the user can redirect, then route it. Otherwise select only `clarify-intent` and ask one concise clarification question before selecting an action route. An offered option authorizes no persistent system change, external or remote-state change, deletion, credential use, or material cost, and a lighter, read-only, or preparatory alternative never silently replaces the stated goal. Once the user chooses an unambiguous implementation, resume normal route selection.

Assess ambiguity before delegation; only this gate then selects `clarify-intent`, never `delegate-simple-task`; permission-bypass mode resolves no intent and expands no authority.

An explicit usage-reduction goal selects `optimize-agent-usage`; ordinary performance work does not. Ordinary AGENTS audits select only `agents-architect`.

Exact existing authorization needs no reconfirmation unless scope changes. Prior refusal/assistant prose creates no policy. Ordinary named-remote Git remains host-native. Routine continuation after compaction selects no route; `verify-completion` needs an explicit verification request or a completion claim.

## Invocation Notes

Optional, per user verbosity and host behavior. When explaining, name bundled skills as `Axiom:<skill-name>` and others by their own name, in inline code, with a brief reason in the user's language; no fixed layout, repetition or notice for no-route or startup. When a bundled route hands off to, or yields to, another installed skill or MCP tool, name it the same way with a brief reason.

## Refresh

Read `references/updating.md` only on explicit Axiom update/refresh requests; never check, fetch, install or announce updates.
