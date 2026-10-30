---
name: verify-completion
description: Verify a completion or progress claim against current direct evidence before it is made or accepted. Use when the user asks to verify or audit whether work is really complete, or when a claim rests on recalled or summarized facts, including after compaction. Advises before complying when evidence conflicts. Not for status questions, routine continuation, Axiom task review, or supervised progress.
---

# Verify Completion

Rebuild a completion, progress, or success claim from current direct evidence before it is made or accepted. Long tasks and repeated compaction let summaries stand in for evidence, and a summary that says "done" is a claim, not a fact. You decide what to check, how deep, and what to recommend.

## Invariants

These invariants bind in every phase, including the references that phase loads. Everything else in this skill is a default you may adapt, saying so when you depart.

1. **Observed facts only.** Only a fact observed in this session, and still current after the last mutation of its subject, supports `met`; recalled and summarized facts are claims to re-verify.
2. **Criteria from the source.** Freeze the acceptance criteria from the earliest available source and the user's latest explicit decisions, never from the latest summary alone; settled decisions are not reopened.
3. **No backfill.** Never fabricate, infer, or round up evidence; a check that cannot run is `NOT-RUN` with its reason, and its criterion stays `unverifiable`.
4. **Advice before compliance.** When evidence conflicts with the request, the plan, or safety, state the conflict, its consequence, and a recommendation before acting within the user's authority; an irreversible or unauthorized action stops instead.
5. **Verification observes.** It reads, runs tests and read-only commands, and queries state within existing permissions; it does not fix, commit, push, deploy, or delete, and a verified gap authorizes nothing.

## Terms

- **Observed**: produced in this session by a file read, command, test, or service response and still current after the last mutation of its subject.
- **Recalled**: remembered from earlier turns and not re-checked. **Summarized**: carried by a compaction summary, handoff note, plan, or task record.
- **Ledger**: one line per criterion with its check, observed result, verdict, and source; verdicts are `met`, `not met`, or `unverifiable`.

## Apply When

- The user asks to verify, audit, or double-check whether work is complete.
- A completion claim about to be made rests on recalled or summarized facts, including a claim carried by a compaction summary.

## Do Not Apply When

- The user asks for an ordinary status update or routine continuation, including continuation after compaction, a fork, or a resume. The startup gate owns reselecting routes at that moment; this skill waits for a verification request or a completion claim.
- The request is to review an identified Axiom task's routing, authorization, or evidence; that is `review-axiom-task`.
- The request is to supervise progress across sessions; that is `continuous-progress`.

## Direction

1. Freeze the criteria. Restate the user's original request and acceptance criteria from the earliest available source: the task record, the first turns, or the user's own words. Record the user's latest explicit decisions; they govern.
2. Re-ground. For each criterion, name the direct check that would prove it now (file contents, command output, test result, remote state, record entry) and run it. Scale depth to risk: a mutated surface needs a fresh observation, and an untouched one may keep an earlier observed fact with its timestamp.
3. Build the ledger as `references/evidence-ledger.md` describes.
4. Reconcile. Compare the ledger with the pending claim. Name every criterion the claim covered without an observed fact, and every observed result that contradicts the claim or the plan.
5. Advise before complying as `references/advisory-stance.md` describes.
6. Report. Give the ledger, the gaps, the remaining work, and the next action. Never write "done" for an unverifiable criterion, and never present an unrun check as passed.

When the request or claim arrives after compaction, a fork, or a handoff, follow `references/regrounding-after-compaction.md` before step 2: treat the summary as an index of what to check, re-read the recorded artifacts, and reselect routes from current evidence before any new mutation.

## Report

State the criteria source, the ledger, the fact class of every input the claim relied on, each `NOT-RUN` check, the advice given and whether the user's instruction was then followed, and the next action. Report in the user's language and keep ledger terms in English. Keep it short enough to read before the next step.

## References

- `references/evidence-ledger.md`
- `references/regrounding-after-compaction.md`
- `references/advisory-stance.md`
