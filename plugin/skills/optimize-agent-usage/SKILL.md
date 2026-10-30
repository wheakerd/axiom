---
name: optimize-agent-usage
description: Reduce or diagnose agent usage of tokens, credits, and context without weakening quality or safety. Use only on an explicit goal to save credits or tokens, trim Skills, instruction files, MCP, or context loading, explain unusually high usage, or design a leaner workflow. Not for ordinary coding, software performance, or generic cost questions.
---

# Optimize Agent Usage

Reduce total agent consumption while preserving the requested outcome, the authorization boundaries, the safety checks, and the completion evidence.

## Invariants

These invariants bind in every phase, including the references that phase loads. Everything else in this skill is a default you may adapt, saying so when you depart.

1. **Quality bar first.** Define the required quality, safety, authorization, rollback, and evidence bar before optimizing; a reduction counts only when that bar still passes.
2. **No safety trade.** Never remove required tests, rollback checks, secret handling, destructive safeguards, or outcome-owning evidence to save context or calls.
3. **Settings stay.** Never change the model, reasoning effort, execution mode, or host configuration on your own; offer a bounded comparison only when the user asks and the host supports the choice.
4. **Unrelated work stays.** Do not reset, stash, clean, stage, commit, push, deploy, install tools, change user Skills, or mutate remote state without separate authorization, and add no telemetry, background work, automatic updates, or network checks.
5. **Honest measures.** Use exact usage metrics only when the host exposes them for the scoped run; label bytes, words, lines, and counts as proxies, and claim no percentage saving without a repeatable before/after workload and equal quality acceptance.

## Load Policy

- For a conceptual explanation or a narrow current-product fact, use this file and the current host's official documentation only. Do not inspect a repository or load the audit reference unless the request needs it.
- For an audit, design change, or implementation involving Skills, instruction files, MCP, context, history, tools, validation, or reporting, read `references/context-audit.md` before changing files.
- Add another Axiom skill only when the implementation crosses into that skill's owner: an AGENTS instruction system, traceable Git state, or a persistent system change. Usage analysis alone needs only this skill.

## Measurement Boundary

- Axiom cannot recover hidden usage data; fetch the host's official documentation only when a volatile host fact affects the decision.
- Never place current prices, plan limits, or model quotas in always-loaded instructions.

## Optimization Order

1. Bound the target workflows and representative requests.
2. Measure always-loaded and common-path context before rare worst cases.
3. Inventory metadata and route edges before reading bodies.
4. Read only candidate owners, then remove duplication or move route detail behind one directly discoverable on-demand reference.
5. Reduce repeated tool calls, checks, updates, and reports only where the next decision does not depend on each intermediate result.
6. Re-run the same routing, authorization, safety, and outcome scenarios.
7. Stop when further reduction would trade away required quality or evidence.

Prefer precise trigger descriptions, one canonical owner per rule, phase-specific references, bounded retries, conclusive stopping conditions, and concise evidence-led reporting. Keep ordinary no-match work outside Axiom.

## Report

Lead with the implemented or recommended outcome. Include affected files or surfaces, comparable before/after measurements, validation results, and real unverified gaps. Omit repeated rationale, routine successful details, and exact usage claims the host did not expose.
