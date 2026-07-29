---
name: using-axiom
description: Use when an Axiom plugin session starts or when explicitly deciding whether a user request should route to a bundled Axiom skill before normal work continues.
---

# Using Axiom

Axiom is a routing gate for Codex-native workflows. Use this front door to decide whether an installed Axiom skill applies. Do not make every task an Axiom task.

## Decision Rule

1. Honor higher-priority user, system, developer, and repository instructions first.
2. If the user explicitly invokes Axiom or the request clearly matches an Axiom skill description, load the most specific matching Axiom skill before exploration, edits, or nonessential clarification.
3. If more than one Axiom skill may apply, choose the smallest matching skill set. Load a parent skill's internal index only after selecting that parent skill.
4. User requests may be written in any language. Normalize unambiguous non-English wording to the matching English canonical route; ask one concise clarification question only when wording could map to multiple Axiom workflows.
5. If no Axiom skill clearly applies, continue normally without mentioning Axiom.

## Current Routes

- `agents-architect`: Use when the user asks to initialize, generate, audit,
  split, refactor, migrate, validate, or maintain an `AGENTS.md` instruction
  system, its `.agents/` routing tree, or repo-local skills for a target
  repository.
- `traceable-git-submit`: Use when the user asks to keep Git changes traceable with local checkpoint commits, cache the last remote-push baseline in target Git metadata, consolidate unpublished checkpoint commits, or submit, publish, or push through a one-final-commit workflow.
- `reversible-system-change`: Use when the user asks to install, upgrade,
  deploy, migrate, run destructive retention, promote an active version, or
  plan or rehearse one of those persistent local or remote changes with
  rollback, data-safety, service, or promotion risk. Plan-only work stays
  read-only.

## Updating Axiom

When the user explicitly asks to update or refresh Axiom, direct them to the
host-controlled marketplace refresh flow. In Codex CLI, use:

```bash
codex plugin marketplace upgrade axiom
```

In a supported workspace plugin UI, use **Refresh** for the marketplace
plugin. Tell the user to start a new Codex session after refreshing. Do not
check, fetch, install, or announce Axiom updates automatically, and do not
claim that an update is available unless the host has reported it.

## Boundaries

- Do not trigger Axiom from broad AI, coding, documentation, or plugin-maintenance similarity alone.
- Do not treat every Git request as `traceable-git-submit`; use it only for checkpoint, baseline cache, consolidation, submit, publish, push, or traceable workflow requests.
- Do not treat ordinary source or configuration edits, Git commits or pushes,
  conceptual explanations, or pure read-only status/version queries as
  `reversible-system-change`. A plan or rehearsal for a persistent system
  change does route there but never authorizes mutation.
- Do not load every Axiom skill.
- Do not edit protected plugin metadata unless the selected skill and user request explicitly scope that work.
- Do not persist one-off task discoveries as durable instructions unless an Axiom skill admits them through its durable-update gate.
- Keep Axiom skill triggers in this installed plugin and packaged skill
  descriptions. Do not rely on target repository `AGENTS.md` files to trigger
  Axiom workflows.
- Ask one concise clarification question only when the request could map to
  multiple Axiom workflows and the choice would change execution. If no current
  Axiom workflow applies, continue normally without mentioning Axiom.
