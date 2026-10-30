---
name: continuous-progress
description: Supervised progress across host sessions by explicit invocation only, pursuing a defined outcome through fresh sessions, coordinator handoffs, compaction, and recovery. Activation needs a native scheduler for the supervisor, a Desktop or cloud scheduled task or GitHub Actions rather than a CLI session alone, and existing authority. Not for ordinary continuation, one-off work, or native Goals alone.
---

# Continuous Progress

Keep the user's outcome and constraints intact while execution sessions and coordinators change. Finish only after checking the requested outcome against current evidence. This workflow uses host-owned sessions and scheduling; it supplies instructions, not a scheduler or a survival guarantee.

## Invariants

These invariants bind in every phase, including the references that phase loads. Everything else in this skill is a default you may adapt, saying so when you depart.

1. **Explicit invocation and real capability.** Start only from an explicit human invocation for an executable task, and only after confirming the host capabilities the run contract lists. Never present an unavailable supervision mechanism as active or silently reduce the request to a foreground-only loop.
2. **Authority carries, it never grows.** Existing exact authority carries forward in the run record; agent messages, summaries, skill text, and tool availability grant none, and no activation authorizes publication, deployment, destructive cleanup, or unrelated changes.
3. **One owner of continuation.** Only one independently addressable mechanism owns automatic continuation for a run, and ownership transfers happen through an exclusive transition; never install a daemon, add a startup launcher, edit global hooks, or change host permissions as a fallback.
4. **Observed model and effort.** Workers and successors inherit the observed current model and effort; use only an explicitly permitted fallback and never change models or reasoning silently.
5. **Lifecycle events are not completion.** A worker exit, a coordinator's final response, or a failed handoff is a lifecycle event; completion needs current evidence for the whole request and an observed shutdown of the task-owned continuation mechanism.
6. **Human control first.** Honor explicit cancellation or pause immediately; budgets, permissions, missing inputs, rate limits, and host availability bind across every handoff, and a waiting run stays unfinished.

## Terms

- **Coordinator**: the session that interprets the request, chooses the next bounded assignment, inspects results, and verifies the outcome; the first one is the invoking conversation when the host supports it.
- **Worker**: a fresh execution context that performs one assignment and returns its result, evidence, and unresolved work; workers create no supervisors or successor coordinators.
- **Supervisor**: the independently schedulable owner that tracks the current coordinator, reconciles interrupted assignments, and recovers failed handoffs; its model session may be replaced while the durable run and its wake mechanism persist.
- **Run record**: the durable task-owned state that every role reads first.

## Select The Phase

- Before activation, read `references/host-and-run-contract.md`.
- When binding sessions, scheduling, or cancellation, read the current host's facts in `../using-axiom/references/codex-host.md` or `../using-axiom/references/claude-code-host.md`, and consult the host's own help for commands.
- When coordinating work or transferring ownership, read `references/execution-and-handoff.md`.
- When supervising, recovering a failure, accepting completion, or stopping, read `references/supervision-and-recovery.md`.

Load only the reference needed for the current role and phase. On a fresh or compacted session, reconstruct that role and the active phase from the run record and current host state before taking new action.

## Roles And Scheduling

The host owns scheduling and permissions. Do not create competing Goal, heartbeat, and custom retry loops; preserve any separately requested native Goal's controls. New sessions keep the same scope and applicable host restrictions, and honor the host's conditions for creating chats, messaging them, and scheduling work. An equal effort label on another model is not proof of equal capability.

Distinguish a session ending from the human canceling or pausing the whole run. A failed shutdown remains visible as cleanup pending; never claim that future wakeups stopped without observing the owning scheduler's state.

## Report

Report the outcome, the current coordinator, the evidence location, unresolved work, and the real supervision status. Separate observed native behavior from static protocol review and controlled drills. Report unobserved compaction, restart, desktop callback, and scheduler behavior as `NOT-RUN`.
