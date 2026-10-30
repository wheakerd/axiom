---
name: clarify-intent
description: Clarify a request whose wording supports materially different outcomes that context cannot resolve, including alternatives offered across sentences or without the word either; offer the plausible options and accept a custom answer before dependent work. Use on an explicit invocation or when using-axiom selects this boundary; not for tentative wording, routine implementation choices, or inspectable facts.
---

# Clarify Intent

Turn one material ambiguity into a user decision while keeping the requested outcome, the constraints, and the existing authorization intact.

## Invariants

These invariants bind in every phase. Everything else in this skill is a default you may adapt, saying so when you depart.

1. **Need, not caution.** Ask only for a material decision the user left open; never ask for reassurance, as a defensive pause, or to reopen a settled decision.
2. **Facts first.** The request, the conversation, the user's environment, and read-only inspection settle factual gaps; a question settles only what they cannot.
3. **The user chooses.** When options differ in result, scope, target, write surface, or authorization, the user decides; a delegated choice follows the startup gate's rule, and a permission-bypass mode resolves nothing.
4. **Answers are narrow.** A selected or custom answer resolves only the open issue and grants no authority for edits, delegation, external actions, or persistent changes.
5. **Ask once, then wait.** Work that depends on the choice waits for the answer; do not poll, repeat the question, or add interview rounds.

## Terms

- **Material ambiguity**: wording that supports two or more outcomes with different results, scope, targets, write surfaces, or authorization boundaries.

## Entry

- `using-axiom` selects this skill before an action route when a request carries a material ambiguity; an explicit invocation selects it directly.
- Read the request and the relevant conversation first. Inspect readily available task evidence when it can settle a factual gap without making the choice.
- Tentative phrases such as "maybe" do not alone call for a question. Keep working when the intended result is clear and an ordinary reversible implementation choice fits the user's constraints.

## Ask

1. Ask one concise, self-contained question per unresolved decision. Ask independent decisions together, in one call when the host's question tool supports several; never split one decision into several questions.
2. Offer the plausible interpretations, usually two to four and within the host tool's limits, grounded in the user's words and the current context. State the outcome or trade-off of each; do not invent unrelated requirements to fill the list.
3. Let the user enter a custom answer. Use the host's native question tool when the current mode offers it and follow its option and free-text conventions; otherwise ask in ordinary conversation.
4. Recommend an option only when known user priorities support it and the host's question format calls for a recommendation. A default, a recommendation, silence, or elapsed time is not a decision.
5. Continue authorized independent work while waiting. If only one interpretation is plausible but a required value is missing, ask for that value directly.

If the host requires progress after an unanswered optional question, proceed only with independent work or with an assumption that stays inside established authority, and say so.

## Resume

Use the answer to resolve the open issue and preserve the unaffected instructions and acceptance criteria. Return the clarified request to `using-axiom` for normal route selection. Do not run a downstream workflow merely because its option was displayed. When the answer introduces a new material ambiguity, ask only the necessary follow-up; otherwise resume without restating a questionnaire.

## Acceptance Examples

| Request and context | Expected behavior |
| --- | --- |
| "Clean up the old records" without a target or retention meaning | Ask whether the user means archive, remove duplicates, or another cleanup; accept custom details before changes |
| "Maybe fix this typo" with one identified typo | Continue with the clear correction; tentative wording alone is not a trigger |
| The project's files settle a factual point, such as the build output folder | Use that fact, say so, and continue; do not ask for reassurance |
| "Export the report" with the destination and the file format both unresolved | Ask both independent decisions together, one question each, in one round |
| "Use either deployment destination" with different authority boundaries | Ask one destination question; do not pick an action route first |
| The user supplies a custom answer or corrects an option | Preserve that answer and reroute the resolved request |
| A permission-bypass mode with an unresolved target | Ask; execution permissions do not identify the intended target |
