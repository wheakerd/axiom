# Implementation Reconciliation

## Purpose

Reconcile existing AGENTS guidance with current implementation from direct
evidence, correct or remove stale claims, and reject speculative additions.

## Activation And Modes

Enter only after the parent or `../runtime-and-updates.md` selects
`effective-instructions:reconcile`,
`effective-instructions:reconcile-preview`, or an explicit unambiguous
equivalent. Either mode may start in a fresh session. Normalize non-English
wording only when the request maps to one mode; ambiguity requires one concise
question.

An ordinary request to update AGENTS stays on the normal maintenance route.
Repository drift and user-identified execution or context discontinuities are
evidence only after explicit activation; they never activate this workflow.
If the user explicitly includes current or earlier task or thread history,
load `context-evidence.md` for its review-window, latest-decision, and coverage
contract; do not load it merely because a discontinuity exists.

The preview mode is read-only. The apply mode permits only evidence-backed
AGENTS-system edits in the identified target and scope. Neither permits
implementation or plugin changes, commits, pushes, deployments, or cleanup.

## Authority And Baseline

Only the current session's loaded instruction chain is active authority at its
actual precedence. Inspected or copied guidance, history, summaries, and worker
reports are evidence only. A stale active rule remains binding this run; edits
affect later eligible loads.

Before delegating, record target repository, scoped AGENTS owners,
implementation surface, and baseline. Default to the live filesystem working
tree; separately record material index/staged divergence, unstaged state,
untracked paths, and ignored content. Use a ref or commit only when the user
selects it; its direct content is then baseline evidence, but report live-tree
divergence. Never silently substitute `HEAD`; other refs, history, task results,
and rollback records support provenance only.

Inspect every scoped path that can change a conclusion. For a material ignored
path, record tracked/ignored state, exact ignore owner, and direct content. A
clean tracked diff never proves complete state. Dirty state alone is not
ambiguous; competing intended baselines or unfinished work that makes
"implemented" unclear is. Mark affected claims unresolved and ask before
apply. Recheck material state before ledger freeze; changes invalidate rows.

## Atomized Evidence Ledger

Split compound rules into independently decidable claims before classification.
For every existing claim in scope and every proposed correction, record:

- claim ID, text, owner, and scope;
- exactly one kind: `implementation-claim`, `normative-constraint`,
  `routing-owner`, `validation-requirement`, or `source-of-truth-pointer`;
- baseline, evidence, counterevidence, and uncertainty;
- observed status, separate from disposition and write action; and
- worker sources plus the coordinator's decisive direct recheck.

Use observed status `confirmed`, `partially-confirmed`, `contradicted`,
`unverified`, or `conflicting`. Record a separate disposition/action pair:

- `keep` / `no-write`;
- `correct` / `edit`, including an evidence-backed narrow or split;
- `add-supported` / `add` only for explicitly scoped missing guidance;
- `remove-stale` / `remove`;
- `move-or-merge` / `move` or `merge`;
- `unresolved` / `defer`; or
- `reject-new` / `no-write`.

Implementation claims need current code, configuration, test, command, or
runtime evidence. Judge normative constraints by authoritative policy, scope,
owner, and continued need, not code. Routing owners need direct tree,
discovery, link, or loading evidence; validation requirements need the current
acceptance contract and configuration; source pointers must resolve to the
canonical owner.

Treat negative evidence as bounded investigation, not proof by search miss.
Check the authoritative owner, expected entry points and possible rename or
replacement, relevant configuration and tests, and scoped untracked or ignored
content. If that remains inconclusive, use `unverified` plus
`unresolved` / `defer`. Missing code or tests cannot by itself remove a
normative constraint, validation rule, route owner, or source pointer.

Use `remove-stale` only when direct baseline evidence disproves applicability,
adjacent ownership is checked, no normative basis remains, and removal is
authorized. Prefer `correct` for partial drift. Default to existing claims. A
missing rule may be `add-supported` only when the user explicitly includes
missing implemented guidance, direct current evidence supports it, and the
durable gate in `maintenance-application.md` passes. A repository scan alone
cannot expand scope; otherwise use `reject-new`. Never copy an implementation
inventory into AGENTS.

## Strict Multi-Agent Contract

Both modes require one coordinator and three independently assigned read-only
workers:

- `instruction-auditor`: atomize rules and inspect owners and inheritance;
- `implementation-auditor`: inspect implementation and test/runtime evidence;
- `provenance-verifier`: establish baseline state and provenance.

All participants receive and obey the loaded chain and remain read-only during
audit. The coordinator alone records authority, fixes scope and baseline,
dispatches, integrates the ledger, directly rechecks decisive evidence,
resolves routing, and validates. Worker audits remain independent.

Never decide by majority vote. The coordinator resolves worker conflict by
checking the owning source directly; otherwise the claim remains
`conflicting` and `unresolved` / `defer`. After the material-state recheck,
freeze the ledger, exact target paths, and authorized operations. Designate
exactly one non-coordinator writer; every other participant remains
non-writing. The writer performs only frozen AGENTS-system edits.

After writing, the coordinator directly reviews every frozen path, including
untracked or ignored paths, and verifies unrelated baseline preservation; a
tracked diff is insufficient. If a role was not independently run, decisive
evidence cannot be checked, or writer isolation is uncertain, safe-stop before
writing. Report the mode incomplete and completion and writes as `NOT-RUN`;
partial findings are not a completed preview.

## Handoff And Stops

Load `authorization-and-safety.md` for unclear provenance, shadowing, or
material rewrite/removal. After ledger freeze, use
`maintenance-application.md` for bounded patches to existing canonical owners.
Use `../migration-policy.md` as the primary terminal for broad reorganization,
cross-owner duplicate removal, or file moves; also load
`../routing-architecture.md` when route topology changes. No handoff expands
authorization.

Stop or remain read-only when target, baseline, authority, owner, or removal
scope is ambiguous; relevant live evidence is unavailable; an active
non-`AGENTS.md` source shadows the result; a requested write conflicts with the
active chain; or only separately authorized implementation work can resolve
the mismatch.

## Report Required

Report mode; target, scope, and baseline; material Git/ignored state; authority
versus evidence; workers, conflicts, and rechecks; each status and disposition;
writer scope or stop; terminal owner; changed files and bytes; direct
post-write review; validation; unresolved items; and activation timing.
