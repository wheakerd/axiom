---
name: clarify-intent
description: Clarify a user request when its wording supports materially different intended outcomes that current context cannot resolve. Offer the most plausible options and accept a custom answer before dependent work. Use on an explicit invocation or when using-axiom selects this ambiguity boundary; do not trigger on tentative wording alone, routine implementation choices, or facts available through inspection.
---

# Clarify Intent

Turn a material ambiguity into a user decision while preserving the requested
outcome, constraints, and existing authorization.

## Entry And Scope

- `using-axiom` may select this skill before choosing an action route when a
  request has multiple plausible meanings with different results, scope,
  targets, write surfaces, or authorization boundaries.
- Read the request and relevant conversation first. Inspect readily available
  task evidence when it can settle a factual gap without making the choice.
- Tentative phrases such as "maybe" do not alone require clarification. Keep
  working when the intended result is clear and an ordinary reversible
  implementation choice can be made within the user's constraints.
- Do not use a question to reopen a settled decision or request authorization
  already established for the same action. Full Access does not resolve an
  ambiguous intended result.

## Ask One Focused Question

1. Name the unresolved decision in one concise, self-contained question.
2. Offer two or three distinct, plausible interpretations grounded in the
   user's words and current context. State the outcome or tradeoff of each;
   do not invent unrelated requirements to fill the choices.
3. Let the user enter a custom answer. Use the host's native question tool
   when available in the current mode and follow its option and free-text
   conventions. If that tool is unavailable, ask in ordinary conversation.
4. Recommend an option only when known user priorities support it and the
   host's question format calls for a recommendation. A default, recommendation,
   silence, elapsed time, or "choose one" is not a submitted decision where
   alternatives change route ownership or action authority.
5. Wait before work that depends on a material choice. Continue authorized
   independent work when useful. Do not poll, repeat the same question, or
   manufacture additional interview rounds.

If there is only one plausible interpretation but a required value is missing,
ask for that value directly instead of manufacturing multiple choices. If the
host requires progress after an unanswered optional question, proceed only
with independent work or an assumption that stays inside established authority.

## Resume

Use the user's selected or custom answer to resolve only the open issue.
Preserve unaffected instructions and acceptance criteria. Return the clarified
request to `using-axiom` for normal route selection; the answer is not blanket
permission for edits, delegation, external actions, or persistent changes.

Do not run a downstream workflow merely because its option was displayed.
When the answer introduces a new material ambiguity, ask only the necessary
follow-up. Otherwise resume the task without restating a questionnaire.

## Acceptance Examples

| Request and context | Expected behavior |
| --- | --- |
| "Clean up the old records" without a target or retention meaning | Ask whether the user means archive, remove duplicates, or another intended cleanup; accept custom details before changes |
| "Maybe fix this typo" with one identified typo | Continue with the clear correction; tentative wording alone is not a trigger |
| "Use either deployment destination" with different authority boundaries | Ask one destination question; do not pick an action route first |
| User supplies a custom answer or corrects an option | Preserve that answer and reroute the resolved request |
| Full Access with an unresolved target | Ask; execution permissions do not identify the intended target |
