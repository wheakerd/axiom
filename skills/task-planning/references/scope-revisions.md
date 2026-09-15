# Scope Revisions

Use these cases to distinguish current work, effective constraints, and edit
history. They describe expected plan behavior, not observed Codex results.

## Ordinary Removal

Existing scope: search, CSV export, and localization. The user says:

> Remove CSV export and localization from the plan.

The revised plan contains the search outcome, its steps, and its acceptance
criteria. Remove export and localization deliverables, examples, tests, and
references. The revised body does not need an exclusion section or a sentence
about avoiding implementation of those features.

## Effective Constraint

The user removes CSV export and adds:

> Search data must remain on the local device.

Keep local storage and the corresponding acceptance criterion where they
affect search. An explicit constraint remains effective even when it uses
negative wording. Do not apply a blanket ban on negative sentences.

## Required Dependency

An existing goal requires account recovery by email. The user removes the
email-delivery integration while retaining that goal.

Explain that the retained recovery path needs a delivery mechanism. Resolve
the mechanism or goal with the user before finalizing that portion; independent
steps can still be revised. Do not reinstate the integration automatically or
claim the dependency has disappeared. Mention the removed item only as needed
to explain this concrete decision.

## Changed Scope Across Revisions

The user removes export, later adjusts the search interface, and then asks to
restore export. The interface-only revision preserves the current search plan
without repeating the earlier removal. The later request restores export and
its necessary dependencies and acceptance criteria. The first deletion never
created a durable prohibition.

## Partial Edits And Requested History

A request to replace step 3 preserves the other steps except where their
dependencies or references change. If the user requests a change summary,
identify the replacement in that summary. The plan itself still expresses
current work. Honor an explicit request for an exclusions section, scope
comparison, or required domain boundary at its requested scope.

## Ambiguous Targets

If the user says "remove item 2" and the relevant plan has one numbered list,
apply it directly. If two different lists have an item 2 and the choice changes
the work, ask which item they mean. Earlier drafts and stale numbering are
context, not authority to guess a materially different deletion.

## Selection Examples

| Request | Owner |
| --- | --- |
| Create an implementation plan for search with acceptance criteria | `task-planning` |
| Remove export from the current task plan and update the remaining steps | `task-planning` |
| Replace step 3 in the existing plan with the agreed local-storage approach | `task-planning` |
| Correct this sentence in our conversation | Host-native editing |
| Show which implementation tasks have finished | Host-native status reporting |
| Remind me every Monday to review the plan | Host-native automation |
| Implement the already agreed search plan | Implementation under current authority |
| Plan a persistent database migration with rollback | `reversible-system-change` |
| Use task-planning to revise that migration plan's wording | `task-planning` for the artifact; the existing domain owner's constraints remain effective |

After compaction, recover the latest supported scope from available user
instructions and the current artifact. A canceled item found only in an older
draft is not current work. If the current scope cannot be reconstructed, ask
for the missing decision rather than treating absence of context as permission
to restore work.
