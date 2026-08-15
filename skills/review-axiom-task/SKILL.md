---
name: review-axiom-task
description: Review the routing, scope, authorization, actions, evidence, stops, and outcome of the current or an explicitly identified Axiom-guided task. Use when the user explicitly asks what Axiom did, why it selected a route, or to audit the task. Do not use for ordinary summaries, code review, or executing or retrying a task.
---

# Review Axiom Task

Produce a compact retrospective from available evidence. This is not an
instrumented execution trace: Axiom supplies routing and workflow instructions,
while the host agent performs actions through its normal tools and authority.

## Scope Gate

- Identify the review target before inspecting history. Use the current task
  segment preceding the review request, or one task or thread the user
  explicitly identifies.
- Freeze the reviewed execution immediately before the triggering request.
  Record that request as review authority, and keep the review's own reads and
  reasoning outside the task being reviewed.
- Ask one concise question only when the target or review window is ambiguous
  in a way that would materially change the report.
- Start with the visible conversation. Inspect another task only when the user
  identified it and the host exposes a read-only task-inspection tool.
- Record the target, first and last reviewed turns or events, and whether older
  history in that window is unavailable. Do not treat compaction summaries as
  full transcripts.
- If no Axiom route applied, report the no-route result. Do not retrofit a route
  onto ordinary host-native work.

## Read-Only Boundary

- Treat the request as authority to review the visible target-task context,
  not as authority to edit, commit, push, deploy, install, migrate, delete,
  retry, clean up, change configuration, or access credentials.
- Use a fresh read-only observation only when it is necessary, already within
  the exact task target, and does not require separately unauthorized
  credential or sensitive-content access. Otherwise mark the evidence
  unavailable.
- Do not open unrelated files, tasks, repositories, remotes, accounts, or
  environments merely to make the report appear complete.
- Do not create a trace file, transcript, cache, telemetry event, background
  process, or persistent review record.
- Omit secrets, credential material, private endpoints, personal data, and raw
  sensitive content. Report only the material category and whether access was
  available or authorized.

## Evidence Contract

Classify material claims with one of these evidence states:

- `observed`: directly present in visible user or agent messages, tool results,
  or an authorized current read-only observation.
- `reconstructed`: inferred from a summary, current state, or incomplete
  sequence. State the basis and the uncertainty.
- `unavailable`: required history, tool output, host metadata, or owning-layer
  observation cannot be read within the review boundary.

Current state may verify that an outcome exists now. It does not by itself
prove who caused it, which instructions were active earlier, or whether the
past action was authorized. Treat current instructions and files as current
evidence unless the target history directly shows that they were active.

Never claim access to hidden reasoning or describe what the model privately
thought. Explain route choice and authorization only from observable requests,
active instructions recorded in the task, reported decisions, and tool
evidence. Keep command success separate from verification of the intended
outcome.

## Review Workflow

1. Restate the reviewed request, intended outcome, target, and review window.
2. Identify every selected Axiom route and its observable trigger. Separate a
   no-route continuation from a missing or uncertain route decision.
3. Separate Axiom workflow constraints from the host's instruction hierarchy
   and the user's explicit authority. Record actions as authorized, withheld,
   prohibited, ambiguous, or unknown only when the evidence supports that
   disposition.
4. Classify material actions as inspection, local mutation, external mutation,
   or stopped/not run. Do not infer an action from a plan or an available tool.
5. Map completion claims to the evidence that supports them. Record failed,
   unavailable, or skipped owning-layer checks and any stop caused by missing
   scope, authority, rollback, or evidence.
6. Produce the concise Markdown report below. Prefer material outcomes and
   summaries; include raw output only when a short excerpt is necessary to
   support a disputed conclusion.

## Report

Use this structure and omit empty detail:

```markdown
## Axiom task review

- Target:
- Review window:
- Coverage: complete | partial | unavailable

### Routing
- Selected route and observable reason, or no-route result

### Authorization
- Authorized actions
- Withheld, prohibited, ambiguous, or unknown actions

### Actions
- Inspections
- Local or external mutations
- Stopped, failed, skipped, or not-run actions

### Evidence
- Material evidence with observed, reconstructed, or unavailable state
- Command-success versus outcome-verification distinction

### Outcome
- verified | partially verified | stopped | failed | unverified
- Remaining gaps
```

Use `complete` only when the required review window is available. A concise
partial report is preferable to filling missing history with assumptions.
