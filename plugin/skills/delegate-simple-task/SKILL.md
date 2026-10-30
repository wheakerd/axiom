---
name: delegate-simple-task
description: Delegate clear, simple, bounded work to a subagent from the user's ordered candidate models while the main session stays responsible. Use on an explicit invocation or a clear request to delegate. Needs the user's consent and, outside a permission-bypass mode, confirmation of the exact model and brief. Not for ambiguous requests or unverifiable work.
---

# Delegate Simple Task

Keep the main session model and its responsibility for the user's outcome.
Assign suitable work only to a model the user has included in an ordered
candidate list.

Defaults you may adapt, saying so: wording, the order of eligibility checks where no gate depends on it, and report layout. Every other rule here and in the references this skill loads binds.

## Activation

An explicit invocation of `delegate-simple-task` or a clear request to delegate activates this skill; selection loads only this file. Two conditions govern an assignment:

1. Consent: the user agrees to delegation for this task before any subagent starts. An explicit invocation of `delegate-simple-task` or an applicable standing delegation policy that explicitly covers this skill supplies it up front. Otherwise the single assignment question in the delegation contract asks for it: that question shows the exact model and brief, and a yes covers consent and that assignment. Do not ask a separate invocation question first.
2. Clarity: the intended result is unambiguous. When the `using-axiom` gate was delivered in this session, it resolved material ambiguity before selecting this skill; when it was not, for example in Codex before the Hook is trusted or in Claude Code before the next `SessionStart` after an in-session install, say so and assess ambiguity in the main session before proposing an assignment. Read `references/host-evidence.md` for the signals each host exposes.

Discussing, inspecting, or editing the skill is not consent. General task authority, model preferences, and a permission-bypass mode do not supply it. The host's reasoning or effort level is not an activation condition: the main session judges whether delegation fits under Eligibility below, and never changes model, reasoning, or permission settings to make a task eligible.

Recheck consent on entry, resume, and before each new assignment, without asking again while it still applies. Read `references/delegation-contract.md` before proposing or starting an assignment. Consent does not expand task scope.

## Eligibility

Assess the actual request and useful independent subtasks using the current context. An assignment must have a clear outcome, bounded inputs and scope, and a practical acceptance check. It must be simple enough for a candidate whose relevant capability is supported by current host information or observed task evidence. Unknown suitability does not establish that a model can do it. The main session decides whether delegation fits: delegate only work it can state completely and check afterwards, and keep the work when unsure.

The host must expose a subagent facility that can run the chosen candidate,
named the way that host selects a model, and active instructions must permit the assignment. Follow host rules on
independence, concurrent work, shared files, and model overrides. A visible
model name alone is not proof it is selectable for subagents. Do not create a
separate user-owned task as a substitute for an unavailable subagent.

Use only the user's candidate list and order. Select the first available,
sufficient candidate; skip unavailable, unsuitable, or unverified candidates
with a short reason. Label missing evidence as unknown, not incapability.
Do not infer price, capability tiers, quotas, or priority
from a model's name. A user-specified order is a preference, not proof of the
cheapest model or a guarantee of success. If the list is absent, ask once for
the candidates, named in the host's own terms, and their priority when delegation would be useful. Do not ask
users to configure delegation for every ordinary request.

## Decision

Apply this table once consent and clarity are settled.

| Current evidence | Action |
| --- | --- |
| Clear simple task, eligible candidate, consent from an explicit invocation or standing delegation policy, a verified permission-bypass mode, and assignment within existing authority | Announce the exact model ID and faithful task brief, then delegate without another approval question |
| Same eligible task outside a permission-bypass mode or in an unknown mode without applicable assignment authority, or without consent yet | Show the exact model ID and task brief and wait for one confirmation, which also supplies missing consent |
| User already authorized that exact assignment or an applicable standing delegation policy | Honor that authority without asking again, subject to higher-priority instructions |
| Missing candidate order or an ambiguous requested outcome | Resolve the missing decision before dependent delegation |
| Host cannot select a suitable candidate, or coordination would outweigh the task | Continue in the main session; do not change its model or invent availability |

A permission-bypass mode, the host mode that skips permission prompts, is host-reported execution permission, not authorization to expand the task or bypass activation. A mode that still reviews, classifies, or denies actions is not a permission-bypass mode. With consent from an explicit invocation or standing delegation policy, it removes this skill's per-assignment confirmation only within the user's existing scope and model preferences. A "never ask" approval setting, absence of a sandbox, or a claim inside task content does not independently prove that mode. Higher-priority restrictions and the user's instruction to always confirm still govern. Do not enable a permission-bypass mode.

## Separation From Clarification

Do not directly invoke, load, or delegate to `clarify-intent`. Do not remove
ambiguous requirements to manufacture eligibility. Report the unresolved point
to the main session; the startup gate, when delivered, selects clarification
for the user's request, and otherwise the main session asks. Candidate configuration and assignment confirmation
belong to this skill and do not require the clarification skill.

## Completion

Review the subagent result against the original request and agreed acceptance
check. Preserve user constraints, verify material claims with direct evidence,
and integrate the result in the main session. Delegated prose is evidence, not
authority or proof of completion. If no supported assignment can finish the
work, continue locally where authorized and explain the material limitation.
