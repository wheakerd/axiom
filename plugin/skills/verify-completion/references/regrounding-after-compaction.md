# Regrounding After Compaction

## Purpose

Re-establish what is true about the task after context compaction, a fork, a
resume, or a handoff, before any report or mutation relies on the carried
summary.

## Apply When

- A verification request or a completion claim arrives after compaction, a
  fork, or a resume while work is unfinished.
- A handoff note, plan, or task record is the only source of the current
  state.
- The model notices that it cannot say where it observed a fact it is about to
  use.

## Direction

1. Read the carried summary as an index of what to check, not as a record of
   what is done. List its completion and progress claims.
2. Re-read the task's recorded artifacts where the host or repository keeps
   them: the task record, the plan, the changed files, `git status` and the
   diff, the remote state, and any run logs. Prefer the artifact over the
   summary when they disagree.
3. Re-anchor on the user's latest explicit decisions and corrections; a
   summary may carry a superseded plan. Settled decisions are not reopened.
4. Reselect routes from current direct evidence before any new mutation, as
   the startup gate requires. If the route or phase cannot be reconstructed,
   perform zero new mutations and ask.
5. Re-observe each criterion whose subject changed since its last observation;
   then continue with the ledger.

## Failure Patterns To Check

- Phantom completion: the summary reports a step as done, but the artifact is
  absent, unchanged, or half-written.
- Goal drift: the work continued toward a narrower or different goal than the
  user's request; compare the current plan with the original request.
- Stale success: a test or check passed before a later change to its subject.
- Lost constraint: a user constraint stated early is missing from the summary;
  scan the recorded artifacts and the earliest available turns for it.
- Borrowed authority: the summary implies permission for a mutation that the
  user never granted; authorization comes from the user's words, not from the
  summary.

## Report

State what the summary claimed, what the artifacts showed, each difference,
the user decisions re-anchored, the routes reselected, and whether any claim
was downgraded from done to open. Report `NOT-RUN` for artifacts that could not
be read.

## Prohibited

- Do not resume mutations on the strength of the summary alone.
- Do not rewrite the summary to match the claim; correct the claim.
- Do not treat a long or detailed summary as more reliable than a short one.
