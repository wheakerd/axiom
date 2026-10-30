---
name: task-planning
description: Revise an existing plan when the user asks to remove, replace, merge, reorder, or narrow its items, or create one on an explicit invocation; keep retained decisions, dependencies, and acceptance criteria consistent. A fresh plan request, scheduling, progress reports, execution, and planning another Axiom route owns stay host-native.
---

# Task Planning

Produce a self-contained plan that describes the work currently requested. The plan is the current agreement about the work: size its detail to the task and keep the user's preferred format when it remains useful.

## Invariants

These invariants bind in every phase, including the references that phase loads. Everything else in this skill is a default you may adapt, saying so when you depart.

1. **Planning is not execution.** A planning request authorizes planning; execution, scheduling, another host task, and saving a file need their own user intent, and a produced plan adds no confirmation gate.
2. **Requirements over suggestions.** User requirements and still-valid decisions survive a revision; an assistant suggestion in an earlier draft is not a requirement.
3. **The latest choice governs.** Apply the user's change at the scope they identify; a removal is not a permanent ban, and a later request may restore the item within current authority.
4. **Owners keep their rules.** A specialized Axiom workflow keeps its domain and authorization rules; this skill shapes presentation and consistency only, and a material workflow choice follows the startup gate's delegated-choice rule.
5. **Ask once, at the decision.** When an item, target, or dependency is materially ambiguous, ask one focused question and continue independent work; clear deletions need no reconfirmation.

## Select The Planning Phase

- Enter on a revision of an existing plan or an explicit invocation; a fresh request for a plan stays host-native, and a visible host plan-mode indicator is not required.
- Carry forward authority already granted.
- Select the owning Axiom workflow for specialized planning. When explicitly invoked to refine such a plan, apply this skill to its presentation and consistency without replacing that owner's rules.
- Read `references/scope-revisions.md` when a revision removes, replaces, or restores scope, or when dependency and constraint treatment is uncertain.

## Establish The Current Requirements

1. Read the latest request, the relevant existing plan, and enough task context to identify the requested outcome. Inspect source material only as needed to make the plan concrete.
2. Distinguish explicit constraints from assistant suggestions, assumptions, and historical discussion.
3. Apply the user's changes at the scope they identify.
4. Use the latest user choice for the affected scope.

## Build Or Revise The Plan

- For a new plan, describe the requested outcome, the necessary steps, the relevant dependencies, and observable acceptance criteria. Add assumptions only when they affect a decision. Scale the structure to the work; a small task may need only a few steps.
- For a revision, preserve unaffected goals, decisions, and useful detail. Apply the requested change and repair the affected structure instead of redesigning unrelated parts.
- Remove canceled or superseded scope wherever it contributes work: goals, steps, deliverables, dependencies, acceptance criteria, examples, and open questions. Renumber and repair references after the change.
- Write the remaining plan affirmatively around its current work. Do not carry canceled items into non-goals, exclusion lists, repeated disclaimers, or explanations of how they will not be implemented.
- Keep an explicit, still-effective constraint when it affects current work, such as local-only data handling or a fixed budget. Place it once where it informs implementation or acceptance. A user-requested scope statement and an applicable domain requirement remain valid reasons to state a boundary.
- If removing an item makes a retained goal infeasible, identify the concrete dependency and resolve the affected choice with the user. Do not silently restore removed work, promise an impossible result, or turn the canceled feature into a continuing task.

## Deliver The Current Plan

Return the updated plan as a complete artifact that reads without the edit history. If the user asks for only a changed section, a diff, or a change summary, provide that format and repair any affected references. Keep requested revision history separate from the plan body.

Before returning the plan, check that:

1. every task and acceptance criterion serves a current requirement or a necessary, supported dependency;
2. removed and superseded work has no remaining implementation obligation or incidental exclusion narrative;
3. retained goals, explicit constraints, and unaffected decisions are intact;
4. steps, dependencies, references, and acceptance criteria agree;
5. material uncertainty is visible at the affected decision, and the plan adds no approval round or execution authority.

These checks cover the plan artifact. They do not prove implementation, execution, or that a future host session will follow the skill.
