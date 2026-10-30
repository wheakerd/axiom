# Supervision And Recovery

## Independent Wakeups

The supervision mechanism belongs to the run, not to a particular coordinator.
Each wake reads the durable record and current host state. A new supervision
model session can do that work; retaining one unlimited transcript is not a
requirement. Record which host supplies subsequent wakeups.

Use native events where supported and a documented bounded cadence for recovery
checks. A timer gives a recovery interval, not instantaneous event delivery.
Stay quiet when nothing actionable changed; notify on completion, failure,
meaningful recovery, or required user input.

Do not infer a dead coordinator solely from silence or a long-running tool.
Check host liveness, queued work, approval requests, and known operation state.
If the supervisor's own session ends while the run remains active, the external
wake mechanism must be able to invoke a replacement from the same record.

Register the wake mechanism against the run record, not the rotating coordinator, and verify its identifier, schedule, enabled state, and one actual wake before depending on recovery; a manual message cannot stand in for a scheduled wake. Its saved prompt states the run-record location, original scope, model and effort, control check, reconciliation rules, exclusive ownership mechanism, and exact shutdown operation. Every wake rereads that record and current host state, changes its own schedule or prompt only when the record calls for it, and never creates another supervisor or wake mechanism. Check for an existing task for this run before creating one and address that same task in every later operation, keeping its other settings when editing it.

## Recovery Decisions

| Observation | Required action |
| --- | --- |
| Worker still running | Preserve its handle; avoid duplicate dispatch. |
| Worker ended with a result | Route the evidence to the current coordinator for verification. |
| Coordinator ended while the goal is unfinished | Reconcile outstanding work and initiate a successor transfer. |
| Transfer failed before creation | Retry within existing authority after diagnosing the failure. |
| Creation outcome or acknowledgment is uncertain | Look up the known attempt and session before any retry. |
| Coordinator compacted | Require rereading of durable state and a verified coordinator transfer. |
| Permission, input, quota, or host availability is missing | Keep a named waiting condition; resume only when the condition changes. |
| Human paused or canceled the run | Honor that state; do not restart it as a failure recovery. |
| Goal appears complete | Run the completion procedure below. |

Preserve partial results and accepted evidence. A failed review generates a
specific follow-up assignment. Do not weaken the goal to make completion easier
or treat activity, repeated summaries, or increasing attempt counts as progress.

Back off repeated infrastructure failures and expose a stable blocker. Retain
the unfinished task and any verified wake mechanism. Never say automatic
recovery will occur when that mechanism is unavailable. Do not reset budgets,
change accounts, lower permissions, or evade user/system stops by rotating
sessions. Budget accounting remains cumulative across the run.

## Interrupted Effects

Before retrying an interrupted operation, check the system that owns its result.
An absent local receipt does not prove that a commit, upload, publication,
deployment, or other external operation failed. Reconcile uncertain outcomes
under that action's applicable authorization and retry rules. Resume only the
remaining work. Task progress does not create missing external-action authority.

## Completion And Shutdown

The coordinator checks every completion condition against current evidence and
records the result. The supervisor verifies that the receipt covers the whole
original request, the evidence is available, ownership is current, and no
outstanding operation could invalidate the outcome. It need not repeat an
unchanged conclusive check merely because a session changed.

Then transition to completion-pending-shutdown, disable or remove the exact
task-owned schedule through its supported host tool, and verify the scheduler
state. Ensure task-owned workers have ended or have been handled within the
existing authority. Mark completed only when the goal and shutdown checks hold.
On shutdown failure, retain cleanup-pending status and explain the remaining
active mechanism. Do not delete unrelated schedules, chats, branches, or files.

Verify shutdown through the surface that owns the mechanism, as the current host's facts describe; the model's own statement, a rendered card, or a green indicator is not a terminal-state observation.

Explicit cancellation ends task dispatch and its wake mechanism even when the
goal is unfinished. A human pause preserves resumable state without continuing
work. A worker or coordinator session ending by itself is a recovery event.

Persist human control before interruption. Cancel the exact active native turn
and drain its task-owned command handles; an interrupted model turn alone does
not prove its tools stopped. Verify command completion and reconcile partial
effects before marking canceled. Use the host's execution identity: a sandbox
PID may belong to a different PID namespace and must not be used as a host PID.
If a command cannot be stopped or observed, retain cleanup-pending and name it.
Disable the task-owned wake mechanism even while that cleanup remains pending.

## Evidence For This Experimental Capability

Keep these claims separate:

- Static protocol and metadata checks.
- Native CLI invocation, results, session IDs, and configured model/effort.
- Controlled coordinator-exit and handoff-recovery drills.
- Actual desktop callback and independent scheduler wakeups.
- Automatic pre-compaction transfer and post-compaction recovery.
- Duplicate-delivery handling, cancellation, and verified scheduler shutdown.

Record the host version with every claim. Distinguish a scheduled wake after the coordinator exited, recovery of a failed handoff, worker and successor completion with session IDs, actual compaction with a durable reread, cancellation of active work, and observed scheduler shutdown after both completion and cancellation.

A controlled drill proves only its observed path. Fresh instruction loading,
unattended scheduling, app restart, and another operating system remain
`NOT-RUN` without direct native evidence. Do not publish a general survival or
attention-quality claim based on one short arithmetic example.
